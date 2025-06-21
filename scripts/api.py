"""
FastAPI app for OSM + Foursquare Smart Reconciler

- POST /merge/run {bbox}: Triggers pipeline, returns job id
- GET /poi: Returns merged POIs as GeoJSON
- GET /poi/{id}: Returns merged POI by ID
"""
import os
import duckdb
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from fastapi.responses import JSONResponse

DB_PATH = "smart.db"

app = FastAPI(title="OSM + Foursquare POI Reconciler")

class BBox(BaseModel):
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

from threading import Thread
from fastapi import BackgroundTasks
import time

jobs = {}

@app.post("/merge/run")
def run_pipeline_async(bbox: BBox):
    import subprocess
    import uuid
    bbox_str = f"{bbox.min_lon},{bbox.min_lat},{bbox.max_lon},{bbox.max_lat}"
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "pending", "stdout": None, "stderr": None}

    def run_pipeline_job(job_id, bbox_str):
        jobs[job_id]["status"] = "running"
        try:
            # Compute project root
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            run_py_path = os.path.join(project_root, "run.py")
            result = subprocess.run([
                "python", run_py_path, f"--bbox={bbox_str}"],
                cwd=project_root,
                capture_output=True, text=True, timeout=600
            )
            jobs[job_id]["stdout"] = result.stdout
            jobs[job_id]["stderr"] = result.stderr
            if result.returncode == 0:
                jobs[job_id]["status"] = "success"
            else:
                jobs[job_id]["status"] = "error"
        except Exception as e:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["stderr"] = str(e)

    thread = Thread(target=run_pipeline_job, args=(job_id, bbox_str))
    thread.start()
    return {"job_id": job_id, "status": "pending"}

@app.get("/merge/status/{job_id}")
def get_job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"error": "Job ID not found"})
    return {
        "job_id": job_id,
        "status": job["status"],
        "stdout": job["stdout"],
        "stderr": job["stderr"]
    }


@app.get("/poi")
def get_pois(limit: int = Query(100, le=1000)):
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="Database not found.")
    con = duckdb.connect(DB_PATH, read_only=True)
    # Join with fsq_features and osm_features to get coordinates and provenance
    try:
        df = con.execute('''
            SELECT c.*,
                   f.lat AS fsq_lat, f.lng AS fsq_lng,
                   o.lat AS osm_lat, o.lon AS osm_lon,
                   f.id AS fsq_id_real, o.id AS osm_id_real
            FROM candidate_pairs_scored c
            LEFT JOIN fsq_features f ON c.fsq_id = f.id
            LEFT JOIN osm_features o ON c.osm_id = o.id
            ORDER BY c.score DESC LIMIT ?
        ''', [limit]).fetchdf()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DuckDB error: {e}")
    features = []
    for _, row in df.iterrows():
        # Prefer FSQ coordinates if available, else OSM
        lat, lng, provenance = None, None, None
        if pd.notnull(row.get("fsq_lat")) and pd.notnull(row.get("fsq_lng")):
            lat, lng = row["fsq_lat"], row["fsq_lng"]
            provenance = "fsq"
        elif pd.notnull(row.get("osm_lat")) and pd.notnull(row.get("osm_lon")):
            lat, lng = row["osm_lat"], row["osm_lon"]
            provenance = "osm"
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lng, lat] if lat is not None and lng is not None else [None, None]
            },
            "properties": {
                **row.to_dict(),
                "provenance": provenance,
                "confidence": row.get("score")
            }
        }
        features.append(feature)
    return {"type": "FeatureCollection", "features": features}

@app.get("/poi/{poi_id}")
def get_poi_by_id(poi_id: str):
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="Database not found.")
    con = duckdb.connect(DB_PATH, read_only=True)
    # Try both fsq_id (string) and osm_id (int)
    queries = []
    params = []
    queries.append("fsq_id = ?")
    params.append(poi_id)
    try:
        osm_id_int = int(poi_id)
        queries.append("osm_id = ?")
        params.append(osm_id_int)
    except Exception:
        pass
    if not queries:
        raise HTTPException(status_code=404, detail=f"POI {poi_id} not found.")
    where_clause = " OR ".join(queries)
    try:
        # Join with fsq_features and osm_features for coordinates
        df = con.execute(f'''
            SELECT c.*,
                   f.lat AS fsq_lat, f.lng AS fsq_lng,
                   o.lat AS osm_lat, o.lon AS osm_lon,
                   f.id AS fsq_id_real, o.id AS osm_id_real
            FROM candidate_pairs_scored c
            LEFT JOIN fsq_features f ON c.fsq_id = f.id
            LEFT JOIN osm_features o ON c.osm_id = o.id
            WHERE {where_clause} LIMIT 1
        ''', params).fetchdf()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DuckDB error: {e}")
    if df.empty:
        raise HTTPException(status_code=404, detail=f"POI {poi_id} not found.")
    row = df.iloc[0]
    lat, lng, provenance = None, None, None
    if pd.notnull(row.get("fsq_lat")) and pd.notnull(row.get("fsq_lng")):
        lat, lng = row["fsq_lat"], row["fsq_lng"]
        provenance = "fsq"
    elif pd.notnull(row.get("osm_lat")) and pd.notnull(row.get("osm_lon")):
        lat, lng = row["osm_lat"], row["osm_lon"]
        provenance = "osm"
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [lng, lat] if lat is not None and lng is not None else [None, None]
        },
        "properties": {
            **row.to_dict(),
            "provenance": provenance,
            "confidence": row.get("score")
        }
    }
    return feature

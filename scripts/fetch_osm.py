#!/usr/bin/env python3
"""
Query OSM Overpass API for a bounding box and save results as Parquet.
- Usage: python scripts/fetch_osm.py --bbox "min_lon,min_lat,max_lon,max_lat" \
    --output data/raw/osm_bbox.parquet
"""
import argparse
import json
import os
import requests
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

def overpass_query(bbox):
    # bbox = [min_lon, min_lat, max_lon, max_lat]
    query = f"""
    [out:json][timeout:60];
    (
      node["amenity"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});
      way["amenity"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});
      relation["amenity"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});
    );
    out center;
    """
    resp = requests.post(
        "https://overpass-api.de/api/interpreter",
        data={"data": query.strip()}
    )
    resp.raise_for_status()
    return resp.json()

def osm_json_to_df(osm_json):
    rows = []
    for el in osm_json.get("elements", []):
        tags = el.get("tags", {})
        rows.append({
            "id": el["id"],
            "type": el["type"],
            "lat": el.get("lat") or el.get("center", {}).get("lat"),
            "lon": el.get("lon") or el.get("center", {}).get("lon"),
            "name": tags.get("name"),
            "amenity": tags.get("amenity"),
            "address": tags.get("addr:full"),
            "tags": json.dumps(tags),  # <-- serialized here
        })
    return pd.DataFrame(rows)

def main():
    default_bbox = "-74.020325,40.700292,-73.907000,40.877483"  # Manhattan
    p = argparse.ArgumentParser(
        description="Fetch OSM amenities for a bounding box and save as Parquet."
    )
    p.add_argument(
        '--bbox', type=str, default=default_bbox,
        help='min_lon,min_lat,max_lon,max_lat (defaults to Manhattan)',
        metavar='BBOX'
    )
    p.add_argument(
        '--output', type=str, required=True,
        help='Output Parquet file path'
    )
    args = p.parse_args()

    try:
        bbox_str = args.bbox.strip()
        bbox = [float(x) for x in bbox_str.split(",")]
        if len(bbox) != 4:
            raise ValueError
        print(f"[DEBUG] Using bbox: {bbox}")
    except Exception as e:
        raise SystemExit(f"Invalid --bbox; expected: min_lon,min_lat,max_lon,max_lat. Error: {e}")

    osm_json = overpass_query(bbox)
    df = osm_json_to_df(osm_json)

    # Write to Parquet
    out_dir = os.path.dirname(args.output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    table = pa.Table.from_pandas(df)
    pq.write_table(table, args.output)
    print(f"Saved {len(df)} OSM POIs to {args.output}")

if __name__ == "__main__":
    main()

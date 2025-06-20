#!/usr/bin/env python3
"""
Query OSM Overpass API for a bounding box and save results as Parquet.
- Usage: python scripts/fetch_osm.py --bbox "min_lon,min_lat,max_lon,max_lat" --output data/raw/osm_bbox.parquet
"""
import argparse
import requests
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import os

def overpass_query(bbox):
    # Example: fetch all amenities in bbox
    query = f"""
    [out:json][timeout:60];
    (
      node["amenity"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});
      way["amenity"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});
      relation["amenity"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});
    );
    out center;
    """
    url = "https://overpass-api.de/api/interpreter"
    resp = requests.post(url, data={"data": query})
    resp.raise_for_status()
    return resp.json()

def osm_json_to_df(osm_json):
    elements = osm_json["elements"]
    rows = []
    for el in elements:
        tags = el.get("tags", {})
        row = {
            "id": el["id"],
            "type": el["type"],
            "lat": el.get("lat", el.get("center", {}).get("lat")),
            "lon": el.get("lon", el.get("center", {}).get("lon")),
            "name": tags.get("name"),
            "amenity": tags.get("amenity"),
            "address": tags.get("addr:full"),
            "tags": tags
        }
        rows.append(row)
    return pd.DataFrame(rows)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bbox', type=str, required=True, help='min_lon,min_lat,max_lon,max_lat')
    parser.add_argument('--output', type=str, required=True)
    args = parser.parse_args()
    bbox = [float(x) for x in args.bbox.split(",")]
    osm_json = overpass_query(bbox)
    df = osm_json_to_df(osm_json)
    table = pa.Table.from_pandas(df)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    pq.write_table(table, args.output)
    print(f"Saved {len(df)} OSM POIs to {args.output}")

if __name__ == "__main__":
    main()

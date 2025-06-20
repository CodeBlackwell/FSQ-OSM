#!/usr/bin/env python3
"""
Fetch Foursquare OS Places CSV for a specified bounding box and save as Parquet.
- Customize the FSQ_CSV_URL and columns as needed.
- Usage: python scripts/fetch_fsq.py --bbox "min_lon,min_lat,max_lon,max_lat" --output data/raw/fsq_bbox.parquet
"""
import argparse
#!/usr/bin/env python3
"""
Fetch Foursquare Places data for a specified bounding box using the Foursquare Places API and save as Parquet.
- Loads API credentials from .env (FSQ_CLIENT_ID, FSQ_CLIENT_SECRET)
- Usage: python scripts/fetch_fsq.py --bbox "min_lon,min_lat,max_lon,max_lat" --output data/raw/fsq_bbox.parquet
"""
import argparse
import os
import requests
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from dotenv import load_dotenv

FSQ_API_URL = "https://places-api.foursquare.com/places/search"
FSQ_COLUMNS = [
    "fsq_id", "name", "geocodes", "location", "categories", "website", "tel"
]

# Helper to flatten FSQ API response to DataFrame
def flatten_fsq_results(results):
    rows = []
    for place in results:
        row = {
            "id": place.get("fsq_id"),
            "name": place.get("name"),
            "lat": place.get("geocodes", {}).get("main", {}).get("latitude"),
            "lng": place.get("geocodes", {}).get("main", {}).get("longitude"),
            "formatted_address": ", ".join(place.get("location", {}).get("formatted_address", [])) if isinstance(place.get("location", {}).get("formatted_address", None), list) else place.get("location", {}).get("formatted_address"),
            "categories": ", ".join([cat["name"] for cat in place.get("categories", [])]),
            "website": place.get("website"),
            "phone": place.get("tel"),
        }
        rows.append(row)
    return pd.DataFrame(rows)

def fetch_fsq_api(api_key, bbox, limit=50):
    min_lon, min_lat, max_lon, max_lat = bbox
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}",
        "X-Places-Api-Version": "2025-06-17",
    }
    params = {
        "ne": f"{max_lat},{max_lon}",  # northeast: lat,lon
        "sw": f"{min_lat},{min_lon}",  # southwest: lat,lon
        "limit": limit,
    }
    results = []
    cursor = None
    while True:
        if cursor:
            params["cursor"] = cursor
        resp = requests.get(FSQ_API_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        results.extend(data.get("results", []))
        cursor = data.get("context", {}).get("next_cursor")
        if not cursor:
            break
    return flatten_fsq_results(results)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bbox', type=str, required=True, help='min_lon,min_lat,max_lon,max_lat')
    parser.add_argument('--output', type=str, required=True)
    args = parser.parse_args()
    bbox = [float(x) for x in args.bbox.split(",")]

    load_dotenv()
    api_key = os.getenv("FSQ_API_KEY")
    if not api_key:
        raise RuntimeError("FSQ_API_KEY must be set in .env")

    df = fetch_fsq_api(api_key, bbox)
    table = pa.Table.from_pandas(df)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    pq.write_table(table, args.output)
    print(f"Saved {len(df)} FSQ POIs to {args.output}")

if __name__ == "__main__":
    main()

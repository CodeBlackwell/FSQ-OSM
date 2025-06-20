#!/usr/bin/env python3
"""
Fetch Foursquare Places data for a specified bounding box using the Foursquare Places API and save as Parquet.
- Loads API key from .env (FSQ_API_KEY)
- Usage: python scripts/fetch_fsq.py --bbox "min_lon,min_lat,max_lon,max_lat" --output data/raw/fsq_bbox.parquet
"""
import argparse
import os
import sys
import requests
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from dotenv import load_dotenv

# Correct Foursquare Places API v3 endpoint - see https://docs.foursquare.com/fsq-developers-places/reference/migration-guide
FSQ_API_URL = "https://places-api.foursquare.com/places/search"

# Helper to flatten FSQ API response to DataFrame
def flatten_fsq_results(results):
    rows = []
    for place in results:
        row = {
            "id": place.get("fsq_id"),
            "name": place.get("name"),
            "lat": place.get("geocodes", {}).get("main", {}).get("latitude"),
            "lng": place.get("geocodes", {}).get("main", {}).get("longitude"),
            # Ensure formatted_address is a string
            "formatted_address": place.get("location", {}).get("formatted_address", ""),
            "categories": ", ".join([cat.get("name", "") for cat in place.get("categories", [])]),
            "website": place.get("website"),
            "phone": place.get("tel"),
        }
        rows.append(row)
    return pd.DataFrame(rows)

# Fetch all pages of results using cursor-based pagination
def fetch_fsq_api(api_key, bbox, limit=50):
    min_lon, min_lat, max_lon, max_lat = bbox
    headers = {
        "Accept": "application/json",
        # For v3 API, use API key directly in Authorization header
        "Authorization": f"Bearer {api_key}",
        # Optional: specify version header
        "X-Places-Api-Version": "2025-06-17",
    }
    params = {
        "ne": f"{max_lat},{max_lon}",  # northeast corner (lat,lon)
        "sw": f"{min_lat},{min_lon}",  # southwest corner (lat,lon)
        "limit": limit,
    }
    results = []
    cursor = None

    while True:
        if cursor:
            params["cursor"] = cursor
        resp = requests.get(FSQ_API_URL, headers=headers, params=params)
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            sys.exit(f"API request failed: {e}\nResponse: {resp.text}")

        data = resp.json()
        results.extend(data.get("results", []))
        cursor = data.get("context", {}).get("next_cursor")
        if not cursor:
            break

    return flatten_fsq_results(results)


def main():
    parser = argparse.ArgumentParser(description="Fetch Foursquare Places for a bounding box and save as Parquet.")
    parser.add_argument(
        '--bbox', type=str, required=True,
        help='Bounding box as "min_lon,min_lat,max_lon,max_lat"'
    )
    parser.add_argument(
        '--output', type=str, required=True,
        help='Output Parquet file path'
    )
    args = parser.parse_args()

    # Parse bbox
    try:
        bbox = [float(x) for x in args.bbox.split(",")]
        if len(bbox) != 4:
            raise ValueError
    except ValueError:
        sys.exit("Invalid --bbox format. Expected: min_lon,min_lat,max_lon,max_lat")

    # Load API key
    load_dotenv()
    api_key = os.getenv("FSQ_API_KEY")
    if not api_key:
        sys.exit("Error: FSQ_API_KEY must be set in your .env file")
    if not api_key.strip():
        sys.exit("Error: FSQ_API_KEY is empty in .env file")
    print("[INFO] Foursquare API key loaded.")

    # Fetch data
    df = fetch_fsq_api(api_key, bbox)
    if df.empty:
        print("No places found for the given bounding box.")
    else:
        table = pa.Table.from_pandas(df, preserve_index=False)
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        pq.write_table(table, args.output)
        print(f"Saved {len(df)} FSQ POIs to {args.output}")

if __name__ == "__main__":
    main()

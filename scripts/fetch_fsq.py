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
import pandas as pd

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
def fetch_fsq_api(api_key, bbox, query="food", limit=50, verbose=False):
    """
    Fetch Foursquare Places using the v3 API with bbox, query, and pagination.
    bbox: [min_lon, min_lat, max_lon, max_lat]
    query: search term (default: 'food')
    limit: number of results per page (max 50)
    verbose: print raw API response (first page)
    """
    # FSQ_API_URL = "https://api.foursquare.com/v3/places/search"
    min_lon, min_lat, max_lon, max_lat = bbox
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}",
        "X-Places-Api-Version": "2025-06-17",
    }
    params = {
        "sw": f"{min_lat},{min_lon}",
        "ne": f"{max_lat},{max_lon}",
        "query": query,
        "limit": limit
    }
    results = []
    cursor = None
    page = 0
    while True:
        if cursor:
            params["cursor"] = cursor
        else:
            params.pop("cursor", None)
        resp = requests.get(FSQ_API_URL, headers=headers, params=params)
        if verbose and page == 0:
            print("[VERBOSE] Raw FSQ API response (first page):")
            print(resp.text)
        if resp.status_code != 200:
            print(f"[ERROR] FSQ API returned {resp.status_code}: {resp.text}")
            break
        data = resp.json()
        results.extend(data.get("results", []))
        cursor = data.get("context", {}).get("next_cursor")
        page += 1
        if not cursor or len(results) >= limit:
            break
    return flatten_fsq_results(results)


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Fetch Foursquare Places for a bounding box and save as Parquet.")
    parser.add_argument(
        '--bbox', type=str, required=True,
        help='Bounding box as "min_lon,min_lat,max_lon,max_lat"'
    )
    parser.add_argument(
        '--output', type=str, required=True,
        help='Output Parquet file path'
    )
    parser.add_argument(
        '--query', type=str, default='food',
        help='Search query for FSQ API (default: "food")'
    )
    parser.add_argument(
        '--verbose', action='store_true',
        help='Print verbose output for debugging.'
    )
    args = parser.parse_args()

    # Fast path: use local CSV if present
    local_csv = "data/ny_places_jan_2022.csv"
    if os.path.exists(local_csv):
        print(f"[INFO] Found {local_csv}. Using this file instead of Foursquare API.")
        df = pd.read_csv(local_csv)
        # Map columns to expected schema
        df_out = pd.DataFrame()
        df_out["id"] = df["fsq_id"]
        df_out["name"] = df["name"]
        df_out["lat"] = df["latitude"]
        df_out["lng"] = df["longitude"]
        df_out["formatted_address"] = df["address"].fillna("")
        # Flatten fsq_category_labels (which is a stringified list of lists)
        def flatten_cats(val):
            try:
                # Remove brackets and quotes, then join
                import ast
                cats = ast.literal_eval(val)
                if isinstance(cats, list):
                    # If nested, flatten
                    if len(cats) > 0 and isinstance(cats[0], list):
                        cats = [item for sublist in cats for item in sublist]
                    return ", ".join(str(x) for x in cats)
                return str(val)
            except Exception:
                return str(val)
        df_out["categories"] = df["fsq_category_labels"].apply(flatten_cats)
        df_out["website"] = df["website"].fillna("")
        df_out["phone"] = df["tel"].fillna("")
        # Save only expected columns
        needed_cols = ["id", "name", "lat", "lng", "formatted_address", "categories", "website", "phone"]
        df_out = df_out[needed_cols]
        df_out.to_parquet(args.output, index=False)
        print(f"[INFO] Saved {args.output} from {local_csv} (columns mapped). Exiting.")
        sys.exit(0)

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
    df = fetch_fsq_api(api_key, bbox, query=args.query, verbose=args.verbose)
    if args.verbose:
        print(f"[VERBOSE] DataFrame shape: {df.shape}")
        print(f"[VERBOSE] DataFrame columns: {list(df.columns)}")
        print(f"[VERBOSE] DataFrame head:\n{df.head()}\n")
    if df.empty:
        print("No places found for the given bounding box and query.")
    else:
        table = pa.Table.from_pandas(df, preserve_index=False)
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        pq.write_table(table, args.output)
        print(f"Saved {len(df)} FSQ POIs to {args.output}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
End-to-end runner for OSM + Foursquare POI reconciliation demo.
- Fetches raw data (if not present)
- Loads data into DuckDB
- Runs feature engineering and candidate generation
- Prints summary stats and next steps
"""

import os
import subprocess
import sys
import argparse
import duckdb


# Step 1: Fetch Foursquare and OSM data if not present
RAW_DIR = "data/raw"
FSQ_PARQUET = os.path.join(RAW_DIR, "fsq_merged.parquet")
OSM_PARQUET = os.path.join(RAW_DIR, "osm_merged.parquet")

fetch_scripts = [
    ("Foursquare", "scripts/fetch_fsq.py", FSQ_PARQUET),
    ("OSM", "scripts/fetch_osm.py", OSM_PARQUET),
]

import pandas as pd

def ensure_data(verbose=False):
    os.makedirs(RAW_DIR, exist_ok=True)
    # Use correct bbox order for OSM (min_lon,min_lat,max_lon,max_lat)
    # Manhattan: -74.020325,40.700292,-73.907000,40.877483
    default_bbox = "-74.020325,40.700292,-73.907000,40.877483"  # Manhattan, NYC
    region_desc = "Manhattan, NYC"
    print(f"[INFO] Default bounding box points to {region_desc}.")
    print("  Format: min_lon,min_lat,max_lon,max_lat")
    print("[INFO] You can enable verbose mode for fetch scripts with --verbose.")
    user_bbox = input(f"Enter bounding box (blank for default: {default_bbox}): ").strip()
    bbox = user_bbox if user_bbox else default_bbox
    for label, script, parquet in fetch_scripts:
        if not os.path.exists(parquet):
            print(f"[INFO] {parquet} not found. Running {script}...")
            if script == "scripts/fetch_osm.py":
                cmd = [sys.executable, script, f"--bbox={bbox}", "--output", parquet]
            else:
                cmd = [sys.executable, script, "--bbox", bbox, "--output", parquet]
            if verbose:
                cmd.append("--verbose")
                print(f"[VERBOSE] Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True)
        else:
            # Check if Parquet file is non-empty
            try:
                df = pd.read_parquet(parquet)
                if df.empty:
                    print(f"[WARNING] {parquet} exists but is empty. Deleting and refetching with {script}...")
                    os.remove(parquet)
                    if script == "scripts/fetch_osm.py":
                        cmd = [sys.executable, script, f"--bbox={bbox}", "--output", parquet]
                    else:
                        cmd = [sys.executable, script, "--bbox", bbox, "--output", parquet]
                    if verbose:
                        cmd.append("--verbose")
                        print(f"[VERBOSE] Running: {' '.join(cmd)}")
                    result = subprocess.run(cmd, check=True)
                    # Re-read after fetch
                    if not os.path.exists(parquet):
                        print(f"[ERROR] {parquet} was not created by {script}. Exiting.")
                        exit(1)
                    df = pd.read_parquet(parquet)
                    if df.empty:
                        print(f"[ERROR] {label} fetch resulted in 0 POIs after refetch. Try a different bounding box. Exiting.")
                        exit(1)
                else:
                    print(f"[INFO] {parquet} found and contains {len(df)} records. Skipping {script}.")
            except Exception as e:
                print(f"[WARNING] Failed to read {parquet}: {e}. Deleting and refetching with {script}...")
                os.remove(parquet)
                if script == "scripts/fetch_osm.py":
                    cmd = [sys.executable, script, f"--bbox={bbox}", "--output", parquet]
                else:
                    cmd = [sys.executable, script, "--bbox", bbox, "--output", parquet]
                if verbose:
                    cmd.append("--verbose")
                    print(f"[VERBOSE] Running: {' '.join(cmd)}")
                result = subprocess.run(cmd, check=True)
                if not os.path.exists(parquet):
                    print(f"[ERROR] {parquet} was not created by {script}. Exiting.")
                    exit(1)
                df = pd.read_parquet(parquet)
                if df.empty:
                    print(f"[ERROR] {label} fetch resulted in 0 POIs after refetch. Try a different bounding box. Exiting.")
                    exit(1)
                print(f"[INFO] {parquet} refetched and contains {len(df)} records.")

# Step 2: Load data into DuckDB as fsq_raw and osm_raw
DB_PATH = "smart.db"
def load_to_duckdb():
    try:
        con = duckdb.connect(DB_PATH)
        if not con.execute("SELECT * FROM information_schema.tables WHERE table_name='fsq_raw'").fetchone():
            print("[INFO] Creating fsq_raw table...")
            con.execute(f"CREATE TABLE fsq_raw AS SELECT * FROM read_parquet('{FSQ_PARQUET}')")
        else:
            print("[INFO] fsq_raw table already exists.")
        if not con.execute("SELECT * FROM information_schema.tables WHERE table_name='osm_raw'").fetchone():
            print("[INFO] Creating osm_raw table...")
            con.execute(f"CREATE TABLE osm_raw AS SELECT * FROM read_parquet('{OSM_PARQUET}')")
        else:
            print("[INFO] osm_raw table already exists.")
        # Add indexes
        con.execute("CREATE INDEX IF NOT EXISTS fsq_id_idx ON fsq_raw(id)")
        con.execute("CREATE INDEX IF NOT EXISTS osm_id_idx ON osm_raw(id)")
        con.execute("CREATE INDEX IF NOT EXISTS fsq_lat_idx ON fsq_raw(lat)")
        con.execute("CREATE INDEX IF NOT EXISTS fsq_lng_idx ON fsq_raw(lng)")
        con.execute("CREATE INDEX IF NOT EXISTS osm_lat_idx ON osm_raw(lat)")
        con.execute("CREATE INDEX IF NOT EXISTS osm_lon_idx ON osm_raw(lon)")
        print("[INFO] DuckDB raw tables ready.")
    except Exception as e:
        print(f"[ERROR] Failed to load data into DuckDB: {e}. This usually means the Parquet file is empty or malformed. Exiting.")
        exit(1)

# Step 3: Run feature engineering pipeline

def run_feature_engineering():
    print("[INFO] Running feature engineering and candidate generation...")
    result = subprocess.run([sys.executable, "scripts/feature_engineering.py"], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the OSM+FSQ pipeline end-to-end.")
    parser.add_argument('--verbose', action='store_true', help='Enable verbose mode for fetch scripts.')
    args = parser.parse_args()
    ensure_data(verbose=args.verbose)
    load_to_duckdb()
    run_feature_engineering()
    print("\n[INFO] Pipeline complete!")
    print("[INFO] Next: Inspect candidate_pairs table or launch the API server.")

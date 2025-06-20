#!/usr/bin/env python3
"""
Ingest Foursquare and OSM POI data into DuckDB.
- Creates smart.db
- Loads fsq_raw and osm_raw tables from Parquet
- Adds Bayer index on id and spatial index on (lat, lng)
"""
import duckdb
import os

# Paths
FSQ_PARQUET = "data/raw/fsq_times_square.parquet"
OSM_PARQUET = "data/raw/osm_times_square.parquet"
DB_PATH = "smart.db"

con = duckdb.connect(DB_PATH)

# Ingest Foursquare data
df_fsq = con.execute(f"SELECT * FROM parquet_scan('{FSQ_PARQUET}')").fetchdf()
con.execute("DROP TABLE IF EXISTS fsq_raw")
con.execute("CREATE TABLE fsq_raw AS SELECT * FROM parquet_scan(?)", (FSQ_PARQUET,))
con.execute("CREATE INDEX fsq_id_idx ON fsq_raw(id)")
con.execute("CREATE INDEX fsq_latlng_idx ON fsq_raw(lat, lng)")

# Ingest OSM data
df_osm = con.execute(f"SELECT * FROM parquet_scan('{OSM_PARQUET}')").fetchdf()
con.execute("DROP TABLE IF EXISTS osm_raw")
con.execute("CREATE TABLE osm_raw AS SELECT * FROM parquet_scan(?)", (OSM_PARQUET,))
con.execute("CREATE INDEX osm_id_idx ON osm_raw(id)")
con.execute("CREATE INDEX osm_latlng_idx ON osm_raw(lat, lon)")

print("DuckDB ingestion complete. Tables: fsq_raw, osm_raw.")

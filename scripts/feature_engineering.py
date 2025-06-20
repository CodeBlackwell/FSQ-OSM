#!/usr/bin/env python3
"""
Feature engineering for POI reconciliation.
- Loads POIs from DuckDB tables (fsq_raw, osm_raw)
- Computes core features: id, name, embedding, name_trigram, category_canon
- Stores additional features in a JSON column (extra_features)
- Writes results to fsq_features and osm_features in DuckDB

"""

import duckdb
import pandas as pd
import json
from sentence_transformers import SentenceTransformer
import re

import os
from dotenv import load_dotenv
from math import radians, sin, cos, sqrt, atan2


load_dotenv()
token = os.getenv("HUGGINGFACE_HUB_READER_TOKEN")
if token:
    os.environ["HUGGINGFACE_HUB_TOKEN"] = token

DB_PATH = "smart.db"


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Compute the great-circle distance between two points (lat/lon) in kilometers.
    """
    R = 6371.0  # Earth radius in kilometers
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def extract_trigrams(text):
    # Lowercase, remove all non-alphanumeric characters (including spaces)
    text = re.sub(r'[^a-z0-9]+', '', text.lower())
    if len(text) < 3:
        return []
    trigrams = [text[i:i+3] for i in range(len(text)-2)]
    return sorted(set(trigrams))

def canonicalize_category(raw_cat, source):
    """
    Map raw category/amenity to a canonical category string for matching.
    """
    # Lowercase and simple normalization
    if not isinstance(raw_cat, str):
        return None
    cat = raw_cat.lower().strip()
    # Simple mapping for demo (expand as needed)
    mapping = {
        'restaurant': ['restaurant', 'food', 'eatery', 'diner', 'bistro'],
        'cafe': ['cafe', 'coffee', 'coffee shop'],
        'bar': ['bar', 'pub', 'tavern'],
        'bank': ['bank', 'atm'],
        'hotel': ['hotel', 'motel', 'hostel', 'inn'],
        'store': ['store', 'shop', 'retail', 'convenience', 'supermarket', 'market', 'grocery'],
        'school': ['school', 'college', 'university', 'academy'],
        'park': ['park', 'playground', 'garden'],
        'pharmacy': ['pharmacy', 'drugstore'],
        'hospital': ['hospital', 'clinic', 'medical'],
        'parking': ['parking', 'car park', 'garage'],
        'museum': ['museum', 'gallery'],
        'church': ['church', 'temple', 'mosque', 'synagogue'],
        'transport': ['station', 'bus', 'train', 'subway', 'metro', 'tram', 'airport'],
    }
    for canon, keywords in mapping.items():
        for kw in keywords:
            if kw in cat:
                return canon
    return cat  # fallback: use as-is

def fuzzy_category_match(cat1, cat2):
    """
    Returns 1 if canonical categories match, else 0. (Extend for fuzzy/partial match if needed)
    """
    if not cat1 or not cat2:
        return 0
    return int(cat1 == cat2)

def normalize_phone(phone):
    """Normalize phone numbers to digits only (for matching)."""
    if not isinstance(phone, str):
        return None
    digits = re.sub(r'\D', '', phone)
    return digits if digits else None

def normalize_website(url):
    """Normalize website URLs by stripping protocol and www."""
    if not isinstance(url, str):
        return None
    url = url.lower().strip()
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^www\.', '', url)
    url = url.rstrip('/')
    return url if url else None

def phone_website_match(f_phone, o_phone, f_web, o_web):
    """
    Returns 1 if either phone or website matches (normalized, non-empty), else 0.
    """
    fp = normalize_phone(f_phone)
    op = normalize_phone(o_phone)
    fw = normalize_website(f_web)
    ow = normalize_website(o_web)
    if fp and op and fp == op:
        return 1
    if fw and ow and fw == ow:
        return 1
    return 0

def compute_core_features(df, source):
    # Load the embedding model only once
    model = SentenceTransformer('all-MiniLM-L6-v2')
    # Compute embeddings for all names
    names = df["name"].fillna("").tolist()
    embeddings = model.encode(names, show_progress_bar=True)
    df["embedding"] = [emb.tolist() for emb in embeddings]
    # Compute sorted list of trigrams for each name
    df["name_trigram"] = df["name"].fillna("").apply(extract_trigrams)
    # Canonicalize categories
    if source == "fsq":
        # Foursquare: column is 'categories' (comma-separated)
        df["category_canon"] = df["categories"].fillna("").apply(lambda x: canonicalize_category(x.split(",")[0] if x else None, source))
        df["phone_norm"] = df["phone"].apply(normalize_phone)
        df["website_norm"] = df["website"].apply(normalize_website)
    elif source == "osm":
        # OSM: main column is 'amenity', phone and website may be in tags
        df["category_canon"] = df["amenity"].fillna("").apply(lambda x: canonicalize_category(x, source))
        # Extract from tags JSON if not present as column
        if "phone" not in df.columns:
            df["phone"] = df["tags"].apply(lambda t: json.loads(t).get("phone") if pd.notnull(t) else None)
        if "website" not in df.columns:
            df["website"] = df["tags"].apply(lambda t: json.loads(t).get("website") if pd.notnull(t) else None)
        df["phone_norm"] = df["phone"].apply(normalize_phone)
        df["website_norm"] = df["website"].apply(normalize_website)
    else:
        df["category_canon"] = None
        df["phone_norm"] = None
        df["website_norm"] = None
    return df


def compute_extra_features(row):
    name = row["name"] if pd.notnull(row["name"]) else ""
    name_lower = name.lower()
    name_no_punct = re.sub(r'[^a-z0-9 ]+', '', name_lower)
    name_no_punct_space = re.sub(r'[^a-z0-9]+', '', name_lower)
    # Remove common legal suffixes (match at end of string, ignore punctuation and case)
    legal_suffixes = [
        "inc", "llc", "ltd", "corp", "co", "pllc", "plc", "gmbh", "ag", "sa", "sarl", "bv", "oy", "ab", "nv", "spa", "sas", "kft", "sro", "as", "aps", "oyj", "pty", "pte"
    ]
    # Remove suffix if present as last word (after stripping punctuation)
    tokens = name_no_punct.strip().split()
    if tokens and tokens[-1] in legal_suffixes:
        tokens = tokens[:-1]
    name_no_legal_suffix = " ".join(tokens)
    features = {
        "name_lower": name_lower if name else None,
        "name_no_punct": name_no_punct if name else None,
        "name_no_punct_space": name_no_punct_space if name else None,
        "name_no_legal_suffix": name_no_legal_suffix if name else None,
        "name_token_count": len(name.split()) if name else 0,
        "name_length": len(name) if name else 0,
    }
    return json.dumps(features)

def main():
    con = duckdb.connect(DB_PATH)
    # Register haversine_distance as a DuckDB UDF
    con.create_function(
        'haversine_distance',
        haversine_distance,
        parameters=['DOUBLE', 'DOUBLE', 'DOUBLE', 'DOUBLE'],
        return_type='DOUBLE'
    )
    print("[INFO] Registered haversine_distance as DuckDB UDF.")

    # Demo: Compute distance between two points (NYC and LA)
    demo_query = """
        SELECT haversine_distance(40.7128, -74.0060, 34.0522, -118.2437) AS nyc_to_la_km
    """
    print("[DEMO] NYC to LA distance (km):", con.execute(demo_query).fetchone()[0])

    for source, raw_table, feat_table in [
        ("fsq", "fsq_raw", "fsq_features"),
        ("osm", "osm_raw", "osm_features"),
    ]:
        df = con.execute(f"SELECT * FROM {raw_table}").fetchdf()
        df = compute_core_features(df, source)
        df["extra_features"] = df.apply(compute_extra_features, axis=1)
        # Select only relevant columns for output
        out_cols = ["id", "name", "embedding", "name_trigram", "category_canon", "extra_features"]
        con.execute(f"DROP TABLE IF EXISTS {feat_table}")
        con.execute(
            f"CREATE TABLE {feat_table} AS SELECT * FROM df"
        )
    print("Feature engineering complete.")

    # Generate candidate pairs for spatial join (radius 25 meters)
    con.execute("""
        CREATE OR REPLACE TABLE candidate_pairs AS
        SELECT
            f.id AS fsq_id,
            o.id AS osm_id,
            haversine_distance(f.lat, f.lng, o.lat, o.lon) AS distance_km
        FROM fsq_features f
        JOIN osm_features o
            ON haversine_distance(f.lat, f.lng, o.lat, o.lon) < 0.025
    """)
    print("[INFO] candidate_pairs table created with spatial join (radius 25 meters)")

if __name__ == "__main__":
    main()

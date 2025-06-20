#!/usr/bin/env python3
"""
Feature engineering for POI reconciliation.
- Loads POIs from DuckDB tables (fsq_raw, osm_raw)
- Computes core features: id, name, embedding, name_trigram, category_canon
- Stores additional features in a JSON column (extra_features)
- Writes results to fsq_features and osm_features in DuckDB

NOTE: Embedding, trigram, and category canonicalization logic are placeholders and must be filled in later.
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

def compute_core_features(df, source):
    # Load the embedding model only once
    model = SentenceTransformer('all-MiniLM-L6-v2')
    # Compute embeddings for all names
    names = df["name"].fillna("").tolist()
    embeddings = model.encode(names, show_progress_bar=True)
    df["embedding"] = [emb.tolist() for emb in embeddings]
    # Compute sorted list of trigrams for each name
    df["name_trigram"] = df["name"].fillna("").apply(extract_trigrams)
    df["category_canon"] = None  # TODO: Map to canonical categories
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

if __name__ == "__main__":
    main()

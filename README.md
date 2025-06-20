# OSM + Foursquare Smart Reconciler

## 🚀 Overview
A robust, reproducible pipeline for merging and deduplicating Points of Interest (POIs) from OpenStreetMap (OSM) and Foursquare (FSQ) within any bounding box. The end goal: **produce a "gold-standard" GeoJSON layer of POIs with provenance, deduplication, and confidence scores**—ready for analytics, mapping, or downstream apps.

---

## 🌟 Features
- **Automated end-to-end pipeline:** Fetch, clean, load, feature engineer, and match POIs in one command.
- **Flexible CLI:** Control bounding box, Foursquare query, spatial threshold, and cleaning from the command line.
- **Modern data stack:** DuckDB, pandas, pyarrow, sentence-transformers, geopy, shapely, FastAPI.
- **Hybrid feature tables:** Core features as columns, experimental features as JSON.
- **Spatial & semantic matching:** Haversine UDF in DuckDB, name/embedding/category/phone heuristics.
- **Reproducibility:** Clean runs, robust error handling, and clear logging.

---

## 🎯 End Goal
- **Input:** Any region (bounding box) and optional POI category (e.g. "food").
- **Output:**
  - `data/processed/poi_merged.geojson` — Gold-standard, deduplicated POIs with provenance and confidence scores.
  - DuckDB tables: `fsq_raw`, `osm_raw`, `*_features`, `candidate_pairs`, `candidate_pairs_scored`.
- **API-ready:** Designed for easy extension with a FastAPI server for querying merged POIs.

---

## 🛠️ Quickstart

### 1. **Install dependencies**
```bash
git clone <repo-url>
cd OSM+FourSquare
poetry install
```

### 2. **Configure API keys**
Create a `.env` file in the project root:
```ini
FSQ_API_KEY=<your_foursquare_api_key>
HUGGINGFACE_HUB_READER_TOKEN=<your_hf_token>
```

### 3. **Run the pipeline (one command!)**
```bash
PYTHONPATH=$(pwd) poetry run python run.py --bbox="-74.020325,40.700292,-73.907000,40.877483" --query="food" --distance-threshold=100 --clean
```
- **`--bbox`**: Bounding box (min_lon,min_lat,max_lon,max_lat)
- **`--query`**: Foursquare category (optional, e.g. "food")
- **`--distance-threshold`**: Max match distance in meters (default: 25)
- **`--clean`**: Start from scratch (removes all local data)

If you omit `--bbox`, you will be prompted for one (default: Manhattan, NYC).

---

## 🖥️ Example Usage
```bash
# Clean and run for Manhattan, food POIs, 100m match threshold
PYTHONPATH=$(pwd) poetry run python run.py --bbox="-74.020325,40.700292,-73.907000,40.877483" --query="food" --distance-threshold=100 --clean

# Run for a custom region and all POIs
PYTHONPATH=$(pwd) poetry run python run.py --bbox="<min_lon>,<min_lat>,<max_lon>,<max_lat>"
```

---

## 📦 Outputs
- `data/raw/fsq_merged.parquet` — Raw Foursquare POIs
- `data/raw/osm_merged.parquet` — Raw OSM POIs
- `smart.db` — DuckDB database with all intermediate and final tables
- `data/processed/poi_merged.geojson` — Final merged POIs (coming soon)

---

## ❓ FAQ
**Q: What if I get API/auth errors?**
A: Double-check your `.env` file and API keys. See blog_notes.md for troubleshooting tips.

**Q: Can I run only part of the pipeline?**
A: Yes, but `run.py` is the recommended entry point for reproducibility.

**Q: How do I change the region or POI type?**
A: Use the `--bbox` and `--query` CLI arguments.

**Q: Where do I find logs and status?**
A: All steps print clear status messages to the console.

---

## 🏆 Project Goal
Deliver a scalable, modern, and research-grade POI reconciliation pipeline that can:
- Merge, deduplicate, and score POIs from heterogeneous sources
- Output a high-confidence, provenance-rich GeoJSON layer
- Serve as a foundation for analytics, mapping, or open-data enrichment

---

## 📄 License
MIT

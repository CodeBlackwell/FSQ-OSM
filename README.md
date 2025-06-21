# P.O.I (point of interest) Alchemist

## 🗺️ OSM + Foursquare Smart Reconciler

> **The next-gen open-source platform for POI deduplication, enrichment, and analytics.**

---

## 🚦 What is this?

A blazing-fast, production-ready pipeline and API for **merging and deduplicating Points of Interest (POIs)** from OpenStreetMap (OSM) and Foursquare (FSQ)—with provenance, confidence, and modern data science baked in.

- **GeoJSON output, ready for analytics, mapping, and apps**
- **Async FastAPI endpoints** for scalable, real-time POI reconciliation
- **No vendor lock-in**: Bring your own data, models, or matching logic

---

## ✨ Why use this?

- **Stop POI duplication headaches**—get a single, trusted source of truth
- **Accelerate location analytics**—with provenance and confidence scores
- **Plug-and-play for maps, dashboards, and machine learning**
- **Modern Python stack**: DuckDB, pandas, pyarrow, sentence-transformers, FastAPI, uvicorn
- **Battle-tested in real-world city-scale deployments**

---

## 🚀 Features at a Glance

- **End-to-end pipeline**: Fetch, clean, feature-engineer, and match POIs in one command
- **Flexible CLI**: Control bounding box, Foursquare query, spatial threshold, and cleaning
- **Hybrid feature tables**: Core features as columns, experimental as JSON
- **Spatial & semantic matching**: Haversine UDF, name/embedding/category/phone heuristics
- **Async API**: Kick off reconciliation jobs and poll status with job IDs
- **GeoJSON output**: Provenance and confidence fields for every POI
- **Extensible**: Add new sources, embeddings, or scoring models

---

## 🖥️ Live API Demo (Async)

```bash
# Start a reconciliation job for Manhattan
curl -X POST "http://127.0.0.1:8000/merge/run" \
  -H "Content-Type: application/json" \
  -d '{"min_lon": -74.02, "min_lat": 40.70, "max_lon": -73.90, "max_lat": 40.88}'

# Poll job status
curl "http://127.0.0.1:8000/merge/status/<job_id>"

# Get merged POIs as GeoJSON
curl "http://127.0.0.1:8000/poi?limit=5"

# Get a single POI by ID
curl "http://127.0.0.1:8000/poi/<poi_id>"
```

---

## 🏗️ Tech Stack

- **Python 3.10+** — Modern language features, async support, and data science ecosystem
- **DuckDB** — In-process analytics database for fast SQL joins, UDFs, and ad hoc queries
- **pandas & pyarrow** — Data wrangling, ETL, and Parquet I/O
- **FastAPI & Uvicorn** — Async API server for job orchestration and GeoJSON delivery
- **sentence-transformers** — State-of-the-art semantic embeddings for name/category matching
- **geopy & shapely** — Geospatial calculations and geometry handling
- **python-dotenv** — Securely manage API keys and secrets
- **pre-commit, pytest, isort, black, flake8** — Code quality, formatting, and testing

---

## 🖼️ How Does It Work? (Visual + ELI5)

```
  [OSM API]         [Foursquare API]
      |                   |
      v                   v
   [Raw Data Fetch & Normalize]
                |
                v
      [Feature Engineering]
                |
                v
       [Candidate Matching]
                |
                v
      [Scoring & Merging]
                |
                v
    [GeoJSON Output + Async API]
```

**ELI5:**
Imagine you have two big boxes of toys from 2 stores—one from OSM, one from Foursquare. Some toys are in both boxes, but their names or details might be a little different. This program is like a super-smart friend who:

- Looks at both boxes,
- Finds which toys are actually the same (even if the names are a bit off),
- Combines their best info into a single, shiny card (with a score showing how sure it is!),
- And then hands you a neat map or list—so you always know what’s really out there, without any repeats!

---

## 🧩 Example Use Cases

- **Urban analytics & city dashboards**
- **Retail site selection & competitive analysis**
- **Open data enrichment for mapping platforms**
- **Academic research on urban mobility or POI quality**

---

## 🧠 How it Works

1. **Fetch**: Pull POIs from OSM (Overpass) and Foursquare for any bounding box
2. **Feature engineering**: Names, categories, embeddings, spatial proximity, phone/website, and more
3. **Candidate generation**: DuckDB SQL joins with Haversine UDF for spatial blocking
4. **Scoring & merging**: Weighted scoring, provenance, and confidence
5. **API**: Async endpoints for job orchestration and GeoJSON retrieval

---

## ❓ FAQ

**Q: What if I get API/auth errors?**
A: Double-check your `.env` file and API keys. See `blog_notes.md` for troubleshooting tips.

**Q: Can I run only part of the pipeline?**
A: Yes, but `run.py` is the recommended entry point for reproducibility.

**Q: How do I change the region or POI type?**
A: Use the `--bbox` and `--query` CLI arguments.

**Q: Where do I find logs and status?**
A: All steps print clear status messages to the console and API.

---

## 🏆 Project Goal

Deliver a scalable, modern, and research-grade POI reconciliation pipeline that can:

- Merge, deduplicate, and score POIs from heterogeneous sources
- Output a high-confidence, provenance-rich GeoJSON layer
- Serve as a foundation for analytics, mapping, or open-data enrichment

---

## 📄 License

MIT

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

Deliver a scalable, modern, and research-grade POI reconciliation pipeline PoC that can:

- Merge, deduplicate, and score POIs from heterogeneous sources
- Output a high-confidence, provenance-rich GeoJSON layer
- Serve as a foundation for analytics, mapping, or open-data enrichment

---

## 📄 License

MIT

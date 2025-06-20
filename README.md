# OSM + Foursquare Smart Reconciler PoC

## Overview
This project merges and deduplicates Points of Interest (POIs) from OpenStreetMap (OSM) and Foursquare (FSQ) for a chosen bounding box, outputting a "gold" GeoJSON layer with provenance and confidence scores.

## Project Structure
- `src/` — Core library code
- `scripts/` — Data acquisition and utility scripts
- `data/raw/` — Raw data (Parquet files)
- `data/processed/` — Processed/merged data
- `notebooks/` — Jupyter notebooks for exploration
- `tests/` — Unit tests

## Setup
1. **Clone the repo and install dependencies:**
   ```bash
   git clone <repo-url>
   cd smart-reconciler
   poetry install
   ```
2. **Set up your Foursquare API credentials:**
   - Create a `.env` file in the project root:
     ```ini
     FSQ_CLIENT_ID="<your_client_id>"
     FSQ_CLIENT_SECRET="<your_client_secret>"
     ```

## Data Acquisition
### 1. Fetch Foursquare POIs
Fetch Foursquare Places for a bounding box and save as Parquet:
```bash
python scripts/fetch_fsq.py --bbox "<min_lon>,<min_lat>,<max_lon>,<max_lat>" --output data/raw/fsq_bbox.parquet
```

### 2. Fetch OSM POIs
Fetch OSM amenities for a bounding box and save as Parquet:
```bash
python scripts/fetch_osm.py --bbox "<min_lon>,<min_lat>,<max_lon>,<max_lat>" --output data/raw/osm_bbox.parquet
```

## Data Verification
After running the fetch scripts, verify the output Parquet files in `data/raw/` using Python or a tool like `parquet-tools`:
```python
import pandas as pd
df = pd.read_parquet('data/raw/fsq_bbox.parquet')
print(df.head())
print(df.dtypes)
print(len(df))
```

## Next Steps
- Ingest both datasets into DuckDB
- Feature engineering and matching
- API and output endpoints
- Testing and evaluation

## License
MIT

# OSM + Foursquare POI Reconciler: Blog Notes

## 2025-06-20T03:23:32-04:00 — Feature Engineering Phase & API Migration Breakthrough

### Task Title / Objective
Hybrid Feature Table Schema Decision and API Version Migration

### Technical Summary
- Successfully fetched and ingested both Foursquare and OSM POI data for Times Square into DuckDB, with spatial and Bayer indexes.
- Migrated Foursquare API usage to the new endpoint and authentication scheme (`places-api.foursquare.com`, `Authorization: Bearer <API_KEY>`, `X-Places-Api-Version` header).
- Chose a hybrid schema for `*_features` tables: core features as columns, experimental/extra features in a JSON column.
- Updated project plan to explicitly support experimentation and comparison of multiple feature engineering and matching strategies.

### Bugs & Obstacles
- Foursquare API migration required careful debugging: new base URL, header syntax, and single API key usage. Initial attempts with old endpoints or client ID/secret failed with 401/400 errors.
- OSM and FSQ longitude column mismatch (`lon` vs `lng`) caused ingestion script errors, resolved by schema-aware indexing.
- Pre-commit hooks (end-of-file-fixer) blocked commits until files were auto-fixed and re-staged.

### Key Deliberations
- Considered wide, long, and hybrid table schemas for feature storage. Chose hybrid for flexibility and efficient querying.
- Decided to support multiple similarity and blocking strategies (semantic, n-gram, string, spatial, category) for later comparison.
- Integrated git-lfs for both Parquet and DuckDB files to handle large data artifacts.

### Color Commentary
What a journey! API migrations are always a puzzle, but the breakthrough came with a working cURL and a careful header-by-header translation. The hybrid schema debate was a real architectural crossroads—balancing flexibility with performance. Now, with the data pipeline humming and the plan ready for experimentation, the project is poised for some serious POI-matching showdowns. Onward to feature engineering! 🚀

---

### 2025-06-20T08:46:13-04:00 — Foursquare API Migration & Authentication Overhaul

- **Task Title / Objective:** Migrate Foursquare data fetching to the latest API, resolve authentication pitfalls, and ensure robust parameter handling for POI acquisition.
- **Technical Summary:** The Foursquare Places API v3/v2 endpoints were deprecated, necessitating a full migration to the new base URL (`https://places-api.foursquare.com`). Correct API usage now requires the `Authorization: Bearer <API_KEY>`, `X-Places-Api-Version: <date>`, and `Accept: application/json` headers. Bounding box parameters must be mapped as `sw=min_lat,min_lon` and `ne=max_lat,max_lon`. Only a single API key is needed, not client ID/secret. Scripts were updated to reflect these requirements, and fetch logic was hardened against misconfiguration.
- **Bugs & Obstacles:** Initial attempts using old endpoints or incorrect headers resulted in 401/400 errors. The distinction between API key and client credentials was unclear from the docs. Bbox parameters were initially mapped incorrectly, leading to empty or failed responses. Debugging required careful inspection of both error messages and Foursquare’s evolving documentation.
- **Key Deliberations:** Considered patching the old scripts versus a full rewrite; opted for a clean migration to avoid tech debt. Weighed the pros and cons of hardcoding header logic versus loading from config. Chose to centralize API requirements for maintainability and future-proofing.
- **Color Commentary:** This was a classic API migration gauntlet: shifting sands in documentation, silent failures, and authentication gotchas at every turn. But after a few “aha!” moments, the new fetch layer emerged stronger, leaner, and ready for production-scale scraping. The lesson? Always check the docs—and then check them again tomorrow!

---

### 2025-06-20T10:44:19-04:00 – Foursquare API Fetch Success

**Task Title / Objective:**
Fix Foursquare API integration to fetch a valid, multi-record POI dataset for Manhattan using the correct endpoint, headers, and parameters.

**Technical Summary:**
- Identified that the previous endpoint (`places-api.foursquare.com`) was deprecated and returned 404 errors.
- Updated the fetch script to use the correct v3 endpoint: `https://api.foursquare.com/v3/places/search`.
- Set the `X-Places-Api-Version` header to a valid date (`20230801`), and ensured the bounding box is mapped as `sw=min_lat,min_lon` and `ne=max_lat,max_lon`.
- Added support for a `--query` CLI argument and improved verbose logging for debugging.
- The script now successfully fetches valid POI data from Foursquare for Manhattan, matching expectations.

**Bugs & Obstacles:**
- Persistent 404 errors due to legacy endpoint and future-dated version header.
- Difficulty confirming parameter mapping and API requirements due to sparse docs and legacy code fragments.
- Solution: Carefully cross-referenced Foursquare docs, updated endpoint and headers, and validated with verbose API output.

**Key Deliberations:**
- Considered legacy vs. new endpoints and header dates; chose the documented v3 endpoint and a recent, valid version header for maximum compatibility.
- Chose to expose the query parameter for flexibility and easier debugging.

**Color Commentary:**
After a string of cryptic 404s, the breakthrough came by aligning precisely with Foursquare’s latest API docs. The tension broke as the first real POI batch streamed in—proof that sometimes, the right URL is everything. This was a classic case of “read the docs, then read them again.”

---

### 2025-06-20T06:08:39-04:00 — Feature Engineering: Embeddings

- **Task Title / Objective:** Implement and run semantic name embeddings for POI feature engineering.
- **Technical Summary:** Integrated `sentence-transformers` (`all-MiniLM-L6-v2`) into the feature engineering pipeline. Script now generates and stores 384-dim embeddings for all POI names in DuckDB.
- **Bugs & Obstacles:** Encountered persistent HuggingFace Hub 401 Unauthorized errors due to token issues. Resolved by creating a new “Read” token and explicitly loading it from `.env` as `HUGGINGFACE_HUB_READER_TOKEN`, mapped to `HUGGINGFACE_HUB_TOKEN` in the script.
- **Key Deliberations:** Considered different ways to inject the access token (global env, `.env`, explicit script logic). Chose `.env` + DRY mapping for reproducibility and clarity.
- **Color Commentary:** Wrestling with HuggingFace authentication felt like a rite of passage! The relief when embeddings started flowing into DuckDB was palpable—onward to trigram similarity!

---

### 2025-06-20T06:49:47-04:00 — Trigram Similarity & Testing Lock-in

- **Task Title / Objective:** Implement robust trigram extraction for POI name similarity and add regression tests.
- **Technical Summary:** Updated `extract_trigrams` to remove all spaces and punctuation before extracting sorted, unique trigrams, following best practices for fuzzy entity matching. Created and updated `pytest` unit tests to match the new logic, ensuring future-proof regression protection.
- **Bugs & Obstacles:** Faced recurring `ModuleNotFoundError` due to Python path confusion between Poetry, pytest, and the shell. Solved by installing pytest as a dev dependency and explicitly setting `PYTHONPATH=$(pwd)` in test runs.
- **Key Deliberations:** Considered whether to include spaces in trigrams; chose to remove them for maximum robustness and alignment with industry standards. Updated tests to reflect the true output of the improved function.
- **Color Commentary:** The test failures were a gauntlet, but each one brought the code closer to bulletproof. Now, every POI name gets the same fair shake—no matter how quirky the spacing or punctuation. Regression safety net: deployed!

---

### 2025-06-20T07:16:35-04:00 — DuckDB UDF for Spatial Proximity

- **Task Title / Objective:** Register Python Haversine distance as a DuckDB UDF for efficient SQL-based spatial candidate generation.
- **Technical Summary:** Integrated the `haversine_distance` Python function into DuckDB as a UDF. Demonstrated correctness with a SQL query for NYC-to-LA distance. This enables scalable, in-database spatial joins and candidate filtering for POI reconciliation.
- **Bugs & Obstacles:** Needed to ensure the UDF was correctly registered and callable from SQL. Verified with both print output and demo query.
- **Key Deliberations:** Weighed Python vs. SQL approaches; chose DuckDB UDF for performance, scalability, and portfolio value. Ensured the solution is extensible for future spatial features.
- **Color Commentary:** This is the kind of hybrid engineering that makes a project stand out—Python and DuckDB, working together for analytics magic. The demo query’s result was a satisfying proof: spatial features, leveled up!

---

## 2025-06-20T13:10:22-04:00 – Unified Pipeline Orchestration & CLI Overhaul

**Task Title / Objective:**
Streamline the OSM + Foursquare POI pipeline into a single orchestrated CLI (`run.py`) with robust argument handling and full automation of data fetching, loading, and feature engineering.

**Technical Summary:**
- Refactored `run.py` to handle the entire pipeline: cleaning, fetching Foursquare/OSM data, loading to DuckDB, and running feature engineering.
- Added CLI arguments for `--clean`, `--bbox`, `--query`, and `--distance-threshold` to allow reproducible, configurable runs.
- Ensured all subprocess calls pass arguments correctly, especially bounding box and query, to avoid `argparse` errors.
- Feature engineering, candidate generation, and scoring now run seamlessly as part of the orchestrator.

**Bugs & Obstacles:**
- Major bug: `argparse` in fetch scripts failed when bbox was split into multiple arguments; fixed by passing `--bbox=<value>` as a single string.
- Early attempts to run feature engineering after cleaning failed due to missing DuckDB tables; solved by enforcing correct pipeline order.
- CLI confusion from redundant `--clean` in feature_engineering.py resolved by centralizing all orchestration in `run.py`.

**Key Deliberations:**
- Considered keeping some manual steps for flexibility, but unified CLI was chosen for reliability and reproducibility.
- Decided to prompt for bbox only if not provided, balancing automation with user control.

**Color Commentary:**
This refactor felt like a relay race—each script now hands off smoothly to the next, no baton drops! The CLI is finally a power tool: one command, full pipeline, zero guesswork. Watching the pipeline run end-to-end with live status updates was a genuine "it just works" moment—dev joy unlocked.

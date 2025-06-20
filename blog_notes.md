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
- **Color Commentary:** This was a classic API migration gauntlet: shifting sands in documentation, silent failures, and authentication gotchas at every turn. But after a series of 401s and a few “aha!” moments, the new fetch layer emerged stronger, leaner, and ready for production-scale scraping. The lesson? Always check the docs—and then check them again tomorrow!

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

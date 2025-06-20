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

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

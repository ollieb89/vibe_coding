# Phase 06-02 Summary: Wiring ClassificationResult to LanceDB

## Overview
Successfully wired the new `ClassificationResult` into the LanceDB schema and indexer pipeline. Construct classification confidence and source are now properly persisted in the vector database, completing the end-to-end implementation of frontmatter-first classification.

## Schema Changes
Added two new nullable fields to `ChunkRecord` in `src/corpus_analyzer/store/schema.py`:
- `classification_source`: string (e.g., 'frontmatter', 'rule_based', 'llm')
- `classification_confidence`: float (0.0 to 1.0)

Implemented `ensure_schema_v3()` for zero-data-loss in-place schema evolution. This uses LanceDB's `add_columns` API to upgrade existing tables automatically when they are opened, without requiring users to rebuild their index.

## Indexer Updates
Updated `src/corpus_analyzer/ingest/indexer.py`:
- Added call to `ensure_schema_v3(table)` inside `CorpusIndex.open()`
- Extracted `ClassificationResult` object returned by `classify_file()`
- Injected `construct_type`, `classification_source`, and `classification_confidence` into the chunk dictionary before upserting into LanceDB

## Test Coverage
Added new integration test in `tests/ingest/test_indexer.py`:
- `test_indexer_stores_frontmatter_classification`: Verifies that indexing a markdown file with `type: skill` frontmatter correctly populates the LanceDB table with `construct_type="skill"`, `classification_source="frontmatter"`, and `classification_confidence=0.95`.

Updated existing `test_all_required_fields_present` in `tests/store/test_schema.py` to include the new fields.

All 192 tests pass successfully.

## Commits
1. `feat(06-02): add classification source and confidence to schema`
2. `feat(06-02): wire ClassificationResult into indexer and apply schema v3`

## Phase 6 Completion
Phase 6 is now complete. Both requirements have been satisfied:
- **CLASS-04**: Store classification confidence and source in vector DB
- **CLASS-05**: Auto-upgrade existing schemas without rebuilding index

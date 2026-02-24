# Score Normalisation (NORM-01) Implementation Summary

## Overview
Successfully implemented RRF score normalisation to 0–1 range in the search engine layer (Phase 23-01).

## Changes Made

### 1. Engine Constants (`src/corpus_analyzer/search/engine.py`)
- Added `_RRF_K = 60` - the RRF k parameter for fusion
- Added `RRF_SCORE_CEILING = 1/60 + 1/60 ≈ 0.0333` - normalisation ceiling

### 2. Score Normalisation Logic
- Moved normalisation to occur BEFORE min_score filtering
- All `_relevance_score` values are now divided by `RRF_SCORE_CEILING` and clamped to `[0.0, 1.0]`
- Empty-query scan rows (no RRF score) remain at 0.0

### 3. Documentation Updates
- Updated `hybrid_search()` docstring: now references 0–1 range instead of raw RRF 0.009–0.033
- Updated CLI `--min-score` help text: references normalised 0–1 range

### 4. Test Coverage (`tests/search/test_engine.py`)
- Added `TestScoreNormalisation` test class with 3 tests:
  - `test_scores_normalised_to_unit_range`: Asserts all scores in [0.0, 1.0]
  - `test_score_ceiling_constant_matches_rrf_k`: Verifies constant matches 1/K + 1/K
  - `test_empty_query_scan_scores_zero`: Confirms empty-query rows have score 0.0

## Test Results
- All 33 search engine tests pass
- All 59 combined tests (search + MCP + API) pass
- Linting passes with no issues

## Impact
- All consumers (CLI, Python API, MCP) automatically receive normalised scores
- min_score filtering now works intuitively on 0–1 scale
- Backward compatible: min_score=0.0 still keeps all results

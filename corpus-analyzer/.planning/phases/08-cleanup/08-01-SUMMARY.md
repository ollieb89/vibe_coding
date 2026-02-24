---
phase: 08-cleanup
plan: "01"
subsystem: ingest
tags: [indexer, config, classification, cleanup, dead-code]

# Dependency graph
requires:
  - phase: 07-graph-linker
    provides: graph store and slug registry wired into indexer
provides:
  - index_source() without use_llm_classification parameter
  - SourceConfig without use_llm_classification field
  - Tests updated to reflect removed field
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dead parameter removal: pass literal default (use_llm=False) rather than removing the arg from classify_file call, to preserve rule-based classification behaviour"

key-files:
  created: []
  modified:
    - src/corpus_analyzer/ingest/indexer.py
    - src/corpus_analyzer/config/schema.py
    - tests/ingest/test_indexer.py
    - tests/config/test_schema.py

key-decisions:
  - "Pass use_llm=False directly to classify_file rather than removing the argument entirely — classify_file defaults to use_llm=True which would silently change behaviour"
  - "Delete the test that existed solely to verify the removed field rather than adapting it"

patterns-established:
  - "When removing a field that had a non-default-of-callee default, hardcode the original value at the call site"

requirements-completed: [CLEAN-01]

# Metrics
duration: 2min
completed: 2026-02-24
---

# Phase 8 Plan 01: Cleanup Summary

**Removed dead `use_llm_classification` parameter from `index_source()` and `SourceConfig`, eliminating a misleading API surface while preserving rule-based classification via `use_llm=False`**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-24T03:05:44Z
- **Completed:** 2026-02-24T03:07:33Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- Removed `use_llm_classification` field from `SourceConfig` in `config/schema.py`
- Removed `use_llm_classification` parameter from `index_source()` signature and docstring
- Replaced `use_llm=source.use_llm_classification` with `use_llm=False` in `classify_file` call
- Removed `use_llm_classification=False` kwarg from test call site in `test_indexer.py`
- Deleted `test_source_config_use_llm_classification_defaults_false` test from `test_schema.py`
- Test suite: 281 passed (baseline 282, minus 1 deleted test)

## Task Commits

Each task was committed atomically:

1. **Task 1: Establish green baseline** - no commit (verification only, 282 tests passed)
2. **Task 2: Remove use_llm_classification from source code** - `73f7505` (refactor)
3. **Task 3: Update tests and verify no regressions** - `d6be1a3` (refactor)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `src/corpus_analyzer/config/schema.py` - Removed `use_llm_classification` field and docstring block from `SourceConfig`
- `src/corpus_analyzer/ingest/indexer.py` - Removed parameter from `index_source()` signature, docstring, and call site; hardcoded `use_llm=False`
- `tests/ingest/test_indexer.py` - Removed `use_llm_classification=False` kwarg from `SourceConfig(...)` in `test_indexer_stores_frontmatter_classification`
- `tests/config/test_schema.py` - Deleted `test_source_config_use_llm_classification_defaults_false` test method

## Decisions Made
- Pass `use_llm=False` explicitly to `classify_file` rather than removing the argument — `classify_file` defaults to `use_llm=True` which would silently switch from rule-based to LLM classification and change production behaviour.
- Delete the test for the removed field rather than adapting it — the test existed only to verify the removed field's existence.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

Pre-existing mypy and ruff errors (42 mypy errors, 529 ruff errors) exist across the codebase unrelated to the files modified in this plan. These are out of scope per deviation rules and have been noted for future cleanup.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 8 complete. The `use_llm_classification` dead parameter is fully removed from source and tests. The codebase API surface is smaller and less confusing. v1.2 milestone is complete.

---
*Phase: 08-cleanup*
*Completed: 2026-02-24*

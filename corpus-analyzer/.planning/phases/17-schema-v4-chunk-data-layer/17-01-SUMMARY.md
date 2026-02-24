---
phase: 17-schema-v4-chunk-data-layer
plan: "01"
subsystem: testing
tags: [lancedb, pydantic, chunker, tdd, schema-migration, pytest]

# Dependency graph
requires:
  - phase: 16-schema-v4-chunk-data-layer
    provides: chunk_typescript with chunk_name emission; 320 green tests
provides:
  - RED test suite for ChunkRecord v4 fields (chunk_name, chunk_text)
  - RED tests for ensure_schema_v4() migration helper
  - RED tests for chunk_markdown/chunk_python v4 field emission
  - Parametrised round-trip integration test across .md, .py, .ts fixtures
affects:
  - 17-02-PLAN (GREEN phase — implements production code to pass these tests)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Deferred import inside test methods to allow module-level collection while keeping non-implemented-function tests RED"
    - "Parametrised round-trip test: write synthetic file -> CorpusIndex.index_source -> direct LanceDB query -> field assertions"

key-files:
  created:
    - tests/ingest/test_round_trip.py
  modified:
    - tests/store/test_schema.py
    - tests/ingest/test_chunker.py

key-decisions:
  - "Deferred import of ensure_schema_v4 inside test methods (not at module level) so pre-existing TestMakeChunkId and TestChunkRecordInstantiation tests remain collectible and GREEN while the ensure_schema_v4 tests fail with ImportError"
  - "MockEmbedder defined locally in test_round_trip.py (not imported from test_indexer.py) — test_indexer.MockEmbedder uses model=nomic-embed-text which would trigger model-mismatch guard; local version uses model=test-model with 0.0 vectors"
  - "Round-trip test uses index._table.search().limit(20).to_list() to dump all rows; no vector similarity search needed"

patterns-established:
  - "RED-only plan: test files only, no production code changes — driven by TDD discipline"
  - "Lazy import pattern for not-yet-implemented functions keeps test module collectable"

requirements-completed:
  - CHUNK-01

# Metrics
duration: 3min
completed: 2026-02-24
---

# Phase 17 Plan 01: Schema v4 RED Tests Summary

**Failing test suite for ChunkRecord v4 fields (chunk_name/chunk_text) covering schema validation, ensure_schema_v4() migration, chunker emission, and LanceDB round-trip across .md/.py/.ts fixtures**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-24T12:34:14Z
- **Completed:** 2026-02-24T12:37:26Z
- **Tasks:** 2
- **Files modified:** 3 (2 modified, 1 created)

## Accomplishments
- Updated `test_all_required_fields_present` to expect `chunk_name` and `chunk_text` in ChunkRecord — immediately RED
- Added `TestEnsureSchemaV4` class with 3 tests: adds chunk_name, adds chunk_text, idempotent — all RED (ImportError)
- Added 4 new tests to `TestChunkMarkdown` and `TestChunkPython` for v4 field emission — all RED (KeyError)
- Created `tests/ingest/test_round_trip.py` with parametrised round-trip test across Markdown, Python, TypeScript fixtures — all RED

## Task Commits

Each task was committed atomically:

1. **Tasks 1+2: RED — test_schema.py + test_chunker.py + test_round_trip.py** - `3be5ace` (test)

**Plan metadata:** committed with docs commit below

_Note: Tasks 1 and 2 were committed together as one atomic RED state commit._

## Files Created/Modified
- `tests/store/test_schema.py` — Added chunk_name/chunk_text to expected_fields; new TestEnsureSchemaV4 class (3 tests)
- `tests/ingest/test_chunker.py` — Added test_chunk_markdown_emits_chunk_name, test_chunk_markdown_emits_chunk_text, test_chunk_python_emits_chunk_name, test_chunk_python_emits_chunk_text
- `tests/ingest/test_round_trip.py` — New: parametrised round-trip test (3 fixtures: .md, .py, .ts)

## Decisions Made
- Deferred import of `ensure_schema_v4` inside each test method body (not at module level) so the rest of `test_schema.py` remains collectable and the 16 pre-existing schema tests stay GREEN
- `MockEmbedder` defined locally in `test_round_trip.py` with `model="test-model"` and zero vectors to avoid model-mismatch guard in `CorpusIndex.open()`
- Round-trip assertions use `index._table.search().limit(20).to_list()` — simple full-table dump, no vector similarity required

## Deviations from Plan

None - plan executed exactly as written. The deferred-import pattern was implied by the plan's note about ImportError being the correct RED state; the plan also explicitly required pre-existing tests to remain GREEN, which necessitated deferred import rather than module-level import.

## Issues Encountered
- Initial attempt used module-level `from corpus_analyzer.store.schema import ensure_schema_v4` which caused an ImportError at collection time, blocking all 20 tests in `test_schema.py` (including the 16 that should stay GREEN). Fixed by moving the import inside each test method body.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- RED state confirmed: 11 new failing tests, 319 pre-existing tests GREEN
- Plan 17-02 implements: ChunkRecord v4 fields, ensure_schema_v4(), chunk_markdown/chunk_python v4 key emission, indexer wiring
- No blockers — clear failing tests define exactly what 17-02 must implement

## Self-Check: PASSED

- FOUND: tests/store/test_schema.py
- FOUND: tests/ingest/test_chunker.py
- FOUND: tests/ingest/test_round_trip.py
- FOUND: .planning/phases/17-schema-v4-chunk-data-layer/17-01-SUMMARY.md
- FOUND: commit 3be5ace

---
*Phase: 17-schema-v4-chunk-data-layer*
*Completed: 2026-02-24*

---
phase: 17-schema-v4-chunk-data-layer
plan: "02"
subsystem: database
tags: [lancedb, pydantic, chunker, tdd, schema-migration, pytest]

# Dependency graph
requires:
  - phase: 17-01
    provides: RED test suite for ChunkRecord v4 fields; 320 green tests
provides:
  - ensure_schema_v4() migration helper in store/schema.py (idempotent, adds chunk_name + chunk_text)
  - ChunkRecord.chunk_name and ChunkRecord.chunk_text fields (str, default empty string)
  - chunk_markdown emits chunk_name (heading line verbatim) and chunk_text (section text)
  - chunk_python emits chunk_name (AST node.name) and chunk_text (raw lines slice)
  - chunk_typescript emits chunk_text (raw source slice); chunk_name already present
  - _enforce_char_limit carries chunk_name and chunk_text through all sub-chunk paths
  - CorpusIndex.open() calls ensure_schema_v4(table); chunk_dict includes chunk_name and chunk_text
  - Round-trip test GREEN for .md, .py, .ts fixtures — zero-hallucination line-range contract
affects:
  - Phase 18+ (any search or display layer reading chunk_name/chunk_text from LanceDB)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Schema evolution with empty-string defaults: add_columns({'col': \"cast('' as string)\"}) for non-nullable string fields"
    - "Pass-through pattern in _enforce_char_limit: chunk.get('chunk_name', '') preserves parent field across splits"
    - "chunk_text set before any mutation path (summary prepend on chunk['text'] does not corrupt chunk_text)"

key-files:
  created: []
  modified:
    - src/corpus_analyzer/store/schema.py
    - src/corpus_analyzer/ingest/chunker.py
    - src/corpus_analyzer/ingest/ts_chunker.py
    - src/corpus_analyzer/ingest/indexer.py
    - tests/ingest/test_indexer.py
    - tests/search/test_engine.py

key-decisions:
  - "chunk_text is read from chunk.get('chunk_text', '') in indexer — safe because summary prepend mutates chunk['text'] only, not chunk['chunk_text']"
  - "Test fixtures that directly insert rows into LanceDB tables (test_engine.py, test_indexer.py) auto-fixed with chunk_name='' and chunk_text='' (Rule 1 auto-fix — schema change broke them)"
  - "ensure_schema_v4 placed before ensure_schema_v3 in ordering would conflict — kept v2→v3→v4 call order in open()"

patterns-established:
  - "ensure_schema_vN pattern: check existing_cols set, call add_columns only if absent — idempotent by construction"
  - "Auto-fix Rule 1: when new schema fields break existing LanceDB insert fixtures, add empty-string defaults to all affected test row dicts"

requirements-completed:
  - CHUNK-01

# Metrics
duration: 4min
completed: 2026-02-24
---

# Phase 17 Plan 02: Schema v4 GREEN Implementation Summary

**ChunkRecord v4 fields (chunk_name/chunk_text) implemented across schema, chunkers, and indexer — 330 tests green, ruff+mypy clean, round-trip contract verified for .md/.py/.ts**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-24T12:40:18Z
- **Completed:** 2026-02-24T12:44:29Z
- **Tasks:** 2
- **Files modified:** 6 (4 production, 2 test)

## Accomplishments

- Added `chunk_name: str = ""` and `chunk_text: str = ""` to `ChunkRecord` with `ensure_schema_v4()` migration helper
- Wired all three chunkers (Markdown, Python, TypeScript) to emit both new fields
- Updated `_enforce_char_limit` to carry `chunk_name`/`chunk_text` through all sub-chunk split paths
- Updated `CorpusIndex.open()` to call `ensure_schema_v4(table)` and `chunk_dict` to include both fields
- All 11 RED tests from 17-01 turned GREEN; 319 pre-existing tests remained GREEN (330 total)

## Task Commits

Each task was committed atomically:

1. **Task 1: GREEN — Add ensure_schema_v4() and ChunkRecord v4 fields to schema.py** - `becadff` (feat)
2. **Task 2: GREEN — Emit chunk_name and chunk_text from all chunkers; update indexer pass-through** - `e0ca208` (feat)

**Plan metadata:** committed with docs commit below

## Files Created/Modified

- `src/corpus_analyzer/store/schema.py` — Added `chunk_name`/`chunk_text` fields to ChunkRecord; added `ensure_schema_v4()` function; updated module docstring
- `src/corpus_analyzer/ingest/chunker.py` — `chunk_markdown`: emit chunk_name + chunk_text per section + preamble-merge path; `chunk_python`: emit chunk_name (node.name) + chunk_text; `_enforce_char_limit`: carry chunk_name/chunk_text through all 4 append sites
- `src/corpus_analyzer/ingest/ts_chunker.py` — Added `chunk_text` key to both `chunks.append()` call sites (export-default branch and main branch)
- `src/corpus_analyzer/ingest/indexer.py` — Import + call `ensure_schema_v4(table)`; add `chunk_name` and `chunk_text` to `chunk_dict`
- `tests/ingest/test_indexer.py` — Added `chunk_name`/`chunk_text` to direct LanceDB insert row dicts (auto-fix)
- `tests/search/test_engine.py` — Added `chunk_name`/`chunk_text` to all seeded row dicts in 3 fixtures (auto-fix)

## Decisions Made

- `chunk_text` is read via `chunk.get("chunk_text", "")` in the indexer — this is safe because the summary prepend (`chunks[0]["text"] = f"{summary_text}\n\n{chunks[0]['text']}"`) mutates `chunk["text"]` only, not `chunk["chunk_text"]`, so no mutation hazard
- Call order `ensure_schema_v2 → ensure_schema_v3 → ensure_schema_v4` preserved to maintain consistent migration chain

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test fixtures that directly insert rows into LanceDB tables broke after ChunkRecord schema gained new required fields**

- **Found during:** Task 2 (after wiring indexer and running full test suite)
- **Issue:** `tests/search/test_engine.py` (`seeded_table`, `sortable_table`, `test_sort_by_construct_uses_confidence_as_tiebreaker`) and `tests/ingest/test_indexer.py` (`test_raises_on_model_mismatch`, `test_open_migrates_agent_config_to_agent`) create LanceDB tables with `ChunkRecord` schema and insert row dicts directly — those dicts lacked `chunk_name` and `chunk_text`, causing `RuntimeError: Append with different schema: missing=[chunk_name, chunk_text]`
- **Fix:** Added `"chunk_name": ""` and `"chunk_text": ""` to all 9 affected row dicts across both test files
- **Files modified:** `tests/search/test_engine.py`, `tests/ingest/test_indexer.py`
- **Verification:** All 330 tests pass; no new test logic — just schema alignment
- **Committed in:** `e0ca208` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — schema change broke existing direct-insert test fixtures)
**Impact on plan:** Necessary for correctness — pre-existing tests must stay green. No scope creep; the fix was purely additive empty-string fields.

## Issues Encountered

None — all planned changes succeeded without debugging loops.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Zero-hallucination line-range contract (CHUNK-01) is fully implemented and verified by round-trip tests
- Every indexed chunk now carries `chunk_name`, `chunk_text`, `start_line`, and `end_line` in LanceDB
- Phase 18 (search layer improvements) can read `chunk_name` and `chunk_text` directly from query results
- No blockers — 330 tests passing, ruff clean, mypy clean

## Self-Check: PASSED

- FOUND: src/corpus_analyzer/store/schema.py (contains ensure_schema_v4)
- FOUND: src/corpus_analyzer/ingest/chunker.py (contains chunk_name, chunk_text)
- FOUND: src/corpus_analyzer/ingest/ts_chunker.py (contains chunk_text)
- FOUND: src/corpus_analyzer/ingest/indexer.py (contains ensure_schema_v4)
- FOUND: commit becadff
- FOUND: commit e0ca208

---
*Phase: 17-schema-v4-chunk-data-layer*
*Completed: 2026-02-24*

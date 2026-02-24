---
phase: 22-name-filtering
plan: 01
subsystem: search
tags: [lancedb, hybrid-search, name-filter, tdd]

# Dependency graph
requires:
  - phase: 21-ts-method-sub-chunking
    provides: chunk_name field populated in LanceDB for TypeScript method chunks
  - phase: 20-py-method-sub-chunking
    provides: chunk_name field populated in LanceDB for Python method chunks
provides:
  - hybrid_search() name= parameter for case-insensitive chunk_name substring filtering
  - Empty-query (name-only) search that scans table without requiring text match
affects:
  - 22-02 (CLI --name flag wiring to engine name= parameter)
  - 22-03 (MCP corpus_search name field wiring)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Post-retrieval name filter: case-insensitive substring on chunk_name after text-term pass"
    - "Empty-query path: LanceDB table scan (not hybrid search) when query.strip() == ''"

key-files:
  created: []
  modified:
    - src/corpus_analyzer/search/engine.py
    - tests/search/test_engine.py

key-decisions:
  - "Empty query uses table.search() scan instead of hybrid search — LanceDB raises ValueError for empty text query in hybrid mode"
  - "name filter applied post-retrieval after text-term filter, before min_score — consistent with existing filter ordering"
  - "name='' treated as None (falsy check `if name:`) — empty fragment matches nothing useful"

patterns-established:
  - "Empty-query scan path: is_empty_query = not query.strip(); branch avoids LanceDB hybrid ValueError"
  - "Name filter: `if name_lower in str(r.get('chunk_name', '') or '').lower()` — handles None chunk_name safely"

requirements-completed: [NAME-01, NAME-03]

# Metrics
duration: 2min
completed: 2026-02-24
---

# Phase 22 Plan 01: Engine Name Filter + Empty-Query Support Summary

**Case-insensitive `name=` substring filter on `chunk_name` added to `hybrid_search()`, with LanceDB table-scan fallback enabling name-only search when query is empty**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-24T17:21:34Z
- **Completed:** 2026-02-24T17:23:28Z
- **Tasks:** 2 (TDD RED + GREEN)
- **Files modified:** 2

## Accomplishments
- Added `name: str | None = None` parameter to `hybrid_search()` — case-insensitive substring filter on `chunk_name`
- Replaced the early-return `if not query_terms: return results` with a conditional skip, enabling name-only search (NAME-03)
- Auto-fixed LanceDB constraint: empty query raises `ValueError` in hybrid mode; implemented scan fallback path
- Full TDD cycle: 7 RED tests committed before implementation; all 30 tests GREEN after

## Task Commits

1. **Task 1: RED — failing tests for name filter** - `2a03f2c` (test)
2. **Task 2: GREEN — implement name filter in engine.py** - `b25c4a4` (feat)

## Files Created/Modified
- `src/corpus_analyzer/search/engine.py` — Added `name=` param, empty-query scan path, name filter block
- `tests/search/test_engine.py` — Added `named_table` fixture and `TestHybridSearchNameFilter` (7 tests)

## Decisions Made
- Empty query uses `table.search()` plain scan rather than hybrid search: LanceDB's hybrid mode raises `ValueError: Text query must be provided` when `query=""`. The scan approach keeps all rows available for name filtering without requiring a text term.
- Name filter placed after text-term filter and before `min_score` — maintains the logical ordering of increasingly restrictive passes.
- `name=""` is treated as `None` via the falsy `if name:` check — an empty name fragment would match everything and is not useful as a filter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] LanceDB raises ValueError for empty text query in hybrid search mode**
- **Found during:** Task 2 (GREEN implementation)
- **Issue:** The plan stated "The LanceDB hybrid search still runs with query='' — this is fine for LanceDB" — this was incorrect. LanceDB raises `ValueError: Text query must be provided for hybrid search.` when `query=""` is passed to `.text()`.
- **Fix:** Added `is_empty_query = not query.strip()` branch. When true, uses `table.search()` (plain scan) with WHERE clauses built from source/file_type/construct_type filters. The text-term filter is already skipped for empty queries by the post-retrieval logic.
- **Files modified:** `src/corpus_analyzer/search/engine.py`
- **Verification:** `test_empty_query_with_name_skips_text_filter` passes; all 30 tests pass
- **Committed in:** `b25c4a4` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug in plan assumption about LanceDB empty query behaviour)
**Impact on plan:** Auto-fix essential for NAME-03 correctness. The scan fallback is semantically correct: empty query should return all matching rows, which a plain scan achieves without text ranking.

## Issues Encountered
None beyond the LanceDB empty-query bug documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Engine contract for NAME-01 and NAME-03 is complete
- `hybrid_search(name=...)` is fully functional and tested
- Phase 22 Plan 02 (CLI `--name` flag) can now wire `name=` through to the engine
- Phase 22 Plan 03 (MCP `corpus_search` name field) can also reference this engine contract

---
*Phase: 22-name-filtering*
*Completed: 2026-02-24*

## Self-Check: PASSED

- engine.py: FOUND
- test_engine.py: FOUND
- SUMMARY.md: FOUND
- commit 2a03f2c (RED tests): FOUND
- commit b25c4a4 (GREEN implementation): FOUND

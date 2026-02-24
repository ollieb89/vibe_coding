---
phase: 20-python-method-sub-chunking
plan: "01"
subsystem: ingest
tags: [python, ast, chunking, sub-chunking, tdd]

# Dependency graph
requires: []
provides:
  - "_chunk_class() helper in chunker.py extracts class header chunk from ClassDef AST node"
  - "chunk_python() now delegates ClassDef nodes to _chunk_class() instead of monolithic class chunks"
  - "10 new TestChunkPythonSubChunking tests covering all SUB-01 header extraction edge cases"
affects: [21-ts-method-sub-chunking, ingest/indexer, search quality]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "AST-based header extraction: decorators + signature + class attributes + __init__ self-assignments up to first non-assignment"
    - "SIM108 ternary style for conditional start_line assignment"

key-files:
  created: []
  modified:
    - src/corpus_analyzer/ingest/chunker.py
    - tests/ingest/test_chunker.py

key-decisions:
  - "_chunk_class() returns a list[dict] to allow future expansion (method chunks in Plan 02)"
  - "header_end_line for __init__-first-method uses stmt.end_lineno for precise line targeting"
  - "No existing tests required migration: current impl already produced named class chunks, only decorator inclusion and init truncation were new behaviours"

patterns-established:
  - "TDD RED: write tests against expected new behaviour; note that some may already pass if existing impl is partially correct"
  - "_chunk_class() iterates init_node.body directly (not ast.walk) to preserve linear statement order for truncation logic"

requirements-completed: [SUB-01]

# Metrics
duration: 3min
completed: 2026-02-24
---

# Phase 20 Plan 01: Python Class Header Sub-Chunking Summary

**AST-based _chunk_class() helper that extracts class contract chunks (decorators, signature, class attributes, __init__ self-assignments) from Python ClassDef nodes, replacing monolithic class chunks in chunk_python()**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-02-24T16:32:51Z
- **Completed:** 2026-02-24T16:35:14Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- Implemented `_chunk_class()` helper that extracts class header chunk from a ClassDef AST node
- Modified `chunk_python()` to call `_chunk_class()` for every ClassDef, removing monolithic class handling
- Header extraction correctly handles: decorators (start_line at first decorator), class-level attributes, __init__ self-assignment inclusion up to first non-assignment, and classes with no methods (full body as header)
- All 10 new `TestChunkPythonSubChunking` tests pass GREEN
- All 48 pre-existing tests continued to pass without modification — no migrations needed
- Full suite: 355 tests pass, ruff clean, mypy clean

## Task Commits

Each task was committed atomically:

1. **Task 1: RED — Failing tests for SUB-01** - `0acc8a4` (test)
2. **Task 2: GREEN — Implement _chunk_class()** - `ad77d6b` (feat)
3. **Task 3: REFACTOR — ruff/mypy cleanup** - `c12d97d` (refactor)

_Note: TDD tasks have three commits (test → feat → refactor)_

## Files Created/Modified
- `src/corpus_analyzer/ingest/chunker.py` — Added `_chunk_class()` helper (lines 196–264); modified `chunk_python()` loop to call it for ClassDef nodes
- `tests/ingest/test_chunker.py` — Added `TestChunkPythonSubChunking` class with 10 SUB-01 tests

## Decisions Made
- `_chunk_class()` returns `list[dict[str, Any]]` (not a single dict) to prepare for Plan 02 which will add method chunks to the return value
- Header end line for the `__init__`-is-first-method case uses `stmt.end_lineno` from the AST, which gives exact source line targeting without re-parsing
- The init body iteration walks `init_node.body` directly (not `ast.walk()`) to preserve linear order — `ast.walk()` would give unordered traversal unsuitable for truncation

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] SIM108 ternary style in _chunk_class()**
- **Found during:** Task 3 (REFACTOR — ruff check)
- **Issue:** `if node.decorator_list: ... else: ...` block flagged by ruff SIM108 rule
- **Fix:** Converted to ternary: `start_line = node.decorator_list[0].lineno if node.decorator_list else node.lineno`
- **Files modified:** `src/corpus_analyzer/ingest/chunker.py`
- **Verification:** `uv run ruff check` passes clean
- **Committed in:** c12d97d (Task 3 refactor commit)

**2. [Rule 1 - Bug] E501 line length violations in test file**
- **Found during:** Task 3 (REFACTOR — ruff check)
- **Issue:** 4 lines exceeding 100-char limit: `_get_header` error message, `write_text()` call, and two docstrings
- **Fix:** Split long lines using string concatenation and line wrapping
- **Files modified:** `tests/ingest/test_chunker.py`
- **Verification:** `uv run ruff check` passes clean
- **Committed in:** c12d97d (Task 3 refactor commit)

---

**Total deviations:** 2 auto-fixed (Rule 1 style/lint fixes found during REFACTOR phase)
**Impact on plan:** Minor style fixes only. No scope creep, no behaviour changes.

### Plan Observation

The plan assumed ALL 10 new tests would fail RED against the current implementation. In practice, 8 tests already passed because `chunk_python()` already produced named class chunks. Only 2 tests genuinely failed RED (decorator inclusion and init truncation at non-assignment). This is expected — the plan's assumptions were conservative. The 2 genuinely new behaviours were the key behavioral changes to implement.

## Issues Encountered
None — implementation was straightforward. The `ast.end_lineno` attribute (Python 3.8+) provided exact line ranges without needing source re-scanning.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `_chunk_class()` returns a list to accommodate method chunk additions in Plan 02
- Plan 02 (SUB-02) will extend `_chunk_class()` to also yield individual method chunks per ClassDef
- The class contract header is now a distinct, focused chunk suitable for LLM class-lookup queries

---
*Phase: 20-python-method-sub-chunking*
*Completed: 2026-02-24*

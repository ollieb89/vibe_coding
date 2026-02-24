---
phase: 15-core-ast-chunker
plan: 01
subsystem: testing
tags: [tree-sitter, typescript, tdd, chunking, ast]

# Dependency graph
requires: []
provides:
  - "TDD RED contract for chunk_typescript() covering all 8 node types, export unwrapping, JSDoc, error handling, caching"
  - "TestChunkTypeScript class with 21 test methods in tests/ingest/test_chunker.py"
  - "TestChunkFile updated with .ts/.tsx/.js/.jsx dispatch assertions"
affects: [15-02]

# Tech tracking
tech-stack:
  added: []
  patterns: ["TDD RED phase: import of non-existent module causes ModuleNotFoundError, establishing contract before implementation"]

key-files:
  created: []
  modified:
    - "tests/ingest/test_chunker.py"

key-decisions:
  - "Module-level import of ts_chunker ensures ALL tests in the file fail RED — consistent with TDD contract approach"
  - "TestChunkTypeScript placed between TestChunkLines and TestChunkFile to maintain logical ordering"
  - "test_dispatches_other_to_chunk_lines renamed to test_dispatches_ts_to_chunk_typescript to correctly reflect planned routing"

patterns-established:
  - "TDD RED import: place ts_chunker import at module level so collection fails cleanly with ModuleNotFoundError"
  - "Dispatch test pattern: use any(chunk_name in c.get('chunk_name', '') for c in chunks) to check AST routing"

requirements-completed: [TEST-01, TEST-02]

# Metrics
duration: 2min
completed: 2026-02-24
---

# Phase 15 Plan 01: Core AST Chunker TDD RED Summary

**21-method TDD RED contract for chunk_typescript() covering all 8 TS/JS node types, export unwrapping, JSDoc detection, error handling, and dispatch routing for .ts/.tsx/.js/.jsx**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-24T08:17:24Z
- **Completed:** 2026-02-24T08:19:08Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Extended `tests/ingest/test_chunker.py` with `TestChunkTypeScript` class containing 21 failing test methods
- Updated `TestChunkFile` with 4 new dispatch tests for `.ts`, `.tsx`, `.js`, `.jsx` extensions
- Confirmed RED state: `ModuleNotFoundError: No module named 'corpus_analyzer.ingest.ts_chunker'`
- All 276 tests outside `test_chunker.py` continue to pass (unbroken)

## Task Commits

Each task was committed atomically:

1. **Task 1: Write RED tests — TestChunkTypeScript + updated TestChunkFile** - `232bb0b` (test)

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `tests/ingest/test_chunker.py` - Added module-level `chunk_typescript` import (RED trigger), `TestChunkTypeScript` class with 21 test methods, updated `TestChunkFile` with 4 new dispatch assertions

## Decisions Made

- Used module-level import for `ts_chunker` so that pytest collection fails at the file level — this is the correct TDD RED pattern that cleanly blocks all tests in the file until the implementation exists
- Replaced `test_dispatches_other_to_chunk_lines` with `test_dispatches_ts_to_chunk_typescript` to correctly reflect the new routing intent for `.ts` files

## Deviations from Plan

None — plan executed exactly as written. Test count matches plan spec (21 TestChunkTypeScript + 4 updated TestChunkFile dispatch tests).

## Issues Encountered

None. The module-level import strategy works cleanly: `ModuleNotFoundError` at collection time means no individual test needs `pytest.importorskip` or similar guards.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Plan 02 (GREEN phase) is unblocked: implement `src/corpus_analyzer/ingest/ts_chunker.py` with `chunk_typescript()` and update `chunker.py` dispatch to route `.ts/.tsx/.js/.jsx` to it
- All 21 test methods define the exact contract `chunk_typescript()` must satisfy
- 276 non-chunker tests continue to pass — no collateral damage

---
*Phase: 15-core-ast-chunker*
*Completed: 2026-02-24*

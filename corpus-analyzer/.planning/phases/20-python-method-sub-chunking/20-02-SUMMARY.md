---
phase: 20-python-method-sub-chunking
plan: "02"
subsystem: ingest
tags: [python, ast, chunking, sub-chunking, tdd, method-chunks]

# Dependency graph
requires:
  - phase: 20-01
    provides: "_chunk_class() helper returning list[dict] for extensibility"
provides:
  - "_chunk_class() now returns header chunk + one ClassName.method_name chunk per FunctionDef/AsyncFunctionDef"
  - "14 new TestChunkPythonMethodChunks tests covering all SUB-02 method-chunk edge cases"
  - "Dot-notation method chunks: dunder, property, classmethod, staticmethod, async methods all named"
affects: [21-ts-method-sub-chunking, ingest/indexer, search quality]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Method chunk extraction: iterate node.body directly (not ast.walk) to keep nested classes opaque"
    - "Decorator-aware start_line: method_start = decorator_list[0].lineno if decorated else method.lineno"
    - "Dot-notation chunk name: f'{node.name}.{method.name}' for all method types"

key-files:
  created: []
  modified:
    - src/corpus_analyzer/ingest/chunker.py
    - tests/ingest/test_chunker.py

key-decisions:
  - "Only iterate node.body (direct children of ClassDef) — nested ClassDef bodies are not recursively sub-chunked; opaque content lives in the enclosing method chunk"
  - "Decorator start_line included in method chunk (method_start = decorator_list[0].lineno) so chunk captures full method definition"
  - "test_nested_not_separate updated: now asserts Outer.method chunk exists and nested() is not a separate chunk (count changed from 1 to 2)"

patterns-established:
  - "Sub-chunk naming: header uses ClassName, methods use ClassName.method_name — consistent dot notation for all class members"

requirements-completed: [SUB-02]

# Metrics
duration: 2min
completed: 2026-02-24
---

# Phase 20 Plan 02: Python Per-Method Sub-Chunking Summary

**Extended _chunk_class() to emit one ClassName.method_name chunk per method (FunctionDef/AsyncFunctionDef) alongside the header chunk, making every Python method independently searchable by name**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-24T16:37:34Z
- **Completed:** 2026-02-24T16:39:42Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- Extended `_chunk_class()` to append per-method chunks after the header chunk; only direct node.body iteration prevents recursive sub-chunking of nested classes
- All method types produce correct dot-notation names: `__init__`, `__str__`, `__repr__`, `@property`, `@classmethod`, `@staticmethod`, `async def`
- Decorator-aware start_line: if a method has decorators, the chunk starts at the first decorator line
- All 14 new `TestChunkPythonMethodChunks` tests pass GREEN; all 58 pre-phase tests continue to pass
- Full suite: 369 tests pass, ruff clean, mypy clean
- Updated `test_nested_not_separate` in `TestChunkPython` to reflect new per-method chunk counts (SUB-02 deviation)

## Task Commits

Each task was committed atomically:

1. **Task 1: RED — Failing SUB-02 tests** - `84a8379` (test)
2. **Task 2: GREEN — Extend _chunk_class() with per-method chunks** - `a2c3284` (feat)
3. **Task 3: REFACTOR — ruff + mypy cleanup** - `0246f9a` (refactor)

_Note: TDD tasks have three commits (test -> feat -> refactor)_

## Files Created/Modified
- `src/corpus_analyzer/ingest/chunker.py` — Extended `_chunk_class()`: appends one dict per FunctionDef/AsyncFunctionDef in node.body with chunk_name `ClassName.method_name`
- `tests/ingest/test_chunker.py` — Added `TestChunkPythonMethodChunks` class with 14 SUB-02 tests; updated `test_nested_not_separate` for new chunk counts

## Decisions Made
- Direct `node.body` iteration (not `ast.walk()`) keeps nested class bodies opaque — a `def method(self)` that contains `class Inner` does not yield `Outer.Inner.inner_method` chunks; `inner_method` is opaque content inside the `Outer.method` chunk
- Decorator start_line is always the first decorator's lineno, so the full method signature including decorators is captured in the chunk text
- `test_nested_not_separate` required updating: the test's intent (nested functions inside methods are not top-level chunks) remains valid; the count assertion `== 1` was incorrect with SUB-02 since `Outer.method` is now a separate chunk

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_nested_not_separate count assertion incompatible with SUB-02**
- **Found during:** Task 2 (GREEN — extend _chunk_class())
- **Issue:** `test_nested_not_separate` asserted `len(chunks) == 1` for a class with one method. With SUB-02, `_chunk_class()` now produces 2 chunks (header + method chunk), breaking this assertion
- **Fix:** Updated test docstring and assertion to check chunk_names instead of count: `"nested" not in chunk_names` (nested function is not a top-level chunk) and `"Outer.method" in chunk_names` (method IS a sub-chunk)
- **Files modified:** `tests/ingest/test_chunker.py`
- **Verification:** `uv run pytest tests/ingest/test_chunker.py -v` — 72 tests pass
- **Committed in:** a2c3284 (Task 2 feat commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — pre-existing test assertion incompatible with new sub-chunking behaviour)
**Impact on plan:** Necessary update; the test's semantic intent is preserved (nested functions are not top-level chunks). No scope creep.

## Issues Encountered
None — implementation was straightforward. The plan's pseudocode translated directly to working code with no surprises.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- SUB-01 (class header) and SUB-02 (per-method) are both complete for Python
- Phase 21 (21-ts-method-sub-chunking) can now implement the same pattern for TypeScript/JavaScript via tree-sitter
- chunk_python() now produces 3+ chunks per class-with-methods: 1 header (ClassName) + N method chunks (ClassName.method_name)
- Any integration test that asserts exact chunk counts for Python classes will need updating in Phase 21 or later

---
*Phase: 20-python-method-sub-chunking*
*Completed: 2026-02-24*

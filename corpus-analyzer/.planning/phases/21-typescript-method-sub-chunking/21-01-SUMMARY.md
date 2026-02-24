---
phase: 21-typescript-method-sub-chunking
plan: "01"
subsystem: ingest
tags: [typescript, tree-sitter, chunking, sub-chunking, tdd, method-chunks]

# Dependency graph
requires:
  - phase: 20-python-method-sub-chunking
    provides: "_chunk_class() pattern: header chunk + per-method dot-notation chunks"
provides:
  - "_chunk_ts_class() helper: header chunk + one ClassName.method_name chunk per method_definition or abstract_method_signature"
  - "13 new TestChunkTypeScriptMethodChunks tests covering all SUB-03 cases"
  - "TypeScript classes fully sub-chunked: constructor, concrete methods, abstract methods all produce individual chunks"
affects: [22-name-filter, ingest/indexer, search quality, round-trip tests]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TS method chunk extraction: iterate class_body.children directly for method_definition + abstract_method_signature nodes"
    - "Abstract method support: abstract_method_signature node type uses child_by_field_name('name') same as method_definition"
    - "Module-level _METHOD_NODE_TYPES frozenset: avoids N806 ruff violation vs inline constant"
    - "Dot-notation chunk name: f'{class_name}.{method_name}' for all TypeScript method types"

key-files:
  created: []
  modified:
    - src/corpus_analyzer/ingest/ts_chunker.py
    - tests/ingest/test_chunker.py

key-decisions:
  - "Include abstract_method_signature in _METHOD_NODE_TYPES alongside method_definition — tree-sitter TypeScript grammar uses a distinct node type for abstract method declarations"
  - "Module-level _METHOD_NODE_TYPES constant (not inline in function) to satisfy ruff N806 rule"
  - "Direct class_body.children iteration (no recursion) keeps nested class bodies opaque — consistent with Python Phase 20 pattern"
  - "Header end_line = first_method.start_point[0] (0-indexed row of first method == 1-indexed line of preceding line)"

patterns-established:
  - "TS sub-chunk naming: header uses ClassName, methods use ClassName.method_name — mirrors Python Phase 20 dot notation"

requirements-completed: [SUB-03]

# Metrics
duration: 3min
completed: 2026-02-24
---

# Phase 21 Plan 01: TypeScript Method Sub-Chunking Summary

**TypeScript class sub-chunking via tree-sitter: _chunk_ts_class() splits any class_declaration or abstract_class_declaration into a header chunk plus one ClassName.method_name chunk per method, making every TypeScript method independently searchable**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-02-24T17:04:30Z
- **Completed:** 2026-02-24T17:07:24Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- Added `_chunk_ts_class()` helper to `ts_chunker.py`: emits header chunk + per-method chunks for class nodes
- Handles both `method_definition` (concrete/constructor) and `abstract_method_signature` (abstract) node types
- Integrated into `chunk_typescript()` main loop via an early branch before the single-chunk path
- All 13 new `TestChunkTypeScriptMethodChunks` tests pass GREEN; all 24 pre-existing `TestChunkTypeScript` tests pass
- Full suite: 382 tests pass (369 pre-phase + 13 new), ruff clean, mypy clean

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing SUB-03 TypeScript method chunk tests** - `ddeaa9e` (test)
2. **Task 2 GREEN: Add _chunk_ts_class() with per-method chunks** - `4385799` (feat)
3. **Task 3: ruff + mypy clean** - `0eab6ea` (refactor)

_Note: TDD tasks have three commits (test -> feat -> refactor)_

## Files Created/Modified
- `src/corpus_analyzer/ingest/ts_chunker.py` — Added `_METHOD_NODE_TYPES` module constant, `_chunk_ts_class()` helper, and early-branch integration in `chunk_typescript()` main loop
- `tests/ingest/test_chunker.py` — Added `TestChunkTypeScriptMethodChunks` class with 13 SUB-03 test cases

## Decisions Made
- `abstract_method_signature` must be included alongside `method_definition` in the collected node types — tree-sitter's TypeScript grammar emits abstract methods under a distinct node type, not as `method_definition`. Discovered during Task 2 GREEN when `test_abstract_method_chunked` failed.
- `_METHOD_NODE_TYPES` defined at module level to satisfy ruff N806 rule (variable in function must be lowercase).
- Direct `class_body.children` iteration (no recursion) keeps nested class literal bodies opaque inside their enclosing method chunk — consistent with Phase 20 Python pattern.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] abstract_method_signature node type not initially included**
- **Found during:** Task 2 (GREEN — first test run)
- **Issue:** `test_abstract_method_chunked` failed because `_chunk_ts_class()` only collected `method_definition` nodes; tree-sitter TypeScript uses `abstract_method_signature` for `abstract run(): void;` declarations
- **Fix:** Added `abstract_method_signature` to `_METHOD_NODE_TYPES`; both node types support `child_by_field_name("name")` for name extraction
- **Files modified:** `src/corpus_analyzer/ingest/ts_chunker.py`
- **Verification:** `uv run pytest tests/ingest/test_chunker.py::TestChunkTypeScriptMethodChunks -v` — 13/13 pass
- **Committed in:** `4385799` (Task 2 feat commit, discovered and fixed in same iteration)

---

**Total deviations:** 1 auto-fixed (Rule 1 — tree-sitter grammar reality: abstract methods use a different node type than concrete methods)
**Impact on plan:** Necessary discovery during GREEN implementation; fully consistent with plan intent. No scope creep.

## Issues Encountered
- The plan stated "Abstract methods: tree-sitter emits abstract method declarations as `method_definition` nodes" — this was incorrect. Tree-sitter TypeScript grammar uses `abstract_method_signature` for abstract methods. Fixed immediately upon test failure.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- SUB-03 (TypeScript method sub-chunking) is complete
- Phase 22 (NAME-01–03 name filter) can proceed
- TypeScript classes now produce 3+ chunks for classes with methods: 1 header (ClassName) + N method chunks (ClassName.method_name)
- Any integration test asserting exact chunk counts for TypeScript classes will need updating if not already updated

---
*Phase: 21-typescript-method-sub-chunking*
*Completed: 2026-02-24*

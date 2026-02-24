---
phase: 15-core-ast-chunker
plan: 02
subsystem: testing
tags: [tree-sitter, typescript, ast, chunking, tdd-green]

# Dependency graph
requires:
  - phase: 15-01
    provides: "TDD RED test contract: 21 TestChunkTypeScript + 4 TestChunkFile dispatch tests"
provides:
  - "chunk_typescript() — tree-sitter AST chunker for .ts/.tsx/.js/.jsx files"
  - "_get_cached_parser(dialect) — @lru_cache grammar loader"
  - "_extract_name() — name resolution for all 8 target node types incl. export default"
  - "Updated chunk_file() dispatch routing .ts/.tsx/.js/.jsx to chunk_typescript"
  - "tree-sitter and tree-sitter-language-pack added to pyproject.toml"
affects: []

# Tech tracking
tech-stack:
  added:
    - "tree-sitter==0.25.2 (pre-compiled wheel, no C toolchain)"
    - "tree-sitter-language-pack==0.13.0 (bundles typescript, tsx, javascript grammars)"
  patterns:
    - "AST-aware chunking: walk root_node.children, unwrap export_statement, extract named constructs"
    - "Lazy import inside chunk_file to avoid circular imports (ts_chunker imports from chunker)"
    - "@lru_cache on grammar loader: one Parser per dialect per process"
    - "Partial-parse tolerance: fallback only on exception or zero constructs, NOT on has_error"
    - "JSDoc lookback: prev_sibling walk + adjacency check (gap <= 1 row)"

key-files:
  created:
    - "src/corpus_analyzer/ingest/ts_chunker.py"
  modified:
    - "src/corpus_analyzer/ingest/chunker.py"
    - "pyproject.toml"
    - "uv.lock"

key-decisions:
  - "tree-sitter-language-pack get_parser() wraps @lru_cache to avoid re-parsing grammars"
  - "export default anonymous function: declaration field is None, so detect 'default' child and emit full export_statement as chunk_name='default'"
  - "No fallback on root_node.has_error: partial trees still yield good constructs"
  - "JSX uses tsx grammar (not javascript) to handle JSX element nodes correctly"
  - "Lazy import of ts_chunker inside chunk_file elif branch avoids circular import"

patterns-established:
  - "ts_chunker.py pattern: _DIALECT map + _TARGET_TYPES frozenset + @lru_cache getter + name extractor + main chunker"
  - "Export default handling: check for 'default' child when declaration field is None, emit full export_statement"
  - "mypy strict compliance: use str() cast on Any.decode() to satisfy no-any-return; use type: ignore[arg-type] for Literal dialect param"

requirements-completed: [DEP-01, IDX-01, IDX-02, IDX-03, IDX-04, IDX-05, IDX-06, IDX-07]

# Metrics
duration: 12min
completed: 2026-02-24
---

# Phase 15 Plan 02: Core AST Chunker GREEN Summary

**AST-aware TypeScript/JavaScript chunker using tree-sitter: extracts 8 node types (function, class, interface, type alias, enum, generator, abstract class, lexical declaration) with correct 1-indexed line boundaries, JSDoc lookback, export unwrapping, and @lru_cache grammar loading — 318 tests GREEN**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-24T08:30:00Z
- **Completed:** 2026-02-24T08:42:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Created `src/corpus_analyzer/ingest/ts_chunker.py` (155 lines) with `chunk_typescript()`, `_get_cached_parser()`, `_extract_name()`, `_DIALECT`, and `_TARGET_TYPES`
- Updated `chunk_file()` in `chunker.py` to route `.ts/.tsx/.js/.jsx` to `chunk_typescript` via lazy import
- Added `tree-sitter>=0.25.0` and `tree-sitter-language-pack>=0.13.0` to `pyproject.toml` with mypy overrides
- All 21 TestChunkTypeScript + 7 TestChunkFile tests GREEN; 318 total tests passing (up from 276)
- Ruff-clean and mypy --strict-clean

## Task Commits

Each task was committed atomically:

1. **Task 1: Add deps to pyproject.toml and run uv sync** - `603b19a` (chore)
2. **Task 2: Implement ts_chunker.py and wire dispatch in chunker.py** - `2d70c29` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `src/corpus_analyzer/ingest/ts_chunker.py` - New: chunk_typescript(), _get_cached_parser(), _extract_name(), _DIALECT, _TARGET_TYPES
- `src/corpus_analyzer/ingest/chunker.py` - Updated chunk_file() elif branch for .ts/.tsx/.js/.jsx → chunk_typescript with lazy import
- `pyproject.toml` - Added tree-sitter and tree-sitter-language-pack deps + mypy overrides
- `uv.lock` - Updated lockfile with 5 new packages

## Decisions Made

- `export default function(): void {}` — tree-sitter parses this as `export_statement` with `declaration` field = `None` and a `function_expression` named child. The plan's `_extract_name()` approach (checking `export_node.children` for `default` type) was not triggered because the code hit `continue` before reaching `_extract_name`. Fixed by detecting the `default` child node within the `declaration is None` branch and emitting the full statement as a `"default"`-named chunk.
- Removed `# type: ignore[import-untyped]` from imports (now handled by `[[tool.mypy.overrides]]`) to avoid `unused-ignore` errors under `warn_unused_ignores = true`
- Used `str()` wrap on `.decode("utf-8")` returns to satisfy `no-any-return` mypy strict rule

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] export default anonymous function produced no chunk**
- **Found during:** Task 2 (after running `uv run pytest tests/ingest/test_chunker.py`)
- **Issue:** `export default function(): void {}` has `child_by_field_name("declaration") == None` in tree-sitter, so the code hit `continue` without emitting a chunk. The test expected `chunk_name == "default"`.
- **Fix:** Added a `has_default` check in the `inner is None` branch: when a `default` child exists, emit the full `export_statement` as a chunk with `chunk_name = "default"` before `continue`-ing.
- **Files modified:** `src/corpus_analyzer/ingest/ts_chunker.py`
- **Verification:** `test_export_default_function` passes; all 22 TestChunkTypeScript tests GREEN
- **Committed in:** `2d70c29` (Task 2 commit)

**2. [Rule 2 - Lint] SIM102 nested if and mypy strict errors**
- **Found during:** Task 2 (ruff check + mypy run post-implementation)
- **Issue:** SIM102 (nested if), unused type: ignore comments, arg-type Literal mismatch for `get_parser`, no-any-return on `.decode()` returns
- **Fix:** Combined nested if with `and`; removed stale type: ignore comments; added `# type: ignore[arg-type]` on `get_parser()` call; wrapped decode returns with `str()`
- **Files modified:** `src/corpus_analyzer/ingest/ts_chunker.py`
- **Verification:** `ruff check` and `mypy src/` both exit 0
- **Committed in:** `2d70c29` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 lint/type)
**Impact on plan:** Both fixes necessary for correctness and code quality. No scope creep.

## Issues Encountered

The initial `uv sync` without `--all-extras` uninstalled dev packages (pytest, mypy, ruff, coverage). Re-synced with `--all-extras` to restore them before running tests. Not a blocker — test run succeeded immediately after.

## User Setup Required

None — tree-sitter-language-pack ships pre-compiled wheels; no C toolchain or external service configuration required.

## Next Phase Readiness

- Phase 15 (Core AST Chunker) complete — both plans done
- Phase 16 (if planned) has full TypeScript/JavaScript AST chunking available via `chunk_typescript`
- 318 tests passing, ruff-clean, mypy-clean — solid foundation for next milestone phase
- `chunk_file()` now routes all 4 TS/JS extensions through the AST-aware path

## Self-Check: PASSED

---
*Phase: 15-core-ast-chunker*
*Completed: 2026-02-24*

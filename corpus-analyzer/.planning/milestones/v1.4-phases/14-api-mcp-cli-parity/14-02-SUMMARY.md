---
phase: 14-api-mcp-cli-parity
plan: "02"
subsystem: api
tags: [python-api, mcp, search, min-score, sort-by, parity]

# Dependency graph
requires:
  - phase: 13-engine-min-score-filter
    provides: min_score parameter on hybrid_search() and _relevance_score post-retrieval filter
provides:
  - sort_by parameter on Python public search() API with _API_SORT_MAP translation (score/date/title -> relevance/date/path)
  - min_score parameter on Python public search() API forwarded to hybrid_search()
  - min_score Optional[float] parameter on MCP corpus_search() tool with None->0.0 conversion
  - ValueError with 'Invalid sort_by' message on invalid sort_by values
  - filtered_by_min_score: True signal in MCP empty-results response when min_score filters all
affects:
  - 14-01 (CLI tier — shares same engine, parallel surface work)
  - Future API consumers using search() or corpus_search()

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "_API_SORT_MAP translation dict pattern: API vocabulary -> engine vocabulary at boundary layer"
    - "frozenset for O(1) membership validation of allowed parameter values"
    - "Optional[float] = None with explicit None->default conversion in MCP tool parameters"
    - "# noqa: UP045 comment for Optional typing in FastMCP tool signatures"

key-files:
  created: []
  modified:
    - src/corpus_analyzer/api/public.py
    - src/corpus_analyzer/mcp/server.py
    - tests/api/test_public.py
    - tests/mcp/test_server.py

key-decisions:
  - "_API_SORT_MAP dict translates user-facing sort vocabulary (score/date/title) to engine vocabulary (relevance/date/path) at the API boundary — keeps each layer's naming conventions independent"
  - "sort_by validation raises ValueError before engine call — fast-fail with clear message listing valid options"
  - "MCP min_score None->0.0 conversion is explicit in the function body, not using a walrus operator — matches existing Optional patterns in corpus_search()"
  - "filtered_by_min_score: True added to empty-results dict when min_score is truthy — gives MCP clients a programmatic signal distinct from 'no matches found'"

patterns-established:
  - "API boundary translation: always map user-facing parameter vocabulary to engine vocabulary at call site, never expose engine internals"
  - "frozenset(_MAP.keys()) for validation set — single source of truth for both map and valid values"

requirements-completed: [PARITY-01, PARITY-02, PARITY-03]

# Metrics
duration: 3min
completed: 2026-02-24
---

# Phase 14 Plan 02: API and MCP Parity Summary

**sort_by+min_score added to Python search() API with _API_SORT_MAP translation, and min_score Optional[float] added to MCP corpus_search() — completing PARITY-01, PARITY-02, PARITY-03**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-24T07:01:58Z
- **Completed:** 2026-02-24T07:04:40Z
- **Tasks:** 2 (TDD: 1 RED + 1 GREEN)
- **Files modified:** 4

## Accomplishments
- Python `search()` API gains `sort_by` (default `"score"`) with `_API_SORT_MAP` translating to engine vocabulary, plus `min_score: float = 0.0` forwarded directly
- `sort_by` validation raises `ValueError` with clear message listing allowed values before any engine call
- MCP `corpus_search()` gains `min_score: Optional[float] = None` — converted to `0.0` when `None`, forwarded to `hybrid_search()`
- Empty results with non-zero `min_score` include `"filtered_by_min_score": True` signal for MCP clients
- 7 new / updated test assertions across both test files; all 18 API+MCP tests pass
- ruff and mypy both clean

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing API and MCP tests for PARITY-01/02/03** - `10d043f` (test)
2. **Task 2 GREEN: sort_by + min_score in Python API and min_score in MCP** - `fa90279` (feat)

**Plan metadata:** (docs commit — created at end)

_Note: TDD plan — RED commit then GREEN commit._

## Files Created/Modified
- `src/corpus_analyzer/api/public.py` - Added `_API_SORT_MAP`, `_VALID_API_SORT_VALUES`, `sort_by`/`min_score` params to `search()`; validation; translation forwarded to `hybrid_search()`
- `src/corpus_analyzer/mcp/server.py` - Added `min_score: Optional[float] = None` to `corpus_search()`; `None->0.0` conversion; `filtered_by_min_score` signal; updated docstring
- `tests/api/test_public.py` - Updated 2 existing assertions + added 3 new tests (sort translation, ValueError, min_score forwarding)
- `tests/mcp/test_server.py` - Updated 1 existing assertion + added 2 new tests (min_score forwarded, None->0.0)

## Decisions Made
- `_API_SORT_MAP` dict translates user-facing sort vocabulary (`score`/`date`/`title`) to engine vocabulary (`relevance`/`date`/`path`) at the API boundary — keeps each layer's naming conventions independent
- `sort_by` validation raises `ValueError` before engine call — fast-fail with clear message listing valid options via `sorted(_VALID_API_SORT_VALUES)`
- MCP `min_score` `None->0.0` conversion is explicit (`min_score if min_score is not None else 0.0`) — matches existing `Optional` patterns in `corpus_search()`
- `filtered_by_min_score: True` added to empty-results dict only when `min_score` is truthy — distinct signal from "no matches" for MCP clients

## Deviations from Plan

None — plan executed exactly as written.

**Note on pre-existing test failure:** `tests/cli/test_search_status.py::test_min_score_option_help_text` was already failing before this plan (RED test from 14-01 CLI work, not yet implemented). Verified via git stash. Not in scope for 14-02 (API+MCP tier only). Will be resolved by 14-01 execution.

## Issues Encountered
Pre-existing RED test `test_min_score_option_help_text` in `tests/cli/test_search_status.py` — this is the 14-01 CLI tier RED test committed in a prior session. Confirmed via git stash that it existed before my changes. Not introduced by this plan.

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- PARITY-01, PARITY-02, PARITY-03 complete — Python API and MCP surfaces for min-score engine finished
- CLI surface (14-01) is the remaining tier for full v1.4 parity
- 292 tests passing (7 new in this plan); ruff-clean; mypy-clean
- Ready for 14-01 CLI implementation

---
*Phase: 14-api-mcp-cli-parity*
*Completed: 2026-02-24*

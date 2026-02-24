---
phase: 14-api-mcp-cli-parity
plan: "01"
subsystem: cli
tags: [typer, search, min-score, sort-by, rrf, filt-02, filt-03]

requires:
  - phase: 13-engine-min-score-filter
    provides: min_score parameter on hybrid_search() and RRF post-filter logic

provides:
  - "--min-score option on corpus search CLI with RRF range help text (FILT-02)"
  - "FILT-03 hint: 'No results above X.XXX. Run without --min-score...' on filtered-all"
  - "--sort-by option translating score|date|title to engine vocabulary"
  - "_CLI_SORT_BY_MAP and _VALID_CLI_SORT_BY_VALUES constants in cli.py"

affects:
  - 14-api-mcp-cli-parity (remaining plans for API and MCP parity)

tech-stack:
  added: []
  patterns:
    - "API-vocabulary translation map (_CLI_SORT_BY_MAP) decouples CLI UX from engine internals"
    - "Sentinel None default on --sort-by distinguishes user-provided from defaulted value"
    - "FILT-03 hint: branch on min_score > 0.0 before generic no-results message"

key-files:
  created:
    - tests/cli/test_search_status.py (three new tests appended)
  modified:
    - src/corpus_analyzer/cli.py
    - tests/cli/test_search_status.py
    - tests/api/test_public.py

key-decisions:
  - "sort_by defaults to None (sentinel) so CLI can distinguish user-provided --sort-by from the default, falling back to --sort when not provided"
  - "Rich terminal wraps long help text across lines; test asserts tokens individually, not as contiguous substring"
  - "Pre-existing SIM117 ruff violation in tests/api/test_public.py auto-fixed as Rule 1 blocking exit criteria"

patterns-established:
  - "CLI option translation: use a frozenset for validation and a dict for value mapping"
  - "TDD with CliRunner: invoke app, assert exact substring in result.stdout"

requirements-completed: [FILT-02, FILT-03]

duration: 4min
completed: 2026-02-24
---

# Phase 14 Plan 01: CLI --min-score and --sort-by Summary

**`--min-score` with RRF range help (FILT-02), filtered-all FILT-03 hint, and API-vocabulary `--sort-by score|date|title` added to `corpus search` CLI**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-24T07:02:00Z
- **Completed:** 2026-02-24T07:06:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- `--min-score` option added with help text documenting RRF score range (~0.009–0.033)
- FILT-03 contextual hint: `No results above X.XXX. Run without --min-score to see available scores.`
- `--sort-by` with API vocabulary (`score|date|title`) translated to engine vocabulary via `_CLI_SORT_BY_MAP`
- 293 tests passing, ruff clean, mypy clean

## Task Commits

1. **Task 1 RED: Failing CLI tests for FILT-02, FILT-03, --sort-by** - `d310e62` (test)
2. **Task 2 GREEN: Implement --min-score, FILT-03 hint, --sort-by** - `a4ac067` (feat)

**Plan metadata:** (docs commit — see below)

_Note: TDD tasks have two commits (test RED → feat GREEN)_

## Files Created/Modified

- `src/corpus_analyzer/cli.py` — Added `_CLI_SORT_BY_MAP`, `_VALID_CLI_SORT_BY_VALUES`, `--min-score` option, `--sort-by` option (sentinel None default), `effective_sort_by` resolution, FILT-03 branch in no-results block
- `tests/cli/test_search_status.py` — Appended `test_min_score_option_help_text`, `test_min_score_filters_all_prints_hint`, `test_sort_by_option_forwards_to_engine`
- `tests/api/test_public.py` — Combined nested `with` blocks into single `with` statement (SIM117 auto-fix)

## Decisions Made

- `--sort-by` uses `None` as sentinel default so the CLI can detect when the user explicitly passed it vs falling back to `--sort`; this preserves all existing `--sort` behavior unchanged
- Rich wraps long help text across table-row boundaries; test assertions use individual token checks rather than contiguous substring to avoid fragility against terminal width changes

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test assertion adapted for Rich terminal line-wrapping**
- **Found during:** Task 1 RED → Task 2 GREEN verification
- **Issue:** Plan specified asserting `"RRF scores range approximately 0.009"` as a contiguous string, but Rich wraps help text across display lines with padding, so the full phrase was never contiguous in stdout
- **Fix:** Split assertion into three individual token checks: `"RRF scores range approximately"`, `"0.009"`, `"0.0 keeps all results"`
- **Files modified:** `tests/cli/test_search_status.py`
- **Verification:** All 12 CLI tests pass
- **Committed in:** a4ac067 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed pre-existing SIM117 ruff violation in tests/api/test_public.py**
- **Found during:** Task 2 GREEN verification (`uv run ruff check .`)
- **Issue:** Nested `with` blocks in `test_search_invalid_sort_by_raises` failed ruff SIM117 check, blocking the `ruff check . → exit 0` success criterion
- **Fix:** Merged nested `with patch(...):` and `with pytest.raises(...):` into a single `with (patch(...), pytest.raises(...)):` statement
- **Files modified:** `tests/api/test_public.py`
- **Verification:** `uv run ruff check .` exits 0
- **Committed in:** a4ac067 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 - correctness)
**Impact on plan:** Both necessary for test correctness and plan exit criteria. No scope creep.

## Issues Encountered

None — implementation was straightforward once the Rich line-wrapping constraint was identified.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- FILT-02 and FILT-03 requirements satisfied at CLI surface
- `--sort-by` translation map pattern established; can be reused in API/MCP plans
- Phase 14 plans 02 and 03 (API and MCP parity) are unblocked

---
*Phase: 14-api-mcp-cli-parity*
*Completed: 2026-02-24*

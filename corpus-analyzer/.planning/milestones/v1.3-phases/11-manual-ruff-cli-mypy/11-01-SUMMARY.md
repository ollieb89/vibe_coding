---
phase: 11-manual-ruff-cli-mypy
plan: "01"
subsystem: cli
tags: [ruff, E501, B023, B904, typer, line-wrapping]

requires:
  - phase: 10-manual-ruff-leaf-to-hub
    provides: Zero ruff violations in all files except cli.py

provides:
  - Zero ruff violations in cli.py (E501, B023, B904 all fixed)
  - Full project ruff clean: `uv run ruff check .` exits 0
affects: [12-mypy]

tech-stack:
  added: []
  patterns:
    - "Annotated[...] parameter wrapping: split type and typer.Option across 3 lines"
    - "Default-arg capture for loop closures: `def f(n, _id=task_id)` pattern"
    - "raise ... from None for deliberate exception suppression in except blocks"

key-files:
  created: []
  modified:
    - src/corpus_analyzer/cli.py

key-decisions:
  - "B023 progress_callback fix: default-arg capture (not functools.partial) — does not change external Callable[[int], None] signature"
  - "B904 search_command: use from None (not from e) — exit is deliberate suppression, not chaining"
  - "Shortened two help strings to fit in 100 chars: construct filter and auto_category"
  - "Extracted best_count local variable in rewrite auto_category to avoid repeated indexing"

patterns-established:
  - "Long Typer Annotated parameters: always wrap to 3 lines (type on line 2, Option on line 3)"
  - "Ternary expressions exceeding 100 chars: parenthesise with each branch on its own line"

requirements-completed:
  - RUFF-07

duration: 18min
completed: 2026-02-24
---

# Phase 11 Plan 01: cli.py Ruff-Clean Summary

**cli.py cleaned of all 47 ruff violations (45 E501 line-length + B023 loop closure + B904 raise-in-except), giving a project-wide zero-violation ruff baseline**

## Performance

- **Duration:** 18 min
- **Started:** 2026-02-24T00:00:00Z
- **Completed:** 2026-02-24T00:18:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Fixed B023: `progress_callback` now uses default-arg capture (`_task_id: TaskID = task_id`) to avoid loop-variable closure issue
- Fixed B904: `raise typer.Exit(code=1) from None` in `search_command` except block
- Wrapped all 45 E501 violations using multi-line `Annotated[...]` parameter syntax
- `uv run ruff check .` now exits 0 with zero output across the entire project
- All 281 tests continue to pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix B023 and B904 semantic violations in cli.py** - `68a5bb7` (fix)
2. **Task 2: Wrap all 45 E501 violations in cli.py** - `3dd0ff5` (fix)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified
- `src/corpus_analyzer/cli.py` - All 47 ruff violations fixed; no logic changes

## Decisions Made
- B023 fix uses default-arg capture (`_task_id: TaskID = task_id`), not `functools.partial` — keeps the external `Callable[[int], None]` signature unchanged
- B904 uses `from None` (not `from e`) because the typer.Exit is deliberate suppression of the RuntimeError, not chaining
- Two help strings shortened (construct filter from 181 chars, auto_category from 145 chars) — only option that fits without breaking the line structure
- Extracted `best_count` local variable in `rewrite` to avoid repeating `len(category_scores[best_category])` twice and eliminate one E501

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `uv run ruff check .` passes with zero violations — Phase 12 (mypy) can begin immediately
- All 281 tests passing; no regressions from formatting changes

---
*Phase: 11-manual-ruff-cli-mypy*
*Completed: 2026-02-24*

## Self-Check: PASSED

- FOUND: src/corpus_analyzer/cli.py
- FOUND: .planning/phases/11-manual-ruff-cli-mypy/11-01-SUMMARY.md
- FOUND: commit 68a5bb7 (Task 1)
- FOUND: commit 3dd0ff5 (Task 2)

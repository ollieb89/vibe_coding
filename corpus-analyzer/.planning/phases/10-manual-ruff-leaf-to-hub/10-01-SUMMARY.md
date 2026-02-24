---
phase: 10-manual-ruff-leaf-to-hub
plan: 01
subsystem: linting
tags: [ruff, E741, E402, B017, pydantic, concurrent.futures]

# Dependency graph
requires:
  - phase: 09-config-and-autofix
    provides: ruff auto-fix pass eliminating 370 auto-fixable violations
provides:
  - E741-clean database.py and chunked_processor.py (ambiguous variable names renamed)
  - E402-clean llm/rewriter.py (import concurrent.futures moved to top; duplicate NamedTuple import removed)
  - B017-clean tests/store/test_schema.py (ValidationError used instead of bare Exception)
  - scripts/ with zero ruff violations (F401/W293 auto-fixed)
affects: [10-02, 10-03, 10-04, 11-mypy-fixes]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Rename l -> link/lnk/line/level_val for E741 compliance"
    - "Mid-file imports extracted to top-of-file stdlib block"
    - "pytest.raises(ValidationError) instead of bare Exception for B017 compliance"

key-files:
  created: []
  modified:
    - src/corpus_analyzer/core/database.py
    - src/corpus_analyzer/llm/chunked_processor.py
    - src/corpus_analyzer/llm/rewriter.py
    - tests/store/test_schema.py
    - scripts/run_rewrite_dry_run.py

key-decisions:
  - "Use lnk (not link2 or link_obj) for the deserialization rename to avoid shadowing the Link class import"
  - "level_val (not lvl or heading_level) for chunked_processor rename — matches semantics of force_level/current_level"
  - "ruff --fix (not --unsafe-fixes) sufficient for scripts/ F401/W293; no unsafe fixes needed"

patterns-established:
  - "E741 renames must propagate all downstream uses within the same scope"
  - "Mid-file imports must be removed from their mid-file position after adding to top block"

requirements-completed: [RUFF-04, RUFF-05, RUFF-06]

# Metrics
duration: 12min
completed: 2026-02-24
---

# Phase 10 Plan 01: Manual Ruff Leaf-to-Hub Semantic Fixes Summary

**Four E741 ambiguous variable renames, one E402 import reorganization, two B017 ValidationError replacements, and scripts/ auto-fix — all 281 tests passing**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-24T04:33:00Z
- **Completed:** 2026-02-24T04:45:00Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- Eliminated all E741 violations: `l` renamed to `link`/`lnk` in database.py and `level_val`/`line` in chunked_processor.py
- Fixed E402 in rewriter.py: `import concurrent.futures` moved to top stdlib block; duplicate `from typing import NamedTuple` (line 233) deleted
- Fixed B017 in test_schema.py: added `from pydantic import ValidationError`; replaced both `pytest.raises(Exception)` with `pytest.raises(ValidationError)` — tests confirm ValidationError is actually raised
- Auto-fixed scripts/run_rewrite_dry_run.py: removed unused `from corpus_analyzer.config import settings` (F401) and trailing whitespace (W293)

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix E741 ambiguous variable names** - `eab2a56` (fix)
2. **Task 2: Fix E402 mid-file imports in rewriter.py** - `a9dcc0b` (fix)
3. **Task 3: Fix B017 + auto-fix scripts/** - `1f4247e` (fix)

## Files Created/Modified
- `src/corpus_analyzer/core/database.py` - line 150: `l` -> `link`; line 310: `l` -> `lnk`
- `src/corpus_analyzer/llm/chunked_processor.py` - line 64: `l` -> `level_val` + `level=l` -> `level=level_val`; line 141: `l` -> `line`
- `src/corpus_analyzer/llm/rewriter.py` - added `import concurrent.futures` to top block; removed mid-file duplicate imports (lines 232-235)
- `tests/store/test_schema.py` - added `from pydantic import ValidationError`; replaced 2x `pytest.raises(Exception)` with `pytest.raises(ValidationError)`
- `scripts/run_rewrite_dry_run.py` - removed unused import and trailing whitespace via ruff --fix

## Decisions Made
- Used `lnk` (not `link2`) for the second rename in database.py to avoid shadowing the imported `Link` class name
- Used `level_val` for chunked_processor.py to match the semantics of the force_level/current_level source variables
- ruff `--fix` (safe fixes only) was sufficient for scripts/ — no `--unsafe-fixes` needed

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None. The `pydantic.ValidationError` import worked correctly on first attempt — no need to try `pydantic_core.ValidationError` alternative.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All semantic violations (E741, E402, B017) eliminated from target files
- 281 tests passing confirms no regressions from variable renames or import moves
- Ready for Phase 10 Plan 02: E501 line-wrapping on the same leaf-to-hub files

## Self-Check: PASSED

All 5 files confirmed present. All 3 task commits confirmed in git history.

---
*Phase: 10-manual-ruff-leaf-to-hub*
*Completed: 2026-02-24*

---
phase: 11-manual-ruff-cli-mypy
plan: 02
subsystem: database
tags: [mypy, sqlite-utils, type-safety, cast, generics]

# Dependency graph
requires:
  - phase: 10-manual-ruff-leaf-to-hub
    provides: ruff-clean codebase (zero non-cli.py E501 violations)
provides:
  - Mypy-clean database layer (zero errors in core/database.py)
  - cast(Table, ...) pattern established for sqlite-utils call sites
affects: [11-03, 11-04, 11-05, future mypy phases]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "cast(Table, self.db[...]) at every sqlite-utils Table-method call site"
    - "Local variable guard for float(row.get(...)) to satisfy mypy arg-type checks"
    - "Parameterised generics: dict[str, Any], list[str] instead of bare dict/list"

key-files:
  created: []
  modified:
    - src/corpus_analyzer/core/database.py

key-decisions:
  - "Use cast(Table, self.db[...]) per call site (not type: ignore) — explicit and refactor-safe"
  - "int(existing[0]) for SQL row ID to fix no-any-return on return path through existing branch"
  - "params: list[str] (not list[Any]) — values are always strings (category values, LIKE patterns)"
  - "_cc/_qs local variable guards satisfy mypy: avoids calling .get() twice and handles None cleanly"

patterns-established:
  - "cast(Table, ...) pattern: wrap self.db['tablename'] before calling Table-only methods"
  - "Local variable guard: assign row.get() to local var, then float(var) if var is not None else default"

requirements-completed: [MYPY-01]

# Metrics
duration: 12min
completed: 2026-02-24
---

# Phase 11 Plan 02: database.py Mypy Fixes Summary

**Zero mypy errors in core/database.py via cast(Table, ...) wrapping, parameterised generics, and float() local-variable guards**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-02-24T05:17:00Z
- **Completed:** 2026-02-24T05:29:37Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Eliminated all 17 mypy errors in `core/database.py` (the most error-dense file, 17/45 total)
- Added `cast(Table, self.db[...])` at every sqlite-utils Table call site (delete_where, insert, update)
- Fixed bare generic annotations: `dict` -> `dict[str, Any]`, `list` -> `list[str]`
- Fixed float(None) arg-type errors with local variable guards for `category_confidence` and `quality_score`
- All 281 tests continue to pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Add cast(Table, ...) at all sqlite-utils call sites** - `7a7b228` (fix)
2. **Task 2: Fix bare generic annotations and float(None) arg-type errors** - `5a7c81a` (fix)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `src/corpus_analyzer/core/database.py` — Added `cast`/`Table` imports, wrapped all Table call sites, parameterised generics, local variable guards for float()

## Decisions Made

- `cast(Table, self.db[...])` per call site instead of `# type: ignore` — explicit and aids future refactors
- `int(existing[0])` for the SQL row-ID return in the existing-document branch fixes the no-any-return error cleanly
- `params: list[str]` not `list[Any]` — all query parameter values in both methods are strings
- Local variable `_cc` / `_qs` pattern: avoids calling `.get()` twice, and mypy narrows the type correctly after `is not None` check

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None — all 17 errors resolved in two tasks without complications.

## Next Phase Readiness

- database.py is now mypy-clean; remaining mypy errors in the codebase are in other files
- The `cast(Table, ...)` pattern is established and documented for use in any future sqlite-utils call sites
- 281 tests green, ruff clean, database.py mypy clean

## Self-Check: PASSED

- FOUND: src/corpus_analyzer/core/database.py
- FOUND: .planning/phases/11-manual-ruff-cli-mypy/11-02-SUMMARY.md
- FOUND: commit 7a7b228 (Task 1)
- FOUND: commit 5a7c81a (Task 2)

---
*Phase: 11-manual-ruff-cli-mypy*
*Completed: 2026-02-24*

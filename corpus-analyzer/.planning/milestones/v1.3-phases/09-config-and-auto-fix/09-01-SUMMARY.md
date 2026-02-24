---
phase: 09-config-and-auto-fix
plan: 01
subsystem: infra
tags: [ruff, mypy, pyproject.toml, linting, per-file-ignores, extend-exclude]

# Dependency graph
requires: []
provides:
  - "ruff extend-exclude for .windsurf, .planning, test_debug.py"
  - "per-file-ignores: E501 suppressed for src/corpus_analyzer/llm/*.py"
  - "per-file-ignores: B006 suppressed for src/corpus_analyzer/cli.py"
  - "mypy frontmatter override with ignore_missing_imports = true"
affects: [09-02, 09-03, 09-04, 10-ruff-auto-fix, 11-manual-fixes]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "extend-exclude over exclude: preserves ruff defaults (.venv, .git) while adding custom dirs"
    - "per-file-ignores using full relative path from project root"
    - "[[tool.mypy.overrides]] TOML array-of-tables for per-module stubs"

key-files:
  created: []
  modified:
    - pyproject.toml

key-decisions:
  - "Use extend-exclude (not exclude) to add .windsurf/.planning without dropping ruff defaults"
  - "Full relative path in per-file-ignores: src/corpus_analyzer/llm/*.py not llm/*.py"
  - "module = [\"frontmatter\"] uses import name, not PyPI package name python-frontmatter"

patterns-established:
  - "Config-first pattern: all suppressions centralised in pyproject.toml, no inline noqa noise"

requirements-completed: [CONF-01, CONF-02, CONF-03, CONF-04]

# Metrics
duration: 1min
completed: 2026-02-24
---

# Phase 9 Plan 01: Config and Auto-Fix Summary

**ruff extend-exclude, per-file-ignores (E501/B006), and mypy frontmatter override added to pyproject.toml — zero .windsurf violations, zero B006, zero E501 in llm/**

## Performance

- **Duration:** ~1 min
- **Started:** 2026-02-24T04:10:39Z
- **Completed:** 2026-02-24T04:11:16Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Added `extend-exclude = [".windsurf", ".planning", "test_debug.py"]` to `[tool.ruff]`
- Added `[tool.ruff.lint.per-file-ignores]` with E501 for llm files, B006 for cli.py
- Added `[[tool.mypy.overrides]]` block suppressing `ignore_missing_imports` for `frontmatter`
- Verified: 0 .windsurf violations, 0 B006, 0 E501 in llm/ after config applied

## Task Commits

Each task was committed atomically:

1. **Task 1: Add ruff and mypy config stanzas to pyproject.toml** - `425f253` (chore)

## Files Created/Modified
- `pyproject.toml` - Added extend-exclude, per-file-ignores section, and [[tool.mypy.overrides]] block

## Decisions Made
- Used `extend-exclude` (not `exclude`) to preserve ruff's built-in exclusion defaults
- Specified full relative paths in per-file-ignores (ruff resolves globs relative to pyproject.toml location)
- Used `"frontmatter"` as module name (import name), not `"python-frontmatter"` (PyPI package name)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- pyproject.toml config is fully in place; ruff auto-fix (plan 09-02) can now run without touching .windsurf/ or .planning/ dirs
- B006 in cli.py is suppressed; the Typer list-default trap will not appear as a violation
- mypy frontmatter import noise is silenced; plan 09-03 mypy fixes can focus on real issues

---
*Phase: 09-config-and-auto-fix*
*Completed: 2026-02-24*

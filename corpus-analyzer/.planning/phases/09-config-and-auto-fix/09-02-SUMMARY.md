---
phase: 09-config-and-auto-fix
plan: 02
subsystem: infra
tags: [ruff, auto-fix, linting, W293, W291, F401, I001, UP045, UP035, F541]

# Dependency graph
requires:
  - phase: 09-01
    provides: "ruff extend-exclude, per-file-ignores, mypy overrides in pyproject.toml"
provides:
  - "All auto-fixable ruff violations eliminated from src/ and tests/"
  - "Zero W293, W291, F401, I001, UP045, UP035, F541 violations in source tree"
  - "37 source and test files cleaned via ruff --fix and --unsafe-fixes"
affects: [09-03, 09-04, 10-manual-fixes, 11-mypy]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ruff --fix then --unsafe-fixes for full auto-fixable sweep (safe pass then unsafe pass)"
    - "Stubborn F401 in __init__.py requiring manual removal after unsafe-fixes pass"

key-files:
  created: []
  modified:
    - src/corpus_analyzer/analyzers/quality.py
    - src/corpus_analyzer/analyzers/shape.py
    - src/corpus_analyzer/classifiers/document_type.py
    - src/corpus_analyzer/classifiers/domain_tags.py
    - src/corpus_analyzer/core/database.py
    - src/corpus_analyzer/core/models.py
    - src/corpus_analyzer/core/samples.py
    - src/corpus_analyzer/core/scanner.py
    - src/corpus_analyzer/extractors/__init__.py
    - src/corpus_analyzer/extractors/markdown.py
    - src/corpus_analyzer/extractors/python.py
    - src/corpus_analyzer/generators/advanced_rewriter.py
    - src/corpus_analyzer/generators/templates.py
    - src/corpus_analyzer/ingest/chunker.py
    - src/corpus_analyzer/ingest/embedder.py
    - src/corpus_analyzer/llm/chunked_processor.py
    - src/corpus_analyzer/llm/ollama_client.py
    - src/corpus_analyzer/llm/quality_scorer.py
    - src/corpus_analyzer/llm/rewriter.py
    - src/corpus_analyzer/llm/unified_rewriter.py
    - src/corpus_analyzer/utils/ui.py
    - tests/ (16 test files)

key-decisions:
  - "Two-pass fix strategy: safe --fix first, then --unsafe-fixes to catch hidden fixable violations"
  - "Manual removal required for F401 in extractors/__init__.py (unused Optional import) — ruff unsafe-fixes skipped __init__.py F401"

patterns-established:
  - "Two-pass ruff fix: `ruff check --fix` then `ruff check --fix --unsafe-fixes` catches all auto-fixable violations"

requirements-completed: [RUFF-01, RUFF-02]

# Metrics
duration: 2min
completed: 2026-02-24
---

# Phase 9 Plan 02: Config and Auto-Fix Summary

**370 auto-fixable ruff violations eliminated from 37 files via two-pass fix (--fix + --unsafe-fixes); 281 tests green**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-24T04:12:51Z
- **Completed:** 2026-02-24T04:14:29Z
- **Tasks:** 1
- **Files modified:** 37

## Accomplishments
- Ran `ruff check --fix` then `ruff check --fix --unsafe-fixes` to eliminate all auto-fixable violations
- Cleared W293 (253), W291 (33), F401 (30), I001 (22), UP045 (14), UP035 (3), F541 (2), B905 (3), B007 (3), SIM102 (2), F841 (4), W605 (1)
- Manually removed unused `Optional` import from `extractors/__init__.py` (F401 skipped by unsafe-fixes on __init__ files)
- All 281 tests pass; smoke test `import corpus_analyzer` exits 0
- Remaining violations are only expected non-auto-fixable: E501 (86), E741 (4), E402 (2), B017 (2), B023 (1), B904 (1)

## Task Commits

Each task was committed atomically:

1. **Task 1: Audit auto-fixable violations and run ruff --fix** - `dc35aad` (fix)

## Files Created/Modified
- `src/corpus_analyzer/analyzers/quality.py` - W293 blank line whitespace fixed
- `src/corpus_analyzer/analyzers/shape.py` - Imports sorted (I001)
- `src/corpus_analyzer/classifiers/document_type.py` - Imports sorted, Optional modernised
- `src/corpus_analyzer/classifiers/domain_tags.py` - Unused import removed (F401)
- `src/corpus_analyzer/core/database.py` - Trailing whitespace, import cleanup
- `src/corpus_analyzer/core/models.py` - Optional[X] -> X | None (UP045), typing.List -> list (UP035)
- `src/corpus_analyzer/core/samples.py` - Trailing whitespace, imports sorted
- `src/corpus_analyzer/core/scanner.py` - Trailing whitespace
- `src/corpus_analyzer/extractors/__init__.py` - Removed unused `from typing import Optional` (F401)
- `src/corpus_analyzer/extractors/markdown.py` - Trailing whitespace
- `src/corpus_analyzer/extractors/python.py` - Trailing whitespace, imports sorted
- `src/corpus_analyzer/generators/advanced_rewriter.py` - Trailing whitespace, imports
- `src/corpus_analyzer/generators/templates.py` - Imports sorted
- `src/corpus_analyzer/ingest/chunker.py` - W293 blank line whitespace, imports
- `src/corpus_analyzer/ingest/embedder.py` - Unused import removed
- `src/corpus_analyzer/llm/chunked_processor.py` - W293 (8 blank lines), B007 loop var renamed
- `src/corpus_analyzer/llm/ollama_client.py` - Trailing whitespace
- `src/corpus_analyzer/llm/quality_scorer.py` - W293 (2 blank lines), B007 loop var renamed
- `src/corpus_analyzer/llm/rewriter.py` - Trailing whitespace, imports
- `src/corpus_analyzer/llm/unified_rewriter.py` - Trailing whitespace, imports, F-strings
- `src/corpus_analyzer/utils/ui.py` - Trailing whitespace
- `tests/` (16 test files) - Trailing whitespace, unused imports, sorted imports

## Decisions Made
- Used two-pass ruff fix: safe `--fix` first then `--unsafe-fixes` to handle all fixable violations cleanly
- Manually removed `from typing import Optional` in `extractors/__init__.py` — ruff skips F401 in `__init__.py` files even with unsafe-fixes to avoid breaking re-export contracts; this particular import was genuinely unused

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Manual F401 removal in extractors/__init__.py**
- **Found during:** Task 1 (verification after ruff --unsafe-fixes)
- **Issue:** `from typing import Optional` remained after both ruff fix passes; ruff's F401 unsafe-fix skips `__init__.py` to avoid breaking re-export patterns
- **Fix:** Manually deleted the unused import line — confirmed `Optional` not referenced anywhere in the file
- **Files modified:** `src/corpus_analyzer/extractors/__init__.py`
- **Verification:** `ruff check src/corpus_analyzer/extractors/__init__.py` reports zero violations
- **Committed in:** dc35aad (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug fix)
**Impact on plan:** The extra manual step was minimal; discovered during Step 3 verification check. No scope creep.

## Issues Encountered
- First `ruff check --fix` pass left 13 violations (11 W293 + 1 W291 + 1 F401). Adding `--unsafe-fixes` resolved all except the `__init__.py` F401. Root cause: ruff treats certain fixes as "unsafe" in safe mode (particularly in `__init__.py` files). Two-pass strategy now documented as project pattern.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Source tree is clean of all auto-fixable violations; plan 09-03 (mypy fixes) can start on a clean base
- Remaining ruff violations (E501 outside llm/, E741, E402, B017, B023, B904) are deferred to Phases 10-11
- All 281 tests green; no regressions introduced by the auto-fix pass

---
*Phase: 09-config-and-auto-fix*
*Completed: 2026-02-24*

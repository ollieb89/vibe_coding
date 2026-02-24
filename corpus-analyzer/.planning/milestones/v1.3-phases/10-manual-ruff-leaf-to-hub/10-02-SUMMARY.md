---
phase: 10-manual-ruff-leaf-to-hub
plan: 02
subsystem: linting
tags: [ruff, E501, line-wrapping, classifiers, analyzers, utils, search, ingest]

# Dependency graph
requires:
  - phase: 10-01
    provides: E741/E402/B017 semantic violations fixed; clean base for E501 wrapping
provides:
  - E501-clean classifiers/document_type.py (11 violations fixed)
  - E501-clean analyzers/quality.py and analyzers/shape.py (2 violations fixed)
  - E501-clean utils/ui.py (3 violations fixed)
  - E501-clean search/engine.py (1 violation fixed)
  - E501-clean ingest/chunker.py and ingest/indexer.py (2 violations fixed)
affects: [10-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Long re.search/re.findall calls wrapped by parenthesising and splitting arguments across lines"
    - "f-string generator expressions extracted to local variables before use in f-string"
    - "Type annotations spanning multiple lines use bracket wrapping: list[\n  tuple[...]\n] ="
    - "Long for-loop unpacking wrapped in parentheses around the iterable"

key-files:
  created: []
  modified:
    - src/corpus_analyzer/classifiers/document_type.py
    - src/corpus_analyzer/analyzers/quality.py
    - src/corpus_analyzer/analyzers/shape.py
    - src/corpus_analyzer/utils/ui.py
    - src/corpus_analyzer/search/engine.py
    - src/corpus_analyzer/ingest/chunker.py
    - src/corpus_analyzer/ingest/indexer.py

key-decisions:
  - "Wrap for-loop unpacking of CLASSIFICATION_RULES by parenthesising the iterable (CLASSIFICATION_RULES), not the unpacking variables"
  - "shape.py f-string: extract depth_rows local variable before the f-string rather than using multi-line expression inside {}"

patterns-established:
  - "E501 wrapping: use parenthesised multi-line calls, not backslash continuation"
  - "f-string expressions longer than ~70 chars: extract to named local variable"

requirements-completed: [RUFF-03]

# Metrics
duration: 8min
completed: 2026-02-24
---

# Phase 10 Plan 02: E501 Leaf-to-Hub Wrapping Summary

**Structural line-wrapping of 19 E501 violations across 7 leaf modules (classifiers, analyzers, utils, search, ingest) with zero test regressions (281 passed)**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-24T12:17:00Z
- **Completed:** 2026-02-24T12:25:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Cleared all 11 E501 violations in `classifiers/document_type.py`
- Cleared all 8 E501 violations across `analyzers/`, `utils/`, `search/`, and `ingest/`
- All 281 tests pass after wrapping; no semantic changes made

## Task Commits

1. **Task 1: Wrap E501 violations in classifiers/document_type.py** - `2932d48` (fix)
2. **Task 2: Wrap E501 violations in analyzers, utils, search, and ingest** - `8a47056` (fix)

## Files Created/Modified

- `src/corpus_analyzer/classifiers/document_type.py` - 11 E501 violations fixed (lines 75-82, 87, 99 function signature, 116 math.log, 125 type annotation, 210 for-loop, 234 membership test)
- `src/corpus_analyzer/analyzers/quality.py` - 1 E501 fixed (line 80: update_document_quality call)
- `src/corpus_analyzer/analyzers/shape.py` - 1 E501 fixed (line 178: extracted `depth_rows` local variable to replace inline generator expression in f-string)
- `src/corpus_analyzer/utils/ui.py` - 3 E501 fixed (lines 10, 35: Table() constructors; line 40: display_cols list)
- `src/corpus_analyzer/search/engine.py` - 1 E501 fixed (line 114: sort key lambda)
- `src/corpus_analyzer/ingest/chunker.py` - 1 E501 fixed (line 252: _enforce_char_limit signature)
- `src/corpus_analyzer/ingest/indexer.py` - 1 E501 fixed (line 97: CorpusIndex.__init__ signature)

## Decisions Made

- Wrapped `for category, base_confidence, ... in CLASSIFICATION_RULES:` by parenthesising the iterable (`(CLASSIFICATION_RULES)`), keeping the unpacking variables on one line — the only clean option that avoids artificial intermediate variables
- Extracted `depth_rows` local variable in `shape.py` per plan guidance: generator expressions inside f-string `{}` are not wrappable cleanly in Python 3.12 and extracting to a named variable improves readability

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All leaf modules (classifiers, analyzers, utils, search, ingest) are now E501-clean
- Remaining E501 violations are in generators/ and core/database.py (Plan 03 scope)
- 281 tests still passing — no regressions introduced

---
*Phase: 10-manual-ruff-leaf-to-hub*
*Completed: 2026-02-24*

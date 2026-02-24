---
phase: 18-cli-chunk-display
plan: "01"
subsystem: testing
tags: [pytest, tdd, red-phase, formatter, search]

# Dependency graph
requires:
  - phase: 17-chunk-indexing
    provides: chunk indexing pipeline and LanceDB schema with chunk_text
provides:
  - RED test suite (10 failing tests) for format_result() function contract
affects:
  - 18-02 (GREEN implementation phase — must satisfy these test assertions)

# Tech tracking
tech-stack:
  added: []
  patterns: [TDD RED phase — import at module level, let ImportError be the RED signal]

key-files:
  created: []
  modified:
    - tests/search/test_formatter.py

key-decisions:
  - "Import format_result at module level so a single ImportError gives RED for all 10 tests simultaneously"
  - "test_format_result_rich_markup_escape_in_path asserts '[deprecated]' appears in primary (escaped form) rather than testing Rich internals directly"
  - "test_format_result_no_ellipsis_at_exactly_200_chars asserts len(preview)==204 (4 indent + 200 chars), matching the spec exactly"

patterns-established:
  - "RED tests live in same file as existing tests (test_formatter.py); new import line is the gating import"
  - "Result dicts use all required keys: file_path, start_line, end_line, construct_type, _relevance_score, chunk_text"

requirements-completed: [CHUNK-02]

# Metrics
duration: 3min
completed: 2026-02-24
---

# Phase 18 Plan 01: format_result() RED Test Suite Summary

**10-test RED suite establishing the complete format_result() contract: grep-style path:line-range output, score formatting, construct brackets, preview truncation, Rich markup escaping, and legacy-row handling**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-24T14:44:48Z
- **Completed:** 2026-02-24T14:47:30Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Added `from corpus_analyzer.search.formatter import format_result` import to test_formatter.py
- Wrote 10 `test_format_result_*` test functions covering all CHUNK-02 spec cases
- Confirmed RED state: collection fails with `ImportError: cannot import name 'format_result'`
- Preserved all 4 existing `extract_snippet` tests unmodified

## Task Commits

Each task was committed atomically:

1. **Task 1: RED — Write failing tests for format_result()** - `0aedbcf` (test)

**Plan metadata:** _(docs commit follows)_

_Note: TDD task — RED phase only. GREEN implementation ships in Plan 02._

## Files Created/Modified
- `tests/search/test_formatter.py` - Added import of format_result and 10 RED test functions

## Decisions Made
- Import `format_result` at module level so a single `ImportError` at collection time covers all 10 tests — cleaner RED signal than per-test `pytest.raises(ImportError)`
- Asserted `"[deprecated]" in primary` for the Rich markup escape test: verifies the escaped string appears in the return value without coupling to Rich internals
- `test_format_result_no_ellipsis_at_exactly_200_chars` uses `len(preview) == 204` (4 indent chars + 200 content chars) to lock in the exact boundary behaviour

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- RED tests are committed and confirmed failing
- Plan 02 (GREEN) implements `format_result()` in `src/corpus_analyzer/search/formatter.py`
- All 10 test function names are exact targets for Plan 02 to turn green

---
*Phase: 18-cli-chunk-display*
*Completed: 2026-02-24*

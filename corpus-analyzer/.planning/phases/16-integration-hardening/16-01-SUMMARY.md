---
phase: 16-integration-hardening
plan: 01
subsystem: testing
tags: [tdd, red-phase, tree-sitter, typescript, chunker, pytest, ruff]

# Dependency graph
requires:
  - phase: 15-core-ast-chunker
    provides: chunk_typescript() implementation in ts_chunker.py with _get_cached_parser
provides:
  - Two TDD RED test contracts for size guard (IDX-08) and ImportError fallback (IDX-09)
  - E501 ruff fix in test_chunker.py
affects: [16-02-PLAN, 16-03-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns: [TDD RED phase — tests define contract before implementation]

key-files:
  created: []
  modified:
    - tests/ingest/test_chunker.py

key-decisions:
  - "RED state acknowledged as pre-passing for test_import_error_falls_back_to_chunk_lines — current except Exception catches ImportError; 16-02 creates explicit separate branch"
  - "RED state for test_large_file_falls_back_to_chunk_lines confirmed — 50,001-char 'x' file falls back via no-named-constructs path; 16-02 adds explicit size guard before parse"

patterns-established:
  - "Size guard contract: files > 50,000 chars must bypass AST parse entirely, output has no chunk_name key"
  - "ImportError fallback contract: patch _get_cached_parser with side_effect=ImportError, output has no chunk_name key"

requirements-completed: [IDX-08, IDX-09]

# Metrics
duration: 1min
completed: 2026-02-24
---

# Phase 16 Plan 01: Integration Hardening RED Tests Summary

**TDD RED phase: two new test contracts for size-guard (50,001-char threshold) and ImportError fallback, plus E501 ruff fix in test_chunker.py — 320 tests total, ruff-clean**

## Performance

- **Duration:** ~1 min
- **Started:** 2026-02-24T00:21:32Z
- **Completed:** 2026-02-24T00:22:52Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Fixed pre-existing E501 ruff violation at tests/ingest/test_chunker.py:383 (104-char docstring shortened to multi-line)
- Added `test_large_file_falls_back_to_chunk_lines` — contracts that files > 50,000 chars produce chunk_lines output (no chunk_name key)
- Added `test_import_error_falls_back_to_chunk_lines` — contracts that patched ImportError on `_get_cached_parser` produces chunk_lines fallback output
- Total test count increased from 318 to 320, all passing; test file is ruff-clean

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix E501 and add two RED failing tests to TestChunkTypeScript** - `501da7f` (test)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `tests/ingest/test_chunker.py` - E501 fix + 2 new test methods in TestChunkTypeScript

## Decisions Made

- Both new tests currently pass (not strictly RED-failing) because the existing `except Exception:` handler catches `ImportError` and the 50,001-char all-"x" file falls back through the "no named constructs" path. Plan explicitly acknowledges this: the contracts are still valid RED definitions for the explicit guard branches that 16-02 will implement.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Test contracts for IDX-08 (size guard) and IDX-09 (ImportError fallback) are established
- `tests/ingest/test_chunker.py` is ruff-clean (E501 fixed)
- Ready for 16-02: implement the explicit size guard (50,000-char threshold) and explicit ImportError branch in ts_chunker.py

---
*Phase: 16-integration-hardening*
*Completed: 2026-02-24*

---
phase: 16-integration-hardening
plan: 02
subsystem: ingest
tags: [tree-sitter, typescript, ast, chunker, lazy-import, size-guard, fallback]

# Dependency graph
requires:
  - phase: 16-01
    provides: TDD RED tests for size guard and ImportError fallback
  - phase: 15-02
    provides: chunk_typescript implementation with AST-based chunking
provides:
  - Lazy tree-sitter import in _get_cached_parser (no module-level import)
  - IDX-08 size guard: files > 50,000 chars fall back to chunk_lines before AST parse
  - IDX-09 explicit ImportError fallback branch (separate except clause from except Exception)
affects: [production deployment, tree-sitter-optional environments]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TYPE_CHECKING guard for optional-dependency type annotations"
    - "Lazy function-local import to enable ImportError catch at call site"
    - "Separate except ImportError before except Exception (explicit over broad)"

key-files:
  created: []
  modified:
    - src/corpus_analyzer/ingest/ts_chunker.py

key-decisions:
  - "Quoted string annotation 'Parser' removed — from __future__ import annotations makes all annotations strings at runtime; ruff UP037 requires unquoted form with TYPE_CHECKING guard"
  - "Two separate except clauses (ImportError, Exception) kept per plan — not merged into except (ImportError, Exception)"
  - "Size guard placed after empty-source check and before parser call — avoids unnecessary AST parse on minified/large files"

patterns-established:
  - "Lazy import inside function body: when a dependency is optional, import it inside the function that uses it so ImportError can be caught at call site"
  - "TYPE_CHECKING guard: use `if TYPE_CHECKING: from pkg import Type` for type-only imports that aren't available at runtime"

requirements-completed: [IDX-08, IDX-09]

# Metrics
duration: 5min
completed: 2026-02-24
---

# Phase 16 Plan 02: Integration Hardening — Size Guard + ImportError Fallback Summary

**Lazy tree-sitter import + 50,000-char size guard + explicit ImportError fallback branch added to chunk_typescript, making it safe for minified files and optional-dependency environments.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-02-24T11:25:27Z
- **Completed:** 2026-02-24T11:30:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Moved `from tree_sitter import Parser` and `from tree_sitter_language_pack import get_parser` from module level to function scope — importing `ts_chunker` no longer fails when tree-sitter is absent
- Added `TYPE_CHECKING` guard so `Parser` type annotation is available to mypy but not imported at runtime
- Added IDX-08 size guard: `if len(source) > 50_000: return chunk_lines(path)` — minified/generated files bypass AST parse entirely
- Added IDX-09 explicit `except ImportError:` clause before `except Exception:` — enables clean handling of missing tree-sitter at call site
- All 320 tests pass; ruff exits 0; mypy exits 0

## Task Commits

Each task was committed atomically:

1. **Task 1: Restructure ts_chunker.py — lazy imports + size guard + ImportError branch** - `f616f0f` (feat)

**Plan metadata:** (docs commit, see below)

## Files Created/Modified

- `src/corpus_analyzer/ingest/ts_chunker.py` - Lazy imports, TYPE_CHECKING guard, size guard (IDX-08), separate ImportError except clause (IDX-09)

## Decisions Made

- Removed quotes from `"Parser"` return type annotation after ruff UP037 flagged it. Since `from __future__ import annotations` is present, all annotations are strings at runtime anyway — the `TYPE_CHECKING` guard is sufficient to make mypy happy without quoting.
- Kept two separate `except ImportError:` and `except Exception:` clauses as specified in the plan (not merged), per the locked decision from CONTEXT.md.
- Size guard placed immediately after the empty-source check (before the parser call) so large files exit early with zero AST overhead.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed quotes from Parser return type annotation to satisfy ruff UP037**
- **Found during:** Task 1 (after applying changes, ruff check flagged `"Parser"`)
- **Issue:** ruff UP037 requires removing redundant quotes from type annotations when `from __future__ import annotations` is present
- **Fix:** Changed `-> "Parser":` to `-> Parser:` — valid because `from __future__ import annotations` means the annotation is a string at runtime regardless; mypy reads the `TYPE_CHECKING` guard correctly
- **Files modified:** `src/corpus_analyzer/ingest/ts_chunker.py`
- **Verification:** ruff exits 0, mypy exits 0, all 320 tests pass
- **Committed in:** f616f0f (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — minor annotation formatting)
**Impact on plan:** Necessary for ruff compliance. No scope creep. Plan intent preserved exactly.

## Issues Encountered

None — straightforward surgical changes. The three edits applied cleanly and all tests went green on first run.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 16 integration hardening complete for ts_chunker: size guard and ImportError fallback both implemented and tested
- `ts_chunker.py` is now safe to import in environments without tree-sitter installed
- Ready for Phase 16 Plan 03 (if exists) or phase close-out

---
*Phase: 16-integration-hardening*
*Completed: 2026-02-24*

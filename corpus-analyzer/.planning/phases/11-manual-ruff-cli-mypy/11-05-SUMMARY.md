---
phase: 11-manual-ruff-cli-mypy
plan: "05"
subsystem: llm
tags: [mypy, type-annotations, rewriter, ollama, bug-fix]

# Dependency graph
requires:
  - phase: 11-04
    provides: OllamaClient.db field (CorpusDatabase | None = None) added to OllamaClient
provides:
  - Zero mypy errors in llm/rewriter.py (MYPY-05 complete)
  - DEFAULT_SYSTEM_PROMPT bug fixed (trailing comma removed — was tuple[str], now str)
  - process_document fully annotated (doc: Document, adv_rewriter: Any)
  - advanced_rewriter.py union-attr resolved (hasattr guard replaced with is not None)
  - uv run mypy src/ exits 0 — entire codebase mypy-clean
affects: [phase-12, llm, generators]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Guard self.client.db with `is not None` (not hasattr) when attribute is typed Optional"
    - "Use adv_rewriter: Any for conditionally-imported types to avoid circular imports"

key-files:
  created: []
  modified:
    - src/corpus_analyzer/llm/rewriter.py
    - src/corpus_analyzer/generators/advanced_rewriter.py

key-decisions:
  - "DEFAULT_SYSTEM_PROMPT trailing comma was a genuine runtime bug — any code path reaching line 401 with an unmapped category would have raised TypeError at runtime"
  - "adv_rewriter: Any is correct — AdvancedRewriter is imported inside the function to avoid circular imports; moving the import would break that pattern"
  - "advanced_rewriter.py hasattr(self.client, 'db') replaced with self.client.db is not None — since plan 04 added the typed field, hasattr always returns True, so the guard must use the value not the existence"

patterns-established:
  - "Union-attr on Optional fields: guard with `is not None` not `hasattr` when attribute is a typed Optional on a class"

requirements-completed: [MYPY-05]

# Metrics
duration: 5min
completed: 2026-02-24
---

# Phase 11 Plan 05: Rewriter.py Mypy Fix Summary

**Fixed DEFAULT_SYSTEM_PROMPT trailing-comma runtime bug and annotated process_document, making llm/rewriter.py and the entire codebase mypy-clean (53 source files, zero errors)**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-24T05:36:00Z
- **Completed:** 2026-02-24T05:36:48Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Removed trailing comma from `DEFAULT_SYSTEM_PROMPT` — fixes genuine runtime `TypeError` for any category not in `CATEGORY_PROMPTS` dict (was `tuple[str]`, now `str`)
- Fully annotated `process_document` with `doc: Document` and `adv_rewriter: Any` (circular import avoidance pattern preserved)
- Fixed `advanced_rewriter.py` `union-attr` by replacing `hasattr(self.client, "db")` with `self.client.db is not None` (plan 04 typed the field, so `hasattr` always returned `True`)
- `uv run mypy src/` exits 0 — 53 source files, zero errors — phase 11 goal achieved
- All 281 tests pass; `uv run ruff check .` passes with zero violations

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix DEFAULT_SYSTEM_PROMPT trailing comma and process_document annotations** - `811c84a` (fix)
2. **Task 2: Full mypy clean gate and final test run** - verification only (no additional changes)

**Plan metadata:** (final commit, see below)

## Files Created/Modified

- `/home/ollie/Development/Tools/vibe_coding/corpus-analyzer/src/corpus_analyzer/llm/rewriter.py` — Removed trailing comma on DEFAULT_SYSTEM_PROMPT, added `Document` and `Any` imports, annotated `process_document` parameters
- `/home/ollie/Development/Tools/vibe_coding/corpus-analyzer/src/corpus_analyzer/generators/advanced_rewriter.py` — Changed `hasattr(self.client, "db")` to `self.client.db is not None` to resolve union-attr

## Decisions Made

- `adv_rewriter: Any` is correct (not `AdvancedRewriter`) — AdvancedRewriter is imported inside the function to prevent circular imports; typing it `Any` is the established pattern per plan research
- `self.client.db is not None` replaces `hasattr(self.client, "db")` — once plan 04 typed the field as `CorpusDatabase | None`, the `hasattr` guard was semantically wrong (always True) and mypy could no longer narrow the type

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed advanced_rewriter.py union-attr not listed in plan**
- **Found during:** Task 1 (after fixing rewriter.py, running mypy revealed remaining error)
- **Issue:** `advanced_rewriter.py:81` still had `union-attr` on `self.client.db.get_gold_standard_documents()` — plan 04 typed `db` as `CorpusDatabase | None` but the guard used `hasattr` which doesn't narrow Optional types
- **Fix:** Replaced `hasattr(self.client, "db")` with `self.client.db is not None` so mypy narrows to `CorpusDatabase`
- **Files modified:** `src/corpus_analyzer/generators/advanced_rewriter.py`
- **Verification:** `uv run mypy src/ --no-error-summary 2>&1` returns empty
- **Committed in:** `811c84a` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug: mypy union-attr not listed in plan but blocking full mypy clean)
**Impact on plan:** Required fix — without it mypy would not exit 0. No scope creep.

## Issues Encountered

None — all three mypy errors resolved cleanly.

## Next Phase Readiness

- Phase 11 goal fully achieved: `uv run mypy src/` exits 0, `uv run ruff check .` exits 0, 281 tests pass
- Phase 12 can proceed with a fully clean codebase (zero ruff violations, zero mypy errors)

---
*Phase: 11-manual-ruff-cli-mypy*
*Completed: 2026-02-24*

## Self-Check: PASSED

- FOUND: src/corpus_analyzer/llm/rewriter.py
- FOUND: src/corpus_analyzer/generators/advanced_rewriter.py
- FOUND: .planning/phases/11-manual-ruff-cli-mypy/11-05-SUMMARY.md
- FOUND commit: 811c84a

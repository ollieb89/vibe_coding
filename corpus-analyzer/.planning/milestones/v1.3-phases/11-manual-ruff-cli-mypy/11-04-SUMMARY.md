---
phase: 11-manual-ruff-cli-mypy
plan: "04"
subsystem: typing
tags: [mypy, type-annotations, Any, dict, ollama, TYPE_CHECKING]

requires:
  - phase: 10-manual-ruff-leaf-to-hub
    provides: E501 wrapping complete — clean codebase baseline

provides:
  - "Zero mypy errors in utils/ui.py (4 errors: missing return + arg types)"
  - "Zero mypy errors in extractors/markdown.py (1 error: bare dict)"
  - "Zero mypy errors in extractors/__init__.py (1 error: abstract class instantiation)"
  - "Zero mypy errors in ingest/chunker.py (1 error: unannotated list var)"
  - "Zero mypy errors in analyzers/shape.py (1 error: bare dict return)"
  - "Zero mypy errors in llm/ollama_client.py (1 error: no-any-return)"
  - "OllamaClient.db: CorpusDatabase | None = None field (unblocks plan 05)"

affects:
  - 11-05-PLAN.md (rewriter.py — attr-defined error on .db now resolved)
  - Any future mypy passes over these 6 files

tech-stack:
  added: []
  patterns:
    - "TYPE_CHECKING guard for optional cross-module type references (avoids circular imports)"
    - "response.message.content attribute access over dict subscript for typed ollama responses"
    - "Explicit dict[str, type[Concrete1] | type[Concrete2]] to narrow abstract instantiation"

key-files:
  created: []
  modified:
    - src/corpus_analyzer/utils/ui.py
    - src/corpus_analyzer/extractors/markdown.py
    - src/corpus_analyzer/extractors/__init__.py
    - src/corpus_analyzer/ingest/chunker.py
    - src/corpus_analyzer/analyzers/shape.py
    - src/corpus_analyzer/llm/ollama_client.py

key-decisions:
  - "Use response.message.content (typed Optional[str]) not response['message']['content'] (Any) — attribute access is typed by the ollama library's ChatResponse/Message models"
  - "OllamaClient is a plain class (not Pydantic) — use self.db: CorpusDatabase | None = None with TYPE_CHECKING guard"
  - "extractors/__init__.py: explicit union dict type narrows away BaseExtractor abstract class, resolving instantiation error without any logic change"

patterns-established:
  - "TYPE_CHECKING guard: avoids runtime circular imports while giving mypy full type info"
  - "Bare dict return types: always parameterise as dict[str, Any] when content is mixed"

requirements-completed: [MYPY-03, MYPY-04, MYPY-06]

duration: 2min
completed: 2026-02-24
---

# Phase 11 Plan 04: Misc Mypy Fixes Summary

**Nine mypy errors fixed across 6 files: type annotations added to UI helpers, dict parameterisation in extractors and shape.py, list[str] annotation in chunker, and OllamaClient.db field added with TYPE_CHECKING guard**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-24T05:27:50Z
- **Completed:** 2026-02-24T05:29:42Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Fixed 4 errors in utils/ui.py: added `Any` parameter types and `-> None` return types to both print functions
- Fixed 4 single errors across extractors/markdown.py, extractors/__init__.py, ingest/chunker.py, analyzers/shape.py
- Fixed ollama_client.py no-any-return by switching to typed attribute access (`response.message.content`); added `db: CorpusDatabase | None = None` field with TYPE_CHECKING guard
- Bonus: `rewriter.py` attr-defined error on `.db` also resolved (was blocked on this plan)

## Task Commits

1. **Task 1: Fix mypy errors in ui.py, extractors, chunker, shape.py** - `eb870ee` (fix)
2. **Task 2: Add OllamaClient.db field and fix no-any-return** - `9b7936f` (fix)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `src/corpus_analyzer/utils/ui.py` - Added `from typing import Any`; annotated both public functions with `Any` param + `-> None`
- `src/corpus_analyzer/extractors/markdown.py` - Added `from typing import Any`; `metadata: dict[str, Any]`
- `src/corpus_analyzer/extractors/__init__.py` - Explicit `dict[str, type[MarkdownExtractor] | type[PythonExtractor]]` annotation on `extractors` dict
- `src/corpus_analyzer/ingest/chunker.py` - `current_lines: list[str] = []` at line 273
- `src/corpus_analyzer/analyzers/shape.py` - Added `Any` to `NamedTuple` import; `-> dict[str, Any]` on `_generate_recommended_schema`
- `src/corpus_analyzer/llm/ollama_client.py` - `from __future__ import annotations`; TYPE_CHECKING guard for CorpusDatabase; `self.db: CorpusDatabase | None = None`; use `response.message.content`

## Decisions Made

- Used `response.message.content` (typed `Optional[str]`) not `response["message"]["content"]` (returns `Any`). The ollama library's `Message` class has `content: Optional[str]` — attribute access gives mypy a typed `str | None` which we then coerce with `str(... or "")`.
- OllamaClient is confirmed to be a plain class (not Pydantic) — `__init__` field assignment is the correct pattern.
- The explicit union dict annotation in `extractors/__init__.py` is the minimal fix: mypy inferred `dict[str, type[BaseExtractor]]` (abstract), but the union of the two concrete types removes the abstract base from scope.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None — all 9 targeted errors were straightforward annotation additions. The bonus side-effect (rewriter.py attr-defined error resolved) was called out in the plan and confirmed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plans 05+ (rewriter.py, advanced rewriting) can now reference `OllamaClient.db` without attr-defined errors
- All 6 files from MYPY-03/04/06 requirements are clean
- 281 tests passing after all changes

## Self-Check: PASSED

All 6 modified files exist. Both task commits verified: eb870ee, 9b7936f.

---
*Phase: 11-manual-ruff-cli-mypy*
*Completed: 2026-02-24*

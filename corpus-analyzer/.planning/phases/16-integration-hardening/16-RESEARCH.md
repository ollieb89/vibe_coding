# Phase 16: Integration Hardening - Research

**Researched:** 2026-02-24
**Domain:** Python defensive programming — size guard, ImportError fallback, ruff/mypy quality gate
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Size guard behavior**
- Silent fallback — no user-visible output when a 50K+ char file is skipped
- 50,000 character threshold is a hardcoded constant (not configurable via corpus.toml)
- Fallback chunks are indistinguishable from normal line-based chunks (no special metadata)
- Guard lives inside `chunk_typescript()` — checks `len(content)` before invoking tree-sitter; returns `chunk_lines()` output directly

**ImportError fallback**
- Silent fallback — no warning, no per-file output; `corpus index` completes normally
- ImportError caught inside `chunk_typescript()` (same module as the size guard, same pattern)
- Explicit separate branch from the `has_error` partial-tree fallback — both call `chunk_lines()` independently, not via a shared helper

**Test approach order**
- TDD RED-first, matching phase 15 discipline: 16-01 writes failing tests, 16-02 implements
- Both size guard and ImportError tests go in one RED plan (same module, related features)
- Plan structure: 16-01 RED, 16-02 GREEN, 16-03 validation gate = 3 plans total
- ImportError test mocks using `unittest.mock.patch` to raise `ImportError` at the import site inside `chunk_typescript()`

**Quality gate scope**
- Minimum test count assertion: ≥318 tests (phase 15 GREEN target; catches accidental deletion)
- Integration smoke test: run `corpus index` against a real TS fixture to confirm end-to-end dispatch wiring
- Validation plan also updates PROJECT.md: move v1.5 requirements from Active to Validated

### Claude's Discretion
- Exact mock patch target path (depends on how `chunk_typescript()` imports tree-sitter at runtime)
- TS fixture to use for smoke test (project's own TS files or a minimal temp file)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| IDX-08 | Files exceeding 50,000 characters skip AST parse and fall back to `chunk_lines()` directly (guard against minified and generated files) | Size guard at top of `chunk_typescript()` body after file read: `if len(source) > 50_000: return chunk_lines(path)` |
| IDX-09 | `ImportError` guard — if `tree-sitter` or `tree-sitter-language-pack` is absent, fall back to line chunking rather than raising at import time | Requires moving module-level tree-sitter imports in `ts_chunker.py` into function-local scope inside `chunk_typescript()`, then catching `ImportError` there |
| QUAL-01 | `uv run ruff check .` exits 0 and `uv run mypy src/` exits 0 after all changes; all 293+ existing tests continue to pass | One pre-existing ruff E501 violation at `tests/ingest/test_chunker.py:383` must be fixed; mypy currently clean |
</phase_requirements>

---

## Summary

Phase 16 delivers three precise surgical changes to the TypeScript chunker plus a quality gate pass. Two new defensive branches must be added to `chunk_typescript()` (the size guard and ImportError fallback), the pre-existing ruff E501 violation in the test file must be fixed, and the full test suite must remain green at 318+ tests.

The most important architectural discovery is that `ts_chunker.py` currently imports `tree_sitter` and `tree_sitter_language_pack` at **module level** (lines 14-15). This means the CONTEXT.md decision to "catch ImportError inside `chunk_typescript()`" requires a structural change: those two imports must move from module-top into the function body of `chunk_typescript()`, where they can be wrapped in a try/except ImportError block. `_get_cached_parser` also imports `get_parser` from the module scope — it must either move into the function or be lazily initialized. The `chunk_file()` lazy import of `ts_chunker` (`from corpus_analyzer.ingest.ts_chunker import chunk_typescript`) already exists and provides the correct outer containment layer, but the ImportError must be caught inside `chunk_typescript()` per the locked decision, which means module-level imports must become function-local.

The quality gate already has one failing check: `uv run ruff check .` exits with E501 at `tests/ingest/test_chunker.py:383` (docstring 104 chars > 100 limit). The fix is a simple docstring split. `uv run mypy src/` currently exits clean. The test count is exactly 318. The validation plan (16-03) is responsible for confirming all gates pass and updating PROJECT.md.

**Primary recommendation:** Restructure `ts_chunker.py` to use lazy function-local imports of tree-sitter; add `len(source) > 50_000` guard before parser call; add `except ImportError` branch; fix the pre-existing ruff E501; follow TDD RED → GREEN order across three plans.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 9.0.2 (installed) | Test runner | Project standard per CLAUDE.md |
| unittest.mock (stdlib) | Python 3.12 built-in | Patching imports for ImportError test | Already used in `tests/ingest/test_indexer.py` |
| ruff | >=0.4.0 | Linter/formatter | Project linter per CLAUDE.md |
| mypy | >=1.9.0 (strict) | Type checker | Project type checker per CLAUDE.md |
| tree-sitter | >=0.25.0 | TS AST parsing | Already in pyproject.toml |
| tree-sitter-language-pack | >=0.13.0 | Grammar pack | Already in pyproject.toml |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| uv | (installed) | Task runner / venv | All test/lint/typecheck commands |

**Commands:**
```bash
uv run pytest -v                        # full suite
uv run pytest tests/ingest/test_chunker.py -v  # chunker tests only
uv run ruff check .                     # lint gate
uv run ruff format .                    # auto-fix formatting
uv run mypy src/                        # type check
```

---

## Architecture Patterns

### Current Module Structure (ts_chunker.py — BEFORE changes)

```
ts_chunker.py
├── module-level: from tree_sitter import Parser       ← MUST MOVE to function body
├── module-level: from tree_sitter_language_pack import get_parser  ← MUST MOVE
├── _DIALECT dict
├── _TARGET_TYPES frozenset
├── _get_cached_parser(dialect) — uses get_parser from module scope  ← AFFECTED
├── _extract_name(node, export_node)
└── chunk_typescript(path) — add size guard + ImportError catch here
```

### Pattern 1: Size Guard — Check Before Parse

**What:** Early-return with `chunk_lines()` output when `len(source) > 50_000`
**When to use:** After reading file content, before calling `_get_cached_parser()`
**Placement:** Inside `chunk_typescript()`, after the `source = f.read()` block

```python
# Source: locked decision in 16-CONTEXT.md
if not source.strip():
    return []

# IDX-08: size guard — minified/generated files skip AST parse
if len(source) > 50_000:
    return chunk_lines(path)

try:
    parser = _get_cached_parser(dialect)
    tree = parser.parse(source.encode("utf-8"))
except Exception:
    return chunk_lines(path)
```

### Pattern 2: ImportError Fallback — Lazy Module-Level Imports

**What:** Move `tree_sitter` imports from module-level into `chunk_typescript()` body; catch `ImportError`
**When to use:** When tree-sitter may not be installed (CI environments, minimal installs)

The key constraint: `_get_cached_parser` currently calls `get_parser` from module scope. Two valid approaches:

**Option A (recommended):** Move `get_parser` import into `_get_cached_parser` function body and keep the `@lru_cache` decorator. The `Parser` import (only used for type annotation) should become a string annotation `"Parser"` or move to `TYPE_CHECKING` block.

```python
# Source: project pattern from chunker.py lazy import of ts_chunker
from __future__ import annotations  # already present — enables string annotations

from typing import TYPE_CHECKING, Any
from functools import lru_cache
from pathlib import Path

if TYPE_CHECKING:
    from tree_sitter import Parser  # type-only; not imported at runtime


@lru_cache(maxsize=8)
def _get_cached_parser(dialect: str) -> "Parser":
    from tree_sitter_language_pack import get_parser  # lazy
    return get_parser(dialect)  # type: ignore[arg-type]


def chunk_typescript(path: Path) -> list[dict[str, Any]]:
    from corpus_analyzer.ingest.chunker import chunk_lines  # lazy: avoid circular

    ext = path.suffix.lower()
    dialect = _DIALECT.get(ext)
    if dialect is None:
        return chunk_lines(path)

    try:
        with open(path, encoding="utf-8") as f:
            source = f.read()
    except (UnicodeDecodeError, OSError):
        return chunk_lines(path)

    if not source.strip():
        return []

    # IDX-08: size guard
    if len(source) > 50_000:
        return chunk_lines(path)

    # IDX-09: ImportError guard — separate branch, not merged with has_error fallback
    try:
        parser = _get_cached_parser(dialect)
        tree = parser.parse(source.encode("utf-8"))
    except ImportError:
        return chunk_lines(path)
    except Exception:
        return chunk_lines(path)

    # ... rest of function unchanged
```

**Important:** The two `except` clauses (ImportError, Exception) MUST remain as separate branches per the locked decision — "Explicit separate branch." This means the try/except wrapping the parser call should catch ImportError first, then Exception. They both call `chunk_lines(path)` independently.

**Option B (simpler if mypy is flexible):** Keep `_get_cached_parser` unchanged but wrap the import itself in `chunk_typescript()`:

```python
def chunk_typescript(path: Path) -> list[dict[str, Any]]:
    try:
        from corpus_analyzer.ingest.ts_chunker import _get_cached_parser  # circular!
    except ImportError:
        ...
```

Option B is not viable due to circular import. Option A is the correct approach.

### Pattern 3: ImportError Test — Mock Patch Target

**What:** Use `unittest.mock.patch` to simulate ImportError when tree-sitter is absent
**Constraint (Claude's Discretion):** Patch target depends on where the import lives at runtime

With Option A (lazy import inside `_get_cached_parser`):
- Patch target: `"corpus_analyzer.ingest.ts_chunker._get_cached_parser"` with `side_effect=ImportError`
- This is simpler and more precise than patching the import itself

```python
# Source: existing project pattern from tests/ingest/test_indexer.py
from unittest.mock import patch

def test_import_error_falls_back_to_chunk_lines(self, tmp_path: Path) -> None:
    """chunk_typescript falls back to chunk_lines when tree-sitter is not installed."""
    ts_file = tmp_path / "test.ts"
    ts_file.write_text("function foo(): void {}\n")

    with patch(
        "corpus_analyzer.ingest.ts_chunker._get_cached_parser",
        side_effect=ImportError("No module named 'tree_sitter'"),
    ):
        result = chunk_typescript(ts_file)

    assert isinstance(result, list)
    assert len(result) > 0  # chunk_lines produces output
    assert all("chunk_name" not in c for c in result)  # line chunks have no chunk_name
```

Note: `@lru_cache` on `_get_cached_parser` means the test must either clear the cache before patching or patch after clearing. The safest approach is to patch the function directly (not its internals), which bypasses the cache entirely.

### Pattern 4: Size Guard Test

```python
def test_large_file_falls_back_to_chunk_lines(self, tmp_path: Path) -> None:
    """Files exceeding 50,000 characters skip AST parse and fall back to chunk_lines."""
    ts_file = tmp_path / "test.ts"
    # 50,001 chars — just above the threshold
    ts_file.write_text("x" * 50_001)

    chunks = chunk_typescript(ts_file)

    # chunk_lines output: list of dicts without chunk_name
    assert isinstance(chunks, list)
    assert all("chunk_name" not in c for c in chunks)
```

### Pattern 5: Ruff E501 Fix

The pre-existing violation is a docstring that is 4 chars too long:

```python
# BEFORE (104 chars — line 383)
"""Single-line // comment preceding declaration is NOT included; start_line is function line."""

# AFTER (two lines, both under 100)
"""Single-line // comment preceding declaration is NOT included.

start_line is the function declaration line, not the comment.
"""
```

Or simply shorten the text:
```python
"""// comment before declaration is NOT included; start_line is the function line."""
```

### Anti-Patterns to Avoid

- **Merging ImportError and Exception branches:** The locked decision requires them as separate clauses — do not write a single `except (ImportError, Exception):`
- **Module-level tree-sitter imports remaining:** If `from tree_sitter import Parser` stays at module level, importing `ts_chunker` will fail when tree-sitter is absent, making the ImportError guard inside `chunk_typescript()` unreachable
- **Patching the wrong target:** If `_get_cached_parser` is the patch target but `lru_cache` has already been called in earlier tests, the cache may hold a real parser, bypassing the mock — always call `_get_cached_parser.cache_clear()` before patching, or use `patch` on the function object (which replaces it entirely, bypassing cache)
- **Not running ruff before commit:** The E501 fix must happen in the same wave as writing new test code, or new lines may introduce more violations

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Simulating missing package | Custom sys.modules manipulation | `unittest.mock.patch(..., side_effect=ImportError)` | Cleaner, reversible, already used in project |
| Size threshold configuration | corpus.toml parser + config lookup | Hardcoded constant `50_000` | Locked decision; simpler; configurable later if needed |
| Cache invalidation between tests | Custom cache wrapper | `_get_cached_parser.cache_clear()` (built into functools.lru_cache) | Standard stdlib approach |

**Key insight:** Both guards (size and ImportError) are one-line early returns inside an existing function — no new modules, no new classes, no new helpers needed.

---

## Common Pitfalls

### Pitfall 1: Module-Level Import Blocks the Guard

**What goes wrong:** `chunk_typescript()` has an ImportError try/except, but `ts_chunker.py` imports `tree_sitter` at module level. When tree-sitter is absent, `import corpus_analyzer.ingest.ts_chunker` fails with ImportError before `chunk_typescript()` is ever called. The guard never executes.

**Why it happens:** Python raises ImportError at module load time for top-level imports, not at call time.

**How to avoid:** Move `from tree_sitter import Parser` and `from tree_sitter_language_pack import get_parser` into function body. For the Parser type annotation, use `TYPE_CHECKING` guard or string annotation (already enabled via `from __future__ import annotations`).

**Warning signs:** The ImportError test passes when tree-sitter IS installed (mock works) but would fail in a real environment without tree-sitter.

### Pitfall 2: lru_cache Holds Stale Parser Across Tests

**What goes wrong:** `_get_cached_parser` is decorated with `@lru_cache`. If an earlier test loads a real parser for dialect "typescript", the cache holds the parser object. A later test patches `_get_cached_parser` to raise ImportError, but the patch replaces the function *object* — meaning the cached result from the real call is gone (the function is replaced entirely). This is actually fine when patching the function directly.

**But:** If you try to patch only the *internals* (e.g., `sys.modules["tree_sitter_language_pack"]`), the lru_cache may return the already-computed parser from before the patch, making the test ineffective.

**How to avoid:** Patch `_get_cached_parser` directly with `side_effect=ImportError`. This replaces the entire function, bypassing the cache.

### Pitfall 3: Size Guard Returns No chunk_name Field

**What goes wrong:** `chunk_lines()` returns dicts with only `text`, `start_line`, `end_line` — no `chunk_name`. If downstream code (or tests) unconditionally accesses `chunk["chunk_name"]`, it raises KeyError.

**Why it happens:** The size guard falls back to `chunk_lines()`, which predates the `chunk_name` field.

**How to avoid:** The locked decision says "fallback chunks are indistinguishable from normal line-based chunks (no special metadata)" — no `chunk_name` is added. Tests for size guard should assert `all("chunk_name" not in c for c in chunks)` to confirm correct fallback behavior.

### Pitfall 4: Pre-Existing Ruff Violation

**What goes wrong:** The QUAL-01 gate requires ruff exits 0. There is already one E501 violation at `tests/ingest/test_chunker.py:383` before Phase 16 touches anything. If the RED plan writes new test code without fixing this, ruff will fail on the validation gate check.

**How to avoid:** Fix the existing E501 at the start of the 16-01 (RED) plan, before adding any new test code. This way ruff is clean throughout.

### Pitfall 5: Test Count Regression

**What goes wrong:** 16-01 RED writes new failing tests (counting as "expected failures" in TDD red state). If these are skipped or accidentally removed during GREEN, test count may drop below 318.

**How to avoid:** The validation gate asserts `≥318 tests`. New tests added in 16-01 and kept in 16-02 will push the count above 318. The gate is a floor, not an exact count.

---

## Code Examples

### Complete Size Guard and ImportError Branches in chunk_typescript()

```python
# Source: derived from locked decisions in 16-CONTEXT.md + existing ts_chunker.py pattern

def chunk_typescript(path: Path) -> list[dict[str, Any]]:
    """..."""
    from corpus_analyzer.ingest.chunker import chunk_lines  # lazy: avoid circular

    ext = path.suffix.lower()
    dialect = _DIALECT.get(ext)
    if dialect is None:
        return chunk_lines(path)

    try:
        with open(path, encoding="utf-8") as f:
            source = f.read()
    except (UnicodeDecodeError, OSError):
        return chunk_lines(path)

    if not source.strip():
        return []

    # IDX-08: size guard — minified/generated files bypass AST parse
    if len(source) > 50_000:
        return chunk_lines(path)

    # IDX-09: ImportError branch — tree-sitter not installed
    try:
        parser = _get_cached_parser(dialect)
        tree = parser.parse(source.encode("utf-8"))
    except ImportError:
        return chunk_lines(path)
    except Exception:
        return chunk_lines(path)

    # ... existing logic unchanged from here
```

### ImportError Test Using Existing Project Pattern

```python
# Source: pattern from tests/ingest/test_indexer.py (unittest.mock.patch usage)
from unittest.mock import patch
from corpus_analyzer.ingest.ts_chunker import chunk_typescript

def test_import_error_falls_back(self, tmp_path: Path) -> None:
    """If tree-sitter is not installed, chunk_typescript returns chunk_lines output."""
    ts_file = tmp_path / "test.ts"
    ts_file.write_text("function foo(): void {}\n")

    with patch(
        "corpus_analyzer.ingest.ts_chunker._get_cached_parser",
        side_effect=ImportError("No module named 'tree_sitter'"),
    ):
        result = chunk_typescript(ts_file)

    assert isinstance(result, list)
    assert len(result) > 0
```

### _get_cached_parser With Lazy Import

```python
# Source: consistent with existing lazy import pattern (chunker.py line 100 / ts_chunker.py line 100)
@lru_cache(maxsize=8)
def _get_cached_parser(dialect: str) -> "Parser":
    """Return a cached tree-sitter Parser for the given grammar dialect."""
    from tree_sitter_language_pack import get_parser  # lazy — allows ImportError catch at call site
    return get_parser(dialect)  # type: ignore[arg-type]
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Module-level `from tree_sitter import Parser` | Function-local lazy import in `_get_cached_parser` | Phase 16 | Enables ImportError catch in `chunk_typescript()` |
| No size guard | `if len(source) > 50_000: return chunk_lines(path)` | Phase 16 | Guards against minified/generated JS/TS files hanging the parser |

**What stays the same:**
- `@lru_cache(maxsize=8)` on `_get_cached_parser` — still correct; lazy import inside cached function works because lru_cache caches the *return value*, not the function call overhead
- `from corpus_analyzer.ingest.chunker import chunk_lines` already lazy (line 100 of ts_chunker.py)
- All existing test assertions — zero changes needed for passing tests

---

## Open Questions

1. **`Parser` type annotation after moving import**
   - What we know: `from __future__ import annotations` is already in ts_chunker.py (line 8); this means all annotations are strings at runtime and the import is not needed at runtime
   - What's unclear: mypy may still complain about `Parser` being used as a type if it's not imported even for type checking
   - Recommendation: Add `if TYPE_CHECKING: from tree_sitter import Parser` block, or just use `Any` as the return type of `_get_cached_parser`; the existing `# type: ignore[arg-type]` already suppresses tree-sitter type errors, so `Any` return type is acceptable

2. **Smoke test fixture for 16-03 validation**
   - What we know: CONTEXT.md leaves this to Claude's Discretion; options are project's own TS files or a minimal temp file
   - What's unclear: Whether the project has real `.ts` files in scope of a typical `corpus index` run
   - Recommendation: Use a minimal `tmp_path` temp file via `CliRunner.invoke` for the smoke test — more hermetic than relying on project files

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `src/corpus_analyzer/ingest/ts_chunker.py` — module-level imports identified at lines 14-15
- Direct code inspection: `src/corpus_analyzer/ingest/chunker.py` — `chunk_file()` lazy import at line 356; existing try/except structure
- Direct code inspection: `tests/ingest/test_chunker.py` — pre-existing E501 at line 383 confirmed via `uv run ruff check .`
- Direct code inspection: `tests/ingest/test_indexer.py` — `unittest.mock.patch` usage pattern
- `pyproject.toml` — ruff config (line-length 100, excludes), mypy config (strict), pytest config

### Secondary (MEDIUM confidence)
- `uv run pytest --tb=no -q` output — 318 tests currently passing
- `uv run ruff check .` output — exactly one existing E501 violation before Phase 16 changes
- `uv run mypy src/` output — clean (no issues in 54 source files)

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already installed and in use; versions confirmed from pyproject.toml
- Architecture: HIGH — code read directly; import structure confirmed; mock patterns confirmed from existing tests
- Pitfalls: HIGH — pitfalls derived from direct code analysis (module-level imports, lru_cache behavior, pre-existing ruff violation confirmed by running tools)

**Research date:** 2026-02-24
**Valid until:** 2026-03-24 (30 days; stable stdlib patterns, no fast-moving dependencies)

# Phase 10: Manual Ruff — Leaf to Hub — Research

**Researched:** 2026-02-24
**Domain:** Python code quality — manual ruff violation remediation
**Confidence:** HIGH

## Summary

Phase 10 is a pure code-quality cleanup pass. No new features, no logic changes. It eliminates all remaining ruff violations in `src/` modules (excluding `cli.py`, which is Phase 11's scope) and in `tests/`. The violations are known and enumerated; the work is mechanical line-wrapping plus a small set of semantic fixes for B-series, E741, and E402 rules.

The violation inventory was obtained by running `uv run ruff check . --output-format=concise` against the post-Phase-9 codebase. There are approximately 39 violations in `src/` non-`cli.py` files and 10 in `tests/`. The B-series violations (B023, B017, B904) require semantic understanding but are well-understood patterns with standard fixes. E741 ambiguous-name violations are `l` used as a loop variable in `database.py` and `chunked_processor.py` — simple rename to `link`, `sym`, or `line`. E402 in `rewriter.py` requires moving two mid-file imports to the top.

**Primary recommendation:** Fix violations file-by-file, starting with semantic violations (B/E741/E402), then wrap E501 lines. Run `uv run ruff check .` and `uv run pytest -v` between each file to verify no regressions.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| RUFF-03 | All E501 line-length violations in leaf modules fixed (wrapping, not shortening content) | Violation inventory below; wrapping patterns catalogued per file |
| RUFF-04 | All B-series violations fixed (B905/B007/B017/B023/B904/B008) | B023 in cli.py (out of scope); B017 in tests/store/test_schema.py; B904 in cli.py (out of scope). Actual in-scope: B017 x2 in tests/store/test_schema.py |
| RUFF-05 | All F841/E741 violations fixed (unused variables, ambiguous names) | E741 `l` in database.py:150, 310 and chunked_processor.py:64, 141 |
| RUFF-06 | All E402 import ordering violations in llm/rewriter.py fixed | E402 at rewriter.py:232-233 — two imports after module-level code |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| ruff | project-installed | Lint and violation detection | Already configured; no new install needed |
| pytest | project-installed | Test regression guard | Already configured |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| uv | project standard | Command runner | All `uv run ruff` and `uv run pytest` invocations |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Manual line wrapping | `ruff format` | `ruff format` doesn't fix E501 on long strings/comments — manual wrapping needed for those |
| Rename `l` variable | `# noqa: E741` | noqa suppression adds technical debt; rename is cleaner and zero-risk |

**No new installation required.** All tooling already present.

## Architecture Patterns

### Recommended Fix Order
```
1. Semantic violations first (E402, E741, B017)
   — these change behaviour-semantics, must be verified with tests
2. E501 wrapping last (mechanical, safe to batch by file)
3. Run pytest after each file changed
4. Run ruff check . to confirm zero violations at end
```

### Pattern 1: E501 — Wrapping Long Function Calls with Keyword Arguments
**What:** Break a long call onto multiple lines, one argument per line.
**When to use:** Function calls like `re.findall(...)`, `db.update_document_quality(...)`
**Example:**
```python
# Before (120+ chars):
features.has_numbered_sections = bool(re.search(r'\b(?:step\s+\d+|\d+\.|\d+\))', features.full_text, re.IGNORECASE))

# After:
features.has_numbered_sections = bool(
    re.search(r'\b(?:step\s+\d+|\d+\.|\d+\))', features.full_text, re.IGNORECASE)
)
```

### Pattern 2: E501 — Wrapping Long Chained Conditionals
**What:** Break ternary/conditional expressions across lines.
**When to use:** `database.py` rows like `float(row.get(...) if row.get(...) is not None else 0.0)`
**Example:**
```python
# Before (125+ chars):
category_confidence=float(row.get("category_confidence") if row.get("category_confidence") is not None else 0.0),

# After:
category_confidence=float(
    row.get("category_confidence")
    if row.get("category_confidence") is not None
    else 0.0
),
```

### Pattern 3: E741 — Rename Ambiguous Variable `l`
**What:** Rename `l` loop variable to a semantically meaningful name.
**When to use:** `database.py:150` (`l.model_dump()` in links list), `database.py:310` (`Link(**l)`), `chunked_processor.py:64` and `:141`
**Example:**
```python
# Before:
"links": json.dumps([l.model_dump() for l in doc.links]),

# After:
"links": json.dumps([link.model_dump() for link in doc.links]),

# Before (database.py:310):
links=[Link(**l) for l in json.loads(row.get("links") or "[]")],

# After:
links=[Link(**lnk) for lnk in json.loads(row.get("links") or "[]")],

# chunked_processor.py:64 and 141:
# l = force_level → level_val = force_level
# sum(len(l) for l in atom.lines) → sum(len(line) for line in atom.lines)
```

### Pattern 4: E402 — Move Mid-File Imports to Top
**What:** `llm/rewriter.py:232-233` has `import concurrent.futures` and `from typing import NamedTuple` placed after a large docstring block. Move to top with other imports.
**When to use:** Always — E402 fires whenever an import follows non-import module-level code.
**Approach:**
```python
# rewriter.py top — existing imports include:
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple  # ← already imported at top! (line 6)

# Lines 232-233 are dead duplicates after a prompt string.
# Fix: Remove them. `concurrent.futures` needs adding at top with existing imports.
```
**IMPORTANT:** Check `from typing import NamedTuple` is already at line 6 — if so, lines 232-233 are pure duplicates and simply need deletion (not moving). `concurrent.futures` must be added to top-of-file imports.

### Pattern 5: B017 — Do Not Assert Blind Exception
**What:** `pytest.raises(Exception)` is too broad; B017 flags this.
**When to use:** `tests/store/test_schema.py:148, 153`
**Fix:** Use the specific exception type (e.g., `pydantic.ValidationError`) or add `match=` parameter. If the exact exception is unknown, use `pytest.raises(Exception, match=r"...")` with a regex that distinguishes the error.
**Example:**
```python
# Before:
with pytest.raises(Exception):
    self._make_valid_record(vector=[0.1] * 512)

# After (preferred):
with pytest.raises(ValidationError):
    self._make_valid_record(vector=[0.1] * 512)

# After (if exact type uncertain):
with pytest.raises(Exception, match=r"vector"):
    self._make_valid_record(vector=[0.1] * 512)
```

### Anti-Patterns to Avoid
- **Changing string content to fit line length:** E501 fix must wrap lines structurally, not shorten variable names, truncate strings, or alter regex patterns.
- **Using `# noqa: E741` instead of renaming:** The project standard says "no type: ignore, no noqa unless necessary." Rename the variable instead.
- **Touching `cli.py` E501 violations:** cli.py E501 is Phase 11 scope. Only cli.py B904 and B023 are in Phase 10 scope — but checking the actual violation list, B904 and B023 are BOTH in cli.py. So Phase 10 has zero cli.py changes.
- **Forgetting the `llm/` E501 exemption:** `src/corpus_analyzer/llm/*.py` has `per-file-ignores = ["E501"]`. Do NOT fix E501 in llm/ files — they are already suppressed by config. The only llm/ file needing changes is `rewriter.py` (E402) and `chunked_processor.py` (E741).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Detecting which lines violate E501 | Custom script | `uv run ruff check --output-format=concise` | Ruff already enumerates exact line numbers |
| Regression detection | Manual inspection | `uv run pytest -v` | 281 tests cover all semantic paths |

**Key insight:** The entire fix set is mechanical. Trust ruff's line numbers, verify with tests, move on.

## Common Pitfalls

### Pitfall 1: The `llm/*.py` E501 Exemption
**What goes wrong:** Developer wraps E501 lines in `llm/unified_rewriter.py` or other llm modules unnecessarily.
**Why it happens:** The per-file-ignores exemption for `llm/*.py` was added in Phase 9. `chunked_processor.py` and `rewriter.py` are in llm/ and thus E501-exempt.
**How to avoid:** Only fix E741 and E402 in llm/ files. Do not touch E501 in any `src/corpus_analyzer/llm/*.py` file.
**Warning signs:** If ruff check stops showing E501 for a file, that's fine — but if you are wrapping lines in llm/ files that weren't in the violation list, you are over-engineering.

### Pitfall 2: `rewriter.py` Line 232 — Duplicate vs. Misplaced Imports
**What goes wrong:** Moving lines 232-233 to top without checking if `NamedTuple` is already imported.
**Why it happens:** The file already has `from typing import NamedTuple` at line 6. Line 233 is a duplicate.
**How to avoid:** Check `rewriter.py` lines 1-15 before fixing. If `NamedTuple` is already imported, delete line 233 entirely. Add `import concurrent.futures` at the top-of-file import block.
**Warning signs:** mypy will catch "duplicate import" in some configurations; pytest may not.

### Pitfall 3: B017 Fix Breaking Test Intent
**What goes wrong:** Changing `pytest.raises(Exception)` to a specific type causes the test to fail if the actual raised exception is a different subtype.
**Why it happens:** The test may legitimately accept any exception (pydantic ValidationError vs. ValueError, etc.).
**How to avoid:** Read the docstring of the test and the code under test. If the exception type is truly flexible, use `pytest.raises((ValidationError, ValueError))` or add `match=` to be precise about the error message rather than the type.
**Warning signs:** Test starts failing after B017 fix.

### Pitfall 4: Wrapping Regex Patterns
**What goes wrong:** Breaking a long regex string across multiple lines using string concatenation changes the regex.
**Why it happens:** `re.search(r'...' r'...')` (adjacent string literals) works for regex but is error-prone with backslash escapes.
**How to avoid:** Keep regex strings on a single (long) line inside a parenthesized call, wrapping only the call arguments:
```python
features.has_numbered_sections = bool(
    re.search(
        r'\b(?:step\s+\d+|\d+\.|\d+\))',
        features.full_text,
        re.IGNORECASE,
    )
)
```
This keeps the pattern intact and wraps the function call structure.

### Pitfall 5: Missing Test E501 Violations
**What goes wrong:** Only fixing `src/` E501 violations, leaving `tests/` violations unaddressed — ruff still exits non-zero.
**Why it happens:** Phase scope is described as "leaf modules and core database hub" but VALID-01 requires `ruff check .` to exit 0 with zero violations (achieved in Phase 12 as a gate). However, Phase 10 must not leave regressions — any test E501 should be fixed too for clean progress.
**How to avoid:** Fix all E501 violations not in `cli.py` — including the 10 test file violations.

## Code Examples

Verified patterns from codebase inspection:

### Wrapping a long method call (analyzers/quality.py:80)
```python
# Before:
self.db.update_document_quality(top_doc.id, top_doc.quality_score, is_gold_standard=True)

# After:
self.db.update_document_quality(
    top_doc.id, top_doc.quality_score, is_gold_standard=True
)
```

### Wrapping a long f-string inside a multiline string (analyzers/shape.py:178)
The line is inside a triple-quoted f-string template. The expression itself:
```python
{chr(10).join(f"| H{level} | {count} |" for level, count in sorted(report.heading_depth_distribution.items()))}
```
This is an expression inside an f-string — it cannot be broken with parentheses inside `{}`. Options:
1. Extract to a local variable before the f-string:
```python
depth_rows = chr(10).join(
    f"| H{level} | {count} |"
    for level, count in sorted(report.heading_depth_distribution.items())
)
# Then use {depth_rows} in the f-string
```
2. Add `# noqa: E501` if extraction makes the code less readable (last resort).
Option 1 is preferred per project style.

### Wrapping the classifiers/document_type.py regex calls
```python
# Before:
features.step_indicators = len(re.findall(r'\b(?:step|first|then|next|finally)\b', features.full_text, re.IGNORECASE))

# After:
features.step_indicators = len(
    re.findall(r'\b(?:step|first|then|next|finally)\b', features.full_text, re.IGNORECASE)
)
```

### database.py E741 rename (line 150)
```python
# Before:
"links": json.dumps([l.model_dump() for l in doc.links]),

# After:
"links": json.dumps([link.model_dump() for link in doc.links]),
```

### database.py E741 rename (line 310)
```python
# Before:
links=[Link(**l) for l in json.loads(row.get("links") or "[]")],

# After:
links=[Link(**lnk) for lnk in json.loads(row.get("links") or "[]")],
```

### chunked_processor.py E741 renames (lines 64, 141)
```python
# Line 64 — before:
l = force_level if force_level else current_level
# After:
level_val = force_level if force_level else current_level
# (update references: atoms.append(Atom(..., level=level_val, ...)))

# Line 141 — before:
atom_size = sum(len(l) for l in atom.lines)
# After:
atom_size = sum(len(line) for line in atom.lines)
```

## Violation Inventory (Complete for Phase 10 Scope)

All violations that must be fixed by Phase 10 (excludes `cli.py` which is Phase 11):

### src/ violations (39 total)
| File | Line | Code | Notes |
|------|------|------|-------|
| analyzers/quality.py | 80 | E501 (109) | Wrap `update_document_quality` call |
| analyzers/shape.py | 178 | E501 (111) | Extract f-string expression to local var |
| classifiers/document_type.py | 75 | E501 (120) | Wrap `re.search` call |
| classifiers/document_type.py | 76 | E501 (111) | Wrap `re.search` call |
| classifiers/document_type.py | 79 | E501 (122) | Wrap `re.findall` call |
| classifiers/document_type.py | 80 | E501 (117) | Wrap `re.findall` call |
| classifiers/document_type.py | 81 | E501 (129) | Wrap `re.findall` call |
| classifiers/document_type.py | 82 | E501 (123) | Wrap `re.findall` call |
| classifiers/document_type.py | 87 | E501 (127) | Wrap `re.findall` call |
| classifiers/document_type.py | 116 | E501 (119) | Wrap `idf = math.log(...)` expression |
| classifiers/document_type.py | 125 | E501 (102) | Wrap `CLASSIFICATION_RULES` type annotation |
| classifiers/document_type.py | 210 | E501 (111) | Wrap `for` loop unpacking line |
| classifiers/document_type.py | 234 | E501 (110) | Wrap conditional in `if feature_name in [...]` |
| core/database.py | 150 | E741 | Rename `l` → `link` |
| core/database.py | 207 | E501 (103) | Wrap long method call |
| core/database.py | 310 | E741 | Rename `l` → `lnk` |
| core/database.py | 318 | E501 (125) | Wrap `category_confidence` ternary |
| core/database.py | 320 | E501 (107) | Wrap `quality_score` ternary |
| core/database.py | 321 | E501 (113) | Wrap `is_gold_standard` ternary |
| generators/advanced_rewriter.py | 43 | E501 (102) | Wrap `raise FileNotFoundError` |
| generators/advanced_rewriter.py | 78 | E501 (146) | Wrap long `gold_docs = list(...)` chain |
| generators/advanced_rewriter.py | 87 | E501 (109) | Wrap long line in f-string or extract var |
| generators/advanced_rewriter.py | 93 | E501 (131) | Wrap long string in multiline string |
| generators/advanced_rewriter.py | 94 | E501 (121) | Wrap long string in multiline string |
| generators/advanced_rewriter.py | 97 | E501 (103) | Wrap long string in multiline string |
| generators/advanced_rewriter.py | 107 | E501 (104) | Wrap long string continuation |
| generators/advanced_rewriter.py | 108 | E501 (105) | Wrap long string continuation |
| generators/advanced_rewriter.py | 142 | E501 (103) | Wrap long string in f-string |
| generators/templates.py | 67 | E501 (130) | Wrap long string |
| ingest/chunker.py | 252 | E501 (101) | Wrap long line |
| ingest/indexer.py | 97 | E501 (101) | Wrap long line |
| llm/chunked_processor.py | 64 | E741 | Rename `l` → `level_val` (update references) |
| llm/chunked_processor.py | 141 | E741 | Rename `l` → `line` |
| llm/rewriter.py | 232 | E402 | Move `import concurrent.futures` to top |
| llm/rewriter.py | 233 | E402 | Delete (duplicate `from typing import NamedTuple`) |
| search/engine.py | 114 | E501 (103) | Wrap long line |
| utils/ui.py | 10 | E501 (105) | Wrap long line |
| utils/ui.py | 35 | E501 (123) | Wrap long line |
| utils/ui.py | 40 | E501 (103) | Wrap long line |

### tests/ violations (10 total)
| File | Line | Code | Notes |
|------|------|------|-------|
| tests/cli/test_search_status.py | 126 | E501 (103) | Wrap long assertion |
| tests/config/test_schema.py | 75 | E501 (105) | Wrap long line |
| tests/ingest/test_indexer.py | 365 | E501 (125) | Wrap long line |
| tests/ingest/test_scanner.py | 168 | E501 (102) | Wrap long line |
| tests/search/test_engine.py | 288 | E501 (104) | Wrap long line |
| tests/search/test_engine.py | 318 | E501 (102) | Wrap long line |
| tests/store/test_schema.py | 148 | B017 | Use specific exception type or `match=` |
| tests/store/test_schema.py | 153 | B017 | Use specific exception type or `match=` |
| tests/test_analyzers/test_quality_logic.py | 35 | E501 (102) | Wrap long line |
| tests/test_core/test_db_migration.py | 38 | E501 (127) | Wrap long line |

### Out of scope (Phase 11)
- `cli.py` E501 violations (45 lines) — RUFF-07
- `cli.py` B023 at line 189
- `cli.py` B904 at line 294

### Not in scope (scripts/)
- `scripts/run_rewrite_dry_run.py` — F401 and W293 violations (auto-fixable; appear to be leftover from Phase 9 pass, should be re-run with `--fix`)

## Special Cases

### `analyzers/shape.py:178` — f-string expression wrapping
This line contains a generator expression inside an f-string `{}`. Python does not allow line breaks inside f-string `{}` expressions in Python < 3.12. The project targets Python 3.12 (`target-version = "py312"` in pyproject.toml), but the safer approach is to extract to a local variable before the f-string to maintain readability and portability.

### `generators/advanced_rewriter.py:78` — long chained call
```python
gold_docs = list(self.client.db.get_gold_standard_documents(category=doc.category, tag=tag)) if hasattr(self.client, 'db') else []
```
This is 146 chars. Best fix: extract the call or break the ternary:
```python
gold_docs = (
    list(self.client.db.get_gold_standard_documents(category=doc.category, tag=tag))
    if hasattr(self.client, "db")
    else []
)
```

### `generators/advanced_rewriter.py:93-108` — long strings in a multiline string
Lines 93-108 are inside a `system_prompt = (...)` parenthesized string. Long string literals can be broken with implicit string concatenation:
```python
system_prompt = (
    "You are an expert technical writer specializing in creating strict, structured "
    "documentation agent instructions. "
    ...
)
```
This is safe as Python concatenates adjacent string literals at compile time.

### `classifiers/document_type.py:125` — type annotation line
```python
CLASSIFICATION_RULES: list[tuple[DocumentCategory, float, list[str], list[str], dict[str, float]]] = [
```
This is a type annotation for a module-level constant. The annotation can be wrapped:
```python
CLASSIFICATION_RULES: list[
    tuple[DocumentCategory, float, list[str], list[str], dict[str, float]]
] = [
```

### `core/database.py:318-321` — ternary expressions in constructor
These are inside a `Document(...)` constructor call. The ternary patterns are:
```python
category_confidence=float(row.get("category_confidence") if row.get("category_confidence") is not None else 0.0),
```
Can simplify AND shorten with `or`:
```python
category_confidence=float(row.get("category_confidence") or 0.0),
```
**CAUTION:** The `or` shortcut changes semantics if `category_confidence` can be `0.0` (falsy) when it should be preserved. The original ternary specifically handles `None` but not `0`. Use the explicit `is not None` form wrapped across lines to be safe:
```python
category_confidence=float(
    row.get("category_confidence")
    if row.get("category_confidence") is not None
    else 0.0
),
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Suppress all violations with noqa | Fix at source | Phase 9 decision | Cleaner codebase, CI enforces quality |
| `llm/*.py` E501 suppressed globally | Per-file-ignores in pyproject.toml | Phase 9 | All other modules must fix E501 |

**Deprecated/outdated:**
- Auto-fix pass (Phase 9): Already applied. Do not re-run `--fix` without verifying it won't re-introduce removed imports.

## Open Questions

1. **`tests/store/test_schema.py` B017 — what exact exception does `_make_valid_record` raise?**
   - What we know: It creates a pydantic model with invalid vector dimensions; pydantic raises `ValidationError`
   - What's unclear: Whether it's `pydantic.ValidationError` or `pydantic_core.ValidationError` or `ValueError`
   - Recommendation: Read the test file's imports and `_make_valid_record` implementation, then use `pytest.raises(ValidationError)` with the correct import

2. **`scripts/run_rewrite_dry_run.py` violations — are scripts/ in scope?**
   - What we know: `pyproject.toml` doesn't exclude scripts/; the violations are W293 and F401 (auto-fixable)
   - What's unclear: Whether VALID-01 requires scripts/ to be clean too, or only src/ and tests/
   - Recommendation: Run `--fix` on scripts/ as well to avoid any surprises at VALID-01 gate

## Sources

### Primary (HIGH confidence)
- Direct `uv run ruff check . --output-format=concise` execution — full violation list as of 2026-02-24 post-Phase-9
- Direct file reads: `rewriter.py`, `database.py`, `chunked_processor.py`, `document_type.py`, `advanced_rewriter.py`, `test_schema.py`
- `pyproject.toml` ruff configuration — per-file-ignores, line-length, select rules

### Secondary (MEDIUM confidence)
- Ruff B017 docs (training knowledge): `pytest.raises(Exception)` must be replaced with specific type or `match=` parameter

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Violation inventory: HIGH — obtained from live ruff run against actual codebase
- Fix patterns: HIGH — standard Python line-wrapping, variable renaming, import reordering
- B017 fix: MEDIUM — need to verify actual exception type from `_make_valid_record` before committing

**Research date:** 2026-02-24
**Valid until:** Until next ruff check run (violations may change if any other work lands on main)

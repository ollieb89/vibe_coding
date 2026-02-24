# Phase 18: CLI Chunk Display - Research

**Researched:** 2026-02-24
**Domain:** Python CLI output formatting, Rich terminal library, search result display
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Text preview line:**
- Indent the preview line with 4 spaces (visually separates snippet from path line, consistent with ripgrep style)
- If `chunk_text` is empty (legacy unmigrated rows), skip the preview line entirely — no blank second line
- If `chunk_text` contains newlines, take only up to the first newline, then truncate to 200 chars
- Ellipsis rule: show up to 200 chars of content, then append `...` if truncated (200 chars + `...`, not 200 total)

**Score & field formatting:**
- Always 3 decimal places: `score:0.021`, `score:0.100` — consistent column width for scanning
- For legacy rows where `start_line=0` and `end_line=0`: omit the line range entirely — show `path/to/file.md [skill] score:0.021` not `:0-0`
- When construct type is empty/unknown: omit the `[brackets]` entirely — don't show `[]` or a fallback label

**Visual grouping:**
- Blank line between results — each path+preview pair is visually isolated
- No summary header — dive straight into results; no count line before or after
- No special grouping for consecutive results from the same file — each chunk is an independent entry
- Use Rich for colour: path bold/white, construct type dimmed, score in cyan; Rich auto-suppresses when piped (TTY detection)

**Empty & edge states:**
- No results: `No results for "query"` — simple, matches existing FILT-03 hint style
- FILT-03 hint (`No results above X.xxx. Run without --min-score to see available scores.`) unchanged
- Empty database treated as zero results — same `No results for "query"` message, no special-casing

**Formatter module:**
- Implement as a standalone module (e.g. `ingest/formatters.py` or similar) — testable in isolation, keeps `cli.py` lean

### Claude's Discretion
- Exact Rich colour/style choices within the guidelines (bold path, dimmed construct, cyan score)
- Exact module path for the formatter (within project conventions)
- Indentation amount (2 or 4 spaces — 4 preferred based on user's selection)

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CHUNK-02 | `corpus search` CLI output changed from 3-line snippet format to grep/compiler-error format: `path/to/file.md:42-67 [skill] score:0.021` on the primary line; chunk text (truncated to 200 chars) on the next line; format is IDE-clickable (VSCode, IntelliJ parse `file:line` natively) | Phase 17 landed `start_line`, `end_line`, `chunk_text` in `ChunkRecord`; formatter module pattern already established in `search/formatter.py`; Rich already in use at `>=13.7.0` (14.2.0 installed) |
</phase_requirements>

---

## Summary

Phase 18 reformats the `corpus search` output from a 3-line snippet block to a grep/compiler-error style that IDEs can parse. The technical work is straightforward: add a `format_result()` function in a new formatter module, replace the render loop in `cli.py`'s `search_command`, and add unit tests for the formatter.

All the upstream data prerequisites are already in place. Phase 17 (CHUNK-01) landed `start_line`, `end_line`, `chunk_name`, and `chunk_text` as columns in the `ChunkRecord` LanceDB schema. Search results returned by `CorpusSearch.hybrid_search()` are plain `dict[str, Any]` objects, so any of these fields can be accessed with `.get()`. Rich 14.2.0 is already installed and used throughout `cli.py`; TTY auto-suppression is built in via `Console()` without extra configuration.

The key design point is the formatter module must be pure Python with no I/O dependencies so it is trivially unit-testable. The existing `search/formatter.py` module (`extract_snippet`) is the natural home for the new `format_result()` function — or a dedicated module at `search/formatters.py` following project conventions. Either way, `cli.py` stays lean and the formatter is tested in isolation, mirroring the pattern already used for `test_formatter.py`.

**Primary recommendation:** Add `format_result(result: dict[str, Any], cwd: Path) -> tuple[str, str | None]` to `src/corpus_analyzer/search/formatter.py` (no new module needed), update the `search_command` render loop in `cli.py` to call it, and add tests in `tests/search/test_formatter.py`.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| rich | >=13.7.0 (14.2.0 installed) | Terminal colour, bold/dim markup, TTY detection | Already used in `cli.py` for all other output; auto-suppresses ANSI when piped |
| pathlib.Path | stdlib | `relative_to(cwd)` for shorter paths | Already used throughout the project |
| typer | already in use | CLI framework; no changes needed | Phase only touches the render loop, not the arg definitions |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| os.getcwd / Path.cwd() | stdlib | Compute CWD for relative path display | Called once per `search_command` invocation, not per result |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `rich.console.Console.print()` with markup strings | `rich.text.Text` objects | Markup strings are simpler and consistent with existing `cli.py` style |
| `Path.relative_to(cwd)` | Manual string prefix stripping | `relative_to` is safer and handles edge cases; falls back to absolute if path is outside CWD |

**Installation:** No new dependencies. All required libraries already present.

---

## Architecture Patterns

### Recommended Project Structure

```
src/corpus_analyzer/search/
├── formatter.py          # ADD: format_result() here alongside extract_snippet()
├── engine.py             # unchanged
├── classifier.py         # unchanged
└── summarizer.py         # unchanged

tests/search/
└── test_formatter.py     # ADD: new test functions for format_result()
```

### Pattern 1: Pure Formatter Function

**What:** A pure function that takes a result dict and CWD, returns the formatted strings to be printed. No Rich Console object inside the function — returns plain strings with Rich markup. The CLI layer calls `console.print()`.

**When to use:** Always — this keeps the formatter testable without capturing Rich output.

**Example:**
```python
# src/corpus_analyzer/search/formatter.py

from __future__ import annotations

from pathlib import Path
from typing import Any


def format_result(result: dict[str, Any], cwd: Path) -> tuple[str, str | None]:
    """Format a single search result for grep/compiler-error style display.

    Returns a tuple of (primary_line, preview_line_or_None).
    Both strings contain Rich markup. preview_line is None when chunk_text is empty.

    Args:
        result: A dict returned by CorpusSearch.hybrid_search().
        cwd: Current working directory used to make file_path relative.

    Returns:
        (primary_line, preview_line) where preview_line is None for legacy rows.
    """
    file_path = str(result.get("file_path", ""))
    start_line = int(result.get("start_line", 0))
    end_line = int(result.get("end_line", 0))
    construct_type = result.get("construct_type") or ""
    score = float(result.get("_relevance_score", 0.0))
    chunk_text = str(result.get("chunk_text") or "")

    # Compute relative path
    try:
        rel_path = str(Path(file_path).relative_to(cwd))
    except ValueError:
        rel_path = file_path  # path outside CWD — use absolute

    # Build location component: omit line range for legacy rows (0-0)
    if start_line > 0 or end_line > 0:
        location = f"{rel_path}:{start_line}-{end_line}"
    else:
        location = rel_path

    # Build construct bracket: omit entirely if empty
    construct_part = f" [dim][{construct_type}][/dim]" if construct_type else ""

    # Score always 3 decimal places in cyan
    score_part = f" [cyan]score:{score:.3f}[/cyan]"

    primary_line = f"[bold]{location}[/bold]{construct_part}{score_part}"

    # Preview line: take first line of chunk_text, truncate to 200 chars
    if not chunk_text:
        return primary_line, None

    first_line = chunk_text.split("\n", 1)[0]
    if len(first_line) > 200:
        preview = first_line[:200] + "..."
    else:
        preview = first_line

    return primary_line, f"    {preview}"
```

### Pattern 2: CLI Render Loop Update

**What:** Replace the existing 3-line render block in `search_command` with calls to `format_result()`.

**When to use:** Only the render loop needs changing — all flag handling, filtering, and sorting remain untouched.

**Example:**
```python
# cli.py — search_command render loop (replaces existing for-loop body)

from corpus_analyzer.search.formatter import extract_snippet, format_result
from pathlib import Path

cwd = Path.cwd()

for result in results:
    primary, preview = format_result(result, cwd)
    console.print(primary)
    if preview is not None:
        console.print(preview)
    console.print()  # blank line between results
```

### Pattern 3: Relative Path Fallback

**What:** `Path.relative_to(cwd)` raises `ValueError` if the path is outside the CWD tree (e.g. `/home/user/other-project/file.md` when CWD is `/home/user/project`). Always catch this and fall back to the absolute path.

**When to use:** Every time `relative_to` is called on an untrusted path.

```python
try:
    rel_path = str(Path(file_path).relative_to(cwd))
except ValueError:
    rel_path = file_path
```

### Anti-Patterns to Avoid

- **Putting `Console()` inside `format_result()`:** Makes the function untestable without mocking Rich. Return markup strings; let the CLI own the console.
- **Using `extract_snippet()` for the preview line:** `extract_snippet` does query-aware windowing across multiple lines. Phase 18 replaces it with `chunk_text` (the exact stored slice). The `extract_snippet` function stays in the module for backward compat but is no longer called from `search_command`.
- **Hardcoding absolute paths in tests:** Tests for `format_result()` should pass a mock `cwd` (`tmp_path` or `Path("/some/cwd")`), not rely on the real process CWD.
- **Showing `:0-0` for legacy rows:** The decision is to omit the line range entirely when both are zero — never show the `:0-0` artifact.
- **Showing `[]` for empty construct type:** Omit brackets entirely — don't render an empty bracket pair.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TTY detection for ANSI suppression | Custom `isatty()` check | `rich.Console()` default | Rich handles stdout/stderr TTY detection automatically; piped output gets plain text |
| Relative path computation | Manual string prefix stripping | `Path.relative_to(cwd)` | Handles OS path separator differences and `.` normalisation correctly |

**Key insight:** Rich's `Console` already does the right thing for IDE-clickable output: when piped (non-TTY), it strips all markup and emits plain text. The `file:line` format is preserved as-is, which is exactly what VSCode and IntelliJ problem matchers need.

---

## Common Pitfalls

### Pitfall 1: `relative_to()` ValueError on Cross-Repo Paths

**What goes wrong:** If the indexed file lives under a different root than CWD (e.g. a source added with an absolute path in another directory), `Path.relative_to()` raises `ValueError`.
**Why it happens:** `relative_to()` only succeeds when the path is a descendant of the base.
**How to avoid:** Always wrap in `try/except ValueError` and fall back to the absolute path string.
**Warning signs:** Tests that set `cwd=Path("/some/cwd")` but `file_path="/other/path/file.md"` — will raise without the guard.

### Pitfall 2: chunk_text Empty for Legacy Rows

**What goes wrong:** Pre-Phase 17 rows have `chunk_text=""`. If the formatter doesn't guard this, it will print a blank indented preview line.
**Why it happens:** Phase 17 sets `chunk_text=""` as the default for existing rows — they are not re-indexed automatically.
**How to avoid:** Check `if not chunk_text:` and return `None` for the preview line. The CONTEXT.md decision: "skip the preview line entirely — no blank second line."
**Warning signs:** Test with a result dict that has `chunk_text=""` — should produce only one line of output.

### Pitfall 3: Newlines in chunk_text

**What goes wrong:** `chunk_text` stores the full raw file slice including internal newlines. Printing it directly produces multi-line output that breaks the two-line-per-result format.
**Why it happens:** `chunk_text` is the exact source text — docstrings, multi-line function bodies, etc. contain `\n`.
**How to avoid:** `chunk_text.split("\n", 1)[0]` — take only up to the first newline before truncation.
**Warning signs:** Test with `chunk_text="line 1\nline 2\nline 3"` — should produce `    line 1` not three lines.

### Pitfall 4: Rich Markup in Path or chunk_text

**What goes wrong:** If `file_path` or `chunk_text` contains `[` or `]` characters, Rich will attempt to parse them as markup tags, potentially causing `MarkupError` or garbled output.
**Why it happens:** Rich's default `Console.print()` interprets square brackets as markup.
**How to avoid:** Use `rich.markup.escape()` on any user-supplied string before embedding it in a markup string. The path, construct type, and preview text should all be escaped.
**Warning signs:** File paths with `[deprecated]` or TypeScript generics like `Array[T]` in chunk_text.

### Pitfall 5: Import of `extract_snippet` in Existing Tests

**What goes wrong:** `tests/search/test_formatter.py` currently imports `extract_snippet` from `corpus_analyzer.search.formatter`. Adding `format_result` to the same module must not break the existing import.
**Why it happens:** Module-level imports fail the whole test file if any import in the module breaks.
**How to avoid:** Add `format_result` as a new export alongside `extract_snippet` — do not rename or remove the existing function.

---

## Code Examples

Verified patterns from the existing codebase:

### Existing Rich markup style in cli.py (lines 409–417)
```python
# src/corpus_analyzer/cli.py — current search render loop (to be replaced)
for result in results:
    console.print(
        f"[bold blue]{result['file_path']}[/]  "
        f"[dim]{result.get('construct_type') or 'documentation'}[/]  "
        f"[dim]score: {result.get('_relevance_score', 0.0):.3f}[/]"
    )
    if result.get("summary"):
        console.print(f"  [italic]{result['summary']}[/italic]")
    console.print(f"  {extract_snippet(str(result['text']), query)}")
    console.print()
```

### ChunkRecord fields available in search results (from store/schema.py)
```python
# Fields Phase 18 uses from each result dict:
file_path: str          # absolute path — must make relative with Path.relative_to(cwd)
start_line: int         # 1-indexed; 0 for legacy rows
end_line: int           # 1-indexed; 0 for legacy rows
construct_type: str | None   # "skill", "agent", etc.; None/empty → omit brackets
_relevance_score: float      # RRF score; always 3 decimal places
chunk_text: str         # raw file slice; empty string for legacy rows
```

### Rich markup escape pattern
```python
from rich.markup import escape

# Safe: user-controlled strings are escaped before interpolation into markup
primary_line = f"[bold]{escape(rel_path)}[/bold]..."
```

### Test pattern for format_result (mirrors existing test_formatter.py style)
```python
# tests/search/test_formatter.py — new tests to add

from pathlib import Path
from corpus_analyzer.search.formatter import format_result

def test_format_result_with_line_range() -> None:
    """Primary line includes line range when start_line > 0."""
    result = {
        "file_path": "/cwd/skills/foo.md",
        "start_line": 42,
        "end_line": 67,
        "construct_type": "skill",
        "_relevance_score": 0.021,
        "chunk_text": "Some chunk content here",
    }
    primary, preview = format_result(result, cwd=Path("/cwd"))
    assert "skills/foo.md:42-67" in primary
    assert "score:0.021" in primary
    assert preview == "    Some chunk content here"


def test_format_result_legacy_row_no_line_range() -> None:
    """Legacy rows (start_line=0, end_line=0) omit line range entirely."""
    result = {
        "file_path": "/cwd/foo.md",
        "start_line": 0,
        "end_line": 0,
        "construct_type": "skill",
        "_relevance_score": 0.015,
        "chunk_text": "",
    }
    primary, preview = format_result(result, cwd=Path("/cwd"))
    assert ":0-0" not in primary
    assert "foo.md" in primary
    assert preview is None


def test_format_result_empty_construct_omits_brackets() -> None:
    """Empty construct type omits brackets entirely."""
    result = {
        "file_path": "/cwd/doc.md",
        "start_line": 1,
        "end_line": 10,
        "construct_type": None,
        "_relevance_score": 0.010,
        "chunk_text": "content",
    }
    primary, preview = format_result(result, cwd=Path("/cwd"))
    assert "[]" not in primary
    assert "[None]" not in primary


def test_format_result_chunk_text_newline_takes_first_line() -> None:
    """chunk_text with newlines: only first line used for preview."""
    result = {
        "file_path": "/cwd/foo.md",
        "start_line": 5,
        "end_line": 8,
        "construct_type": "skill",
        "_relevance_score": 0.020,
        "chunk_text": "first line\nsecond line\nthird line",
    }
    _, preview = format_result(result, cwd=Path("/cwd"))
    assert preview == "    first line"


def test_format_result_truncates_at_200_chars() -> None:
    """Preview truncated to 200 chars + '...' if longer."""
    long_text = "x" * 250
    result = {
        "file_path": "/cwd/foo.md",
        "start_line": 1,
        "end_line": 1,
        "construct_type": "skill",
        "_relevance_score": 0.010,
        "chunk_text": long_text,
    }
    _, preview = format_result(result, cwd=Path("/cwd"))
    assert preview is not None
    assert preview.endswith("...")
    # 4 spaces indent + 200 chars content + 3 dots = 207
    assert len(preview) == 207
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 3-line snippet block (`file_path`, `summary`, `extract_snippet(text)`) | 2-line grep format (`path:start-end [type] score:X.XXX` + indented chunk_text) | Phase 18 | IDE-clickable, pipe-friendly, concise |
| `extract_snippet()` does query-aware multi-line window | `chunk_text` is the exact stored slice (first line only for display) | Phase 17+18 | Accurate line provenance; no heuristic windowing |

---

## Open Questions

1. **Rich markup escaping scope**
   - What we know: `file_path` is an absolute OS path (unlikely to contain `[`); `chunk_text` is arbitrary source text (TypeScript generics, documentation with `[link]` syntax, etc.)
   - What's unclear: How aggressively to escape — just `chunk_text`, or also `rel_path` and `construct_type`?
   - Recommendation: Escape all three user-data strings (`rel_path`, `construct_type`, preview text) with `rich.markup.escape()`. The overhead is negligible and correctness is more important than micro-optimisation.

2. **`search/formatter.py` vs new `search/formatters.py`**
   - What we know: `search/formatter.py` already exports `extract_snippet` and is tested in `tests/search/test_formatter.py`. The CONTEXT.md says the module can be at `ingest/formatters.py` or "similar". Project convention is singular (`formatter.py`, not `formatters.py`).
   - What's unclear: Whether to add to the existing module or create a new one.
   - Recommendation: Add `format_result` to the existing `search/formatter.py`. It is the search result formatting home; adding a sibling function keeps related code co-located, avoids a new module import, and the existing tests file is the right place for the new tests.

---

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection — `src/corpus_analyzer/cli.py` lines 408–417 (current render loop)
- Direct codebase inspection — `src/corpus_analyzer/search/formatter.py` (existing formatter)
- Direct codebase inspection — `src/corpus_analyzer/store/schema.py` (ChunkRecord fields from Phase 17)
- Direct codebase inspection — `tests/search/test_formatter.py` (existing test patterns)
- `pyproject.toml` — `rich>=13.7.0` confirmed; installed 14.2.0

### Secondary (MEDIUM confidence)
- Rich 14.2.0 documentation — `rich.markup.escape()` for escaping user strings in markup; `Console()` TTY auto-detection behavior

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in the project; no new dependencies
- Architecture: HIGH — formatter module pattern directly mirrors existing `search/formatter.py`; all data fields verified present in Phase 17 schema
- Pitfalls: HIGH — derived from direct reading of the codebase and CONTEXT.md decisions; Rich markup escaping is a known real-world issue

**Research date:** 2026-02-24
**Valid until:** 2026-03-26 (stable domain — stdlib + Rich; no fast-moving external dependencies)

# Phase 11: Manual Ruff — CLI + Mypy - Research

**Researched:** 2026-02-24
**Domain:** Python static analysis — ruff E501 line wrapping, mypy --strict type annotation
**Confidence:** HIGH

## Summary

Phase 11 is a pure code-quality phase: no new features, no dependencies to install, no library APIs to learn. Every task is a precise mechanical edit to a specific file guided by the exact compiler output from `ruff check` and `mypy src/`. Both tools are already installed and configured in `pyproject.toml`.

The 45 E501 violations in `cli.py` are Typer `Annotated[...]` parameter signatures — long because the help strings run past column 100. The wrapping technique is to break the `Annotated[..., typer.Option(...)]` call across lines by putting the `typer.Option(...)` call on the next line and splitting the `help=` string into a continuation or shorter phrase. B006 list defaults (`= ["**/*"]`, `= []`) are already suppressed by the `per-file-ignores` config in `pyproject.toml`; they are not ruff violations in this file.

The 41 mypy errors across 9 files are all straightforward and fall into four categories: (1) `sqlite-utils` union-attr — the subscript operator on `self.db[...]` returns `Table | View` and mypy does not know only Table methods are called; the fix is `cast(Table, self.db["..."])` at every call site; (2) missing/incomplete type annotations on module-level and nested functions; (3) a genuine bug where `DEFAULT_SYSTEM_PROMPT` was accidentally made a `tuple[str]` by a trailing comma, causing a `str | tuple[str]` operator error on line 401 of `rewriter.py`; (4) abstract class instantiation error in `extractors/__init__.py` — the dict dispatch stores class objects typed as `type[BaseExtractor]` (abstract) and mypy reports you cannot instantiate an abstract class, even though all concrete classes implement `extract`.

**Primary recommendation:** Work file-by-file, run `uv run mypy src/ --no-error-summary 2>&1 | grep "^src/corpus_analyzer/FILE"` after each file to confirm zero errors before moving on. For cli.py, process E501 wrapping in a single pass.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| RUFF-07 | All 45 E501 violations in `cli.py` fixed (lines wrapped) | Line-wrapping patterns for Typer Annotated signatures documented below |
| MYPY-01 | `core/database.py` zero mypy errors — `cast(Table, ...)` at all sqlite-utils call sites | `cast` pattern + bare `dict`/`list` annotations documented below |
| MYPY-02 | `llm/chunked_processor.py` zero mypy errors — nested functions annotated, `Atom` promoted to module level | Promotion + annotation patterns documented below |
| MYPY-03 | `utils/ui.py` zero mypy errors | Return type + argument annotation fixes documented below |
| MYPY-04 | `extractors/markdown.py` and `extractors/__init__.py` zero mypy errors | `dict[str, ...]` annotation and abstract class dispatch fix documented below |
| MYPY-05 | `llm/rewriter.py` zero mypy errors — operator bug investigated and fixed; `OllamaClient.db` field added | Bug root cause confirmed: trailing comma makes `DEFAULT_SYSTEM_PROMPT` a tuple; fix: remove trailing comma; `db` field: add `Optional` attribute to `OllamaClient` |
| MYPY-06 | `llm/ollama_client.py`, `ingest/chunker.py`, `analyzers/shape.py` zero mypy errors | Individual patterns documented below |
</phase_requirements>

## Standard Stack

### Core (already installed — no new dependencies)
| Tool | Version | Purpose | Config |
|------|---------|---------|--------|
| ruff | >=0.4.0 | Linter + formatter | `pyproject.toml [tool.ruff]` |
| mypy | >=1.9.0 | Static type checker (--strict) | `pyproject.toml [tool.mypy]` |
| sqlite-utils | >=3.36 | DB access layer (causes union-attr errors) | N/A |

### Key imports needed for fixes
```python
from typing import cast
from sqlite_utils.db import Table   # for cast(Table, ...) pattern
from typing import Any              # already used in some files
```

**Verification commands:**
```bash
uv run ruff check src/corpus_analyzer/cli.py        # target: 0 errors
uv run mypy src/ --no-error-summary                 # target: 0 errors
uv run pytest -v                                    # must stay green (281 tests)
```

## Architecture Patterns

### Pattern 1: sqlite-utils union-attr fix — cast(Table, ...)

**What:** `self.db["tablename"]` returns `Table | View`. sqlite-utils intentionally types the subscript this way. The correct mypy fix is a `cast` at the call site.

**When to use:** Every call site where `self.db["documents"]` or `self.db["chunks"]` is subscripted and a `Table`-only method is called (`.insert`, `.update`, `.delete_where`).

**Example:**
```python
# Before (causes union-attr errors):
self.db["chunks"].delete_where("document_id = ?", [doc_id])
self.db["documents"].update(doc_id, data, alter=True)
self.db["chunks"].insert(data)

# After (mypy-clean):
from typing import cast
from sqlite_utils.db import Table

cast(Table, self.db["chunks"]).delete_where("document_id = ?", [doc_id])
cast(Table, self.db["documents"]).update(doc_id, data, alter=True)
cast(Table, self.db["chunks"]).insert(data)
```

**Affected lines in `core/database.py`:** 94, 96, 100, 175, 229, 233, 243, 254

### Pattern 2: Bare generic annotations

**What:** mypy --strict requires `dict[str, ...]` not bare `dict`, and `list[SomeType]` not bare `list`.

**Affected locations:**
- `database.py` line 140: `def _doc_to_dict(self, doc: Document) -> dict:` → `-> dict[str, Any]:`
- `database.py` line 185: `params: list = []` → `params: list[str | int] = []` or `params: list[Any] = []`
- `database.py` line 271: same pattern
- `database.py` line 302: `def _row_to_document(self, row: dict) -> Document:` → `row: dict[str, Any]`
- `extractors/markdown.py` line 68: `def _extract_title(self, ..., metadata: dict, ...) -> str:` → `metadata: dict[str, Any]`
- `analyzers/shape.py` line 212: `def _generate_recommended_schema(report: ShapeReport) -> dict:` → `-> dict[str, Any]:`

### Pattern 3: float() from None — arg-type fix

**What:** `database.py` lines 322 and 328 call `float(row.get("x"))` where `.get()` returns `Any | None`. `float(None)` is a runtime error and mypy flags it.

**Current code (lines 321-329):**
```python
category_confidence=float(
    row.get("category_confidence")
    if row.get("category_confidence") is not None
    else 0.0
),
```

**Fix:** The inline ternary is already there but mypy still infers `Any | float | None` because `Any` subsumes the None check. Use explicit cast or local variable:
```python
_cc = row.get("category_confidence")
category_confidence=float(_cc) if _cc is not None else 0.0,
```

### Pattern 4: Nested function annotation — chunked_processor.py

**What:** `finalize_atom`, `get_chunk_text`, and `chain_lines` are nested functions inside `split_on_headings`. mypy --strict requires all functions to have full type annotations.

**The Atom dataclass** is also defined inside the function, which mypy cannot analyse in a typed context (forward reference issues for the nested `list[Atom]` annotation). The project decision (STATE.md `[v1.3 planning]`) is to promote `Atom` to module level.

**Fix:**
1. Move `@dataclass class Atom` to module level (before `split_on_headings`).
2. Add full signatures to nested functions:

```python
def finalize_atom(
    force_heading: str | None = None,
    force_level: int = 0,
    is_code_atom: bool = False,
) -> None:
    ...

def get_chunk_text(atoms_list: list[Atom]) -> str:
    ...

def chain_lines(atoms_list: list[Atom]) -> list[str]:
    ...
```

**Note:** `force_heading=None, force_level=0` are `nonlocal` mutating functions — the `nonlocal` declaration must stay inside the function body.

### Pattern 5: Promote Atom to module level

```python
# At module level (before split_on_headings):
@dataclass
class Atom:
    """Atomic block unit for document chunking."""
    lines: list[str]
    heading: str | None
    level: int
    is_code: bool
    start_idx: int
```

### Pattern 6: utils/ui.py — missing annotations

Two functions need return type and argument annotations:

```python
def print_table_schema(table_name: str, table_obj: Any) -> None:
    ...

def print_sample_data(table_name: str, table_obj: Any, limit: int = 5) -> None:
    ...
```

The `table_obj` parameter is a sqlite-utils `Table` object but since it's accessed via duck-typing (`.columns`, `.pks`, `.rows_where`), `Any` is the safe annotation here. Import `Any` from `typing`.

### Pattern 7: extractors/__init__.py — abstract class instantiation

**Error:** `Cannot instantiate abstract class "BaseExtractor" with abstract attribute "extract"` at line 33.

**Root cause:** The `extractors` dict maps suffix strings to extractor classes. The type is inferred as `dict[str, type[BaseExtractor]]` because `MarkdownExtractor` and `PythonExtractor` are subclasses of `BaseExtractor`. mypy then complains that `type[BaseExtractor]` is abstract.

**Fix:** Annotate the dict explicitly as `dict[str, type[MarkdownExtractor | PythonExtractor]]` or use `type[BaseExtractor]` with a `# type: ignore[abstract]` for just that line — but since abstractness is a real constraint, the cleanest fix is to type the dict as `dict[str, type[MarkdownExtractor] | type[PythonExtractor]]`:

```python
from corpus_analyzer.extractors.markdown import MarkdownExtractor
from corpus_analyzer.extractors.python import PythonExtractor

extractors: dict[str, type[MarkdownExtractor] | type[PythonExtractor]] = {
    ".md": MarkdownExtractor,
    ".py": PythonExtractor,
    ".txt": MarkdownExtractor,
    ".rst": MarkdownExtractor,
}
extractor_class = extractors.get(suffix)
if extractor_class:
    extractor = extractor_class()
    return extractor.extract(file_path, root)
```

Note: the imports must be at the call site (inside the function) to avoid circular imports — they already are. Just add the explicit type annotation to the `extractors` dict declaration.

### Pattern 8: rewriter.py — DEFAULT_SYSTEM_PROMPT trailing comma bug

**What:** Line 230 ends with `""",` — a trailing comma after the string literal. In Python, this makes `DEFAULT_SYSTEM_PROMPT` a `tuple[str]` (single-element tuple), not a `str`.

**Mypy error:** `No overload variant of "__add__" of "tuple" matches argument type "str"` at line 401: `system_prompt += "..."`. The `.get()` call can return `DEFAULT_SYSTEM_PROMPT` (a `tuple[str]`) as the default value.

**Fix:** Remove the trailing comma from line 230:
```python
# Before:
Be concise but comprehensive. Preserve important details. Do not include these instructions in the output.""",

# After:
Be concise but comprehensive. Preserve important details. Do not include these instructions in the output."""
```

This is a genuine bug, not just a type annotation issue. Runtime behaviour: calling `rewrite_category(...)` with a category not in `CATEGORY_PROMPTS` would assign a tuple to `system_prompt` and crash at the `+=` line.

### Pattern 9: rewriter.py — OllamaClient.db attribute

**Error:** `"OllamaClient" has no attribute "db"` at line 409: `adv_rewriter.client.db = db`.

**Context (STATE.md):** "OllamaClient — verify whether it is a Pydantic model or plain class before adding `db: Optional[...]` field"

**Verified:** `OllamaClient` is a plain class (not Pydantic). The fix is to add an optional field:

```python
from corpus_analyzer.core.database import CorpusDatabase  # TYPE_CHECKING guard to avoid circular

class OllamaClient:
    def __init__(self, ...) -> None:
        ...
        self.db: CorpusDatabase | None = None
```

**Circular import risk:** `ollama_client.py` does not currently import from `core/database.py`. Use `TYPE_CHECKING` guard if circular:
```python
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from corpus_analyzer.core.database import CorpusDatabase
```
Then annotate: `self.db: CorpusDatabase | None = None`.

### Pattern 10: rewriter.py — process_document missing annotation

**Error:** `Function is missing a type annotation for one or more arguments` at line 240.

**Current signature:**
```python
def process_document(
    doc,
    client: OllamaClient,
    ...
    adv_rewriter,
    ...
```

**Fix:** Annotate `doc` and `adv_rewriter`:
```python
from corpus_analyzer.core.models import Document
from typing import Any

def process_document(
    doc: Document,
    client: OllamaClient,
    ...
    adv_rewriter: Any,
    ...
```

`adv_rewriter` is typed `Any` because `AdvancedRewriter` is imported conditionally inside the function. Alternatively import under `TYPE_CHECKING`.

### Pattern 11: ollama_client.py — no-any-return

**Error:** Line 41: `Returning Any from function declared to return "str"` in `generate()`.

**Root cause:** `response["message"]["content"]` — `response` is typed as `ChatResponse` by the ollama library but subscript access returns `Any`.

**Fix:** Explicit cast or attribute access:
```python
# Option A — use attribute access (if ollama library has typed attributes):
return str(response.message.content)

# Option B — cast:
from typing import cast
return cast(str, response["message"]["content"])
```

Check which one is appropriate: the ollama library's `ChatResponse` type. If `response.message.content` is a typed `str` attribute, use it directly. If not, `cast(str, ...)` is fine.

Similarly in `generate_stream`, `chunk.get("message", {}).get("content")` — this is already gated by `if content :=` so the yield is fine; but verify if there's a similar error there.

Also in `list_models()`, `response.get("models", [])` and `m["name"]` — both return `Any`. Fix: `[m["name"] for m in response.get("models", [])]` → cast or use typed attributes.

### Pattern 12: ingest/chunker.py — var-annotated

**Error:** Line 273: `Need type annotation for "current_lines"`.

**Fix:** Add explicit annotation:
```python
current_lines: list[str] = []
```

### Pattern 13: analyzers/shape.py — bare dict return type

**Error:** Line 212: `Missing type parameters for generic type "dict"` in `_generate_recommended_schema`.

**Fix:**
```python
def _generate_recommended_schema(report: ShapeReport) -> dict[str, Any]:
```

### Pattern 14: E501 wrapping in cli.py — Typer Annotated signatures

**What:** 45 lines exceed 100 characters. Nearly all are Typer `Annotated[type, typer.Option(..., help="...")]` parameter declarations.

**Wrapping technique:** Split the `Annotated[...]` across two lines by putting the `typer.Option(...)` call on a new indented line:

```python
# Before (too long):
name: Annotated[str | None, typer.Option("--name", "-n", help="Source name (default: directory basename)")] = None,

# After (wrapped):
name: Annotated[
    str | None,
    typer.Option("--name", "-n", help="Source name (default: directory basename)"),
] = None,
```

For `help=` strings that themselves exceed 100 chars (e.g., line 800: 145 chars), shorten the help text:
```python
# 145-char line — shorten help text:
auto_category: Annotated[
    bool,
    typer.Option("--auto-category", help="Auto-select category by classification confidence"),
] = False,
```

**String literals in console.print:** wrap with implicit string concatenation:
```python
# Before:
console.print(f"[red]Error:[/] Source '{source_name}' or path '{directory}' already exists. Use --force to re-add.")

# After:
console.print(
    f"[red]Error:[/] Source '{source_name}' or path '{directory}' already exists. "
    "Use --force to re-add."
)
```

**B023 fix (line 189):** `progress_callback` captures `task_id` from loop but B023 is already suppressed by `per-file-ignores` for `cli.py`? No — `cli.py` only has B006 suppressed, not B023.

Verify: `ruff check src/corpus_analyzer/cli.py 2>&1 | grep B023` → yes, B023 is present.

**B023 fix:** The standard fix is to capture the variable as a default argument:
```python
def progress_callback(n: int, _task_id: TaskID = task_id) -> None:
    progress.advance(_task_id, n)
```
Or use `functools.partial`. The default-argument capture is idiomatic Python.

**B904 fix (line 294):** Change `raise typer.Exit(code=1)` to `raise typer.Exit(code=1) from None` inside `except RuntimeError as e:`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| sqlite-utils Table type narrowing | Custom type guard | `cast(Table, ...)` from `typing` | One import, zero runtime cost |
| Line wrapping | Manual count | Editor column ruler + ruff --check to verify | ruff is the arbiter |
| Nested function type inference | Refactoring entire module | Promote to module level + annotate | Minimal change, preserves logic |

## Common Pitfalls

### Pitfall 1: cast import source
**What goes wrong:** Importing `Table` from wrong location.
**Why it happens:** sqlite-utils re-exports some things at top level but `Table` as a type is in `sqlite_utils.db`.
**How to avoid:** `from sqlite_utils.db import Table` — verify this import resolves at runtime by checking the installed package.
**Warning signs:** `ModuleNotFoundError` during test run.

Verify:
```bash
python -c "from sqlite_utils.db import Table; print(Table)"
```

### Pitfall 2: DEFAULT_SYSTEM_PROMPT trailing comma
**What goes wrong:** Removing the comma changes runtime type from tuple to str — this is the intended fix, but any code that accidentally relied on tuple behaviour would break.
**Why it happens:** Never relied on tuple — the `+=` call at line 401 would have raised `TypeError` at runtime anyway.
**How to avoid:** After fix, run `uv run pytest -v` to confirm no tests break.

### Pitfall 3: Circular import when adding CorpusDatabase to OllamaClient
**What goes wrong:** `ollama_client.py` imports `CorpusDatabase` which imports from `models.py` etc. — might create a cycle.
**Why it happens:** The import graph is `rewriter.py → ollama_client.py` and `rewriter.py → database.py` — adding `database.py → (via ollama_client.py →) rewriter.py` would be circular, but `database.py` does NOT import from `rewriter.py`, so the cycle does not exist.
**How to avoid:** Use `TYPE_CHECKING` guard anyway as a precaution; the runtime attribute `self.db: CorpusDatabase | None = None` is set at `__init__` time without needing the import.

### Pitfall 4: B006 Typer list defaults
**What goes wrong:** "Fixing" `= ["**/*"]` or `= []` defaults by replacing with `None` breaks `--help` output.
**How to avoid:** These are already suppressed by `pyproject.toml` per-file-ignores for `cli.py`. No action needed.

### Pitfall 5: B023 fix breaks progress callback signature
**What goes wrong:** If `progress_callback` is passed to `index.index_source(..., progress_callback=progress_callback)`, it must match the expected `Callable[[int], None]` signature. Adding `_task_id` with a default arg does NOT change the external callable signature — `n: int` is still the only positional parameter.
**How to avoid:** Default argument capture is safe. Verify the callback type expected by `index_source` first.

### Pitfall 6: extractors/__init__.py — circular import from moving imports outside function
**What goes wrong:** Moving `from corpus_analyzer.extractors.markdown import MarkdownExtractor` outside the function body causes a circular import (extractors `__init__` importing from extractors submodules at module init time).
**How to avoid:** Keep the imports inside the function. Only add a local type annotation to the `extractors` dict variable.

## Code Examples

### cast(Table, ...) pattern
```python
# Source: mypy cast pattern, standard library
from typing import cast
from sqlite_utils.db import Table

# At every Table call site:
cast(Table, self.db["documents"]).update(doc_id, data, alter=True)
cast(Table, self.db["chunks"]).delete_where("document_id = ?", [doc_id])
cast(Table, self.db["documents"]).insert(data, alter=True)
cast(Table, self.db["chunks"]).insert(data)
```

### Promoting nested dataclass
```python
# Module level (before the function that uses it):
@dataclass
class Atom:
    """Atomic block unit used by split_on_headings."""
    lines: list[str]
    heading: str | None
    level: int
    is_code: bool
    start_idx: int

# Inside split_on_headings — remove the nested @dataclass class Atom definition entirely.
```

### Typer Annotated line wrap
```python
# Standard pattern for all Typer option parameters:
verbose: Annotated[
    bool,
    typer.Option("--verbose", "-v", help="Show detailed progress information"),
] = False,
```

### TYPE_CHECKING guard for OllamaClient.db
```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from corpus_analyzer.core.database import CorpusDatabase

class OllamaClient:
    def __init__(self, host: str | None = None, model: str | None = None) -> None:
        """Initialize Ollama client."""
        self.host = host or settings.ollama_host
        self.model = model or settings.ollama_model
        self.client = ollama.Client(host=self.host)
        self.db: CorpusDatabase | None = None
```

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| `self.db["table"].method()` — ignores union | `cast(Table, self.db["table"]).method()` | Mypy-clean, zero runtime cost |
| Nested `@dataclass` class Atom | Module-level `@dataclass class Atom` | Enables typed annotations in caller |
| Missing annotations on `table_obj: Any` | Explicit `table_obj: Any` annotation | Satisfies --strict |

**Deprecated/outdated:**
- `DEFAULT_SYSTEM_PROMPT = """...""",` with trailing comma: runtime bug — fix by removing comma.

## Open Questions

1. **ollama library ChatResponse type**
   - What we know: `response["message"]["content"]` returns `Any` in mypy's view
   - What's unclear: Whether `response.message.content` is a typed `str` attribute in the ollama package's stubs
   - Recommendation: Test `python -c "import ollama; help(ollama.ChatResponse)"` at the start of the MYPY-05 task. If typed, use attribute access. If not, use `cast(str, ...)`.

2. **B023 callback type signature**
   - What we know: `progress_callback` is passed to `index_source(progress_callback=...)`
   - What's unclear: The exact callable type expected by `index_source`
   - Recommendation: Read `ingest/indexer.py` `index_source` signature before implementing the B023 fix to confirm `Callable[[int], None]` is compatible with default-arg capture.

## Sources

### Primary (HIGH confidence)
- Direct inspection of source files + `uv run mypy src/` output — all 41 errors enumerated with file:line
- Direct inspection of `uv run ruff check src/corpus_analyzer/cli.py` output — all 47 errors enumerated

### Secondary (MEDIUM confidence)
- `pyproject.toml` confirms: B006 suppressed for `cli.py`, E501 suppressed for `llm/*.py`, mypy strict mode enabled
- STATE.md confirms: `DEFAULT_SYSTEM_PROMPT` operator error is a genuine bug; `cast(Table, ...)` is the decided pattern; `OllamaClient` must get an optional `db` field

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — tools already installed, exact errors enumerated by running both tools
- Architecture/patterns: HIGH — all patterns verified from actual source code + compiler output
- Pitfalls: HIGH — root causes traced from actual error messages

**Research date:** 2026-02-24
**Valid until:** 2026-03-25 (stable: source files do not change except by this phase's edits)

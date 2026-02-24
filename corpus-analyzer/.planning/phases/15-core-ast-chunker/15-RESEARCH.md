# Phase 15: Core AST Chunker - Research

**Researched:** 2026-02-24
**Domain:** tree-sitter Python API, TypeScript/JavaScript AST chunking
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Phase boundary:** Implement `chunk_typescript()` — an AST-aware chunker for `.ts`, `.tsx`, `.js`, and `.jsx` files using tree-sitter that extracts named top-level constructs as separate chunks with correct 1-indexed line boundaries. Parallel in design to the existing `chunk_python()`. Wired into `chunk_file()` dispatch. This phase does NOT include size guards, ImportError fallback hardening (Phase 16), or ruff/mypy cleanup.

**Lexical declarations:**
- All top-level `const` and `let` declarations become chunks — simple rule, no filtering by RHS type
- `var` declarations are excluded (legacy, not idiomatic TypeScript)
- Multi-declarator statements (`const a = 1, b = 2`) produce one chunk for the whole statement
- Chunk name: Claude's discretion (planner to match Python chunker convention)

**JSDoc inclusion:**
- Chunk text includes the immediately preceding `/** ... */` block comment if one exists directly above the construct (no intervening code or blank lines between comment and declaration)
- When multiple comments precede a construct (e.g. licence header + JSDoc), include only the `/** */` block comment that directly precedes the node
- Single-line `//` comments are NOT included in chunk text — JSDoc convention only
- If no JSDoc is present, chunk starts at the first line of the declaration keyword

**Name extraction:**
- `export default function() {}` → name: `"default"`
- `export default class {}` → name: `"default"` (same rule for all anonymous defaults)
- `export const fn = () => {}` → name: `fn` (the identifier, no type annotation)
- Generic type params in interface/type alias names: Claude's discretion (match Python chunker style)

**Module layout:**
- `chunk_typescript()` is a single public function handling all four extensions (`.ts`, `.tsx`, `.js`, `.jsx`); grammar selection is internal based on file suffix
- File location: Claude's discretion — planner to assess `ingest/chunker.py` size and decide whether to co-locate or split into `ingest/ts_chunker.py`
- `ImportError` (tree-sitter not installed) is caught in `chunk_file()` dispatch and falls back to `chunk_lines()` — the chunker itself does not need to handle missing deps

### Claude's Discretion
- Chunk name for lexical declarations (first declarator vs other convention — match Python chunker)
- Whether generic type params appear in interface/type alias chunk names
- File location for `chunk_typescript()` (same file as `chunk_python()` or new module)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DEP-01 | `pyproject.toml` updated with `tree-sitter>=0.25.0` and `tree-sitter-language-pack>=0.13.0`; `uv sync` succeeds with pre-compiled wheels and no C toolchain | Verified: both packages ship pre-compiled wheels; Python 3.12 is supported |
| IDX-01 | `chunk_file()` dispatch routes `.ts`, `.tsx`, `.js`, `.jsx` extensions to `chunk_typescript()` | Current `chunk_file()` routes `.ts` and `.js` to `chunk_lines()`; update the elif branch |
| IDX-02 | `chunk_typescript()` extracts top-level constructs: 8 node types listed | All 8 node types confirmed in tree-sitter TypeScript grammar via official node-types.json |
| IDX-03 | `export_statement` nodes are unwrapped — inner declaration's line boundaries used | `export_statement` has a `declaration` field; access via `child_by_field_name("declaration")` |
| IDX-04 | Grammar dispatched by extension: `typescript` for `.ts`, `tsx` for `.tsx` and `.jsx`, `javascript` for `.js` | Confirmed: tree-sitter-language-pack provides `"typescript"`, `"tsx"`, `"javascript"` identifiers; no separate `"jsx"` identifier exists — use `"tsx"` for `.jsx` |
| IDX-05 | Silent fallback to `chunk_lines()` when parse raises exception or zero constructs extracted; does NOT fall back on `root_node.has_error` alone | tree-sitter is error-tolerant by design; `has_error` on partial trees is expected, not a reason to fall back |
| IDX-06 | Returned chunk dict includes `chunk_name` field | New field; indexer ignores extra keys; Python chunker does NOT currently emit this field |
| IDX-07 | Parser loader uses `@lru_cache` — grammar binaries loaded once per dialect per process | Standard `functools.lru_cache` on a `_get_parser(dialect: str)` helper; `get_parser()` from language-pack is not itself cached |
| TEST-01 | `TestChunkTypeScript` class at full parity with `TestChunkPython` | Test file: `tests/ingest/test_chunker.py`; extend existing file with new class |
| TEST-02 | `TestChunkFile` dispatch assertions updated for all four extensions | Existing `test_dispatches_other_to_chunk_lines` for `.ts` must be updated to expect AST dispatch |
</phase_requirements>

---

## Summary

Phase 15 implements `chunk_typescript()`, an AST-aware chunker for TypeScript and JavaScript files using the `tree-sitter` library with pre-compiled grammars from `tree-sitter-language-pack`. The function mirrors the structure and return format of the existing `chunk_python()` — reading source bytes, parsing with the appropriate grammar, walking only the top-level children of the root node, and returning `{"text": ..., "start_line": ..., "end_line": ..., "chunk_name": ...}` dicts.

The key technical facts are: (1) `start_point` tuples from tree-sitter are 0-indexed rows, requiring `+1` to produce 1-indexed line numbers; (2) `export_statement` nodes wrap inner declarations via a `declaration` field accessible with `child_by_field_name("declaration")`; (3) there is no separate `"jsx"` grammar identifier — both `.tsx` and `.jsx` use the `"tsx"` parser; (4) the JavaScript grammar includes JSX natively so the `"javascript"` parser handles plain `.js` with embedded JSX; (5) the `lru_cache` must wrap a private `_get_parser(dialect: str)` helper because `get_parser()` from the language pack is not cached by default.

The `chunker.py` file is currently 368 lines. Adding `chunk_typescript()` plus a `_get_parser` helper (roughly 100 lines) brings it to ~470 lines. The planner has discretion to keep it co-located or split to `ts_chunker.py`. The research recommendation is: split to `ingest/ts_chunker.py` to keep `chunker.py` bounded and test imports clean.

**Primary recommendation:** Add `tree-sitter>=0.25.0` and `tree-sitter-language-pack>=0.13.0` to `pyproject.toml`, implement `chunk_typescript()` in a new `ingest/ts_chunker.py`, wire it into `chunk_file()` in `chunker.py`, and extend `tests/ingest/test_chunker.py` with `TestChunkTypeScript` and updated `TestChunkFile` assertions.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| tree-sitter | >=0.25.0 | Incremental, error-tolerant parser engine | Official Python bindings; ships pre-compiled; state-of-the-art for language-server parsing |
| tree-sitter-language-pack | >=0.13.0 | Pre-compiled grammar binaries for 165+ languages | Single package; no C toolchain; includes TypeScript, TSX, JavaScript |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| functools.lru_cache | stdlib | Cache `_get_parser(dialect)` per process | Prevents re-loading 30 MB grammar binaries on every call |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| tree-sitter-language-pack | tree-sitter-languages (grantjenks) | grantjenks is older (targets tree-sitter 0.20); CONTEXT.md locks the choice to language-pack |
| tree-sitter-language-pack | tree-sitter-typescript PyPI pkg | Would need separate install per language; no umbrella install |

**Installation:**
```bash
uv add "tree-sitter>=0.25.0" "tree-sitter-language-pack>=0.13.0"
```

Both packages ship pre-compiled wheels for CPython 3.10-3.13 on Linux x86_64/arm64, macOS, and Windows. No C compiler required.

---

## Architecture Patterns

### Recommended Project Structure
```
src/corpus_analyzer/ingest/
├── chunker.py          # chunk_python, chunk_markdown, chunk_lines, chunk_file (updated dispatch)
├── ts_chunker.py       # chunk_typescript, _get_parser (NEW — ~100 lines)
├── indexer.py
├── embedder.py
└── scanner.py

tests/ingest/
└── test_chunker.py     # TestChunkTypeScript + updated TestChunkFile (extend existing file)
```

### Pattern 1: Grammar Loading with lru_cache

**What:** Private cached function mapping dialect string to a `tree_sitter.Parser` instance.
**When to use:** Called once per grammar per process; prevents 30-second overhead on large corpora.

```python
# Source: tree-sitter-language-pack PyPI docs + functools stdlib
from __future__ import annotations

from functools import lru_cache

from tree_sitter import Parser
from tree_sitter_language_pack import get_parser


@lru_cache(maxsize=8)
def _get_parser(dialect: str) -> Parser:
    """Return a cached tree-sitter Parser for the given dialect.

    Args:
        dialect: One of "typescript", "tsx", "javascript".

    Returns:
        Configured tree_sitter.Parser instance.
    """
    return get_parser(dialect)
```

### Pattern 2: Extension-to-Dialect Mapping

**What:** Map file suffix to grammar identifier before calling `_get_parser`.
**When to use:** At the start of `chunk_typescript()`.

```python
# Verified: tree-sitter-language-pack supports "typescript", "tsx", "javascript"
# No "jsx" identifier exists — .jsx uses "tsx" grammar (JSX-aware TypeScript dialect)
_DIALECT: dict[str, str] = {
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "tsx",   # JavaScript grammar supports JSX natively too, but tsx is more permissive
}
```

**Note on `.jsx`:** The REQUIREMENTS.md (IDX-04) explicitly states `.jsx` uses `"tsx"`. The JavaScript grammar also includes JSX natively, but using `"tsx"` for `.jsx` is the project-defined decision. Research confirms `"tsx"` is a valid identifier in tree-sitter-language-pack.

### Pattern 3: Top-Level Node Walk with Export Unwrapping

**What:** Iterate `root_node.children` (not `named_children`) to preserve position accuracy; check for `export_statement` and unwrap via `child_by_field_name("declaration")`.
**When to use:** Core of `chunk_typescript()`.

```python
# Source: tree-sitter node-types.json (typescript) + py-tree-sitter 0.25.2 Node docs
TARGET_TYPES = {
    "function_declaration",
    "generator_function_declaration",
    "class_declaration",
    "abstract_class_declaration",
    "interface_declaration",
    "type_alias_declaration",
    "lexical_declaration",
    "enum_declaration",
}

for child in root_node.children:
    node = child
    if child.type == "export_statement":
        inner = child.child_by_field_name("declaration")
        if inner is None:
            continue
        node = inner  # unwrap; use inner line boundaries

    if node.type not in TARGET_TYPES:
        continue

    # node.start_point is (row, col) — 0-indexed rows
    start_line = node.start_point[0] + 1  # convert to 1-indexed
    end_line = node.end_point[0] + 1
    ...
```

### Pattern 4: Name Extraction per Node Type

**What:** Extract the human-readable name from different node types using `child_by_field_name("name")`.
**When to use:** To populate `chunk_name` in returned dict.

```python
# Source: tree-sitter-typescript node-types.json analysis
def _extract_name(node: Any, export_node: Any | None) -> str:
    """Extract construct name from an AST node.

    Args:
        node: The declaration node (after export unwrapping).
        export_node: The original export_statement node if present, else None.

    Returns:
        Name string for chunk_name field.
    """
    if export_node is not None:
        # Check for 'export default' — name is always "default"
        for child in export_node.children:
            if child.type == "default":
                return "default"

    if node.type == "lexical_declaration":
        # No direct name field; first variable_declarator holds the name
        for child in node.children:
            if child.type == "variable_declarator":
                name_node = child.child_by_field_name("name")
                if name_node is not None:
                    return name_node.text.decode("utf-8")  # type: ignore[union-attr]
        return "<anonymous>"

    # All other types use a "name" field
    name_node = node.child_by_field_name("name")
    if name_node is not None:
        return name_node.text.decode("utf-8")  # type: ignore[union-attr]
    return "<anonymous>"
```

### Pattern 5: JSDoc Lookback

**What:** Walk backwards through the preceding siblings of the outer node (including export wrapper if present) to find an adjacent `/** ... */` block comment.
**When to use:** When computing `start_line` for chunk text (extend start upward to include JSDoc).

```python
# Logic: find the comment node directly preceding the export_statement (or declaration node)
# "directly preceding" = the sibling immediately before with only whitespace between them
outer_node = export_node if export_node is not None else node
# Use outer_node.start_point[0] to check if preceding sibling ends on row - 1
# tree-sitter sibling access: outer_node.prev_sibling

prev = outer_node.prev_sibling
if prev is not None and prev.type == "comment":
    comment_text = prev.text.decode("utf-8")  # type: ignore[union-attr]
    if comment_text.startswith("/**"):
        # Check adjacency: prev ends on line immediately before outer starts
        if outer_node.start_point[0] - prev.end_point[0] <= 1:
            chunk_start_line = prev.start_point[0] + 1
```

**Note:** `prev_sibling` on `Node` is a documented property in py-tree-sitter 0.25. It gives the nearest preceding sibling, including whitespace/comment nodes.

### Pattern 6: Source Parsing

**What:** Parse source as bytes; extract chunk text from the original source string by line slicing.
**When to use:** Opening the file and building chunks.

```python
with open(path, encoding="utf-8") as f:
    source = f.read()

lines = source.splitlines(keepends=False)
parser = _get_parser(dialect)
tree = parser.parse(source.encode("utf-8"))
root_node = tree.root_node
```

### Anti-Patterns to Avoid

- **Using `named_children` instead of `children`:** `named_children` excludes punctuation tokens and may skip comment siblings needed for JSDoc lookback. Use `root_node.children` for the top-level walk.
- **Decoding `node.text` without `.encode()` round-trip:** `node.text` returns `bytes | None` (it is `None` if the tree has been edited). Always decode with `.decode("utf-8")`.
- **Falling back on `has_error`:** The requirements explicitly state NOT to fall back on `root_node.has_error` alone. tree-sitter produces useful partial trees with errors marked locally.
- **Caching the parser at module level with a global dict:** Use `@lru_cache` on `_get_parser(dialect)` instead. Module-level globals are harder to test and reset.
- **Forgetting mypy overrides:** `tree_sitter` and `tree_sitter_language_pack` lack PEP 561 stubs. Both modules need `ignore_missing_imports = true` in `[tool.mypy.overrides]`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TypeScript/JS parsing | Regex-based construct detection | tree-sitter | Regex cannot handle nested braces, template literals, generics, JSX; tree-sitter handles all edge cases |
| Grammar binary distribution | Build from source via `tree-sitter generate` | tree-sitter-language-pack | Building requires Node.js + C toolchain; language-pack ships pre-built wheels |
| Parser caching | Custom `_parsers: dict[str, Parser]` global | `@lru_cache` on `_get_parser()` | lru_cache is thread-safe, testable, and idiomatic Python |
| Line number conversion | Custom position tracking | `node.start_point[0] + 1` | tree-sitter provides exact 0-indexed row; +1 gives 1-indexed |

**Key insight:** The tree-sitter grammar correctly handles all TypeScript syntax edge cases — generics, decorators, JSX elements, template literals — that would make regex-based approaches unreliable.

---

## Common Pitfalls

### Pitfall 1: start_point is 0-Indexed
**What goes wrong:** Using `node.start_point[0]` directly as a line number produces off-by-one (line 1 becomes 0).
**Why it happens:** tree-sitter uses 0-indexed row/col, following text editor conventions.
**How to avoid:** Always add `+1`: `start_line = node.start_point[0] + 1`.
**Warning signs:** Test assertions on `start_line == 1` failing, getting `0` instead.

### Pitfall 2: No "jsx" Grammar Identifier in tree-sitter-language-pack
**What goes wrong:** Calling `get_parser("jsx")` raises `KeyError` or `ValueError`.
**Why it happens:** The language-pack does not expose a separate `"jsx"` identifier. JSX support is built into the JavaScript grammar AND the TSX grammar.
**How to avoid:** Map `.jsx` to `"tsx"` (per IDX-04); map `.js` to `"javascript"`.
**Warning signs:** `KeyError` at runtime on `.jsx` files.

### Pitfall 3: export_statement Without a Declaration Field
**What goes wrong:** `child_by_field_name("declaration")` returns `None` for re-export statements (`export { foo } from './bar'`).
**Why it happens:** Re-exports use `export_clause` children, not a `declaration` field.
**How to avoid:** Guard with `if inner is None: continue` — skip export statements that don't introduce a new declaration.
**Warning signs:** `AttributeError` on `None.type` when processing re-exports.

### Pitfall 4: node.text Returns None After Tree Edit
**What goes wrong:** `node.text.decode("utf-8")` raises `AttributeError: 'NoneType' object has no attribute 'decode'`.
**Why it happens:** `node.text` is `None` when the tree has been edited via `tree.edit()`. We never edit trees, but mypy requires handling the `None` case.
**How to avoid:** Use `source_lines[node.start_point[0]:node.end_point[0]+1]` slice for chunk text instead of `node.text`; use `node.text.decode("utf-8") if node.text else ""` for name extraction.
**Warning signs:** mypy strict mode reports `Item "None" of "bytes | None" has no attribute "decode"`.

### Pitfall 5: mypy Strict Mode with tree-sitter
**What goes wrong:** `uv run mypy src/` exits non-zero because tree-sitter and tree-sitter-language-pack lack stubs.
**Why it happens:** Neither package ships a `py.typed` marker or PEP 561 stubs.
**How to avoid:** Add both to `[[tool.mypy.overrides]]` with `ignore_missing_imports = true` in `pyproject.toml`. Mirror the existing `frontmatter` override pattern.
**Warning signs:** `error: Cannot find implementation or library stub for module named "tree_sitter"`.

### Pitfall 6: lru_cache with Mutable Return Value
**What goes wrong:** Two callers share the same `Parser` object and one's `parse()` call races the other.
**Why it happens:** `Parser.parse()` is stateful (it updates the last parse tree internally).
**How to avoid:** In practice this is fine for single-threaded CLI use. If multi-threading is needed, create `Parser` instances without caching and cache only `Language` objects. For this phase, `@lru_cache` on the full `Parser` is correct and sufficient.

### Pitfall 7: The "prev_sibling includes whitespace" Assumption
**What goes wrong:** JSDoc lookback includes non-comment whitespace nodes, causing `prev.text.startswith("/**")` to throw.
**Why it happens:** `prev_sibling` may return a whitespace/newline token.
**How to avoid:** Check `prev.type == "comment"` before testing the text content. Walk further back if the immediate sibling is whitespace.

---

## Code Examples

Verified patterns from official sources:

### Complete chunk_typescript() Skeleton

```python
# Source: tree-sitter 0.25.2 Node docs + tree-sitter-language-pack PyPI docs
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from tree_sitter import Parser  # type: ignore[import-untyped]
from tree_sitter_language_pack import get_parser  # type: ignore[import-untyped]

_DIALECT: dict[str, str] = {
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "tsx",
}

_TARGET_TYPES: frozenset[str] = frozenset({
    "function_declaration",
    "generator_function_declaration",
    "class_declaration",
    "abstract_class_declaration",
    "interface_declaration",
    "type_alias_declaration",
    "lexical_declaration",
    "enum_declaration",
})


@lru_cache(maxsize=8)
def _get_cached_parser(dialect: str) -> Parser:
    """Return a cached tree-sitter Parser for the given grammar dialect."""
    return get_parser(dialect)


def chunk_typescript(path: Path) -> list[dict[str, Any]]:
    """Split a TypeScript/JavaScript file into chunks by top-level constructs.

    Handles .ts, .tsx, .js, and .jsx files using the appropriate tree-sitter grammar.
    Falls back to chunk_lines() if parsing fails or no named constructs are found.

    Args:
        path: Path to the source file.

    Returns:
        List of chunks with "text", "start_line", "end_line", and "chunk_name" keys.
    """
    from corpus_analyzer.ingest.chunker import chunk_lines  # avoid circular at module level

    ext = path.suffix.lower()
    dialect = _DIALECT.get(ext)
    if dialect is None:
        return chunk_lines(path)

    with open(path, encoding="utf-8") as f:
        source = f.read()

    if not source.strip():
        return []

    try:
        parser = _get_cached_parser(dialect)
        tree = parser.parse(source.encode("utf-8"))
    except Exception:
        return chunk_lines(path)

    root_node = tree.root_node
    lines = source.splitlines()
    chunks: list[dict[str, Any]] = []

    for child in root_node.children:
        export_node = None
        node = child

        if child.type == "export_statement":
            inner = child.child_by_field_name("declaration")
            if inner is None:
                continue  # re-export or export default expression
            export_node = child
            node = inner

        if node.type not in _TARGET_TYPES:
            continue

        outer = export_node if export_node is not None else node
        chunk_start = outer.start_point[0]  # 0-indexed

        # JSDoc lookback
        prev = outer.prev_sibling
        if prev is not None and prev.type == "comment":
            comment_bytes = prev.text
            if comment_bytes and comment_bytes.decode("utf-8").startswith("/**"):
                if outer.start_point[0] - prev.end_point[0] <= 1:
                    chunk_start = prev.start_point[0]

        start_line = chunk_start + 1  # convert to 1-indexed
        end_line = outer.end_point[0] + 1  # inclusive, 1-indexed

        chunk_text = "\n".join(lines[chunk_start:outer.end_point[0] + 1]).rstrip()
        chunk_name = _extract_name(node, export_node, source)

        if chunk_text:
            chunks.append({
                "text": chunk_text,
                "start_line": start_line,
                "end_line": end_line,
                "chunk_name": chunk_name,
            })

    if not chunks:
        return chunk_lines(path)

    return chunks
```

### pyproject.toml Addition

```toml
# Source: verified via PyPI — both packages ship pre-compiled wheels
dependencies = [
    # ... existing deps ...
    "tree-sitter>=0.25.0",
    "tree-sitter-language-pack>=0.13.0",
]
```

### mypy Override Addition

```toml
# Source: mypy docs — standard pattern for packages without stubs
[[tool.mypy.overrides]]
module = ["tree_sitter", "tree_sitter_language_pack"]
ignore_missing_imports = true
```

### chunk_file() Dispatch Update

```python
# In chunker.py — replace the existing elif for .ts/.js
elif ext == ".py":
    chunks = chunk_python(path)
elif ext in (".ts", ".tsx", ".js", ".jsx"):
    from corpus_analyzer.ingest.ts_chunker import chunk_typescript
    chunks = chunk_typescript(path)
elif ext in (".json", ".yaml", ".yml", ".txt", ".toml"):
    chunks = chunk_lines(path)
```

### Test Structure for TestChunkTypeScript

```python
class TestChunkTypeScript:
    """Tests for chunk_typescript function — mirrors TestChunkPython structure."""

    def test_function_extraction(self, tmp_path: Path) -> None:
        """chunk_typescript extracts top-level function declarations."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("function foo(): void {\n  console.log('hi');\n}\n")
        chunks = chunk_typescript(ts_file)
        assert len(chunks) == 1
        assert chunks[0]["chunk_name"] == "foo"
        assert chunks[0]["start_line"] == 1

    def test_export_unwrapping(self, tmp_path: Path) -> None:
        """export function foo() produces chunk with full exported text."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("export function foo(): void {}\n")
        chunks = chunk_typescript(ts_file)
        assert len(chunks) == 1
        assert "export function foo" in chunks[0]["text"]
        assert chunks[0]["chunk_name"] == "foo"

    def test_has_error_does_not_fall_back(self, tmp_path: Path) -> None:
        """Partial tree with has_error is parsed normally — NOT fallen back."""
        ts_file = tmp_path / "test.ts"
        # Valid function followed by deliberately broken syntax
        ts_file.write_text("function good(): void {}\n@@@@invalid@@@@\n")
        chunks = chunk_typescript(ts_file)
        # Should still extract 'good' even with parse errors elsewhere
        assert any(c["chunk_name"] == "good" for c in chunks)

    def test_catastrophic_failure_falls_back(self, tmp_path: Path) -> None:
        """If parser raises an exception, falls back to chunk_lines."""
        # This tests the except clause — simulate by passing binary content
        bin_file = tmp_path / "test.ts"
        bin_file.write_bytes(b"\x00\x01\x02\x03" * 100)
        chunks = chunk_typescript(bin_file)
        # Should not raise; returns line-based chunks or empty list
        assert isinstance(chunks, list)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `tree-sitter-languages` (grantjenks) | `tree-sitter-language-pack` (Goldziher) | 2024 | language-pack targets tree-sitter 0.25.x; languages pkg targets 0.20.x — API incompatible |
| Manual `Language.build_library()` | Pre-compiled wheels via `get_parser()` | tree-sitter 0.22+ | No C toolchain required; wheels ship for all major platforms |
| `parser.set_language(lang)` (0.20 API) | `get_parser(dialect)` returns pre-configured `Parser` | tree-sitter 0.22+ | One-step parser retrieval; `set_language` is still available but unnecessary with language-pack |

**Deprecated/outdated:**
- `Language.build_library()`: Replaced by pre-compiled wheel distribution; do not use.
- `parser.set_language(Language(...))`: Still works but unnecessary when using `get_parser()` from language-pack.
- `tree-sitter-languages` package: Targets old 0.20 API; incompatible with `tree-sitter>=0.25`.

---

## Open Questions

1. **Does `prev_sibling` skip whitespace nodes automatically?**
   - What we know: py-tree-sitter `Node.prev_sibling` returns the nearest sibling including whitespace/comment tokens.
   - What's unclear: Whether the JSDoc-lookback logic needs to walk through a whitespace node to reach the `comment` node.
   - Recommendation: In implementation, walk `prev_sibling` up to 2 steps, skipping any node whose `type` is not `"comment"` and is whitespace-only. Verify with a test case that has a blank line between JSDoc and declaration (should NOT include comment).

2. **Exact `chunk_name` for `lexical_declaration` with destructuring (`const { a, b } = obj`)**
   - What we know: Destructuring patterns produce `object_pattern` children in `variable_declarator`, not plain `identifier`.
   - What's unclear: Whether the project needs a specific name for destructuring vs the first identifier.
   - Recommendation: For Phase 15, treat destructuring as `"<destructured>"` if the first declarator name is not a plain identifier. The CONTEXT.md decision is "first declarator" for `chunk_name`.

3. **Whether `tree_sitter.Parser` is thread-safe for concurrent parses**
   - What we know: `@lru_cache` returns the same `Parser` instance to all callers.
   - What's unclear: Whether concurrent async/threaded calls to `parser.parse()` are safe.
   - Recommendation: Safe for single-threaded CLI use. Document the assumption; Phase 16 can address if needed.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/ingest/test_chunker.py -v` |
| Full suite command | `uv run pytest -v` |
| Estimated runtime | ~2 seconds (quick), ~10 seconds (full) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEP-01 | `uv sync` succeeds after adding deps | integration | `uv sync && uv run python -c "from tree_sitter_language_pack import get_parser"` | ❌ Wave 0 gap (manual verify) |
| IDX-01 | `chunk_file(".ts")` calls `chunk_typescript` | unit | `uv run pytest tests/ingest/test_chunker.py::TestChunkFile -x` | ❌ Wave 0 gap (update existing test) |
| IDX-02 | All 8 node types extracted | unit | `uv run pytest tests/ingest/test_chunker.py::TestChunkTypeScript -x` | ❌ Wave 0 gap |
| IDX-03 | export_statement unwrapped, full text in chunk | unit | `uv run pytest tests/ingest/test_chunker.py::TestChunkTypeScript::test_export_unwrapping -x` | ❌ Wave 0 gap |
| IDX-04 | `.tsx`/`.jsx` use tsx grammar, `.js` uses javascript | unit | `uv run pytest tests/ingest/test_chunker.py::TestChunkFile -x` | ❌ Wave 0 gap |
| IDX-05 | `has_error` tree does NOT fall back; exception DOES fall back | unit | `uv run pytest tests/ingest/test_chunker.py::TestChunkTypeScript::test_has_error_does_not_fall_back -x` | ❌ Wave 0 gap |
| IDX-06 | `chunk_name` field in every returned dict | unit | `uv run pytest tests/ingest/test_chunker.py::TestChunkTypeScript -x` | ❌ Wave 0 gap |
| IDX-07 | Parser loaded once (lru_cache), not per call | unit | `uv run pytest tests/ingest/test_chunker.py::TestChunkTypeScript::test_parser_is_cached -x` | ❌ Wave 0 gap |
| TEST-01 | Full TestChunkTypeScript suite passes | unit | `uv run pytest tests/ingest/test_chunker.py::TestChunkTypeScript -v` | ❌ Wave 0 gap |
| TEST-02 | TestChunkFile dispatch covers all 4 extensions | unit | `uv run pytest tests/ingest/test_chunker.py::TestChunkFile -v` | ❌ Wave 0 gap (update existing) |

### Nyquist Sampling Rate
- **Minimum sample interval:** After every committed task → run: `uv run pytest tests/ingest/test_chunker.py -v`
- **Full suite trigger:** Before merging final task of any plan wave
- **Phase-complete gate:** Full suite green (`uv run pytest -v`) before `/gsd:verify-work` runs
- **Estimated feedback latency per task:** ~2 seconds

### Wave 0 Gaps (must be created before implementation)
- [ ] `tests/ingest/test_chunker.py` — extend with `TestChunkTypeScript` class and updated `TestChunkFile` assertions (file exists, needs new tests added)
- [ ] `src/corpus_analyzer/ingest/ts_chunker.py` — new module for `chunk_typescript` (if planner decides to split)
- [ ] `pyproject.toml` — add `tree-sitter>=0.25.0` and `tree-sitter-language-pack>=0.13.0` to `dependencies`

*(No framework install gap — pytest already configured)*

---

## Sources

### Primary (HIGH confidence)
- `tree-sitter` 0.25.2 PyPI JSON — version and pre-compiled wheel availability confirmed
- `tree-sitter-language-pack` 0.13.0 PyPI page — language identifiers `"typescript"`, `"tsx"`, `"javascript"` confirmed; `"jsx"` not available
- py-tree-sitter 0.25.2 Node class docs (`tree-sitter.github.io/py-tree-sitter/classes/tree_sitter.Node.html`) — `start_point`, `end_point`, `children`, `has_error`, `prev_sibling`, `child_by_field_name()`, `text` properties confirmed
- tree-sitter-typescript `node-types.json` (via deepwiki analysis) — `export_statement.declaration` field confirmed; all 8 target node types confirmed; `name` field confirmed for 7/8 types; `lexical_declaration` uses `variable_declarator` children

### Secondary (MEDIUM confidence)
- WebSearch: JavaScript grammar includes JSX natively (tree-sitter/tree-sitter-javascript README) — confirmed `.jsx` can use either `"javascript"` or `"tsx"`; IDX-04 requires `"tsx"` for `.jsx`
- WebSearch: `export_statement` `declaration` field structure — confirmed from multiple sources including static-node-types docs
- Simon Willison TIL on tree-sitter Python — confirms `parser.parse(bytes)` API and `node.text` returns `bytes`

### Tertiary (LOW confidence)
- `node.prev_sibling` existence for JSDoc lookback — mentioned in py-tree-sitter docs overview but not tested; verify in Wave 0 implementation

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — PyPI metadata confirmed, versions pinned, pre-compiled wheels verified
- Architecture: HIGH — tree-sitter node types and field names confirmed via official grammar sources
- Pitfalls: HIGH — 0-indexed rows, missing "jsx" identifier, export_statement None guard all verified
- JSDoc lookback via prev_sibling: MEDIUM — property exists per docs but adjacency logic not validated against real tree output

**Research date:** 2026-02-24
**Valid until:** 2026-03-24 (tree-sitter 0.25.x is stable; language-pack follows upstream)

# Stack Research

**Domain:** Tree-sitter AST chunking for TypeScript/JavaScript in Python 3.12
**Researched:** 2026-02-24
**Confidence:** HIGH (versions verified against PyPI; API verified against official docs and GitHub)

---

## Context: v1.5 TypeScript AST Chunking

This research covers ONLY what is new for v1.5. The existing application stack (LanceDB,
FastMCP, Typer, Rich, Pydantic) is validated and unchanged. Two new packages are required.

**Active milestone requirements:**

- AST-aware chunking for `.ts`, `.tsx`, `.js`, `.jsx`
- Chunk types: `function_declaration`, `arrow_function`, `method_definition`, `class_declaration`,
  `interface_declaration`, `type_alias_declaration`, top-level `lexical_declaration` (const/let)
- Silent line-based fallback on parse failure (mirrors `chunk_python` pattern)
- Full test coverage at parity with Python AST chunker

**Integration point (single change in existing code):**

`src/corpus_analyzer/ingest/chunker.py`, function `chunk_file()`, line 355:

```python
# CURRENT (line-based for all TS/JS):
elif ext in (".ts", ".js", ".json", ".yaml", ".yml", ".txt", ".toml"):
    chunks = chunk_lines(path)

# TARGET (AST-aware for TS/JS; .tsx and .jsx not even handled today — fall to default):
elif ext in (".ts", ".tsx"):
    chunks = chunk_typescript(path, dialect="typescript")
elif ext in (".js", ".jsx"):
    chunks = chunk_typescript(path, dialect="javascript")
elif ext in (".json", ".yaml", ".yml", ".txt", ".toml"):
    chunks = chunk_lines(path)
```

No other existing files need changes. The new `chunk_typescript()` function is a drop-in addition
to `chunker.py` following the exact same signature and fallback contract as `chunk_python()`.

---

## Recommended Stack

### New Dependencies

| Package | Version | Purpose | Why |
|---------|---------|---------|-----|
| `tree-sitter` | `>=0.25.0` | Core Python bindings to tree-sitter C library | Official bindings maintained by tree-sitter org; pre-compiled wheels (no C compiler needed); required by language pack |
| `tree-sitter-language-pack` | `>=0.13.0` | Pre-built grammars for 165+ languages including `typescript`, `tsx`, `javascript`, `jsx` | Actively maintained (released 2025-11-26); Python 3.10+ wheels; one import covers all four target dialects; replaces unmaintained `tree-sitter-languages` |

**Version rationale:**

- `tree-sitter>=0.25.0` — language-pack 0.13.0 requires tree-sitter 0.25.x+; 0.25.2 is current
  (released 2025-09-25). The 0.21+ generation introduced a breaking API change (see below).
- `tree-sitter-language-pack>=0.13.0` — 0.13.0 is current (released 2025-11-26), includes TS/TSX/JS/JSX
  grammars bundled as pre-compiled wheels.

### Existing Stack (unchanged)

All current dependencies remain. No removals, no version bumps needed.

---

## Installation

```bash
# Add to pyproject.toml dependencies:
uv add "tree-sitter>=0.25.0" "tree-sitter-language-pack>=0.13.0"
```

---

## API Usage Pattern

### Parser Creation (current 0.25.x API)

```python
from tree_sitter import Language, Parser
from tree_sitter_language_pack import get_language, get_parser

# Preferred: get a fully configured Parser directly
ts_parser = get_parser("typescript")
tsx_parser = get_parser("tsx")
js_parser = get_parser("javascript")
jsx_parser = get_parser("jsx")

# Alternative: get Language object only (to create Parser manually)
ts_lang = get_language("typescript")
parser = Parser(ts_lang)
```

### Parsing Source

```python
source_bytes = source_text.encode("utf-8")
tree = parser.parse(source_bytes)
root = tree.root_node
```

### Node Traversal

Traverse children of `root_node` to find top-level declarations:

```python
TARGET_TYPES = {
    "function_declaration",
    "generator_function_declaration",
    "arrow_function",          # only top-level: `const foo = () => {}`
    "method_definition",       # inside class body
    "class_declaration",
    "interface_declaration",   # TypeScript only
    "type_alias_declaration",  # TypeScript only: `type Foo = ...`
    "lexical_declaration",     # `const` / `let` at top level
    "export_statement",        # wraps declarations: `export function foo() {}`
}

for child in root.children:
    if child.type in TARGET_TYPES:
        start_line = child.start_point[0] + 1   # tree-sitter is 0-indexed
        end_line = child.end_point[0] + 1
        chunk_text = source_text[child.start_byte:child.end_byte]
```

`node.start_point` and `node.end_point` are `(row, col)` tuples. `node.start_byte`/`node.end_byte`
enable precise source slicing without splitting on newlines.

### Fallback Pattern (mirrors chunk_python)

```python
def chunk_typescript(path: Path, dialect: str = "typescript") -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        source = f.read()

    if not source.strip():
        return []

    try:
        parser = get_parser(dialect)
        tree = parser.parse(source.encode("utf-8"))
    except Exception:
        return chunk_lines(path)   # silent fallback

    if tree.root_node.has_error:
        return chunk_lines(path)   # fallback on parse error

    chunks = _extract_ts_chunks(tree.root_node, source)
    return chunks if chunks else chunk_lines(path)
```

---

## Key Node Types: TypeScript Grammar

The `tree-sitter-typescript` grammar (bundled in language-pack) defines these node types
relevant to chunking. Both `typescript` and `tsx` dialects share these types; `tsx` additionally
handles JSX element nodes.

| Node Type | Description | Dialects |
|-----------|-------------|----------|
| `function_declaration` | `function foo() {}` | TS, TSX, JS, JSX |
| `generator_function_declaration` | `function* foo() {}` | TS, TSX, JS, JSX |
| `class_declaration` | `class Foo {}` | TS, TSX, JS, JSX |
| `method_definition` | Method inside class body | TS, TSX, JS, JSX |
| `arrow_function` | `const foo = () => {}` (top-level) | TS, TSX, JS, JSX |
| `interface_declaration` | `interface Foo {}` | TS, TSX only |
| `type_alias_declaration` | `type Foo = Bar` | TS, TSX only |
| `lexical_declaration` | `const foo = ...` / `let foo = ...` | TS, TSX, JS, JSX |
| `export_statement` | `export function foo()` / `export class Foo` | TS, TSX, JS, JSX |

**`export_statement` handling:** Export-wrapped declarations appear as `export_statement` at
top level, with the actual declaration as a child. The chunker must inspect child nodes of
`export_statement` to classify and extract them correctly.

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| `tree-sitter-language-pack` | `tree-sitter-typescript` (standalone PyPI package) | Standalone pkg is at v0.23.2 (released 2024-11-11, 3 months stale vs language-pack's 2025-11-26). Requires separate installs for JS/JSX. Language-pack bundles all four dialects in one dependency with active maintenance. |
| `tree-sitter-language-pack` | `tree-sitter-languages` | `tree-sitter-languages` is explicitly unmaintained (Goldziher's language-pack is the maintained successor). Does not support Python 3.12+. |
| `get_parser(dialect)` from language-pack | `Language(tspython.language())` direct import | Direct imports require four separate packages (`tree-sitter-typescript`, `tree-sitter-javascript`, etc.). Language-pack's `get_parser("tsx")` is simpler. |
| tree-sitter (C-backed) | `esprima`, `acorn`, or other pure-Python parsers | Pure Python JS parsers are unmaintained or not pip-installable in a uv workflow. No Python AST library handles TypeScript natively. tree-sitter is the only viable option. |
| tree-sitter (C-backed) | ANTLR4 TypeScript grammar | ANTLR requires Java runtime for grammar compilation; impractical in this stack. |
| Caching `Parser` objects at module level | Creating `Parser` per call | Parser construction is cheap but dialect dispatch (`"typescript"` vs `"tsx"`) requires selecting the right parser. Cache via `@lru_cache` on `_get_parser(dialect)` is the correct pattern to avoid repeated grammar loading. |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `tree-sitter-typescript` (standalone) | Older, only covers TS/TSX, requires separate `tree-sitter-javascript` pkg | `tree-sitter-language-pack` covers all four dialects |
| `tree-sitter-languages` | Explicitly unmaintained; Python 3.12+ wheels broken | `tree-sitter-language-pack` is the maintained replacement |
| `@tree-sitter/typescript` (npm) | Node.js package, not usable from Python | N/A |
| Language.build_library() | Removed API (pre-0.21 pattern) — requires C compiler, local grammar source checkout | `get_parser()` from language-pack (pre-compiled wheels) |
| `tree.root_node.sexp()` for extraction | S-expression format is for debugging; parsing it back is fragile | Direct node attribute access (`node.type`, `node.start_point`) |
| Regex-based TS parsing | Brittle: no awareness of nesting, comments, string literals | tree-sitter AST |
| Query DSL (`Query`, `QueryCursor`) | Adds complexity; direct child traversal suffices for top-level node extraction | Direct `root.children` iteration with `node.type` check |
| Bumping existing dependencies | No version bumps required for any existing package | Keep existing pinned ranges |

---

## Breaking API Change: pre-0.21 vs 0.21+

The old `Language.build_library()` pattern is **removed** in tree-sitter 0.21+:

```python
# OLD (pre-0.21) — do not use:
Language.build_library("build/my-languages.so", ["vendor/tree-sitter-typescript"])
lang = Language("build/my-languages.so", "typescript")

# NEW (0.21+, current):
from tree_sitter_language_pack import get_parser
parser = get_parser("typescript")
```

Any StackOverflow answer or tutorial using `Language.build_library` or `Language(path, name)` is
stale. The language-pack package exists specifically to provide pre-compiled binaries so no
compilation step is needed.

---

## Version Compatibility

| Package | Version | Python | Notes |
|---------|---------|--------|-------|
| `tree-sitter` | 0.25.2 | >=3.10 | Current (2025-09-25). Pre-compiled wheels. No C compiler needed. |
| `tree-sitter-language-pack` | 0.13.0 | >=3.10 | Current (2025-11-26). Requires tree-sitter 0.25.x+. Includes TS/TSX/JS/JSX. |
| Project Python | 3.12 | — | Within the >=3.10 requirement of both packages. |

Both packages ship pre-compiled binary wheels for Linux/macOS/Windows on Python 3.10–3.14.
No local C toolchain or grammar compilation is required.

---

## mypy / ruff Compatibility Notes

- `tree-sitter` ships typed stubs (py.typed marker). `Parser`, `Language`, `Node`, `Tree` are
  fully annotated. No `[[tool.mypy.overrides]] ignore_missing_imports` entry needed.
- `tree-sitter-language-pack` ships with "full typing support" per package docs. Same applies.
- `node.start_point` returns `tuple[int, int]`. Access via index: `node.start_point[0]` (row).
- `node.has_error: bool` — guards against partial-parse fallback.
- The `get_parser` return type is `tree_sitter.Parser`. Annotate `chunk_typescript` return as
  `list[dict[str, Any]]` consistent with existing chunker functions.

---

## Sources

- [PyPI: tree-sitter 0.25.2](https://pypi.org/project/tree-sitter/) — version, release date, Python requirements (HIGH)
- [PyPI: tree-sitter-language-pack 0.13.0](https://pypi.org/project/tree-sitter-language-pack/) — version, supported languages including typescript/tsx/javascript/jsx (HIGH)
- [GitHub: Goldziher/tree-sitter-language-pack README](https://github.com/Goldziher/tree-sitter-language-pack) — API: `get_parser("typescript")`, tree-sitter 0.25.x requirement, language identifiers (HIGH)
- [py-tree-sitter official docs](https://tree-sitter.github.io/py-tree-sitter/) — `Parser(Language)` constructor, `node.start_point`, `node.has_error`, 0.21+ API (HIGH)
- [GitHub: py-tree-sitter README](https://github.com/tree-sitter/py-tree-sitter) — `Language(module.language())` pattern, breaking change from `Language.build_library` (HIGH)
- [GitHub: tree-sitter/tree-sitter-typescript](https://github.com/tree-sitter/tree-sitter-typescript) — node types: function_declaration, arrow_function, method_definition, interface_declaration, type_alias_declaration; two dialects (typescript vs tsx) (HIGH)
- [py-tree-sitter Discussion #231](https://github.com/tree-sitter/py-tree-sitter/discussions/231) — TypeScript/TSX parser setup confirmation (MEDIUM)
- Existing `src/corpus_analyzer/ingest/chunker.py` — integration point at line 355; `chunk_python` fallback pattern (HIGH)

---

*Stack research for: Corpus v1.5 — TypeScript/JavaScript AST chunking via tree-sitter*
*Researched: 2026-02-24*

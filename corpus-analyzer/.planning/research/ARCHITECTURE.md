# Architecture Research

**Domain:** tree-sitter TS/JS AST chunker integration into corpus-analyzer
**Researched:** 2026-02-24
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
  corpus index (CLI)
        |
        v
  CorpusIndex.index_source()          [ingest/indexer.py — UNCHANGED]
        |
        v
  chunk_file(path)                    [ingest/chunker.py — ONE LINE CHANGE]
        |
   dispatch on ext
        |
   .ts/.tsx/.js/.jsx  ──────────>  chunk_typescript(path)   [NEW FUNCTION]
        |                                    |
        |                           tree-sitter parse
        |                                    |
        |                           parse error? ─yes─> chunk_lines(path)
        |                                    |
        |                           walk root_node.children (depth 1 only)
        |                                    |
        |                           filter by _TS_CHUNK_NODE_TYPES
        |                                    |
        |                           yield construct chunks
        v
  _enforce_char_limit()               [ingest/chunker.py — UNCHANGED]
        |
        v
  embed + upsert to LanceDB           [ingest/indexer.py — UNCHANGED]
```

### Component Responsibilities

| Component | Responsibility | Status |
|-----------|----------------|--------|
| `ingest/chunker.py :: chunk_file()` | Dispatch to correct chunker by extension | MODIFY (dispatch table only) |
| `ingest/chunker.py :: chunk_typescript()` | AST-aware chunking for .ts/.tsx/.js/.jsx | NEW |
| `ingest/chunker.py :: _get_ts_language()` | Lazy-load and cache tree-sitter Language objects | NEW |
| `ingest/chunker.py :: _TS_CHUNK_NODE_TYPES` | Frozenset of node types that constitute chunk boundaries | NEW |
| `ingest/chunker.py :: chunk_lines()` | Line-based fallback (window/overlap) | UNCHANGED |
| `ingest/indexer.py :: CorpusIndex.index_source()` | Walk source, call chunk_file, embed, upsert | UNCHANGED |
| `store/schema.py :: ChunkRecord` | LanceDB row schema (chunk_id, start_line, end_line, etc.) | UNCHANGED |
| `tests/ingest/test_chunker.py` | Unit tests for all chunkers | EXTEND (new class) |
| `pyproject.toml` | Project dependencies | MODIFY (add 3 packages) |

## Recommended Project Structure

```
src/corpus_analyzer/ingest/
├── chunker.py          # Add chunk_typescript(), _get_ts_language(), _TS_CHUNK_NODE_TYPES
│                       # Modify chunk_file() dispatch for .ts/.tsx/.js/.jsx
├── indexer.py          # No changes needed
├── embedder.py         # No changes needed
└── scanner.py          # No changes needed

tests/ingest/
└── test_chunker.py     # Add TestChunkTypeScript class; extend TestChunkFile assertions
```

### Structure Rationale

- **Single file, not a new module:** `chunk_typescript()` belongs in `ingest/chunker.py` alongside `chunk_python()`. The Python AST chunker is already there; adding a sibling function keeps the dispatch table co-located with all chunker implementations and avoids unnecessary module proliferation.
- **No new `extractors/typescript.py`:** The `extractors/` module is the original corpus-analyzer pipeline (scan → extract → classify). The LanceDB ingest pipeline lives entirely in `ingest/`. The Python AST chunker already lives in `ingest/chunker.py` — not in `extractors/`. A TS chunker follows the same pattern.
- **Test in the existing test file:** `tests/ingest/test_chunker.py` already has `TestChunkPython`. Adding `TestChunkTypeScript` in the same file keeps the parity visible side-by-side and makes it easy to verify matching coverage.

## Architectural Patterns

### Pattern 1: Mirror the Python AST Chunker Structure

**What:** `chunk_typescript()` follows the exact same code structure as `chunk_python()`: read file, parse, find top-level constructs, build chunk dicts with `text`/`start_line`/`end_line`, fall back to `chunk_lines()` on failure.

**When to use:** Always for TS/JS. The mirror structure means tests, confidence level, and observable behaviour match the Python chunker contract with no surprises for callers.

**Trade-offs:** Top-level-only chunking (no recursion into classes) keeps parity with the Python chunker. Methods inside a class are included in the class chunk body — same as Python methods inside a class body. This may under-split very large classes but avoids overlapping chunk ranges.

```python
def chunk_typescript(path: Path) -> list[dict[str, Any]]:
    """Split a TypeScript/JavaScript file by top-level AST constructs.

    Handles .ts, .tsx, .js, .jsx. Uses tree-sitter for AST-aware splitting.
    Falls back to chunk_lines() silently on any parse failure.

    Args:
        path: Path to the file to chunk.

    Returns:
        List of chunks with "text", "start_line", and "end_line" keys.
    """
    with open(path, encoding="utf-8") as f:
        source = f.read()

    if not source.strip():
        return []

    try:
        language = _get_ts_language(path.suffix.lower())
        parser = Parser(language)
        tree = parser.parse(source.encode("utf-8"))
    except Exception:  # noqa: BLE001 — silent fallback on grammar/encoding errors
        return chunk_lines(path)

    top_level_nodes = [
        node for node in tree.root_node.children
        if node.type in _TS_CHUNK_NODE_TYPES
    ]

    if not top_level_nodes:
        return chunk_lines(path)

    lines = source.split("\n")
    chunks: list[dict[str, Any]] = []

    for i, node in enumerate(top_level_nodes):
        start_line = node.start_point[0] + 1  # tree-sitter is 0-indexed rows
        end_line = (
            top_level_nodes[i + 1].start_point[0]  # line before next node
            if i + 1 < len(top_level_nodes)
            else len(lines)
        )
        # trim trailing blank lines (mirrors chunk_python behaviour)
        actual_end = end_line
        while actual_end > start_line and not lines[actual_end - 1].strip():
            actual_end -= 1

        chunk_text = "\n".join(lines[start_line - 1 : actual_end]).rstrip()
        if chunk_text:
            chunks.append({
                "text": chunk_text,
                "start_line": start_line,
                "end_line": actual_end,
            })

    return chunks
```

---

### Pattern 2: Lazy Language Loading with Module-Level Cache

**What:** tree-sitter `Language` objects are constructed once and cached at module level. Per-file calls to `chunk_typescript()` reuse the cached object.

**When to use:** Always. Language object construction loads a compiled grammar binding. On a corpus with hundreds of TS files, per-call construction is measurably wasteful.

**Trade-offs:** Module-level globals require `global` declarations but are idiomatic for this class of Python parsing tool. A singleton class would add ceremony with no benefit.

```python
import tree_sitter_typescript as tsts
import tree_sitter_javascript as tsjs
from tree_sitter import Language, Parser

_TS_LANG: Language | None = None
_TSX_LANG: Language | None = None
_JS_LANG: Language | None = None


def _get_ts_language(ext: str) -> Language:
    """Return cached tree-sitter Language for a given file extension."""
    global _TS_LANG, _TSX_LANG, _JS_LANG
    if ext == ".ts":
        if _TS_LANG is None:
            _TS_LANG = Language(tsts.language_typescript())
        return _TS_LANG
    if ext in (".tsx", ".jsx"):
        # tsx grammar handles JSX syntax in both .tsx and .jsx
        if _TSX_LANG is None:
            _TSX_LANG = Language(tsts.language_tsx())
        return _TSX_LANG
    # .js falls through to JavaScript grammar
    if _JS_LANG is None:
        _JS_LANG = Language(tsjs.language())
    return _JS_LANG
```

**Grammar selection rationale:**
- `.ts` → `tsts.language_typescript()` — standard TypeScript
- `.tsx` and `.jsx` → `tsts.language_tsx()` — TSX grammar handles JSX syntax; also handles JavaScript with Flow annotations
- `.js` → `tsjs.language()` — plain JavaScript

---

### Pattern 3: Node Types as a Frozen Set Constant

**What:** Declare the set of tree-sitter node types that constitute chunk boundaries as a module-level `frozenset[str]` constant.

**When to use:** Keeps the "what to chunk on" decision explicit and easy to extend. Frozenset membership check is O(1).

```python
_TS_CHUNK_NODE_TYPES: frozenset[str] = frozenset({
    "function_declaration",      # function foo() {}
    "class_declaration",         # class Foo {}
    "interface_declaration",     # interface Foo {}
    "type_alias_declaration",    # type Foo = ...
    "method_definition",         # top-level method (rare in .js modules)
    "lexical_declaration",       # const foo = () => {} — covers arrow functions
    "variable_declaration",      # var foo = () => {}
})
```

**Trade-offs:** `lexical_declaration` and `variable_declaration` cover exported arrow functions (`export const handler = async () => {}`), which are common in TypeScript codebases. Deeply nested arrow functions inside a function body are NOT separately chunked — they remain inside the parent construct's chunk. This is correct: we want coherent construct-level chunks, not micro-chunks of nested closures.

---

### Pattern 4: Silent Fallback on Parse Error

**What:** Wrap the entire tree-sitter parse in a bare `except Exception` and return `chunk_lines(path)` on any failure. Do NOT check `tree.root_node.has_error`.

**When to use:** Always. tree-sitter is error-tolerant: it produces a partial tree with `has_error=True` for files with minor syntax issues (e.g., generics in JSX contexts, decorator syntax edge cases). These partial trees are usually structurally sound. Falling back on `has_error` would degrade chunk quality for many valid real-world files.

Only fall back on an actual uncaught exception, which covers: library initialisation failures, encoding issues, grammar version mismatches at import time.

```python
try:
    language = _get_ts_language(path.suffix.lower())
    parser = Parser(language)
    tree = parser.parse(source.encode("utf-8"))
except Exception:  # noqa: BLE001 — intentional: any failure falls back to line chunking
    return chunk_lines(path)

# proceed with tree.root_node — accept partial parse trees
```

**Trade-offs:** Broad exception catch triggers ruff BLE001. Add `# noqa: BLE001` with the inline comment shown above — consistent with how `ingest/indexer.py` handles graph edge failures.

## Data Flow

### Dispatch Change (the only modification to existing code)

```
chunk_file(path: Path) -> list[dict[str, Any]]
    |
    ext = path.suffix.lower()
    |
    ".md"                    -> chunk_markdown(path)      [existing]
    ".py"                    -> chunk_python(path)        [existing]
    ".ts" | ".tsx"           -> chunk_typescript(path)   [NEW — replaces chunk_lines]
    ".js" | ".jsx"           -> chunk_typescript(path)   [NEW — replaces chunk_lines]
    ".json" | ".yaml" | ...  -> chunk_lines(path)         [existing]
    everything else          -> chunk_lines(path)         [existing fallback]
    |
    _enforce_char_limit(chunks, max_chars=4000)            [unchanged]
```

The dispatch modification is mechanical: four extensions move from the `chunk_lines` branch to a new `chunk_typescript` branch. No other code in `indexer.py`, `cli.py`, `search/`, or any other module changes.

### ChunkRecord Schema: No Migration Required

The existing `ChunkRecord` has all required fields: `start_line`, `end_line`, `file_type`, `text`, `chunk_id`. `chunk_typescript()` returns the same `dict[str, Any]` shape as `chunk_python()`. No `ensure_schema_v4()` migration is needed. Existing LanceDB records for TS/JS files will be replaced on the next `corpus index` run when their content hash changes (normal re-index flow).

## Integration Points

### New vs Modified Components — Explicit Breakdown

| Component | Change Type | What Changes |
|-----------|-------------|--------------|
| `ingest/chunker.py` | MODIFY | Add `_TS_CHUNK_NODE_TYPES`, `_get_ts_language()`, `chunk_typescript()`; update `chunk_file()` dispatch |
| `tests/ingest/test_chunker.py` | EXTEND | Add `TestChunkTypeScript` class; update `TestChunkFile` dispatcher assertions for TS/JS |
| `pyproject.toml` | MODIFY | Add `tree-sitter>=0.25.0`, `tree-sitter-typescript>=0.23.2`, `tree-sitter-javascript>=0.25.0` |

### Unchanged Components

| Component | Why Unchanged |
|-----------|---------------|
| `ingest/indexer.py` | Calls `chunk_file()` — dispatch is internal to chunker |
| `store/schema.py` | `ChunkRecord` shape is compatible; no new fields |
| `search/engine.py` | Retrieval is agnostic to how chunks were created |
| `cli.py` | No new commands; `corpus index` picks up TS/JS automatically |
| `graph/` | Graph extraction operates on Markdown only |
| `classifiers/` | Classification operates on whole-file text; not chunk-aware |
| `extractors/` | Original corpus-analyzer pipeline; not the LanceDB ingest path |

### External Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `chunker.py` → `tree-sitter` (core) | Direct Python import, in-process | Pre-compiled wheels; no native build; requires Python >= 3.10 (project uses 3.12 — compatible) |
| `chunker.py` → `tree-sitter-typescript` | `tsts.language_typescript()` / `tsts.language_tsx()` | Two grammars in one package; latest v0.23.2 (Nov 2024) |
| `chunker.py` → `tree-sitter-javascript` | `tsjs.language()` | Separate package; latest v0.25.0 (Sep 2025) |

## Recommended Build Order

Build order is determined by test isolation: write tests first (RED), implement (GREEN), wire dispatch, validate full suite.

1. **Add dependencies to `pyproject.toml`** — run `uv sync` to confirm wheels resolve on the target platform; this unblocks everything else
2. **Write `TestChunkTypeScript` test class (RED)** — cover: functions, classes, interfaces, type aliases, arrow functions as `const`, line-range accuracy for 1-indexed start/end, fallback on syntax error, `.tsx` file with JSX, `.js` file
3. **Write `TestChunkFile` dispatch assertions (RED)** — assert `.ts`, `.tsx`, `.js`, `.jsx` use AST chunking (produce named construct chunks, not overlapping line windows)
4. **Implement `_TS_CHUNK_NODE_TYPES`, `_get_ts_language()`, `chunk_typescript()` (GREEN)** — make all new tests pass
5. **Modify `chunk_file()` dispatch** — route `.ts`, `.tsx`, `.js`, `.jsx` to `chunk_typescript()`
6. **Run full test suite** — `uv run pytest -v`; all 293 existing tests must stay green
7. **Run linting** — `uv run ruff check .` and `uv run mypy src/`; fix BLE001 noqa, ensure type annotations on new functions satisfy `--strict`

Steps 2–4 are the substantive work. Steps 5 and 6 are mechanical. Step 7 enforces the zero-violation baseline established in v1.3.

## Anti-Patterns

### Anti-Pattern 1: Recursive AST Walk

**What people do:** Write a recursive DFS that descends into every node, collecting any `function_declaration` or `class_declaration` anywhere in the tree — including nested functions inside methods.

**Why it's wrong:** Produces overlapping chunk ranges (a method chunk whose text also appears inside the class chunk). Breaks `_enforce_char_limit` assumptions. Creates many tiny micro-chunks that destroy retrieval quality for class-heavy TypeScript files. Does not match the behaviour of `chunk_python()`, which only visits `tree.body` (top-level nodes).

**Do this instead:** Walk only `tree.root_node.children` (depth 1). This directly mirrors `for node in tree.body` in the Python chunker.

---

### Anti-Pattern 2: Creating a Language Object Per File

**What people do:** Call `Language(tsts.language_typescript())` inside `chunk_typescript()` on every invocation, or at the top of the function before parsing.

**Why it's wrong:** Language object construction loads a compiled grammar binary. On a corpus of 500 TS files this is 500 redundant constructions. Measurably slows `corpus index`.

**Do this instead:** Cache at module level with `_TS_LANG: Language | None = None` and a `_get_ts_language(ext)` helper (see Pattern 2).

---

### Anti-Pattern 3: A New `extractors/typescript.py` Module

**What people do:** Create `src/corpus_analyzer/extractors/typescript.py` to mirror the existing extractor structure.

**Why it's wrong:** The `extractors/` module belongs to the original corpus-analyzer pipeline (scan → extract → classify → analyze). The LanceDB ingest pipeline (`ingest/`) is a separate code path. The Python AST chunker already lives in `ingest/chunker.py` — not in `extractors/`. Placing a TS chunker in `extractors/` creates cross-pipeline confusion.

**Do this instead:** Add `chunk_typescript()` to `ingest/chunker.py` as a sibling of `chunk_python()`.

---

### Anti-Pattern 4: Falling Back on `tree.root_node.has_error`

**What people do:** Check `if tree.root_node.has_error: return chunk_lines(path)` immediately after parsing.

**Why it's wrong:** tree-sitter is an error-tolerant parser. Real TypeScript files with minor syntax issues (generics in JSX contexts, experimental decorators, non-standard syntax) commonly produce `has_error=True` on the root node but still yield a structurally complete tree. Aggressive fallback on `has_error` degrades chunk quality for many valid files unnecessarily.

**Do this instead:** Only fall back on an uncaught exception from `parser.parse()`. Accept partial parse trees — they are reliable for top-level construct extraction even when individual nodes contain error nodes.

---

### Anti-Pattern 5: Treating `.jsx` as Needing the JavaScript Grammar

**What people do:** Route `.jsx` to `tree-sitter-javascript` because "jsx is javascript with JSX".

**Why it's wrong:** `tree-sitter-javascript` does not handle JSX syntax — it parses standard ECMAScript. JSX support requires the TSX grammar from `tree-sitter-typescript`, which was designed to handle JSX in both `.tsx` and `.jsx` contexts (and also handles JavaScript+Flow).

**Do this instead:** Route `.jsx` (and `.tsx`) to `tsts.language_tsx()` — the TSX grammar handles JSX syntax for both file types.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Current (local, single user) | No changes needed. `chunk_typescript()` is in-process and fast. |
| Larger corpora (10k+ TS files) | Language object caching (Pattern 2) ensures O(1) grammar loading. tree-sitter itself is incremental-parse capable but we re-parse from scratch on each changed file — adequate for batch indexing. |
| Parallel indexing (hypothetical) | Module-level globals are not thread-safe. If `index_source()` ever becomes multi-threaded, language caching would need a lock. Not a concern for current single-threaded design. |

## Sources

- [py-tree-sitter official documentation](https://tree-sitter.github.io/py-tree-sitter/) — HIGH confidence; current API for Parser, Language, Node
- [tree-sitter PyPI page (v0.25.2, Sep 2025)](https://pypi.org/project/tree-sitter/) — HIGH confidence; Python >= 3.10 requirement confirmed, pre-compiled wheels confirmed
- [tree-sitter-typescript PyPI (v0.23.2, Nov 2024)](https://pypi.org/project/tree-sitter-typescript/) — HIGH confidence; two grammars confirmed: `language_typescript()` and `language_tsx()`
- [tree-sitter-javascript PyPI (v0.25.0, Sep 2025)](https://pypi.org/project/tree-sitter-javascript/) — HIGH confidence; `language()` function confirmed
- [py-tree-sitter GitHub README](https://github.com/tree-sitter/py-tree-sitter) — HIGH confidence; traversal API, Parser/Language usage
- [DeepWiki: tree-sitter-typescript node types](https://deepwiki.com/tree-sitter/tree-sitter-typescript/1.2-getting-started) — MEDIUM confidence; node type list (`function_declaration`, `class_declaration`, `interface_declaration`, `type_alias_declaration`, `method_definition`, `arrow_function`) cross-referenced against grammar source
- Direct inspection: `ingest/chunker.py` — `chunk_python()` structure used as mirror template
- Direct inspection: `ingest/indexer.py` — `chunk_file()` call site; confirms no dispatch logic in indexer
- Direct inspection: `store/schema.py` — confirms `ChunkRecord` shape is compatible; no migration needed
- Direct inspection: `tests/ingest/test_chunker.py` — `TestChunkPython` used as parity template for `TestChunkTypeScript`

---
*Architecture research for: corpus-analyzer v1.5 tree-sitter TS/JS chunker*
*Researched: 2026-02-24*

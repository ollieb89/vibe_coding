# Feature Research

**Domain:** TypeScript/JavaScript AST-aware chunking for local semantic search indexing
**Researched:** 2026-02-24
**Confidence:** HIGH (existing Python chunker audited directly; tree-sitter TypeScript node types verified against official node-types.json; chunking patterns verified against LanceDB RAG blog, supermemory code-chunk library, and cAST academic paper)

---

## Context: Existing Python Chunker as the Parity Target

The Python AST chunker (`chunk_python` in `ingest/chunker.py`) sets the design contract
that the TypeScript chunker must match:

| Property | Python chunker behaviour |
|----------|--------------------------|
| Granularity | Top-level `FunctionDef`, `AsyncFunctionDef`, `ClassDef` only — nested defs are NOT separate chunks |
| Output fields | `{"text": str, "start_line": int, "end_line": int}` — no extra fields |
| Fallback | `chunk_lines(path)` when parse fails OR no top-level defs found |
| Character limit | `_enforce_char_limit(chunks, max_chars=4000)` applied by `chunk_file()` dispatcher |
| Dispatch point | `chunk_file()` in `chunker.py` routes `.py` → `chunk_python` |

The new `chunk_typescript` function must produce the same dict shape (`text`, `start_line`,
`end_line`) and be wired into `chunk_file()` for `.ts`, `.tsx`, `.js`, `.jsx`.

---

## Established TypeScript/JavaScript AST Node Types

The tree-sitter-typescript grammar (v0.23.2) defines these node type strings, verified
against the official `node-types.json` file:

| Node Type String | What It Represents |
|------------------|-------------------|
| `function_declaration` | `function foo() {}` |
| `generator_function_declaration` | `function* gen() {}` |
| `arrow_function` | `const fn = () => {}` (top-level only if assigned to a `lexical_declaration`) |
| `class_declaration` | `class Foo {}` |
| `method_definition` | Methods inside a class body (child of `class_declaration`) |
| `interface_declaration` | `interface Foo {}` (TypeScript only) |
| `type_alias_declaration` | `type Foo = ...` (TypeScript only) |
| `enum_declaration` | `enum Color {}` (TypeScript only) |
| `lexical_declaration` | `const`/`let` declarations — wraps arrow functions and exported constants |
| `export_statement` | `export function foo()` / `export default class` / `export const` — wrapper around a declaration |
| `abstract_class_declaration` | `abstract class Foo {}` (TypeScript only) |
| `ambient_declaration` | `declare module ...` / `declare const ...` (TypeScript `.d.ts` ambient) |

The TSX grammar adds JSX-specific nodes but does not change which declaration nodes
are relevant for chunking. The TypeScript grammar handles `.ts`/`.tsx` and the JavaScript
grammar (via `tree_sitter_languages` or `tree-sitter-javascript`) handles `.js`/`.jsx`.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Missing any of these makes the chunker incomplete relative to the Python AST chunker,
which is the baseline users already have for Python files.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Function declaration extraction | Functions are the primary semantic unit in any codebase; line-based chunks split functions arbitrarily, causing truncation and duplication | LOW | Node types: `function_declaration`, `generator_function_declaration`. Use `node.start_point[0]` + `node.end_point[0]` for line ranges (0-indexed → convert to 1-indexed) |
| Class declaration extraction | Classes are atomic units; splitting a class across two line-window chunks destroys its meaning for search | LOW | Node type: `class_declaration`, `abstract_class_declaration`. Entire class (including methods) as one chunk — mirrors Python chunker which does NOT sub-chunk methods |
| Interface declaration extraction (TypeScript) | Interfaces are type contracts and are frequently searched by name; missing them degrades search quality for TS-heavy repos | LOW | Node type: `interface_declaration`. TypeScript-only; JS parser will not encounter these |
| Type alias extraction (TypeScript) | `type Foo = ...` declarations are often the thing users search for in TypeScript codebases (e.g., "find the RequestPayload type") | LOW | Node type: `type_alias_declaration`. Often short; rarely needs char-limit splitting |
| Top-level constant extraction | `export const BASE_URL = ...` and similar top-level constants are searched directly; mixing them into line-window chunks reduces precision | MEDIUM | Node type: `lexical_declaration`. Scope: top-level only. Distinguish from local variable declarations — only extract from root program body |
| Silent fallback on parse failure | tree-sitter parse failure (e.g., JSX in a `.js` file, syntax error, encoding issue) must not crash indexing; graceful degradation to `chunk_lines()` | LOW | Mirrors Python chunker: `try/except` around `parser.parse()`; return `chunk_lines(path)` on error |
| Silent fallback when no top-level constructs found | Some TS/JS files are pure type-only imports or re-exports with no extractable constructs; must not return empty | LOW | If extracted chunk list is empty after traversal, return `chunk_lines(path)` — mirrors Python chunker |
| `.ts`, `.tsx`, `.js`, `.jsx` dispatch | All four extensions must route to the new chunker in `chunk_file()`; currently all four fall through to `chunk_lines()` | LOW | One elif branch in `chunk_file()` replacing the existing `chunk_lines` fallback for these extensions |
| Test suite at full parity with Python chunker | The Python chunker has 5 test classes covering: top-level extraction, nested-not-separate, async variants, line ranges, and no-defs fallback. The TS chunker must have equivalent coverage | MEDIUM | New test file `tests/ingest/test_chunker_typescript.py`; use `tmp_path` fixtures with inline source; test each node type separately |

### Differentiators (Competitive Advantage)

These go beyond the minimum parity contract and improve search quality meaningfully.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Export-unwrapping for exported declarations | `export function foo()` wraps a `function_declaration` inside an `export_statement` node. Extracting the inner declaration (not the export wrapper) preserves the function text cleanly, including the `export` keyword in the chunk text | LOW | Walk `export_statement` children: if child is a declaration node, treat the declaration as the chunk boundary but include the full `export_statement` text. Avoids double-counting |
| `chunk_name` field in returned dict | Adding the extracted construct name (e.g., `"UserService"`, `"fetchData"`) to the chunk dict enables future `--construct` filtering and name-based search without re-parsing | LOW | Python chunker does NOT return a name field — this would be a forward extension. Pass as optional key; `chunk_file()` and indexer do not need to use it yet but schema migration is simpler if added now |
| Enum declaration extraction (TypeScript) | `enum Color { Red, Green, Blue }` is a lookup table searched by name; it is a distinct semantic unit that line-based chunking splits badly | LOW | Node type: `enum_declaration`. Short by nature; rarely hits char limit |
| Separate TypeScript vs JavaScript grammar dispatch | TypeScript files need the `typescript`/`tsx` grammar; JavaScript files need the `javascript` grammar. Using the TypeScript grammar on `.js` files works but is heavier than needed | LOW | Dispatch by extension within `chunk_typescript()`: `.ts`/`.tsx` → `tree_sitter_languages.get_language("typescript")` or `"tsx"`; `.js`/`.jsx` → `"javascript"` |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Method-level chunking (extracting class methods as separate chunks) | Finer granularity seems better for search precision | Methods are meaningless without their class context. A method chunk for `getUser()` that lacks the class name `UserService` is unsearchable. The Python chunker deliberately does NOT sub-chunk methods for this reason. The existing `chunk_python` tests explicitly assert "nested not separate". | Extract the entire class as one chunk. If the class is too large, `_enforce_char_limit` will split it at character boundaries — this is acceptable because it keeps the class header in the first sub-chunk |
| Import statement chunking | Import blocks contain useful dependency information | Import blocks have near-zero standalone search value — searching for `import { useState } from 'react'` is not a use case. They inflate chunk count and add noise to BM25. The `code-chunk` library offers imports as an entity type but notes they are used as context rather than as searchable entities. | Leave imports in the chunk text of whatever follows them (they appear before the first construct), or include them in the file-level preamble if a preamble chunk is desired |
| JSDoc/comment extraction as separate chunks | Documentation comments are valuable | Comment chunks have no executable context; they embed poorly because they are natural language without code signals. JSDoc belongs in the chunk text of the function it documents (it precedes the function declaration in the AST and is included naturally by using `node.start_point` as the chunk boundary). | Include preceding JSDoc in chunk text by starting the chunk text at the comment line above the declaration, not at the `function` keyword |
| `ambient_declaration` and `.d.ts` file chunking | Type declaration files are part of the codebase | `.d.ts` files are generated artefacts in most projects (e.g., `dist/`, `node_modules/`). Including them doubles chunk count for generated types. The extension allowlist in `corpus.toml` already handles exclusion at the scanner level. | Rely on scanner-level exclusion via `source.extensions` and `source.exclude` paths in `corpus.toml`; do not special-case in the chunker |
| Storing `chunk_name` in `ChunkRecord` LanceDB schema | Enables name-based filtering | Adds a schema migration (`ensure_schema_v4()`) and a new nullable column in LanceDB. The `ChunkRecord` schema warning states "Changing them requires dropping and rebuilding the entire table." Schema changes require careful migration discipline. This is a v2 candidate. | Add `chunk_name` to the `dict` returned by `chunk_typescript()` but have `index_source()` ignore the extra key for now. When the schema migration is ready, the key is already there. |
| Real-time AST re-parse on search | Provide line-context highlighting at query time | Significant latency increase on every search call. The chunker runs at index time; the indexer already stores `start_line`/`end_line`. Search-time re-parsing would require storing raw source or re-reading files. | Store `start_line`/`end_line` at index time (already done); use them to display line ranges in search results when chunk-level result display ships (v2 candidate per PROJECT.md) |

---

## Feature Dependencies

```
[chunk_typescript() function]
    └──requires──> [tree-sitter + tree-sitter-languages installed]
    └──requires──> [chunk_lines() fallback exists]  ← already done
    └──requires──> [_enforce_char_limit() applied]  ← already done in chunk_file()

[chunk_file() dispatch updated]
    └──requires──> [chunk_typescript() implemented]
    └──replaces──> [chunk_lines() for .ts/.tsx/.js/.jsx]

[Test suite]
    └──requires──> [chunk_typescript() implemented]
    └──mirrors──> [TestChunkPython test structure]

[Export-unwrapping]
    └──requires──> [chunk_typescript() top-level extraction working]
    └──enhances──> [function_declaration extraction]

[chunk_name field in dict]
    └──requires──> [chunk_typescript() returning node name]
    └──independent of──> [LanceDB schema — ignored by indexer until schema migration ships]

[Separate TS vs JS grammar dispatch]
    └──requires──> [chunk_typescript() implemented]
    └──is part of──> [chunk_typescript() internal logic]
```

### Dependency Notes

- **`tree-sitter-languages` vs separate packages:** `tree-sitter-languages` is a PyPI package that ships pre-compiled grammars for 100+ languages via binary wheels. It is simpler to install than `tree-sitter-typescript` (which requires compilation). The STACK.md for this milestone should specify which package to use. `tree-sitter-languages` is the preferred choice for this project because it avoids C compilation in the `uv sync` pipeline. MEDIUM confidence — verify current `tree-sitter-languages` version ships TypeScript + TSX grammars.

- **TSX grammar for `.tsx` files:** The TypeScript tree-sitter grammar repo ships two grammars: `typescript` (for `.ts`) and `tsx` (for `.tsx` and Flow-typed `.js`). `chunk_typescript()` must select the correct grammar by extension.

- **`chunk_name` optional field:** The Python chunker's output dict has only `text`, `start_line`, `end_line`. Adding `chunk_name` is forward-compatible (Python dicts accept extra keys); `index_source()` builds `chunk_dict` explicitly and will not store `chunk_name` until the schema is ready. This is safe to add now without a schema migration.

- **Character limit is applied in `chunk_file()`:** The `_enforce_char_limit(chunks, max_chars=4000)` call in `chunk_file()` applies after dispatch. `chunk_typescript()` does not need to implement it — parity with Python chunker.

---

## MVP Definition

### Launch With (v1.5)

The minimum set to replace line-based chunking for TS/JS with meaningful AST chunking.

- [ ] `chunk_typescript(path)` function extracting top-level: `function_declaration`, `generator_function_declaration`, `class_declaration`, `abstract_class_declaration`, `interface_declaration`, `type_alias_declaration`, `lexical_declaration` (top-level consts) — IDX-01, IDX-02
- [ ] Export-unwrapping: `export_statement` nodes whose child is a declaration are handled by extracting the full `export_statement` text with the declaration's line boundaries — IDX-02 detail
- [ ] Silent fallback to `chunk_lines(path)` on parse failure and on empty extraction — IDX-03
- [ ] Grammar selection by extension: `typescript` for `.ts`, `tsx` for `.tsx`, `javascript` for `.js`/`.jsx` — IDX-01 detail
- [ ] `chunk_file()` dispatcher updated: `.ts`, `.tsx`, `.js`, `.jsx` → `chunk_typescript` — IDX-04
- [ ] Test file `tests/ingest/test_chunker_typescript.py` with classes for: function extraction, class extraction, interface/type/enum extraction, top-level const extraction, line ranges, nested-not-separate, export-wrapped declarations, parse-failure fallback, no-constructs fallback — TEST-01

### Add After Validation (v1.x)

- [ ] `chunk_name` field in returned dict — add the extracted name string to the dict; `index_source()` ignores it until schema migration is ready. Low-risk, enables future `--construct` filtering by name without re-parse.
- [ ] `enum_declaration` extraction — TypeScript enums are a differentiator; include if test time allows

### Future Consideration (v2+)

- [ ] `chunk_name` persisted in LanceDB `ChunkRecord` schema — requires `ensure_schema_v4()` migration; deferred to avoid schema churn
- [ ] Method-level chunk option (class methods as separate chunks with class context prepended) — only valuable after chunk-level result display ships (PROJECT.md v2 candidate)
- [ ] Ambient declaration handling for `.d.ts` files — only relevant if users index TypeScript declaration files explicitly

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| `function_declaration` extraction | HIGH — primary search target in any JS/TS codebase | LOW — two node type strings, one traversal | P1 |
| `class_declaration` extraction | HIGH — classes are atomic units; line-based splits break class search | LOW — one node type string | P1 |
| `interface_declaration` extraction | HIGH for TS repos — interfaces are the contract types users search | LOW — TypeScript grammar only | P1 |
| `type_alias_declaration` extraction | HIGH for TS repos — types are frequently searched by name | LOW — short nodes, minimal risk | P1 |
| Top-level `lexical_declaration` extraction | MEDIUM — catches `export const` and large constants | MEDIUM — requires filtering to root-body only; must avoid extracting local variables | P1 |
| Silent fallback on parse failure | HIGH — prevents indexing crashes on malformed files | LOW — try/except, return chunk_lines | P1 |
| Grammar selection by extension | HIGH — wrong grammar produces garbage parse trees | LOW — dict lookup on extension | P1 |
| `chunk_file()` dispatch update | HIGH — without this, chunker is never invoked | LOW — one elif branch change | P1 |
| Test suite parity | HIGH — maintains 293+ green tests baseline | MEDIUM — 8–12 test cases across node types | P1 |
| Export-unwrapping | MEDIUM — improves chunk text quality for exported declarations | LOW — one extra walk step in traversal | P1 |
| `enum_declaration` extraction | MEDIUM for TS repos — enums are discrete named units | LOW — one node type string | P2 |
| `chunk_name` in dict | LOW now, HIGH later — enables future filtering without re-parse | LOW — `node.child_by_field_name("name").text` | P2 |
| Separate TS vs JS grammar dispatch | LOW — TypeScript grammar parses JS but is heavier | LOW — extension lookup | P2 |

**Priority key:**
- P1: Required for v1.5 milestone
- P2: Add during v1.5 if scope allows; no milestone risk if deferred
- P3: Future consideration only

---

## Parity Matrix: Python Chunker vs TypeScript Chunker

| Behaviour | Python chunker | TypeScript chunker (target) |
|-----------|---------------|----------------------------|
| Top-level function extraction | `FunctionDef`, `AsyncFunctionDef` | `function_declaration`, `generator_function_declaration` |
| Class extraction | `ClassDef` | `class_declaration`, `abstract_class_declaration` |
| Type/interface extraction | Not applicable (Python has no interfaces) | `interface_declaration`, `type_alias_declaration` |
| Enum extraction | Not applicable | `enum_declaration` |
| Top-level const extraction | Not applicable (Python falls back to chunk_lines on no defs) | `lexical_declaration` at root body |
| Nested constructs | NOT separate chunks | NOT separate chunks (methods stay inside class chunk) |
| Parse failure fallback | `chunk_lines(path)` | `chunk_lines(path)` |
| No-constructs fallback | `chunk_lines(path)` | `chunk_lines(path)` |
| Output dict shape | `{text, start_line, end_line}` | `{text, start_line, end_line}` (plus optional `chunk_name`) |
| Char limit enforcement | Applied by `chunk_file()` caller | Applied by `chunk_file()` caller — same location |
| Library used | `ast` (stdlib) | `tree-sitter-languages` (PyPI) |

---

## Sources

- Direct audit of `/src/corpus_analyzer/ingest/chunker.py` (`chunk_python`, `chunk_file`, `_enforce_char_limit`) — HIGH confidence
- Direct audit of `tests/ingest/test_chunker.py` (parity test structure) — HIGH confidence
- [tree-sitter-typescript node-types.json (TSX)](https://github.com/tree-sitter/tree-sitter-typescript/blob/master/tsx/src/node-types.json) — HIGH confidence (official grammar source)
- [tree-sitter-typescript PyPI (v0.23.2)](https://pypi.org/project/tree-sitter-typescript/) — HIGH confidence (official package)
- [py-tree-sitter documentation](https://tree-sitter.github.io/py-tree-sitter/) — HIGH confidence (official docs)
- [supermemory code-chunk library — entity types and metadata](https://github.com/supermemoryai/code-chunk) — MEDIUM confidence (actively maintained OSS; entity type list verified against README)
- [Building code-chunk: AST Aware Code Chunking (supermemory blog)](https://supermemory.ai/blog/building-code-chunk-ast-aware-code-chunking/) — MEDIUM confidence (design rationale and metadata fields)
- [LanceDB: Building RAG on codebases Part 1](https://lancedb.com/blog/building-rag-on-codebases-part-1/) — MEDIUM confidence (node type names, metadata recommendations)
- [cAST paper: Enhancing Code RAG with Structural Chunking via AST](https://arxiv.org/html/2506.15655v1) — MEDIUM confidence (empirical evidence for AST chunking quality gains)
- [Better retrieval beats better models — AST chunking and hierarchical indexing](https://sderosiaux.substack.com/p/better-retrieval-beats-better-models) — MEDIUM confidence (function-level granularity recommendation)

---
*Feature research for: v1.5 TypeScript/JavaScript AST-aware chunking*
*Researched: 2026-02-24*

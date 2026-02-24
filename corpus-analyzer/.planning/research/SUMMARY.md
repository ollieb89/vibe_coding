# Project Research Summary

**Project:** corpus-analyzer v1.5 — TypeScript/JavaScript AST Chunking
**Domain:** Tree-sitter AST-aware code chunking for local semantic search indexing
**Researched:** 2026-02-24
**Confidence:** HIGH

## Executive Summary

This milestone adds AST-aware chunking for TypeScript and JavaScript files to the existing corpus-analyzer LanceDB ingest pipeline. The approach is a deliberate incremental change: one new function (`chunk_typescript`) added to `ingest/chunker.py`, a single dispatch change in `chunk_file()`, two new dependencies, and a new test class at full parity with the existing Python AST chunker. The entire change is scoped to three files — `chunker.py`, `test_chunker.py`, and `pyproject.toml`. Nothing else in the system requires modification.

The recommended library pair is `tree-sitter>=0.25.0` and `tree-sitter-language-pack>=0.13.0`. The language-pack bundles pre-compiled grammars for all four target dialects (TypeScript, TSX, JavaScript, JSX) in a single dependency with no C toolchain required. The design mirrors the existing `chunk_python()` function exactly: top-level constructs only, silent fallback to `chunk_lines()` on failure, same `{text, start_line, end_line}` output shape. The Python chunker is the parity target — every design decision reduces to "what does `chunk_python` do?"

The most dangerous implementation risk is the grammar/bindings ABI mismatch: `tree-sitter` core and the grammar packages must be pinned to compatible versions or runtime failures emerge silently as corrupt parse trees. The second most dangerous risk is silently missing all arrow functions — the dominant pattern in modern TypeScript — because `const foo = () => {}` produces a `lexical_declaration` node, not a `function_declaration`. Both risks are well-understood and have clear prevention strategies. Pin versions on day one; include `lexical_declaration` in the node-type filter from the start.

## Key Findings

### Recommended Stack

The existing application stack (LanceDB, FastMCP, Typer, Rich, Pydantic, Python 3.12) is unchanged. Two new packages are required and sufficient.

See full details: `.planning/research/STACK.md`

**Core technologies:**
- `tree-sitter>=0.25.0` — Python bindings to tree-sitter C library; pre-compiled wheels, no C compiler needed; typed stubs included (mypy compatible under `--strict`)
- `tree-sitter-language-pack>=0.13.0` — pre-built grammars for TypeScript, TSX, JavaScript, JSX in one package; active maintenance (released 2025-11-26); replaces unmaintained `tree-sitter-languages`; entry point is `get_parser(dialect)` which returns a fully configured `Parser`

**Critical version constraint:** language-pack 0.13.0 requires tree-sitter 0.25.x. Both packages must be pinned to compatible versions or ABI errors appear at runtime, often silently as corrupt parse trees rather than clean import errors.

**API entry point:** `from tree_sitter_language_pack import get_parser` — one call covers all four dialects. Cache via `@lru_cache` or module-level globals to avoid redundant grammar loading across files in a large corpus.

**What NOT to use:** `tree-sitter-languages` (explicitly unmaintained; Python 3.12+ wheels broken), `tree-sitter-typescript` standalone (stale, requires separate JS package), `Language.build_library()` (removed in tree-sitter 0.21+), `Parser.set_language()` (removed in tree-sitter 0.23+).

### Expected Features

See full details: `.planning/research/FEATURES.md`

**Must have (table stakes — v1.5 P1):**
- `function_declaration` and `generator_function_declaration` extraction — primary search target in any JS/TS codebase
- `class_declaration` and `abstract_class_declaration` extraction — classes are atomic units; line-based splitting destroys class search quality
- `interface_declaration` extraction (TypeScript-only) — type contracts are frequently searched by name in TS repos
- `type_alias_declaration` extraction (TypeScript-only) — `type Foo = ...` declarations are high-value search targets
- Top-level `lexical_declaration` extraction — captures `export const handler = async () => {}` arrow function patterns (critical: this is the dominant pattern in modern TS)
- Export-unwrapping: `export_statement` nodes whose child is a declaration are handled by extracting full text with declaration's line boundaries
- Silent fallback to `chunk_lines()` on parse failure and on empty extraction
- Grammar selection by extension: `typescript` for `.ts`, `tsx` for `.tsx` and `.jsx`, `javascript` for `.js`
- `chunk_file()` dispatcher updated to route all four extensions to `chunk_typescript()`
- Test suite at full parity with `TestChunkPython`: functions, classes, interfaces/types, top-level consts, line ranges, nested-not-separate, export-wrapped, fallback cases

**Should have (v1.5 P2, if scope allows):**
- `enum_declaration` extraction — TypeScript enums are discrete named units; one node type string, low implementation cost
- `chunk_name` field in returned dict — forward-compatible key (ignored by indexer until schema migration); enables future `--construct` filtering without re-parse

**Defer (v2+):**
- `chunk_name` persisted in LanceDB `ChunkRecord` schema — requires `ensure_schema_v4()` migration
- Method-level chunking (class methods as separate chunks) — only valuable after chunk-level result display ships; methods without class context are unsearchable
- Ambient declaration handling for `.d.ts` files — rely on scanner-level exclusion instead

**Anti-features to avoid:**
- Method-level chunking — methods without class context are unsearchable; Python chunker deliberately does not sub-chunk methods
- Import statement chunking — near-zero standalone search value; inflates chunk count and BM25 noise
- JSDoc/comment extraction as separate chunks — belong embedded in the function chunk text that follows them
- Schema migration in this milestone — `ChunkRecord` shape is fully compatible; no migration needed

### Architecture Approach

The change is surgical: three files modified, no new modules. `chunk_typescript()` lives in `ingest/chunker.py` alongside `chunk_python()` — the dispatch table stays co-located with all chunker implementations and avoids unnecessary module proliferation. No new `extractors/typescript.py` module (that belongs to the original corpus-analyzer pipeline, not the LanceDB ingest path). Tests extend the existing `tests/ingest/test_chunker.py` with a `TestChunkTypeScript` class, keeping Python and TypeScript parity visible side-by-side.

See full details: `.planning/research/ARCHITECTURE.md`

**Major components and changes:**
1. `ingest/chunker.py` — MODIFY: add `_TS_CHUNK_NODE_TYPES` (frozenset), `_get_ts_language()` (cached language loader), `chunk_typescript()` (new function); update `chunk_file()` dispatch for `.ts`/`.tsx`/`.js`/`.jsx`
2. `tests/ingest/test_chunker.py` — EXTEND: add `TestChunkTypeScript` class; extend `TestChunkFile` dispatch assertions for all four extensions
3. `pyproject.toml` — MODIFY: add `tree-sitter>=0.25.0` and `tree-sitter-language-pack>=0.13.0`

**Unchanged components:** `ingest/indexer.py`, `store/schema.py`, `search/engine.py`, `cli.py`, `graph/`, `classifiers/`, `extractors/`.

**Key patterns:**
- Mirror `chunk_python()` structure exactly — same signature contract, same fallback behaviour, same output shape
- Cache `Language`/`Parser` objects at module level — construction loads compiled grammar binary; per-call construction on 500 TS files adds ~30s to `corpus index`
- Walk `root_node.children` at depth 1 only — no recursive descent; mirrors `for node in tree.body` in `chunk_python()`
- Only fall back on uncaught exception or zero named constructs — do NOT fall back on `root_node.has_error` (tree-sitter is error-tolerant; most real-world files have minor errors that set `has_error` but still yield valid top-level structure)

### Critical Pitfalls

See full details: `.planning/research/PITFALLS.md`

1. **Grammar/bindings ABI version mismatch** — Pin `tree-sitter` and `tree-sitter-language-pack` to the same major.minor in `pyproject.toml` on day one. Add a smoke-test that parses a 2-line TS snippet without error to catch mismatches on `uv sync`. Failure mode is silent corrupt trees, not clean import errors.

2. **Arrow functions missing because they are `lexical_declaration` nodes** — Modern TypeScript heavily uses `const foo = () => {}` which produces `lexical_declaration`, not `function_declaration`. Must include `lexical_declaration` in `_TS_CHUNK_NODE_TYPES` from the start. Missing this produces zero AST chunks for many real-world TS files.

3. **Wrong grammar for `.tsx`/`.jsx` — silent fallback on all JSX** — `.tsx` files parsed with the TypeScript grammar produce ERROR nodes at every JSX element. Must dispatch `.tsx` and `.jsx` to the TSX grammar, not the TypeScript grammar. Test with a file containing `<Component />` syntax.

4. **Off-by-one line numbers** — tree-sitter uses 0-indexed rows; the rest of the codebase and LanceDB schema use 1-indexed lines. Always apply `node.start_point[0] + 1` conversion. Make this explicit in test assertions, not just an implementation detail.

5. **`node.text` returns `bytes | None`** — Use `source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")` for chunk text extraction. The `errors="replace"` argument handles non-ASCII identifiers and generated code without crashing the indexer.

6. **Over-aggressive `has_error` fallback** — `root_node.has_error` is True on many valid real-world files with minor syntax errors. Only fall back when the root node itself is an ERROR type (catastrophic failure) or when zero named constructs are extracted. Never fall back on `has_error` alone.

7. **Parser/Language constructed per file** — Language object construction loads a compiled grammar binary. At 500+ TS files this adds ~30s to `corpus index`. Cache at module level.

## Implications for Roadmap

Research strongly supports a two-phase implementation. All work is self-contained within `ingest/chunker.py`; there are no cross-module dependencies to sequence around. The natural split is: core chunker implementation (RED→GREEN test-driven), then integration hardening and quality polish.

### Phase 1: Core AST Chunker Implementation

**Rationale:** All P1 features are concentrated in a single function. Test-driven development (write `TestChunkTypeScript` first, implement to green) is the recommended build order from architecture research. Dependencies must be installed and smoke-tested before any chunker code is written — ABI mismatch is a day-one risk that must be caught before writing any implementation code.

**Delivers:** A fully functional `chunk_typescript()` replacing line-based chunking for all four extensions, with test coverage at parity with the Python chunker.

**Addresses:**
- All P1 features: function/class/interface/type/const extraction, export-unwrapping, fallback, grammar dispatch, `chunk_file()` dispatch update
- Full test suite: 8–12 new test cases covering all node types, line-range accuracy, fallback paths, JSX parse, `.js`/`.jsx` dispatch

**Avoids:**
- Pitfall 1 (ABI mismatch) — pin versions in `pyproject.toml` as first commit action; add smoke-test
- Pitfall 2 (removed API) — use `get_parser(dialect)` from language-pack; grep confirms no `build_library` or `set_language` calls
- Pitfall 3 (wrong grammar for TSX/JSX) — `_get_ts_language()` dispatch table routes `.tsx`/`.jsx` to TSX grammar from first implementation; test with `<Component />` source
- Pitfall 4 (missing arrow functions) — include `lexical_declaration` in `_TS_CHUNK_NODE_TYPES` from the start; test with arrow-function-only source file
- Pitfall 5 (off-by-one) — explicit `+ 1` named in test assertions as a required behaviour
- Pitfall 6 (bytes not decoded) — byte-range slicing with `errors="replace"` throughout; test with non-ASCII identifier
- Pitfall 7 (over-aggressive `has_error` fallback) — only fall back on exception or zero constructs; test with deliberate mid-file syntax error

**Build order (from ARCHITECTURE.md):**
1. Add dependencies to `pyproject.toml`; run `uv sync`; run smoke-test
2. Write `TestChunkTypeScript` test class (RED)
3. Write `TestChunkFile` dispatch assertions (RED)
4. Implement `_TS_CHUNK_NODE_TYPES`, `_get_ts_language()`, `chunk_typescript()` (GREEN)
5. Modify `chunk_file()` dispatch

### Phase 2: Integration Hardening and Quality Polish

**Rationale:** After core chunker is green and wired, validate integration-level concerns (performance guards, ImportError handling) and add P2 features if scope permits. These do not block the core milestone but prevent production-level issues on real-world corpora.

**Delivers:** Production-ready integration with performance safeguards, ruff/mypy compliance, and optional P2 enhancements.

**Addresses:**
- Performance trap: character-count guard for large generated/minified files (skip AST parse for files over ~50k chars; return `chunk_lines()` directly)
- `ImportError` guard in `chunk_file()` — if `tree-sitter` is absent, fall back gracefully to line chunking rather than raising `ImportError` at import time
- Full test suite green: all 293 existing tests pass; new tests added
- P2 (if scope allows): `enum_declaration` extraction, `chunk_name` field in returned dict

**Implements:** Architecture anti-patterns prevention confirmed under real corpus load; mypy `--strict` compliance (node.text None guards); ruff compliance (BLE001 `# noqa` with inline comments).

### Phase Ordering Rationale

- Phase 1 is entirely self-contained: the chunker function, its tests, and its dependencies. No other system component changes.
- Phase 2 is integration-quality polish: no new user-visible features, but prevents production failures on edge cases (minified files, missing package install).
- This ordering mirrors the recommended build order from ARCHITECTURE.md: test-driven RED→GREEN→wire→validate→lint.
- P2 features (`enum_declaration`, `chunk_name` dict field) are correctly deferred — they carry no blocking risk and can be added as low-cost extensions after core is stable.

### Research Flags

No phases require `/gsd:research-phase` during planning. All implementation details are resolved by this research.

Phases with standard patterns (skip additional research):
- **Phase 1:** All patterns are verified against official tree-sitter docs; the parity target (`chunk_python`) provides a concrete implementation template; node types verified against official `node-types.json`; API entry points confirmed against current PyPI releases
- **Phase 2:** Integration patterns (ImportError guards, performance thresholds) are standard Python; no novel library research needed; `uv run ruff check` and `uv run mypy src/` are the verification mechanism

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Versions verified against PyPI release dates (2025-09-25 and 2025-11-26); API verified against official tree-sitter docs, GitHub, and py-tree-sitter README; package choice is unambiguous (language-pack over standalone packages) |
| Features | HIGH | Existing Python chunker audited directly as parity target; TS node types verified against official `node-types.json`; feature boundaries backed by multiple independent sources (LanceDB RAG blog, supermemory code-chunk, cAST paper) |
| Architecture | HIGH | Integration points verified by direct code inspection of `chunker.py`, `indexer.py`, `schema.py`, and `test_chunker.py`; change surface is minimal and unambiguous; all unchanged components confirmed by inspection |
| Pitfalls | HIGH | All 7 critical pitfalls sourced from official docs, GitHub issues, and direct code inspection; prevention strategies are concrete and independently testable |

**Overall confidence:** HIGH

### Gaps to Address

One minor tension exists between STACK.md and ARCHITECTURE.md on the caching pattern. STACK.md recommends `@lru_cache` on `_get_parser(dialect)` using the language-pack's `get_parser()` directly. ARCHITECTURE.md shows module-level globals (`_TS_LANG: Language | None = None`) with a `_get_ts_language()` helper using direct package imports (`tree_sitter_typescript`). Both are functionally equivalent.

**Resolution:** Use `get_parser(dialect)` from `tree_sitter_language_pack` with `@lru_cache` — this is the simpler pattern, keeps the dependency surface to one import, and matches the stack recommendation. The architecture module-level global pattern is also acceptable if preferred.

No other gaps. Research is complete and internally consistent for planning purposes.

## Sources

### Primary (HIGH confidence)
- [PyPI: tree-sitter 0.25.2](https://pypi.org/project/tree-sitter/) — version, Python requirements, pre-compiled wheels confirmation
- [PyPI: tree-sitter-language-pack 0.13.0](https://pypi.org/project/tree-sitter-language-pack/) — supported languages, tree-sitter version requirement
- [GitHub: Goldziher/tree-sitter-language-pack README](https://github.com/Goldziher/tree-sitter-language-pack) — `get_parser()` API, dialect identifiers, typing support
- [py-tree-sitter official docs](https://tree-sitter.github.io/py-tree-sitter/) — Parser constructor, node attributes (`start_point`, `start_byte`, `has_error`), 0.21+ breaking API change
- [GitHub: py-tree-sitter README](https://github.com/tree-sitter/py-tree-sitter) — traversal API, Language/Parser usage, `Language.build_library` removal
- [GitHub: tree-sitter/tree-sitter-typescript](https://github.com/tree-sitter/tree-sitter-typescript) — node types verified; two grammar functions (`language_typescript()`, `language_tsx()`)
- [tree-sitter-typescript node-types.json (TSX)](https://github.com/tree-sitter/tree-sitter-typescript/blob/master/tsx/src/node-types.json) — official grammar source; all target node type strings confirmed
- Direct code inspection: `src/corpus_analyzer/ingest/chunker.py` — integration point at line 355; `chunk_python()` parity template
- Direct code inspection: `tests/ingest/test_chunker.py` — `TestChunkPython` structure as test parity template
- Direct code inspection: `store/schema.py` — `ChunkRecord` compatibility confirmed; no migration needed
- Direct code inspection: `ingest/indexer.py` — `chunk_file()` call site; no dispatch logic in indexer

### Secondary (MEDIUM confidence)
- [supermemory code-chunk library](https://github.com/supermemoryai/code-chunk) — entity types, metadata recommendations, import-exclusion rationale
- [LanceDB: Building RAG on codebases Part 1](https://lancedb.com/blog/building-rag-on-codebases-part-1/) — node type names, metadata field recommendations
- [cAST paper: Enhancing Code RAG with Structural Chunking via AST](https://arxiv.org/html/2506.15655v1) — empirical evidence for AST chunking quality gains over line-based
- [py-tree-sitter Discussion #231](https://github.com/tree-sitter/py-tree-sitter/discussions/231) — TypeScript/TSX parser setup edge cases
- [Tree-sitter packaging fragmentation article](https://ayats.org/blog/tree-sitter-packaging) — ABI mismatch context and history
- [DeepWiki: tree-sitter-typescript node types](https://deepwiki.com/tree-sitter/tree-sitter-typescript/1.2-getting-started) — node type list cross-referenced against grammar source
- [Better retrieval beats better models — AST chunking](https://sderosiaux.substack.com/p/better-retrieval-beats-better-models) — function-level granularity recommendation

---
*Research completed: 2026-02-24*
*Ready for roadmap: yes*

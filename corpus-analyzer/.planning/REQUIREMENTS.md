# Requirements: Corpus Analyzer

**Defined:** 2026-02-24
**Core Value:** Surface relevant agent files instantly — query an entire local agent library and get ranked, relevant results in under a second

## v1.5 Requirements

Requirements for milestone v1.5 TypeScript AST Chunking.

### Dependencies

- [x] **DEP-01**: `pyproject.toml` updated with `tree-sitter>=0.25.0` and `tree-sitter-language-pack>=0.13.0`; `uv sync` succeeds with pre-compiled wheels and no C toolchain

### Indexer

- [x] **IDX-01**: `chunk_file()` dispatch routes `.ts`, `.tsx`, `.js`, `.jsx` extensions to `chunk_typescript()`
- [x] **IDX-02**: `chunk_typescript()` extracts top-level constructs: `function_declaration`, `generator_function_declaration`, `class_declaration`, `abstract_class_declaration`, `interface_declaration`, `type_alias_declaration`, `lexical_declaration`, `enum_declaration`
- [x] **IDX-03**: `export_statement` nodes are unwrapped — `export function foo()` and `export class Bar` produce a chunk with the full exported text and the inner declaration's line boundaries
- [x] **IDX-04**: Grammar dispatched by extension: `typescript` for `.ts`, `tsx` for `.tsx` and `.jsx`, `javascript` for `.js`
- [x] **IDX-05**: Silent fallback to `chunk_lines()` when parse raises an exception or zero named constructs are extracted; does NOT fall back on `root_node.has_error` alone (tree-sitter is error-tolerant)
- [x] **IDX-06**: Returned chunk dict includes `chunk_name` field (name of extracted construct); indexer ignores the extra key today; forward-compatible with future `--construct` name filtering
- [x] **IDX-07**: Parser loader uses `@lru_cache` — grammar binaries loaded once per dialect per process (prevents 30s overhead on 500+ TS file corpora)
- [ ] **IDX-08**: Files exceeding 50,000 characters skip AST parse and fall back to `chunk_lines()` directly (guard against minified and generated files)
- [ ] **IDX-09**: `ImportError` guard in `chunk_file()` — if `tree-sitter` or `tree-sitter-language-pack` is absent, fall back to line chunking rather than raising at import time

### Tests

- [x] **TEST-01**: `TestChunkTypeScript` class at full parity with `TestChunkPython` — covers: function extraction, generator extraction, class extraction, interface extraction, type alias extraction, lexical declaration (arrow functions), enum extraction, export-unwrapping, line-range accuracy (1-indexed), JSX syntax in TSX grammar, non-ASCII identifiers, `has_error` partial tree (should NOT fall back), deliberate catastrophic parse failure (should fall back), size guard fallback
- [x] **TEST-02**: `TestChunkFile` dispatch assertions updated for all four extensions (`.ts`, `.tsx`, `.js`, `.jsx` → `chunk_typescript`); existing `.ts` line-based dispatch test updated to reflect new behaviour

### Quality

- [ ] **QUAL-01**: `uv run ruff check .` exits 0 and `uv run mypy src/` exits 0 after all changes; all 293+ existing tests continue to pass

## Future Requirements

### v2 Candidates

- **CHUNK-01–CHUNK-03**: Chunk-level search results with line ranges — high precision, deferred until result display layer is designed
- **IDX-10**: `chunk_name` persisted in LanceDB `ChunkRecord` schema (`ensure_schema_v4()`) — enables `--construct name:foo` filtering
- **IDX-11**: Method-level chunking (class methods as separate chunks) — only useful after chunk-level result display ships; methods without class context are unsearchable
- **IDX-12**: `.d.ts` ambient declaration handling — currently excluded at scanner level; could be indexed for API discovery use cases

## Out of Scope

| Feature | Reason |
|---------|--------|
| Method-level sub-chunking (class methods as separate chunks) | Methods without class context are unsearchable; Python chunker deliberately avoids this; defer until chunk-level display lands |
| Import statement chunks | Near-zero standalone search value; inflates chunk count and BM25 noise |
| JSDoc/comment extraction as separate chunks | Belong embedded in the function chunk text they annotate |
| Schema migration (`ensure_schema_v4`) | `ChunkRecord` shape is fully compatible; `chunk_name` field in returned dict costs nothing without a schema change |
| Web UI | CLI + MCP sufficient for target users |
| Hosted/cloud index | Local-only (privacy, simplicity) |
| Real-time file watching | Manual index refresh only; daemon complexity not justified yet |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DEP-01 | Phase 15 | Complete |
| IDX-01 | Phase 15 | Complete |
| IDX-02 | Phase 15 | Complete |
| IDX-03 | Phase 15 | Complete |
| IDX-04 | Phase 15 | Complete |
| IDX-05 | Phase 15 | Complete |
| IDX-06 | Phase 15 | Complete |
| IDX-07 | Phase 15 | Complete |
| IDX-08 | Phase 16 | Pending |
| IDX-09 | Phase 16 | Pending |
| TEST-01 | Phase 15 | Complete |
| TEST-02 | Phase 15 | Complete |
| QUAL-01 | Phase 16 | Pending |

**Coverage:**
- v1.5 requirements: 13 total
- Mapped to phases: 13
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-24*
*Last updated: 2026-02-24 after roadmap creation*

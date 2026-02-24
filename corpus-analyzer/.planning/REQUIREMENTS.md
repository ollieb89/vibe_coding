# Requirements: Corpus v2.1 Result Quality

**Defined:** 2026-02-24
**Core Value:** Surface relevant agent files instantly — query your entire local agent library and get ranked results in under a second

## v2.1 Requirements

### MCP Completeness

- [x] **CHUNK-03**: MCP `corpus_search` response includes `start_line`, `end_line`, and full untruncated `text` per result — self-contained unit of knowledge for LLM callers
- [ ] **SORT-01**: MCP `corpus_search` accepts `sort_by` parameter (same vocabulary as CLI: `relevance | construct | confidence | date | path`); translated to engine vocabulary via existing `_API_SORT_MAP`
- [ ] **NORM-01**: Scores normalised to 0–1 per query via min-max normalisation inside the search engine; Python API `SearchResult.score`, CLI display, and MCP response all see the same normalised value

### Method Sub-Chunking

- [x] **SUB-01**: Python AST chunker produces a class header chunk (`ClassName`) containing docstring + `__init__` body up to first non-assignment statement; replaces monolithic class chunk
- [x] **SUB-02**: Python AST chunker produces per-method chunks (`ClassName.method_name`) for each method in a class; `__init__`, `__str__`, etc. follow the same dot-notation
- [x] **SUB-03**: TypeScript AST chunker produces per-method chunks (`ClassName.method_name`) for `method_definition` nodes in class bodies; constructor becomes `ClassName.constructor`

### Name Filtering

- [x] **NAME-01**: `corpus search --name <fragment>` CLI flag; case-insensitive substring match on `chunk_name`; composable with all existing filter flags
- [x] **NAME-02**: MCP `corpus_search` accepts `name: Optional[str]` parameter; same case-insensitive substring match semantics
- [x] **NAME-03**: `corpus search --name foo` (no positional query) is valid; lists all chunks matching the name filter ordered by `--sort-by` (default: relevance)

### JSON Output

- [ ] **JSON-01**: `corpus search --output json` emits a valid JSON array to stdout; suppresses Rich formatting entirely; composable with all filter flags including `--name`

### Graph MCP

- [ ] **GRAPH-01**: MCP `corpus_graph` tool accepts `slug: str`; returns `upstream: list[str]` and `downstream: list[str]` neighbour paths; reuses `GraphStore` without new storage

### Quality

- [ ] **QUAL-01**: `pytest --cov --cov-branch` reports 85%+ branch coverage on `chunking/` modules (`chunker.py`, `py_chunker.py`, `ts_chunker.py`)
- [ ] **QUAL-02**: Parametrised zero-hallucination integration test: every stored `start_line`/`end_line` matches actual file content across `.md`, `.py`, and `.ts` fixtures

## v3 Requirements (Deferred)

### Ranking

- **RANK-01**: MMR-style result diversity — near-duplicate/same-file chunks penalised; architectural spread ensured
- **RANK-02**: Contiguous sub-chunk merging — adjacent method chunks from same file merged into single display entry
- **RANK-03**: Optional `--rerank` flag — two-stage cross-encoder/LLM re-ranking of top-20 results

### Graph Traversal

- **GEXP-01**: `corpus search --expand-graph` — results include immediate graph neighbours labelled `[Depends On]` / `[Imported By]`
- **GWALK-01**: `corpus graph --depth N` — recursive N-hop walk (default 2); hub nodes labelled with indegree count
- **GWALK-02**: Cycle detection (`visited: set[str]`) before any recursive graph walk
- **GCENT-01**: Centrality scoring — `corpus index` computes indegree centrality; high-centrality files receive score multiplier in hybrid search
- **GSCOPE-01**: `corpus search --within-graph <slug>` — +20% score boost for results in same graph component

### Multi-Query

- **MULTI-01**: Multiple `--query` flags — AND-intersection of semantic spaces via overfetch+score-sum
- **MULTI-02**: `--exclude-path <glob>` — structural negative filter on file path

### Cross-Source

- **XSRC-01**: CLI results display source name prefix
- **XSRC-02**: MCP `corpus_search` includes `source` field per result

## Out of Scope

| Feature | Reason |
|---------|--------|
| Chunk overlap / sliding window | AST-based chunking is non-overlapping by design; overlap requires different strategy |
| Streaming MCP responses | Chunk text bounded by 50K size guard; streaming complexity not justified yet |
| Persistent cross-query normalisation | Cross-query normalisation is misleading for hybrid scores; per-query is correct |
| Cloud/hosted index | Local-only (privacy, simplicity constraint) |
| Web UI | CLI + MCP sufficient for target users |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CHUNK-03 | Phase 19 | Complete |
| SUB-01 | Phase 20 | Complete |
| SUB-02 | Phase 20 | Complete |
| SUB-03 | Phase 21 | Complete |
| NAME-01 | Phase 22 | Complete |
| NAME-02 | Phase 22 | Complete |
| NAME-03 | Phase 22 | Complete |
| NORM-01 | Phase 23 | Pending |
| SORT-01 | Phase 23 | Pending |
| JSON-01 | Phase 24 | Pending |
| QUAL-01 | Phase 25 | Pending |
| QUAL-02 | Phase 25 | Pending |
| GRAPH-01 | Phase 25 | Pending |

**Coverage:**
- v2.1 requirements: 13 total
- Mapped to phases: 13
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-24*
*Last updated: 2026-02-24 after roadmap creation (Phases 19–25)*

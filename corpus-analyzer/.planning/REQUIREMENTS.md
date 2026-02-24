# Requirements: Corpus

**Defined:** 2026-02-24
**Core Value:** Surface relevant agent files instantly — query an entire local agent library and get ranked, relevant results in under a second

## v1 Requirements

### Graph Linking

- [x] **GRAPH-01**: Developer can query a file's upstream relationships (files that reference it) via `corpus graph <slug>`
- [x] **GRAPH-02**: Developer can query a file's downstream relationships (files it references) via `corpus graph <slug>`
- [x] **GRAPH-03**: `corpus index` automatically extracts and persists `## Related Skills` / `## Related Files` relationship edges per indexed file
- [x] **GRAPH-04**: Slug ambiguity is resolved by closest-prefix matching; duplicate slugs are warned during `corpus index`
- [x] **GRAPH-05**: Developer can list all duplicate slug collisions via `corpus graph --show-duplicates`

### Cleanup

- [x] **CLEAN-01**: Dead `use_llm_classification` parameter removed from `index_source()` function signature

## v2 Requirements

### Search Precision

- **SEARCH-EXT-01**: Search results include chunk-level line ranges for precise navigation
- **SEARCH-EXT-02**: TypeScript/JS files use AST-aware chunking (currently line-based)

### Graph Enhancements

- **GRAPH-EXT-01**: `corpus graph` supports depth-N traversal (multi-hop relationships)
- **GRAPH-EXT-02**: Graph data exposed via MCP tool for agent-driven dependency queries

## Out of Scope

| Feature | Reason |
|---------|--------|
| Hosted/cloud index | Local-only by design (privacy, simplicity) |
| Real-time file watching | Daemon complexity not justified; manual `corpus index` is sufficient |
| Web UI | CLI + MCP covers all target workflows |
| LLM rewriting | Retained in codebase but not the focus of this project direction |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| GRAPH-01 | Phase 7 | Complete |
| GRAPH-02 | Phase 7 | Complete |
| GRAPH-03 | Phase 7 | Complete |
| GRAPH-04 | Phase 7 | Complete |
| GRAPH-05 | Phase 7 | Complete |
| CLEAN-01 | Phase 8 | Complete |

**Coverage:**
- v1 requirements: 6 total
- Mapped to phases: 6
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-24*
*Last updated: 2026-02-24 after v1.2 roadmap creation*

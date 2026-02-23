# Requirements: Corpus

**Defined:** 2026-02-23
**Core Value:** Surface relevant agent files instantly — query your entire local agent library and get ranked results in under a second

## v1 Requirements

### Configuration

- [ ] **CONF-01**: User can configure source directories to index via `corpus.toml`
- [ ] **CONF-02**: User can set embedding model in config (local Ollama vs OpenAI/Cohere)
- [ ] **CONF-03**: User can configure file type inclusion/exclusion patterns per source
- [ ] **CONF-04**: Config supports named sources (e.g., "my-skills", "cloned-repos")
- [ ] **CONF-05**: User can run `corpus add <dir>` to append a source to `corpus.toml` from the CLI

### Ingestion

- [ ] **INGEST-01**: User can run `corpus index` to index all configured sources
- [ ] **INGEST-02**: Indexer supports `.md`, `.py`, `.ts`, `.js`, `.json`, `.yaml` file types
- [ ] **INGEST-03**: Indexer uses structure-aware chunking: heading-based for `.md`, AST-based for `.py`; line-based fallback for other types
- [ ] **INGEST-04**: Each chunk has a deterministic content-hash-based ID (re-indexing is idempotent, no duplicates)
- [ ] **INGEST-05**: Incremental indexing: only re-embeds files whose content has changed (mtime + sha256 check)
- [ ] **INGEST-06**: Per-chunk metadata stored: file path, line range, file type, source name, content hash, embedding model version, last-indexed timestamp
- [ ] **INGEST-07**: Re-index detects and removes stale chunks for deleted or moved files (no ghost documents)

### Search

- [ ] **SEARCH-01**: User can search with a natural language query and get ranked results
- [ ] **SEARCH-02**: Search uses hybrid ranking: vector similarity + BM25 keyword, fused via RRF
- [ ] **SEARCH-03**: User can filter results by source name
- [ ] **SEARCH-04**: User can filter results by file type (`.md`, `.py`, etc.)
- [ ] **SEARCH-05**: Result format varies by interface: snippets for CLI, full content for MCP, structured objects for Python API

### Classification

- [ ] **CLASS-01**: Indexer classifies each file by agent construct type: `skill`, `prompt`, `workflow`, `agent_config`, `code`, `documentation`
- [ ] **CLASS-02**: Construct type is stored as metadata per chunk and is filterable at query time
- [ ] **CLASS-03**: User can filter search results by construct type

### AI Summaries

- [ ] **SUMM-01**: Indexer generates an AI summary for each indexed file at index time (using Ollama)
- [ ] **SUMM-02**: Summaries are embedded and indexed alongside raw chunk text to improve retrieval on short or poorly-named files
- [ ] **SUMM-03**: Summary generation is skippable per source (config flag) for large repos where LLM cost is prohibitive

### CLI

- [ ] **CLI-01**: `corpus index` indexes all configured sources (respects incremental)
- [ ] **CLI-02**: `corpus search "<query>"` returns ranked results with file path, snippet, and score
- [ ] **CLI-03**: `corpus search` supports `--source`, `--type`, `--construct`, `--limit` flags
- [ ] **CLI-04**: `corpus status` shows index stats: file count, chunk count, last indexed, embedding model in use
- [ ] **CLI-05**: `corpus add <dir> [--name <name>]` appends a directory to `corpus.toml` as a named source

### MCP Server

- [ ] **MCP-01**: Corpus exposes a FastMCP server registerable with Claude Code via stdio transport
- [ ] **MCP-02**: MCP `search` tool returns full file content for top matches (not just snippets)
- [ ] **MCP-03**: MCP `search` tool accepts: `query` (required), `source` (optional), `type` (optional), `construct` (optional), `top_k` (optional, default 5)
- [ ] **MCP-04**: MCP server writes nothing to stdout; all logging goes to stderr
- [ ] **MCP-05**: MCP tool input schema uses top-level `type: "object"` with no Union types (Claude Code compatibility)
- [ ] **MCP-06**: Embedding model is pre-warmed at MCP server startup to eliminate cold-start latency

### Python API

- [ ] **API-01**: `from corpus import search` accepts a query string and returns structured results: `path`, `file_type`, `construct_type`, `summary`, `score`, `snippet`
- [ ] **API-02**: `from corpus import index` triggers incremental re-index programmatically
- [ ] **API-03**: Python API results use the same underlying query engine as CLI and MCP (no divergence)

## v2 Requirements

### Chunk-Level Results

- **CHUNK-01**: Search returns chunk-level results (specific line ranges) rather than file-level
- **CHUNK-02**: MCP tool returns only the relevant chunk content, not the full file
- **CHUNK-03**: CLI shows line range alongside file path for chunk-level hits

### Enhanced Indexing

- **IDX-01**: TypeScript/JavaScript AST-aware chunking (via tree-sitter)
- **IDX-02**: Automatic re-index on file change (file watcher daemon)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Hosted/cloud index | Local-only for v1 — privacy and simplicity |
| Web UI | CLI + MCP sufficient for target users (developers, agents) |
| Real-time file watching | Daemon complexity; explicit `corpus index` is sufficient for v1 |
| LLM rewriting | corpus-analyzer original feature retained but not the focus |
| Multi-user / shared index | Single-user local tool only |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CONF-01 | Phase 1 | Pending |
| CONF-02 | Phase 1 | Pending |
| CONF-03 | Phase 1 | Pending |
| CONF-04 | Phase 1 | Pending |
| CONF-05 | Phase 1 | Pending |
| INGEST-01 | Phase 1 | Pending |
| INGEST-02 | Phase 1 | Pending |
| INGEST-03 | Phase 1 | Pending |
| INGEST-04 | Phase 1 | Pending |
| INGEST-05 | Phase 1 | Pending |
| INGEST-06 | Phase 1 | Pending |
| INGEST-07 | Phase 1 | Pending |
| SEARCH-01 | Phase 2 | Pending |
| SEARCH-02 | Phase 2 | Pending |
| SEARCH-03 | Phase 2 | Pending |
| SEARCH-04 | Phase 2 | Pending |
| SEARCH-05 | Phase 2 | Pending |
| CLASS-01 | Phase 2 | Pending |
| CLASS-02 | Phase 2 | Pending |
| CLASS-03 | Phase 2 | Pending |
| SUMM-01 | Phase 2 | Pending |
| SUMM-02 | Phase 2 | Pending |
| SUMM-03 | Phase 2 | Pending |
| CLI-01 | Phase 2 | Pending |
| CLI-02 | Phase 2 | Pending |
| CLI-03 | Phase 2 | Pending |
| CLI-04 | Phase 2 | Pending |
| CLI-05 | Phase 2 | Pending |
| MCP-01 | Phase 3 | Pending |
| MCP-02 | Phase 3 | Pending |
| MCP-03 | Phase 3 | Pending |
| MCP-04 | Phase 3 | Pending |
| MCP-05 | Phase 3 | Pending |
| MCP-06 | Phase 3 | Pending |
| API-01 | Phase 3 | Pending |
| API-02 | Phase 3 | Pending |
| API-03 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 37 total
- Mapped to phases: 37
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-23*
*Last updated: 2026-02-23 after roadmap creation*

# Roadmap: Corpus

## Overview

Corpus pivots the existing corpus-analyzer codebase into a local semantic search engine for AI agent libraries. Phase 1 builds the embedding pipeline and index storage foundation that everything else depends on. Phase 2 delivers the full search experience — hybrid BM25+vector retrieval, agent construct classification, AI summaries, and the CLI interface — making the index queryable end-to-end. Phase 3 exposes the search engine to code agents via an MCP server and adds a Python API, completing the v1 product.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation** - Embedding pipeline, LanceDB schema, source config, and ingestion pipeline
- [ ] **Phase 2: Search Core** - Hybrid search engine, construct classification, AI summaries, and CLI commands
- [ ] **Phase 3: Agent Interfaces** - MCP server, Python API, and index status UX

## Phase Details

### Phase 1: Foundation
**Goal**: A working ingestion pipeline that indexes configured source directories into a queryable LanceDB store, with incremental re-indexing and no ghost documents
**Depends on**: Nothing (first phase)
**Requirements**: CONF-01, CONF-02, CONF-03, CONF-04, CONF-05, INGEST-01, INGEST-02, INGEST-03, INGEST-04, INGEST-05, INGEST-06, INGEST-07
**Success Criteria** (what must be TRUE):
  1. User can run `corpus index` and all configured source directories are indexed into LanceDB
  2. Running `corpus index` a second time on unchanged files does not re-embed anything (mtime + hash check)
  3. Deleting a file from disk and running `corpus index` removes its chunks from the index (no ghost documents)
  4. User can run `corpus add <dir>` to append a directory to `corpus.toml` as a named source with optional `--name`
  5. All supported file types (`.md`, `.py`, `.ts`, `.js`, `.json`, `.yaml`) are extracted and embedded with structure-aware chunking
**Plans**: 5 plans

Plans:
- [ ] 01-01-PLAN.md — TDD: LanceDB ChunkRecord schema and make_chunk_id() helper
- [ ] 01-02-PLAN.md — TDD: CorpusConfig Pydantic models and TOML load/save I/O
- [ ] 01-03-PLAN.md — TDD: File chunker (md/py/lines) and scanner with change detection
- [ ] 01-04-PLAN.md — Embedder (OllamaEmbedder) and core indexer (CorpusIndex) engine
- [ ] 01-05-PLAN.md — CLI commands: corpus add and corpus index with progress bar

### Phase 2: Search Core
**Goal**: Users can query the index with natural language and get ranked, relevant results with snippets — filterable by source, file type, and construct type
**Depends on**: Phase 1
**Requirements**: SEARCH-01, SEARCH-02, SEARCH-03, SEARCH-04, SEARCH-05, CLASS-01, CLASS-02, CLASS-03, SUMM-01, SUMM-02, SUMM-03, CLI-01, CLI-02, CLI-03, CLI-04, CLI-05
**Success Criteria** (what must be TRUE):
  1. User can run `corpus search "<query>"` and get ranked results with file path, snippet, and score
  2. Search results combine vector similarity and BM25 keyword matching — exact names and semantic queries both return relevant results
  3. User can filter results with `--source`, `--type`, `--construct`, and `--limit` flags
  4. Each indexed file has a construct type label (`skill`, `prompt`, `workflow`, `agent_config`, `code`, `documentation`) visible in results
  5. `corpus status` shows file count, chunk count, last indexed timestamp, and embedding model in use
**Plans**: 5 plans

Plans:
- [ ] 02-01-PLAN.md — Schema extension (ChunkRecord + SourceConfig) and Wave 0 test scaffolds
- [ ] 02-02-PLAN.md — TDD: CorpusSearch hybrid search engine (BM25+vector+RRF, filters, status)
- [ ] 02-03-PLAN.md — TDD: ConstructClassifier (rule-based + LLM fallback) and extract_snippet formatter
- [ ] 02-04-PLAN.md — TDD: Summarizer and CorpusIndex.index_source() extension for classify+summarize
- [ ] 02-05-PLAN.md — CLI commands: corpus search and corpus status with Rich output

### Phase 3: Agent Interfaces
**Goal**: Claude Code and other agents can search the corpus index programmatically via MCP, and Python scripts can query it via `from corpus import search`
**Depends on**: Phase 2
**Requirements**: MCP-01, MCP-02, MCP-03, MCP-04, MCP-05, MCP-06, API-01, API-02, API-03
**Success Criteria** (what must be TRUE):
  1. Claude Code can call a `corpus_search` MCP tool and receive full file content for top matches
  2. The MCP server starts without blocking and the first search query completes without cold-start latency (embedding pre-warmed at startup)
  3. `from corpus import search` returns structured results with `path`, `file_type`, `construct_type`, `summary`, `score`, and `snippet`
  4. MCP server writes nothing to stdout; all logging goes to stderr (Claude Code compatibility)
**Plans**: 3 plans

Plans:
- [ ] 03-01-PLAN.md — pyproject.toml setup (fastmcp dep + corpus entry point) + FastMCP server module with lifespan pre-warm and corpus_search tool
- [ ] 03-02-PLAN.md — Python public API (SearchResult, search(), index()) + corpus re-export package + enhanced corpus status command
- [ ] 03-03-PLAN.md — corpus mcp serve CLI subcommand + unit tests for MCP server and Python API

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 0/5 | Not started | - |
| 2. Search Core | 0/TBD | Not started | - |
| 3. Agent Interfaces | 0/3 | Not started | - |

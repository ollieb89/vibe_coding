# Project Research Summary

**Project:** Corpus — Local Semantic Search Engine for AI Agent Libraries
**Domain:** Hybrid vector + BM25 search engine with MCP server integration
**Researched:** 2026-02-23
**Confidence:** HIGH

## Executive Summary

Corpus is a local, embedded semantic search engine purpose-built for AI agent library files (skills, workflows, prompts, code). The product extends the existing corpus-analyzer pipeline — which already handles extraction, classification, and quality scoring — by adding vector embeddings, hybrid search, and an MCP server interface so that code agents (primarily Claude Code) can retrieve relevant files without human mediation. Research confirms this is a well-understood problem space: LanceDB provides a battle-tested embedded vector store with native BM25 via tantivy and built-in Reciprocal Rank Fusion, while FastMCP (now bundled in the official `mcp` SDK) makes the agent interface straightforward. The dominant pattern across comparable tools (QMD, DeepContext, files-db) is: index offline with incremental mtime+hash detection, query at runtime with hybrid retrieval, expose via MCP over stdio.

The recommended approach favors simplicity and local-first operation throughout. LanceDB replaces the sqlite-vec alternative considered in ARCHITECTURE.md, because it ships hybrid search, BM25 via tantivy, and RRF reranking natively — eliminating the need to implement fusion SQL manually. Ollama is the default embedding provider (nomic-embed-text, 768-dim), keeping the tool fully offline. The embedding provider abstraction is a Protocol-based pluggable interface so OpenAI or sentence-transformers can be swapped in without touching search logic. The MCP server is a thin read-only wrapper over a `SearchEngine` class; all search logic lives in `SearchEngine` so CLI and MCP share identical behavior.

The primary risks are well-documented and have clear mitigations. Embedding model mismatch (indexing with model A, querying with model B) causes silent quality degradation and must be prevented by storing the model name in the database and validating it on every query — this cannot be retrofitted later. SQLite concurrency during simultaneous index + query requires WAL mode and a 5-second busy timeout, also set at database initialization. AST-aware chunking for code files (vs. character splitting) must be decided before any embeddings are generated because changing chunking strategy forces a full reindex. These three schema/architecture decisions must be locked in Phase 1.

---

## Key Findings

### Recommended Stack

LanceDB (0.29.x) is the clear choice for the vector store: it is embedded (no server process), stores vectors alongside metadata in a Lance format file, provides FTS via tantivy for BM25, and includes a built-in `RRFReranker` — eliminating the need to write fusion SQL or run a separate search process. The `mcp` package (1.26.x) includes FastMCP with decorator-based tool registration and handles both stdio (Claude Code default) and streamable-HTTP transports. Sentence-transformers (5.2.x) provides the local non-Ollama embedding path; `all-MiniLM-L6-v2` runs on CPU without a GPU. All tooling (ruff, mypy, pytest, uv) is already configured.

**Core technologies:**
- **LanceDB 0.29.x**: Vector store + hybrid search — embedded, native BM25 via tantivy, built-in RRF reranker; designed as "SQLite for AI"
- **mcp 1.26.x (FastMCP)**: MCP server — official Anthropic SDK, decorator-based tools, stdio transport for Claude Code
- **sentence-transformers 5.2.x**: Local CPU embeddings — fallback when Ollama is unavailable; all-MiniLM-L6-v2 fast on CPU
- **ollama 0.6.x**: Default embedding provider — nomic-embed-text (768-dim) already available; embed() added in 0.4.x
- **pydantic 2.6.x**: Embedding provider config — already in use; models for OllamaProvider, OpenAIProvider
- **tantivy 0.25.x**: BM25/FTS index — LanceDB dependency; pin explicitly to avoid breakage

See `/home/ollie/Development/Tools/vibe_coding/corpus-analyzer/.planning/research/STACK.md` for full alternatives analysis.

### Expected Features

The core value proposition is: surface relevant agent files instantly with results an agent can immediately act on (absolute path, score, snippet, metadata). Features derived from analysing QMD, DeepContext, and files-db reveal a clear MVP boundary — hybrid search + MCP exposure + incremental indexing are the minimum to be useful; classifier-based filters (category, domain, quality) are low-cost differentiators the existing pipeline provides for free.

**Must have (table stakes):**
- Hybrid search (BM25 + vector, RRF fusion) — pure keyword misses semantic matches; pure vector misses exact names
- Absolute file path + relevance score (0.0–1.0) + snippet in every result — minimum result shape for agent consumption
- Multi-file-type indexing: `.md`, `.py`, `.json`, `.yaml` — covers 95%+ of agent library files
- Incremental indexing with mtime + SHA-256 hash detection — large repos make full reindex impractical
- MCP server with `corpus_search` tool — primary interface for code agents
- Source directory management (`corpus add <dir>` + corpus.toml) — without this, every index call requires manual path specification
- `top_k` parameter (default 5) — token budget management; non-negotiable for MCP consumption

**Should have (competitive differentiators — low-cost given existing pipeline):**
- Document category in results — agents understand what a file is (howto, runbook, persona) without reading it
- Domain tag filter — filter to `domain:frontend` or `domain:ai`; DomainTag enum already exists
- File type / extension filter — reduces signal-to-noise for type-specific queries
- Quality score / gold standard filter — agents prefer exemplary files; quality_score + is_gold_standard already exist
- Directory scope filter — prevents cross-repo confusion for multi-repo collections
- Python API — thin wrapper over SearchEngine; natural for the Python codebase

**Defer (v2+):**
- Chunk-level results — highest value, highest complexity; validate file-level search first
- Cloud embedding providers (OpenAI, Cohere) — Ollama works for v1; add when offline constraint is validated
- Source-aware named search — premature without knowing real collection sizes

**Explicit anti-features (do not build):**
- Real-time file watching — daemon complexity; explicit `corpus index --refresh` is sufficient
- Web UI — CLI + MCP is the right interface; web UI adds server + frontend for zero benefit
- LLM query expansion — kills sub-second latency target; hybrid search handles synonyms via embeddings

See `/home/ollie/Development/Tools/vibe_coding/corpus-analyzer/.planning/research/FEATURES.md` for MCP tool interface design and competitor analysis.

### Architecture Approach

The architecture is two cleanly separated pipelines sharing a LanceDB persistence layer as the boundary. The write path (indexing) runs on demand; the read path (search) is stateless and never writes. All search logic centralizes in a `SearchEngine` class that both the CLI and MCP server consume as thin wrappers — this ensures consistent behavior and testability without an MCP client. The `EmbeddingProvider` is a Protocol-based abstraction used in both pipelines: batched at index time, single-query at search time.

**Major components:**
1. **EmbeddingProvider (embeddings/)** — Pluggable abstraction over Ollama, OpenAI, sentence-transformers; `embed()` and `embed_batch()` contract
2. **IndexPipeline (indexing/)** — Orchestrates scan → extract → embed → store; IncrementalTracker handles mtime/hash detection
3. **SearchEngine (search/)** — Hybrid search orchestration: embed query, run vector + BM25 legs in parallel, RRF fusion, return SearchResult
4. **MCP Server (mcp/)** — Single thin file; instantiates SearchEngine, exposes `corpus_search` tool via FastMCP stdio transport
5. **SourceConfig (config.py)** — Reads/writes corpus.toml; tracks which directories are indexed and their embedding model
6. **CLI (cli.py)** — Extended with `index`, `search`, `add`, `status` commands; depends on SearchEngine + IndexPipeline

**Build order (strict dependency chain):**
EmbeddingProvider → LanceDB schema → IndexPipeline → SearchEngine → CLI → MCP Server

See `/home/ollie/Development/Tools/vibe_coding/corpus-analyzer/.planning/research/ARCHITECTURE.md` for data flow diagrams and anti-patterns.

### Critical Pitfalls

1. **Embedding model mismatch (silent quality failure)** — Store the model name + version in the LanceDB table metadata at index creation; validate against current config on every query; raise an explicit error if they differ. Never allow silent re-use of a stale index. Must be designed into Phase 1 schema; cannot be retrofitted.

2. **BM25 + vector raw score fusion** — Never combine raw BM25 scores with cosine similarity scores; BM25 dominates (unbounded vs 0–1). Always use RRF: `score = 1/(60 + rank_bm25) + 1/(60 + rank_vector)`. LanceDB's `RRFReranker` implements this natively — use it rather than implementing manually.

3. **SQLite concurrency / database locked** — Set `PRAGMA busy_timeout = 5000` and `PRAGMA journal_mode = WAL` on all connections at database initialization. Commit indexing in batches of 100–500 documents, not in a single transaction. This must be set at Phase 1 database setup; later retrofitting causes data loss risk.

4. **MCP server cold-start latency** — After Ollama's 5-minute `KEEP_ALIVE` expires, the first search takes 5–15 seconds; Claude Code agents time out. Set `OLLAMA_KEEP_ALIVE=-1` and add a pre-warm embed call at MCP server startup. Design this into Phase 3 before writing the server.

5. **Character-boundary code chunking** — Fixed-size character splitting breaks function definitions across chunk boundaries; embedding quality degrades; search misses known functions. Use AST-aware splitting for `.py` files (built-in `ast` module, already used in extractors) and heading-boundary splitting for `.md`. This must be decided before any embeddings are generated; changing strategy requires a full reindex.

6. **FTS5 BM25 sign convention** — SQLite FTS5 `bm25()` returns negative values; `ORDER BY bm25(...)` (ascending) is correct for relevance. `ORDER BY bm25(...) DESC` returns worst matches. Verify with a smoke test in Phase 2.

See `/home/ollie/Development/Tools/vibe_coding/corpus-analyzer/.planning/research/PITFALLS.md` for verification checklists and recovery strategies.

---

## Implications for Roadmap

Research establishes a clear build order driven by hard dependencies: the embedding provider and LanceDB schema must exist before any indexing code can run; IndexPipeline must complete before SearchEngine is meaningful; SearchEngine must be stable before CLI or MCP server are built on top of it. The classifier-based metadata filters (category, domain tags, quality score) are free given the existing pipeline — they require only exposure as search parameters, not new classifier work. Chunk-level results are deliberately deferred because they require re-architecting the embedding step and validating file-level search first.

### Phase 1: Foundation — Embedding Pipeline + LanceDB Schema

**Rationale:** Everything downstream depends on this. The embedding provider abstraction, LanceDB table schema (with model name metadata), and incremental change tracker must be locked in before any indexing code is written. Pitfalls 1, 3, 5, and 6 all require decisions made in this phase to be present from the start.
**Delivers:** Working embedding pipeline (Ollama default + provider abstraction); LanceDB schema with FTS + vector tables; IncrementalTracker with mtime/hash detection; corpus.toml source config; model-name validation on query
**Addresses:** Incremental indexing, multi-file-type extraction, source directory management
**Avoids:** Embedding model mismatch (stored model name in schema); SQLite concurrency (WAL + busy_timeout at init); character chunking (AST-aware chunking strategy locked before first embed); chunk strategy version stored in schema
**Needs research-phase:** No — LanceDB FTS, tantivy integration, and schema patterns are well-documented

### Phase 2: Hybrid Search Core

**Rationale:** Search is the primary value delivery. Build vector-only search first to validate recall, then layer in FTS + RRF. The "Looks Done But Isn't" checklist in PITFALLS.md provides acceptance criteria. CLI search command makes the pipeline end-to-end testable without an MCP client.
**Delivers:** `SearchEngine` with hybrid BM25 + vector search via LanceDB RRFReranker; `corpus search` CLI command with rich table output; SearchResult model with path, score, snippet, category, domain_tags, quality_score; `top_k` parameter; `corpus index` CLI command wired to IndexPipeline
**Uses:** LanceDB RRFReranker (built-in, no custom fusion code); EmbeddingProvider from Phase 1
**Implements:** SearchEngine, RRF fusion, snippet extraction
**Avoids:** Raw score combination (use LanceDB RRFReranker); FTS5 sign convention bug (unit test verifies ranking direction)
**Needs research-phase:** No — hybrid search with LanceDB is verified via official docs and examples

### Phase 3: MCP Server Integration

**Rationale:** MCP is a thin wrapper over SearchEngine, which is now complete and tested. The server is the primary interface for Claude Code. Cold-start latency and pre-warming must be designed before writing the server, not added as an afterthought.
**Delivers:** FastMCP server with `corpus_search` tool (stdio transport); structured JSON output per MCP spec; pre-warm embed call at startup; `OLLAMA_KEEP_ALIVE` documentation; Claude Code mcp.json configuration instructions
**Uses:** mcp 1.26.x (FastMCP); SearchEngine from Phase 2
**Implements:** mcp/server.py (thin wrapper only — all logic in SearchEngine)
**Avoids:** MCP cold-start latency (pre-warm at startup); logic in MCP layer (SearchEngine owns all search logic); sensitive path exposure (source-dir allow-list validation on tool inputs)
**Needs research-phase:** No — FastMCP stdio pattern is well-documented via official SDK

### Phase 4: Search Quality Filters + Status UX

**Rationale:** The classifier-based filters (category, domain, gold standard) are near-zero-cost additions because the pipeline already produces these fields. This phase adds them as search parameters and improves observability with `corpus status`. These are v1.x features, not MVP blockers.
**Delivers:** Category filter, domain tag filter, file type filter, gold standard filter, directory scope filter in `corpus_search`; `corpus status` command showing last index time, file count, unindexed file count, embedding model, chunk strategy version; Python API (thin SearchEngine wrapper)
**Addresses:** Domain tag filter, quality score filter, directory scope filter, is_gold_standard filter (all P2 from FEATURES.md)
**Avoids:** Stale index UX (corpus status shows unindexed file count); no progress feedback during indexing (progress bar/count added)

### Phase 5: Chunk-Level Results (v2 Candidate)

**Rationale:** Chunk-level results are the highest-value differentiator but require re-embedding at chunk granularity, which is architecturally more complex and requires validating file-level search quality first. Deferred until Phase 1–4 are stable and real agent usage is observed.
**Delivers:** Chunk-level embeddings stored separately from document embeddings; chunk-level search returns the specific section that matched; reduced token consumption in agent context windows
**Addresses:** Chunk-level results (P3 from FEATURES.md)
**Needs research-phase:** Yes — chunk-level search with LanceDB needs deeper validation of how chunk and document tables interact in a hybrid query

### Phase Ordering Rationale

- Phase 1 must precede everything: embedding provider and schema decisions cannot be changed without full reindex
- Phase 2 before Phase 3: MCP is meaningless without a tested search engine; building MCP first would put logic in the wrong layer
- Phase 2 delivers CLI search: this is testable end-to-end without an MCP client, reducing integration risk
- Phase 4 after Phase 3: classifier filters add value but are not needed to validate search quality; defer until MCP integration is confirmed working
- Phase 5 deferred: file-level search must prove its value before chunk-level architecture is justified

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 5 (chunk-level results):** LanceDB chunk + document hybrid query patterns need validation; chunk embedding storage schema unclear

Phases with standard patterns (skip research-phase):
- **Phase 1:** LanceDB schema + tantivy FTS patterns verified via official docs; incremental mtime/hash tracking is standard
- **Phase 2:** Hybrid search with LanceDB RRFReranker is documented with examples; snippet extraction from FTS is standard
- **Phase 3:** FastMCP stdio pattern verified via official SDK and Claude Code integration docs
- **Phase 4:** Classifier filters are trivial additions to existing SearchEngine parameters

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All package versions verified via PyPI; LanceDB FTS + RRF patterns verified via official docs and Context7; FastMCP API verified via official SDK |
| Features | MEDIUM-HIGH | MCP spec verified; search feature patterns from 3 real tools (QMD, DeepContext, files-db); agent-specific patterns from ecosystem observation |
| Architecture | HIGH | Indexing/search/hybrid patterns HIGH; MCP server pattern HIGH; source config management MEDIUM (standard patterns, no single canonical reference) |
| Pitfalls | HIGH | Most pitfalls verified via official docs (SQLite WAL, FTS5 sign convention, sqlite-vec ANN status) or high-confidence issue trackers |

**Overall confidence:** HIGH

### Gaps to Address

- **sqlite-vec ANN index maturity:** sqlite-vec v0.1.x is brute-force only; ANN index support is planned but not stable as of early 2026. LanceDB mitigates this (built-in HNSW), but if sqlite-vec is used as a fallback, plan for migration. Design indexer with an abstraction layer that allows the vector backend to be swapped.
- **LanceDB tantivy version pinning:** LanceDB docs previously pinned tantivy==0.20.1 for older versions; 0.25.x should work with 0.29.x but must be verified at integration time. Pin explicitly and test.
- **Source config management canonical pattern:** No single authoritative Python pattern for corpus.toml-style source config. Derived from multiple systems (CocoIndex, Open Semantic Search). The proposed corpus.toml structure is reasonable but may need adjustment based on real usage patterns.
- **Chunk-level search in LanceDB:** FEATURES.md identifies chunk-level results as a P3 high-value feature. How to store chunk embeddings separately from document embeddings in LanceDB and run a hybrid query across both tables requires validation before Phase 5 planning.
- **Ollama cold-start in Claude Code context:** The pre-warm strategy (no-op embed at MCP startup) mitigates cold start, but Claude Code's exact process lifecycle for stdio MCP servers needs confirmation. Test this behavior explicitly in Phase 3.

---

## Sources

### Primary (HIGH confidence)
- `/lancedb/lancedb` (Context7) — hybrid search, FTS, RRF reranker, sentence-transformer integration
- `/modelcontextprotocol/python-sdk` (Context7) — FastMCP API, transports, stdio integration
- `/asg017/sqlite-vec` (Context7) — installation, KNN API, alpha/brute-force status
- [MCP Tools Specification 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) — tool schema, structuredContent, outputSchema
- [PyPI: lancedb 0.29.2](https://pypi.org/project/lancedb/) — latest version confirmed
- [PyPI: mcp 1.26.0](https://pypi.org/project/mcp/) — latest version confirmed
- [Ollama embedding models](https://ollama.com/blog/embedding-models) — nomic-embed-text, mxbai-embed-large confirmed
- [SQLite WAL docs](https://sqlite.org/wal.html) — concurrency model, checkpoint behaviour
- [sqlite-vec RRF hybrid search example](https://github.com/asg017/sqlite-vec/blob/main/examples/nbc-headlines/3_search.ipynb) — verified SQL pattern
- [DagsHub: Vector database pitfalls](https://dagshub.com/blog/common-pitfalls-to-avoid-when-using-vector-databases/) — embedding mismatch, score fusion
- [ParadeDB: Hybrid search in PostgreSQL](https://www.paradedb.com/blog/hybrid-search-in-postgresql-the-missing-manual) — BM25 sign convention, RRF

### Secondary (MEDIUM confidence)
- [QMD: local hybrid search tool](https://github.com/tobi/qmd) — competitor feature reference
- [DeepContext MCP Server](https://skywork.ai/skypage/en/deepcontext-mcp-server-ai-engineers/1980841962807820288) — incremental indexing pattern, snippet design
- [Weaviate: Hybrid search explained](https://weaviate.io/blog/hybrid-search-explained) — RRF rationale
- [Elastic hybrid search guide](https://www.elastic.co/what-is/hybrid-search) — fusion pattern confirmation
- [FastMCP docs / Claude Code integration](https://gofastmcp.com/integrations/claude-code) — stdio transport confirmed
- [Firecrawl: Best chunking strategies for RAG](https://www.firecrawl.dev/blog/best-chunking-strategies-rag-2025) — AST-aware chunking rationale
- [supermemory.ai: AST-aware code chunking](https://supermemory.ai/blog/building-code-chunk-ast-aware-code-chunking/) — Python AST chunking approach
- [MCP Server slow startup (Gemini CLI issue)](https://github.com/google-gemini/gemini-cli/issues/4544) — cold-start latency measurements

### Tertiary (LOW confidence)
- [CocoIndex incremental indexing](https://medium.com/@cocoindex.io/) — single vendor blog; incremental indexing pattern independently confirmed elsewhere

---
*Research completed: 2026-02-23*
*Ready for roadmap: yes*

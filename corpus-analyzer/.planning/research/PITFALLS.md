# Pitfalls Research

**Domain:** Local semantic search engine for AI agent libraries (hybrid vector + BM25, MCP server, Python API)
**Researched:** 2026-02-23
**Confidence:** HIGH (embedding/BM25 fusion, SQLite concurrency) | MEDIUM (MCP lifecycle, chunking) | LOW (sqlite-vec ANN specifics)

---

## Critical Pitfalls

### Pitfall 1: Embedding Model Mismatch Between Index and Query Time

**What goes wrong:**
If the embedding model used to index documents differs from the model used at query time — whether due to a config change, a model update, or provider swap (Ollama local vs OpenAI) — the vector space is semantically incompatible. The cosine similarities returned become meaningless. The index appears to work (no crash) but returns irrelevant results consistently. This is a silent failure.

**Why it happens:**
The model used for indexing is not stored alongside the index. Developers change the model in config (e.g., switch from `all-minilm` to `nomic-embed-text`) without rebuilding the index, not realizing the vector spaces are incompatible. Dimension mismatches at least throw an error (`Index query vector has 1024 dimensions, but indexed vectors have 384`); same-dimension-different-model mismatches silently degrade quality.

**How to avoid:**
- Store the embedding model name AND its version in the database at index creation time (e.g., in a `corpus_meta` table).
- On every query, check the stored model against the current configured model and raise an error if they differ.
- Provide an explicit `corpus reindex --force` command; never allow silent re-use of a stale index with a new model.
- Log which model produced each batch of embeddings at row level in the `documents` table.

**Warning signs:**
- All queries return the same set of "vaguely similar" documents regardless of query content.
- Search results include documents with no apparent relevance to query terms.
- Similarity scores cluster tightly (e.g., all between 0.45 and 0.55) — this indicates the vectors live in different spaces.
- Dimension mismatch error on first query after changing config.

**Phase to address:**
Phase 1 (Embedding pipeline) — the model-name storage and validation must be designed in before any indexing code is written. Retrofitting this is painful.

---

### Pitfall 2: BM25 + Vector Score Fusion Using Raw Score Combination

**What goes wrong:**
Directly combining BM25 scores with cosine similarity scores produces broken rankings. BM25 scores are unbounded (can be 0, 10, 100+) while cosine similarity is bounded [0, 1]. The BM25 score dominates, making the vector component irrelevant. The result feels like pure keyword search — exact filename matches always win, semantic similarity is ignored.

**Why it happens:**
Score normalization seems like an obvious fix: normalize both to [0, 1] and add. But normalized scores are relative to the current result set, not absolute. If BM25 returns one strong match and nine weak ones, normalization artificially inflates the weak ones. If all vector results are equally mediocre, normalization can't distinguish them.

**How to avoid:**
Use **Reciprocal Rank Fusion (RRF)** instead of score fusion. RRF combines rank positions, not raw scores: `score = 1/(k + rank_bm25) + 1/(k + rank_vector)` where `k=60` is the standard constant. This is stable regardless of score scale, handles empty results on one side gracefully (that side contributes 0), and is the approach used by Weaviate, Qdrant, and OpenSearch in 2025.

**Warning signs:**
- Exact filename matches always appear at rank 1 regardless of query meaning.
- Semantic queries ("find authentication helpers") return lexically matching but semantically irrelevant results.
- Changing vector weight in a linear formula has no visible effect on ranking.
- All query results are the same as pure BM25 results.

**Phase to address:**
Phase 2 (Hybrid search) — build RRF from day one; never implement raw score combination even as a prototype.

---

### Pitfall 3: SQLite "Database is Locked" During Concurrent Index + Query

**What goes wrong:**
Running `corpus index` in one terminal while querying from the MCP server or CLI in another produces `sqlite3.OperationalError: database is locked`. The indexing process holds a write lock; the query process times out. In WAL mode this is less common for reads-during-writes, but it still occurs if the indexer opens a long write transaction (e.g., batch inserting 10k embeddings in one transaction).

**Why it happens:**
SQLite with WAL mode allows concurrent reads during writes, but only one writer at a time. If the indexer wraps the entire corpus in a single `BEGIN` transaction (for speed), any other write — including MCP server tool logging or stats writes — is blocked for the duration of the transaction. The default `busy_timeout` is 0ms, meaning queries fail immediately on contention.

**How to avoid:**
- Set `PRAGMA busy_timeout = 5000` on all connections (5 seconds). This alone eliminates most production lock errors.
- Use WAL mode: `PRAGMA journal_mode = WAL`.
- Break indexing into smaller transactions: commit every 100-500 documents, not every 10,000.
- Keep the query path read-only; never write stats or logs during a query if they share the indexer's write window.
- Open separate connections for reading (MCP server) vs writing (indexer) with appropriate timeout settings.

**Warning signs:**
- Intermittent `database is locked` errors in logs.
- MCP tool calls timeout during indexing runs.
- Indexing jobs fail if the CLI is used simultaneously.

**Phase to address:**
Phase 1 (Database setup) — WAL mode and busy_timeout must be set at database initialization. Phase 3 (MCP server) — connection handling strategy must account for concurrent access.

---

### Pitfall 4: MCP Server Spawned as a New Process Per Call

**What goes wrong:**
If the MCP server is configured as a stdio transport and the host (Claude Code) spawns a new process per session, every search tool call incurs: Python startup (~200ms) + Ollama model load (1-10 seconds cold, ~200ms warm) + SQLite open. The first search after a 5-minute idle feels broken — 10+ second response time. Agents time out or retry, producing duplicate results.

**Why it happens:**
The MCP Python SDK defaults to stdio transport, which spawns a new process per client session. Developers test with a warm Ollama instance and miss the cold-start penalty. Ollama's default `KEEP_ALIVE` is 5 minutes — after idle, the embedding model unloads from VRAM.

**How to avoid:**
- Design the MCP server to be long-lived (persistent process), not per-call.
- For Claude Code's stdio transport, the server process lives for the duration of the Claude Code session — this is acceptable if startup is fast. Ensure Python startup is fast: lazy-import heavy dependencies (`sqlite_vec`, embedding client) after the server is listening.
- Set `OLLAMA_KEEP_ALIVE=-1` in the user's environment when Corpus is running; document this requirement prominently.
- Pre-warm the embedding model at MCP server startup with a no-op embed call so the first real query is fast.
- Implement a health-check that logs the model load time at startup so users can diagnose slowness.

**Warning signs:**
- First search after idle takes >5 seconds.
- Claude Code shows "tool call timed out" intermittently.
- Search responses are fast sometimes and slow other times (correlates with Ollama model unload cycle).

**Phase to address:**
Phase 3 (MCP server) — startup sequence and warm-up must be designed before the server is written.

---

### Pitfall 5: Code Chunked Like Prose — Splitting at Character Boundaries

**What goes wrong:**
Using a fixed-size character splitter (e.g., 500 characters with 50-character overlap) on Python and TypeScript files breaks function definitions across chunks. A function's signature lands in chunk N, its body in chunk N+1, its docstring in chunk N-1. Embedding each chunk independently produces fragments that embed poorly and match no real query. A search for "async HTTP request handler" misses the function because no single chunk contains both the signature and the implementation.

**Why it happens:**
Character splitting works well enough for prose/markdown and is the default in most RAG tutorials. Developers reuse the same strategy for code without recognizing that code has structural boundaries (functions, classes, methods) that prose doesn't. The corpus-analyzer codebase already uses Python AST extraction (`symbols`) — this capability exists but isn't wired to chunking.

**How to avoid:**
- Use **AST-aware chunking** for Python and TypeScript: split at function/class/method boundaries using Python's built-in `ast` module (already used in `extractors/`) and tree-sitter for TypeScript/JavaScript.
- For Markdown: split at heading boundaries (H2/H3), not character count. The existing markdown extractor already extracts headings — use them as split points.
- Target ~400-600 tokens per chunk (not characters), since embedding models have token budgets.
- Prepend context to each chunk: `# file.py\n## ClassName.method_name\n` before the code body. This anchors the embedding in the file/class namespace.
- Overlap strategy: for code, include the function signature in the previous chunk's tail (not random character overlap).

**Warning signs:**
- Search for a known function name returns no results.
- Chunks in the database contain half a function definition.
- Embedding quality improves dramatically when testing with full-function content vs. truncated content.

**Phase to address:**
Phase 1 (Extraction pipeline extension) — chunking strategy must be defined before any embeddings are generated. Changing chunking strategy requires a full reindex.

---

### Pitfall 6: Vector Index Rebuild Required After Chunking Strategy Change

**What goes wrong:**
After indexing 50,000 chunks with strategy A (character split), the team decides to switch to strategy B (AST-aware). The metadata and FTS5 index update correctly, but the vector index now contains embeddings computed from different chunk boundaries than the stored chunk text. Results are inconsistent: BM25 returns the correct text chunk, but the vector component returns the old chunk's embedding. The index is silently corrupted.

**Why it happens:**
Incremental indexing adds new vectors for new files, but doesn't detect when existing chunks need re-embedding due to a strategy change. There's no version stored for "how was this chunk created."

**How to avoid:**
- Store a `chunk_strategy_version` field in the chunks table. When the strategy changes, bump the version.
- On index startup, compare the current strategy version against the stored version; if different, require `corpus reindex --force` or trigger an automatic full reindex.
- Document clearly: **changing chunking strategy requires a full reindex**. Make this prominent in CLI output.
- Implement `corpus status` that shows: total files indexed, total chunks, embedding model, chunk strategy version, index age.

**Warning signs:**
- Search quality degrades after a config change without an obvious reason.
- BM25 and vector results diverge (one returns relevant chunks, the other doesn't).
- Chunks in the database have different average lengths than expected.

**Phase to address:**
Phase 1 (Data model) — version fields must exist in the schema before any indexing occurs. Phase 2 (Incremental indexing) — version comparison logic.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Fixed-size character chunking for all file types | Fast to implement, works for markdown | Broken code search; requires full reindex to fix | Never for code files; acceptable for markdown-only MVP |
| Single transaction for entire corpus index | 2-5x faster indexing | Database locked for all queries during indexing | Never; batch-commit every 100-500 documents |
| No embedding model version stored in DB | Simpler schema | Silent search quality degradation on model change; no way to detect | Never |
| Linear score combination instead of RRF | Easy math, one line of code | BM25 dominates; vector component wasted | Never |
| Skipping pre-warm on MCP server startup | Slightly faster startup | First query after idle takes 5-15 seconds; agent timeouts | Only acceptable if Ollama keep-alive is guaranteed configured |
| No `corpus status` / health command | Save one phase's worth of work | Users can't diagnose stale index, wrong model, or schema issues | Defer past MVP, but add in Phase 2 |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Ollama embeddings API | Calling embed one document at a time | Batch embed 32-128 documents per API call; single-call latency is 200-2000ms |
| Ollama embeddings API | Assuming model is loaded | Pre-warm with a no-op call at startup; set `OLLAMA_KEEP_ALIVE=-1` for search workloads |
| sqlite-vec | Using brute-force KNN on 500k+ vectors in a single query | sqlite-vec v0.1.x is brute-force only; ANN index support is planned but not stable as of early 2026. Design for a migration path to HNSW when it lands. |
| SQLite FTS5 | Using default `unicode61` tokenizer for code | Code identifiers with underscores, dots, slashes are poorly tokenized. Use `unicode61 tokenchars "._-/"` to preserve them as single tokens. |
| SQLite FTS5 BM25 | Calling `bm25()` without understanding sign convention | SQLite FTS5 `bm25()` returns negative values (more negative = more relevant). `ORDER BY bm25(...)` is correct; `ORDER BY bm25(...) DESC` returns worst matches. |
| OpenAI embeddings API | Not caching embeddings for frequently-queried content | Each API call costs money and adds 200-500ms latency. Cache embeddings at the chunk level. |
| MCP stdio transport | Importing all dependencies at module load | Python's import time for `numpy`, `sqlite_vec`, `httpx` adds 300-800ms to every process spawn. Use lazy imports. |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Embedding all file types without filtering | Indexing takes hours; index includes `.pyc`, lock files, `node_modules` | Default ignore patterns for binary, generated, and vendor files; show file count estimates before indexing | At 10k+ files in a repo |
| Re-embedding unchanged files on every `corpus index` run | Reindex takes same time as initial index | Track file mtimes and content hashes; only re-embed files that changed | At 1k+ files |
| Brute-force KNN on all vectors at query time | Queries take >500ms | sqlite-vec is fast up to ~100k vectors with brute-force; beyond that, plan for ANN or partitioning | At 100k+ chunks |
| Loading all embeddings into Python memory for fusion | OOM on large corpora | Do vector search inside SQLite; only transfer top-K results to Python for RRF fusion | At 50k+ vectors |
| No query result caching | Every repeated query hits SQLite + Ollama | Cache query embeddings (keyed on query text + model name) for 5-minute TTL | At >10 queries/minute (agents in loops) |
| FTS5 index not rebuilt after mass delete/reindex | FTS5 internal b-tree fragmented; query speed degrades | Run `INSERT INTO fts_index(fts_index) VALUES('rebuild')` after bulk deletes | After bulk reindex of >10k documents |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| MCP tool accepts arbitrary directory paths without validation | Agent indexes sensitive directories (`.ssh/`, `/etc/`) | Validate all paths against configured `source_dirs` allow-list; reject paths outside configured sources |
| Storing cloud API keys in the corpus config file | Key exposure in shared repos or agent context | Use environment variables only; never write API keys to `corpus.toml` or the database |
| MCP tool returns full file content in search snippets | Large file content in agent context windows, potential PII exposure | Return only snippet (200-500 chars around match), file path, and score — never full file content |
| No rate limiting on MCP search tool | Agent in a loop calls search hundreds of times per second | Add per-session rate limiting: 60 calls/minute; log and return a friendly error on excess |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Search returns results with no explanation of relevance | Developer doesn't know why a file ranked #1; can't improve query | Include: similarity score, matching snippet with highlighted terms, which classifier tags matched |
| `corpus index` runs silently for minutes with no progress | Developer assumes it crashed; kills the process mid-index | Show real-time progress: files scanned, files embedded, estimated time remaining |
| Hybrid search returns 0 results when either BM25 or vector returns 0 | Frustrating; sparse index or new query vocabulary causes complete failure | With RRF, one empty side contributes 0 to the score — it doesn't zero out the other side. Never AND the result sets. |
| First-run experience requires manual Ollama setup with no guidance | Developer runs `corpus index` and gets a confusing connection error | On startup, check Ollama connectivity and emit a clear error: "Ollama is not running. Start it with: `ollama serve`. Then pull an embedding model: `ollama pull nomic-embed-text`." |
| No way to tell if index is stale | Developer queries a corpus that hasn't been re-indexed in weeks; misses new files | `corpus status` shows last index time and count of unindexed files (files in source dirs not in DB) |

---

## "Looks Done But Isn't" Checklist

- [ ] **Hybrid search:** RRF fusion implemented — verify it produces different rankings than pure BM25. Run a semantic query ("authentication helper") and confirm a semantically-relevant but keyword-mismatched file appears in top 5.
- [ ] **Embedding model validation:** Change `CORPUS_EMBEDDING_MODEL` config, run a query, confirm an error is raised (not silent bad results).
- [ ] **Incremental indexing:** Modify one file, run `corpus index`, confirm only that file is re-embedded (check embedding count in DB, not total file count).
- [ ] **MCP server first query latency:** Start the MCP server, wait 6 minutes (past Ollama keep-alive default), run a search. Measure response time. If >3 seconds, pre-warm is not working.
- [ ] **SQLite concurrency:** Start `corpus index` on a large directory, then immediately run `corpus search "test"` from another terminal. Confirm no lock error.
- [ ] **FTS5 BM25 sign convention:** Run `corpus search "test"` and verify results are sorted most-relevant-first (not last).
- [ ] **Code chunking boundaries:** Index a Python file with multiple functions. Search for a term in the second function's body. Confirm the returned chunk includes the function signature, not just the body.
- [ ] **Source path validation (MCP):** Call the MCP search tool with a path outside configured sources. Confirm it is rejected, not silently indexed.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Embedding model mismatch discovered after index is built | HIGH — full reindex required | (1) `corpus db clear-embeddings`, (2) update config, (3) `corpus index --force`. Duration: same as initial indexing. |
| Wrong chunking strategy indexed | HIGH — full reindex required | (1) `corpus db nuke`, (2) update chunk strategy config, (3) `corpus index`. All embeddings regenerated. |
| SQLite WAL file grown unbounded | MEDIUM | (1) Stop all readers, (2) run `PRAGMA wal_checkpoint(TRUNCATE)`, (3) restart. Preventable with scheduled checkpoints. |
| BM25 score sign bug causing reversed rankings | LOW | Fix the SQL `ORDER BY` direction. No data migration needed. |
| FTS5 index corrupted after bulk delete | LOW | `INSERT INTO fts_index(fts_index) VALUES('rebuild')`. Takes 30-60 seconds for 100k documents. |
| Ollama cold start causing agent timeouts | LOW | Set `OLLAMA_KEEP_ALIVE=-1`, restart Ollama, add pre-warm call to MCP startup. |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Embedding model mismatch | Phase 1: Embedding pipeline | Integration test: change model config, assert error on query |
| BM25/vector raw score fusion | Phase 2: Hybrid search | Unit test: RRF produces different ranking than pure BM25; semantic query returns semantic result in top 5 |
| SQLite concurrency / database locked | Phase 1: Database setup (WAL + timeout) | Concurrent load test: indexer + query running simultaneously for 30 seconds |
| MCP server cold start latency | Phase 3: MCP server | Timing test: query after 6-minute idle < 2 seconds with pre-warm |
| Code chunked at character boundaries | Phase 1: Extraction/chunking | Manual test: search for function body term; returned chunk contains the function signature |
| Chunk strategy version mismatch | Phase 1: Data model schema | Integration test: change strategy version, assert reindex is required |
| FTS5 sign convention bug | Phase 2: Hybrid search | Smoke test: `corpus search "common_term"` returns most-matching document first |
| No progress on long index | Phase 1: CLI UX | Acceptance test: index 500+ files shows progress bar/count |
| Stale index UX | Phase 2: CLI UX | `corpus status` shows unindexed file count and last index timestamp |

---

## Sources

- [Common Pitfalls When Using Vector Databases — DagsHub](https://dagshub.com/blog/common-pitfalls-to-avoid-when-using-vector-databases/) — HIGH confidence
- [Hybrid Search in PostgreSQL: The Missing Manual — ParadeDB](https://www.paradedb.com/blog/hybrid-search-in-postgresql-the-missing-manual) — HIGH confidence
- [Building Effective Hybrid Search in OpenSearch — OpenSearch blog](https://opensearch.org/blog/building-effective-hybrid-search-in-opensearch-techniques-and-best-practices/) — HIGH confidence
- [Hybrid Search & Reciprocal Rank Fusion — minimalistinnovation.co](https://www.minimalistinnovation.co/post/hybrid-search-reciprocal-rank-fusion-lexical-semantic) — MEDIUM confidence
- [sqlite-vec Tracking Issue: ANN Index — GitHub asg017/sqlite-vec #25](https://github.com/asg017/sqlite-vec/issues/25) — HIGH confidence (official issue tracker)
- [SQLite WAL Concurrency — SQLite official docs](https://sqlite.org/wal.html) — HIGH confidence
- [SQLite Concurrent Writes and "database is locked" — tenthousandmeters.com](https://tenthousandmeters.com/blog/sqlite-concurrent-writes-and-database-is-locked-errors/) — MEDIUM confidence
- [Ollama Slow Embeddings — langchain-ai/langchain issue #21870](https://github.com/langchain-ai/langchain/issues/21870) — MEDIUM confidence
- [Speed Up Ollama: Preloading Models into RAM — Medium](https://medium.com/@rafal.kedziorski/speed-up-ollama-how-i-preload-local-llms-into-ram-for-lightning-fast-ai-experiments-291a832edd48) — MEDIUM confidence
- [Best Chunking Strategies for RAG — Firecrawl](https://www.firecrawl.dev/blog/best-chunking-strategies-rag-2025) — MEDIUM confidence
- [AST-Aware Code Chunking — supermemory.ai](https://supermemory.ai/blog/building-code-chunk-ast-aware-code-chunking/) — MEDIUM confidence
- [MCP Server Slow Startup — Gemini CLI Issue #4544](https://github.com/google-gemini/gemini-cli/issues/4544) — HIGH confidence (direct bug report with measured times)
- [Why Your MCP Server is Slow — Arsturn](https://www.arsturn.com/blog/mcp-server-performance-issues-and-fixes) — MEDIUM confidence
- [State of Vector Search in SQLite — Marco Bambini](https://marcobambini.substack.com/p/the-state-of-vector-search-in-sqlite) — MEDIUM confidence

---
*Pitfalls research for: local semantic search engine — AI agent library indexing (Corpus)*
*Researched: 2026-02-23*

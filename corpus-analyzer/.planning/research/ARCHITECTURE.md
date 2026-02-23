# Architecture Research

**Domain:** Local semantic search engine for AI agent libraries
**Researched:** 2026-02-23
**Confidence:** HIGH (indexing/search/hybrid patterns), HIGH (MCP server pattern), MEDIUM (source config management — standard patterns verified but no single canonical reference)

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Interface Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  CLI (Typer) │  │  MCP Server  │  │    Python API         │  │
│  │  corpus ...  │  │  (FastMCP)   │  │    SearchEngine()     │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         └─────────────────┴──────────────────────┘              │
│                            │                                     │
├────────────────────────────▼────────────────────────────────────┤
│                    Search Service Layer                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   SearchEngine                             │  │
│  │  query() → [embed query] → [parallel retrieve] → [fuse]   │  │
│  └──────┬────────────────────────────────┬────────────────────┘  │
│         │                                │                        │
│  ┌──────▼──────┐                ┌────────▼───────┐               │
│  │ Vector Leg  │                │   BM25/FTS Leg  │               │
│  │ sqlite-vec  │                │   SQLite FTS5   │               │
│  └──────┬──────┘                └────────┬───────┘               │
│         └────────────────┬───────────────┘                       │
│                   ┌──────▼──────┐                                 │
│                   │  RRF Fusion │                                  │
│                   └─────────────┘                                 │
├─────────────────────────────────────────────────────────────────┤
│                    Indexing Pipeline                              │
│  ┌───────────┐  ┌───────────┐  ┌────────────┐  ┌────────────┐  │
│  │  Scanner  │→ │ Extractor │→ │  Embedder  │→ │   Indexer  │  │
│  │(existing) │  │(existing) │  │(new layer) │  │(new layer) │  │
│  └───────────┘  └───────────┘  └────────────┘  └────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                      Persistence Layer                           │
│  ┌──────────────────────┐  ┌────────────────────────────────┐  │
│  │  SQLite (metadata)   │  │  sqlite-vec (vector index)     │  │
│  │  + FTS5 (BM25 index) │  │  embeddings table              │  │
│  └──────────────────────┘  └────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                     Config Layer                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  corpus.toml — source dirs, embedding provider, model    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| CLI | User-facing commands: `index`, `search`, `add`, `status` | SearchEngine, IndexPipeline, SourceConfig |
| MCP Server (FastMCP) | Exposes `search` as an MCP tool for Claude Code and agents | SearchEngine (reads only) |
| Python API | Programmatic interface to SearchEngine | SearchEngine |
| SearchEngine | Orchestrates hybrid search: embed query, run both legs, fuse results | EmbeddingProvider, sqlite-vec, SQLite FTS5 |
| IndexPipeline | Orchestrates: scan → extract → embed → write to index | Scanner, Extractor, EmbeddingProvider, VectorStore, FTS index |
| EmbeddingProvider | Abstraction over embedding backends (Ollama / OpenAI / Cohere) | Ollama client, HTTP clients |
| VectorStore (sqlite-vec) | KNN search over stored embeddings | SQLite |
| FTS5 index | BM25 keyword search | SQLite |
| RRF Fusion | Combines ranked lists from vector and BM25 legs into a single ranking | SearchEngine |
| SourceConfig | Reads/writes `corpus.toml`; tracks which directories are indexed and their state hashes | Filesystem |
| IncrementalTracker | Compares file mtime/hash against stored state; decides which files need re-embedding | CorpusDatabase, Filesystem |

---

## Indexing Pipeline vs. Search/Query Pipeline

These are **cleanly separate** pipelines with a shared persistence layer as the boundary.

### Indexing Pipeline (write path)

```
SourceConfig.get_sources()
    ↓
Scanner.scan(directory)                 ← existing corpus-analyzer code
    ↓
Extractor.extract(file_path) → Document ← existing corpus-analyzer code
    ↓
IncrementalTracker.needs_reindex(doc)   ← new: compare mtime/hash
    ↓  (skip if unchanged)
EmbeddingProvider.embed(text) → vector  ← new layer
    ↓
VectorStore.upsert(doc_id, vector)      ← sqlite-vec
FTS5.upsert(doc_id, text)               ← SQLite FTS5
CorpusDatabase.upsert_document(doc)     ← existing + extended
```

The indexing pipeline runs on demand (`corpus index`) or incrementally (`corpus index --changed`). It is **not** in the hot path at query time. Embedding generation only happens here, not at query time for stored documents.

### Search/Query Pipeline (read path)

```
query_text (string)
    ↓
EmbeddingProvider.embed(query_text) → query_vector   ← at query time only
    ↓
[Parallel]
    VectorStore.knn_search(query_vector, k=20)        → [(doc_id, distance)]
    FTS5.search(query_text, k=20)                     → [(doc_id, bm25_score)]
    ↓
RRFusion.fuse(vector_results, fts_results)            → [(doc_id, combined_rank)]
    ↓
CorpusDatabase.get_documents(doc_ids)                 → [Document + snippet]
    ↓
[SearchResult(path, score, snippet, metadata), ...]
```

The query pipeline is **stateless** — it never writes. The only write-path operation that touches query time is embedding the user's query string, which is discarded after use.

---

## Where Embedding Generation Fits

**At index time:** All document embeddings are generated once and stored in `sqlite-vec`. This is the expensive operation and must happen offline/on-demand.

**At query time:** Only the user's query string is embedded. This must be fast (sub-100ms for a good embedding model like `nomic-embed-text` via Ollama).

**Implication:** The `EmbeddingProvider` abstraction is used in both pipelines, but with different performance expectations. Index-time can be batched; query-time cannot.

**Embedding model consistency constraint:** The model used at index time must match the model used at query time. Changing the embedding model requires a full reindex. The model name/version must be stored in `SourceConfig` or the database schema so this is enforced.

---

## Hybrid Search Ranking Architecture

**Confidence:** HIGH — verified via sqlite-vec official examples (RRF in SQL) and Elastic documentation.

The standard pattern is **Reciprocal Rank Fusion (RRF)**, which avoids the problem of normalizing incompatible score scales (BM25 is unbounded; cosine similarity is 0–1).

### RRF Formula

```
combined_rank(doc) = weight_vec / (rrf_k + vec_rank) + weight_fts / (rrf_k + fts_rank)
```

Where `rrf_k = 60` is standard. Higher combined_rank = more relevant.

A document missing from one leg still gets a score from the other leg (`COALESCE` to 0 for the missing rank component). This means a document that is rank-1 in BM25 but absent from vector results still surfaces.

### Execution Pattern (sqlite-vec verified)

```sql
WITH vec_matches AS (
  SELECT article_id,
         ROW_NUMBER() OVER (ORDER BY distance) AS rank_number
  FROM vec_articles
  WHERE headline_embedding MATCH embed(:query) AND k = :k
),
fts_matches AS (
  SELECT rowid,
         ROW_NUMBER() OVER (ORDER BY rank) AS rank_number
  FROM fts_articles
  WHERE headline MATCH :query
  LIMIT :k
),
final AS (
  SELECT
    COALESCE(1.0 / (60 + fts_matches.rank_number), 0.0) * :weight_fts
    + COALESCE(1.0 / (60 + vec_matches.rank_number), 0.0) * :weight_vec AS combined_rank,
    ...
  FROM fts_matches
  FULL OUTER JOIN vec_matches ON vec_matches.article_id = fts_matches.rowid
)
SELECT * FROM final ORDER BY combined_rank DESC;
```

This runs entirely within SQLite — no external fusion service required.

### Why RRF over weighted score normalization

Weighted score normalization requires min-max scaling across the result set, which changes every query. RRF only depends on rank position, which is stable and requires no calibration. It handles the "BM25 favors longer documents" problem automatically.

---

## MCP Server Pattern

**Confidence:** HIGH — verified via FastMCP official docs and MCP specification 2025-06-18.

The standard pattern for an MCP server wrapping a search engine:

1. **Transport:** stdio (for Claude Code integration) or SSE/HTTP for other clients. FastMCP handles both.
2. **Tools:** One primary `search` tool with `query`, `limit`, and optional filter parameters.
3. **Resources (optional):** Expose individual indexed files as `file://` resources if the client wants to read full content.
4. **No state mutation through MCP:** The MCP server is read-only. Indexing is triggered through CLI, not MCP.

### FastMCP implementation pattern

```python
from fastmcp import FastMCP
from corpus_analyzer.search import SearchEngine

mcp = FastMCP("corpus")

@mcp.tool
def search(query: str, limit: int = 10, domain: str | None = None) -> list[dict]:
    """Search the indexed agent library corpus.

    Returns ranked files with path, score, snippet, category, and domain tags.
    """
    engine = SearchEngine.from_config()
    results = engine.search(query, limit=limit, domain_filter=domain)
    return [r.model_dump() for r in results]
```

The MCP server is a thin wrapper — it instantiates the `SearchEngine` and delegates. All search logic lives in `SearchEngine`, not in the MCP layer.

### MCP vs CLI relationship

The MCP server and CLI both depend on `SearchEngine`. Neither is built on top of the other. Build order: `SearchEngine` → `CLI` → `MCP server` (MCP is just another consumer of `SearchEngine`).

---

## Source Configuration Management

**Confidence:** MEDIUM — no single canonical Python pattern; derived from multiple systems (CocoIndex, Open Semantic Search, common practice).

### Recommended pattern: `corpus.toml` config file

```toml
[index]
database = "corpus.sqlite"
embedding_model = "nomic-embed-text"
embedding_provider = "ollama"
ollama_host = "http://localhost:11434"

[[sources]]
name = "my-skills"
path = "/home/user/.claude/skills"
recursive = true
extensions = [".md", ".py", ".yaml", ".json"]

[[sources]]
name = "agent-repos"
path = "/home/user/ghrepos"
recursive = true
extensions = [".md", ".py"]
exclude = ["node_modules", ".git", "__pycache__"]
```

`corpus.toml` lives in the current directory (project-local) or `~/.config/corpus/corpus.toml` (global). Config is read at startup; `corpus add <dir>` appends a new `[[sources]]` entry.

### Incremental indexing with change tracking

Each source maintains a state table in SQLite:

```
file_index_state(path TEXT, mtime REAL, content_hash TEXT, indexed_at DATETIME, embedding_model TEXT)
```

At index time: compare current mtime and hash against stored state. Only re-embed files that changed. Delete state records for files that no longer exist on disk.

The embedding model name is stored per file so that a model change triggers selective or full reindex.

---

## Recommended Project Structure

```
src/corpus_analyzer/
├── core/
│   ├── models.py          # Document, Chunk, SearchResult (extend existing)
│   ├── database.py        # CorpusDatabase (extend for vectors + FTS)
│   └── scanner.py         # existing — no changes needed
├── extractors/            # existing — no changes needed
├── classifiers/           # existing — no changes needed
├── embeddings/            # NEW
│   ├── __init__.py
│   ├── base.py            # EmbeddingProvider abstract class
│   ├── ollama.py          # OllamaEmbedder
│   └── openai.py          # OpenAIEmbedder (optional, v1 stretch)
├── indexing/              # NEW
│   ├── __init__.py
│   ├── pipeline.py        # IndexPipeline: orchestrates scan→extract→embed→store
│   └── tracker.py         # IncrementalTracker: mtime/hash change detection
├── search/                # NEW
│   ├── __init__.py
│   ├── engine.py          # SearchEngine: hybrid search orchestration
│   ├── fusion.py          # RRFusion: rank combination
│   └── models.py          # SearchResult, SearchQuery Pydantic models
├── mcp/                   # NEW
│   ├── __init__.py
│   └── server.py          # FastMCP server, exposes search tool
├── config.py              # extend: add SourceConfig, embedding settings
└── cli.py                 # extend: add index, search, add, status commands
```

### Structure Rationale

- **embeddings/**: Isolated from search — swappable provider without touching search logic. `EmbeddingProvider` base class enforces `embed(text: str) -> list[float]` and `embed_batch(texts: list[str]) -> list[list[float]]` contract.
- **indexing/**: Separated from search because indexing is a write-path, scheduled/on-demand operation; search is a read-path, latency-sensitive operation. They share the DB but have no runtime coupling.
- **search/**: `SearchEngine.search()` is the primary API surface consumed by CLI, MCP, and Python API.
- **mcp/**: Thin wrapper only. All logic in `search/`. One file sufficient for v1.

---

## Architectural Patterns

### Pattern 1: Dual-Index Storage (FTS5 + sqlite-vec in same database)

**What:** Store BM25 index (FTS5) and vector index (sqlite-vec) in the same SQLite database file. Hybrid query runs as a single SQL statement using CTEs.

**When to use:** Local deployment, single-user, no concurrent write pressure. This is the right choice for Corpus.

**Trade-offs:** Simplicity wins — no separate vector database process, no network calls, single file to back up. Trade-off is SQLite's write-lock (one writer at a time) which is acceptable for local use.

**Example schema addition:**
```sql
-- FTS5 for BM25
CREATE VIRTUAL TABLE corpus_fts USING fts5(
    content,
    path UNINDEXED,
    content='documents',
    content_rowid='rowid'
);

-- sqlite-vec for KNN
CREATE VIRTUAL TABLE corpus_vec USING vec0(
    doc_id INTEGER PRIMARY KEY,
    embedding FLOAT[768]  -- dimension matches chosen model
);
```

### Pattern 2: Provider Abstraction for Embeddings

**What:** `EmbeddingProvider` abstract base class with `embed()` and `embed_batch()`. Concrete implementations for Ollama, OpenAI, and possibly Cohere. Config selects provider at startup.

**When to use:** Always — the embedding provider is the most likely thing to change (offline vs. online, model upgrades).

**Trade-offs:** Minor abstraction overhead; pays for itself the first time you want to test with a different model.

### Pattern 3: SearchEngine as the Core API

**What:** `SearchEngine` class is the single entry point for all search operations. CLI and MCP are both thin consumers. Python API is just `SearchEngine` exposed.

**When to use:** Always — prevents logic duplication between CLI and MCP, ensures consistent results.

**Trade-offs:** None meaningful. This is the correct factoring.

---

## Data Flow

### Indexing Flow

```
corpus index [--changed]
    ↓
SourceConfig.get_sources() → list[SourceDir]
    ↓
for each source:
    Scanner.scan(source.path) → Iterable[Path]
    ↓
    for each file:
        IncrementalTracker.needs_reindex(path) → bool
        ↓ (skip if False)
        Extractor.extract(path) → Document
        EmbeddingProvider.embed_batch([doc.content]) → [vector]
        CorpusDatabase.upsert_document(doc)
        VectorStore.upsert(doc.id, vector)
        FTS5.upsert(doc.id, doc.content)
        IncrementalTracker.mark_indexed(path, mtime, hash, model)
```

### Search Flow

```
corpus search "query text" --limit 10
    ↓
SearchEngine.search(query="query text", limit=10)
    ↓
EmbeddingProvider.embed(query) → query_vector    [~50-100ms with Ollama local]
    ↓
[Parallel SQL CTEs in one query]
    VectorStore.knn(query_vector, k=20)          → [(doc_id, rank)]
    FTS5.search(query_text, k=20)                → [(doc_id, rank)]
    ↓
RRFusion.fuse(vec_results, fts_results)          → [(doc_id, combined_rank)]
    ↓
CorpusDatabase.get_documents(top_N_ids)          → [Document]
    ↓
[Build SearchResult with snippet extraction]     → [SearchResult]
    ↓
CLI: rich table display  OR  MCP: JSON tool response  OR  API: list[SearchResult]
```

### Source Add Flow

```
corpus add /path/to/directory
    ↓
SourceConfig.load_or_create()
    ↓
SourceConfig.add_source(path, name, extensions)
    ↓
SourceConfig.save()  → writes corpus.toml
    ↓
[Optional: corpus index --source <name> to index immediately]
```

---

## Build Order

**Dependency graph:**

```
EmbeddingProvider (base + Ollama)
    ↓
VectorStore (sqlite-vec integration in CorpusDatabase)
FTS5 (extend CorpusDatabase schema)
    ↓
IndexPipeline (Scanner + Extractor already exist; add Embedder + Tracker)
    ↓
SearchEngine (depends on VectorStore + FTS5 + RRFusion + EmbeddingProvider)
    ↓
SourceConfig (depends on SearchEngine knowing what sources exist)
    ↓
CLI search + index commands (depends on SearchEngine + IndexPipeline + SourceConfig)
    ↓
Python API (thin wrapper over SearchEngine — trivially added)
    ↓
MCP Server (thin wrapper over SearchEngine — can be added any time after SearchEngine exists)
```

### Milestones that unlock further work

| Milestone | What it unlocks |
|-----------|----------------|
| EmbeddingProvider + sqlite-vec schema | Everything downstream |
| IndexPipeline working | Can index and store; search not yet possible |
| SearchEngine (vector-only first) | First searchable state; can validate recall before adding BM25 |
| Add FTS5 + RRF | Hybrid search; better recall for exact name matches |
| CLI search command | End-to-end user experience; validates the full pipeline |
| MCP Server | Agent integration; can be added after CLI search is working |
| SourceConfig | Source management; can be stubbed initially (hardcode a path) |

**Key insight: You can search before you have hybrid.** Build vector-only search first, validate recall, then layer in FTS5 + RRF. This keeps each phase shippable.

**Key insight: MCP can be added any time after SearchEngine exists.** MCP is not a prerequisite for CLI, and CLI is not a prerequisite for MCP. Both are thin consumers of `SearchEngine`.

---

## Anti-Patterns

### Anti-Pattern 1: Embedding at Query Time for Stored Documents

**What people do:** Recompute document embeddings on every search query because they skipped the indexing step.
**Why it's wrong:** Embedding 10,000 documents at query time takes minutes. The entire point of an index is to precompute.
**Do this instead:** Index-time embedding only. Query-time embedding for the query string only.

### Anti-Pattern 2: Putting Search Logic in the MCP Layer

**What people do:** Build the hybrid search directly inside `mcp/server.py` because that is where queries arrive first.
**Why it's wrong:** Logic cannot be tested without an MCP client. CLI and API diverge. Logic is duplicated.
**Do this instead:** All search logic in `SearchEngine`. MCP is one line: `return engine.search(query)`.

### Anti-Pattern 3: Separate Vector Database Process

**What people do:** Add ChromaDB or Qdrant as a standalone server because it is what they know from cloud RAG tutorials.
**Why it's wrong:** Local single-user tool does not need a separate process. sqlite-vec runs in-process, zero infra overhead.
**Do this instead:** sqlite-vec in the existing SQLite database. Revisit if multi-user or scale demands it.

### Anti-Pattern 4: Full Reindex on Every Run

**What people do:** Skip incremental tracking and reindex everything each time `corpus index` runs.
**Why it's wrong:** For large corpora (1000+ files), this is slow. Re-embedding unchanged files wastes Ollama calls.
**Do this instead:** mtime + content hash tracking per file. Only reindex changed/new files. Full reindex is a `--force` option.

### Anti-Pattern 5: Storing Embeddings in the Document Table

**What people do:** Add an `embedding BLOB` column to the existing `documents` table.
**Why it's wrong:** sqlite-vec requires its own virtual table structure for KNN queries. Blobs in regular columns cannot be searched with ANN indexing.
**Do this instead:** Separate `corpus_vec` virtual table via `CREATE VIRTUAL TABLE ... USING vec0(...)`, linked to `documents` by `doc_id`.

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Ollama (embeddings) | HTTP client to `http://localhost:11434/api/embeddings` | Existing OllamaClient can be extended; use `nomic-embed-text` model |
| OpenAI Embeddings | HTTP via `openai` Python SDK | Optional v1 stretch goal; use `text-embedding-3-small` |
| Claude Code (MCP) | FastMCP stdio transport | Claude Code reads MCP server config from `mcp.json` |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| IndexPipeline ↔ CorpusDatabase | Direct Python call, passes Document and vector | Write path only |
| SearchEngine ↔ CorpusDatabase | Direct Python call, SQL query via sqlite-utils | Read path only |
| CLI ↔ SearchEngine | Direct Python instantiation | CLI creates SearchEngine with config |
| MCP Server ↔ SearchEngine | Direct Python instantiation | MCP creates SearchEngine with config, same as CLI |
| Python API ↔ SearchEngine | SearchEngine is the API | No additional wrapper needed |

---

## Scalability Considerations

This is a local single-user tool. Scalability considerations are about corpus size, not concurrent users.

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0–1K files | sqlite-vec default settings sufficient; all indexing in seconds |
| 1K–10K files | Batch embedding calls (embed_batch); incremental indexing critical at this scale |
| 10K–50K files | Consider chunking large files rather than whole-file embedding; chunk table already exists |
| 50K+ files | sqlite-vec ANN index tuning; potentially consider external vector store; unlikely for local agent libraries |

### Scaling Priorities

1. **First bottleneck:** Embedding generation speed — mitigated by incremental indexing and batching.
2. **Second bottleneck:** Vector index memory — sqlite-vec loads index into memory for search; for 50K+ files with 768-dim embeddings, this is ~150MB+ which is fine for local use.

---

## Sources

- sqlite-vec RRF and hybrid search examples (HIGH confidence): https://github.com/asg017/sqlite-vec/blob/main/examples/nbc-headlines/3_search.ipynb
- Elastic hybrid search guide (MEDIUM confidence — cloud system, but fusion patterns apply): https://www.elastic.co/what-is/hybrid-search
- MCP Tools specification 2025-06-18 (HIGH confidence): https://modelcontextprotocol.io/specification/2025-06-18/server/tools
- FastMCP documentation (HIGH confidence): https://github.com/jlowin/fastmcp
- Hypermode embedding pipeline guide (MEDIUM confidence): https://hypermode.com/blog/build-embedding-pipelines-for-ai-retrieval
- CocoIndex incremental indexing architecture (MEDIUM confidence): https://medium.com/@cocoindex.io/building-intelligent-codebase-indexing-with-cocoindex-a-deep-dive-into-semantic-code-search-e93ae28519c5

---
*Architecture research for: local semantic search engine for AI agent libraries (Corpus)*
*Researched: 2026-02-23*

# Stack Research

**Domain:** Local semantic search engine (Python, embedded, no server)
**Researched:** 2026-02-23
**Confidence:** HIGH (all critical choices verified via Context7, official docs, or live PyPI)

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12 | Runtime | Already in use; asyncio support needed for MCP server |
| uv | latest | Package manager | Already in use; mandatory per project constraints |
| LanceDB | 0.29.x | Vector store + hybrid search | Embedded (no server), built-in BM25 FTS via tantivy, built-in RRF reranker, native Python + Arrow; designed as "SQLite for AI" |
| mcp | 1.26.x | MCP server (FastMCP) | Official Anthropic Python SDK; FastMCP became part of this package in v1.x; FastMCP 2.0 builds on top |
| bm25s | 0.3.x | Standalone BM25 (if needed outside LanceDB) | Pure Python + scipy/numpy, 500x faster than rank-bm25, no native dependencies, handles in-memory index |
| sentence-transformers | 5.2.x | Local embedding generation (non-Ollama path) | Official SBERT library; all-MiniLM-L6-v2 runs fast on CPU; static embedding variants 100-400x faster still |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tantivy | 0.25.x | BM25/FTS index (LanceDB dependency) | Automatically pulled in by LanceDB FTS; install explicitly to pin version |
| openai | 1.109.x | OpenAI embeddings provider | When user configures `text-embedding-3-small` or `text-embedding-3-large` as provider |
| httpx | 0.27.x | HTTP client | Already transitive dep via ollama; used for Ollama embed API calls |
| pyarrow | latest | Arrow in-memory tables | Transitive via LanceDB; needed for data interchange |
| pydantic | 2.6.x | Embedding provider config models | Already in use; models for provider config (OllamaProvider, OpenAIProvider) |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| ruff | Lint + format | Already configured; line length 100 |
| mypy --strict | Type checking | Already configured |
| pytest | Test runner | Already configured |
| pytest-cov | Coverage | Already configured |

---

## Installation

```bash
# Vector store + hybrid search (pulls tantivy transitively)
uv add "lancedb>=0.29.0"
uv add "tantivy>=0.25.0"  # pin explicitly to avoid breakage

# MCP server (includes FastMCP)
uv add "mcp>=1.26.0"

# Embedding providers
uv add "sentence-transformers>=5.2.0"  # local non-Ollama path
uv add "openai>=1.109.0"               # optional, for OpenAI embedding provider

# BM25 standalone (only if doing search outside LanceDB)
uv add "bm25s>=0.3.0"
```

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| LanceDB | ChromaDB 1.5.x | ChromaDB's embedded (persistent) mode works but its FTS is not built-in — you'd add a separate BM25 library and wire them manually. LanceDB ships hybrid search natively with RRF. ChromaDB also has a history of breaking API changes between versions. Use ChromaDB if you need a simpler collection/document API without joining on row IDs. |
| LanceDB | sqlite-vec 0.1.x | sqlite-vec stores and queries vectors inside SQLite — perfect fit with the existing sqlite-utils stack. BUT: no built-in BM25/FTS (you'd wire rank_bm25 or bm25s separately), no built-in hybrid search or reranking, and the library is still alpha (v0.1.6). Choose sqlite-vec only if you want zero new storage backends and can implement hybrid fusion yourself. |
| LanceDB | hnswlib | hnswlib is an in-memory HNSW index library only. No persistence, no FTS, no hybrid search. You'd need to serialize/deserialize yourself. Not suitable unless ultra-low latency ANN on a fixed in-memory corpus is the only requirement. |
| LanceDB | Faiss | Same story as hnswlib: index only, no persistence layer, no FTS. Faiss requires a C++ build toolchain and has non-trivial Python packaging. Overkill for a local corpus of <1M docs. |
| bm25s | rank-bm25 | rank-bm25 is a pure Python BM25 with no sparse matrix optimisation; 500x slower than bm25s at query time. Fine for <10K docs; unacceptable for larger corpora. |
| bm25s | whoosh | Whoosh is unmaintained (last release 2013-era, no Python 3.12 guarantee). Avoid. |
| mcp (FastMCP) | Building raw MCP protocol by hand | FastMCP provides decorator-based registration identical to Flask/FastAPI; the underlying low-level SDK handles JSON-RPC lifecycle. No reason to build raw. |
| sentence-transformers | Cohere embed API | Cohere requires network access — violates offline-first constraint for default config. Make it an optional provider, not the default. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| whoosh | Unmaintained since ~2013; no support for Python 3.12+ ecosystem; BM25 implementation is suboptimal | bm25s (in-memory) or LanceDB FTS (persistent) |
| rank-bm25 | 500x slower than bm25s on large corpora; no sparse matrix storage; blocks query path | bm25s |
| sqlite-vss | Superseded by sqlite-vec by the same author; archived/not maintained | sqlite-vec (if you want SQLite-only vector search) |
| Faiss (standalone) | Complex C++ build; no persistence; no FTS; significant binary size | LanceDB (wraps efficient vector search with full data lifecycle) |
| hnswlib (standalone) | Memory-only; no persistence; no FTS; manual save/load | LanceDB |
| ChromaDB for hybrid search | No native BM25; hybrid requires external library + manual fusion; API instability history | LanceDB |
| fastembed (as default) | Good library but adds another embedding runtime alongside Ollama already present; redundant | sentence-transformers (for local non-Ollama) or Ollama directly |

---

## Stack Patterns by Variant

**If user is fully offline (default, Ollama-only):**
- Use `ollama.embed()` (via existing ollama==0.6.x dep) with `nomic-embed-text` or `mxbai-embed-large`
- Store vectors in LanceDB
- LanceDB FTS handles BM25 via tantivy
- Because: zero new network dependencies, works day-1 without cloud accounts

**If user wants higher quality embeddings (cloud provider):**
- Add `openai>=1.109.0` as optional dep
- Default to `text-embedding-3-small` (1536-dim, fast, cheap)
- Provide `text-embedding-3-large` as upgrade option
- Because: best MTEB benchmark scores for English retrieval at reasonable cost

**If user wants local embeddings without Ollama:**
- `sentence-transformers>=5.2.0` with `all-MiniLM-L6-v2` (384-dim, fast on CPU)
- Or `static-retrieval-mrl-en-v1` for 100-400x faster CPU inference at 85% quality
- Because: no Ollama server required; runs in-process

**For MCP server (Claude Code integration):**
- Use `mcp>=1.26.0` with FastMCP
- Transport: stdio for local (Claude Code default); streamable-http for remote
- Register `search` as an MCP tool with structured input/output
- Because: FastMCP is now part of the official SDK (no separate package needed); Claude Code expects stdio transport for local tools

**For hybrid search ranking:**
- Use LanceDB's built-in `RRFReranker` (Reciprocal Rank Fusion, k=60 default)
- Formula: `score = sum(1 / (k + rank))` across vector and FTS result lists
- Because: RRF requires no score normalization, no tuning, works well out of the box; LanceDB implements it natively so no manual merge code needed

---

## Embedding Provider Architecture Pattern

Design a pluggable provider interface using a Protocol/ABC:

```python
from typing import Protocol
import numpy as np

class EmbeddingProvider(Protocol):
    """Pluggable embedding provider interface."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts, returning float vectors."""
        ...

    @property
    def dimensions(self) -> int:
        """Vector dimension for this provider."""
        ...
```

Concrete providers:
- `OllamaEmbeddingProvider` — calls `ollama.embed(model=..., input=texts)` via existing ollama dep
- `OpenAIEmbeddingProvider` — calls `openai.embeddings.create(model=..., input=texts)`
- `SentenceTransformerProvider` — wraps `SentenceTransformer(model_name).encode(texts)`

Configure via Pydantic Settings:
```
CORPUS_EMBEDDING_PROVIDER=ollama         # or: openai, sentence-transformers
CORPUS_EMBEDDING_MODEL=nomic-embed-text  # provider-specific model name
CORPUS_OLLAMA_HOST=http://localhost:11434
CORPUS_OPENAI_API_KEY=...               # only needed when provider=openai
```

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| lancedb>=0.29.0 | tantivy>=0.22.0 | LanceDB docs pin tantivy==0.20.1 for older versions; test with 0.25.x and pin if issues arise |
| lancedb>=0.29.0 | pyarrow>=14.0 | LanceDB requires Arrow; transitive but must not conflict with other Arrow consumers |
| mcp>=1.26.0 | Python>=3.10 | FastMCP uses asyncio features available in 3.10+; 3.12 is fine |
| sentence-transformers>=5.2.0 | torch>=2.0 | Pulls in PyTorch; large binary (~1GB); add as optional dependency group |
| bm25s>=0.3.0 | numpy>=1.24, scipy>=1.10 | Pure Python; no native code; no known conflicts |
| ollama>=0.6.1 | httpx>=0.25 | Already pinned in project; embed() added in ~0.4.x |

---

## Recommended Embedding Models

| Provider | Model | Dimensions | Notes |
|----------|-------|-----------|-------|
| Ollama (default) | `nomic-embed-text` | 768 | Outperforms OpenAI ada-002; fast; recommended default |
| Ollama (quality) | `mxbai-embed-large` | 1024 | Better on context-heavy queries; slower |
| OpenAI | `text-embedding-3-small` | 1536 | Best price/performance; ~$0.02/1M tokens |
| OpenAI (quality) | `text-embedding-3-large` | 3072 | Highest quality; ~$0.13/1M tokens |
| sentence-transformers | `all-MiniLM-L6-v2` | 384 | Fast CPU; good for dev/CI with no Ollama |
| sentence-transformers | `static-retrieval-mrl-en-v1` | 1024 | 100-400x faster than MiniLM on CPU; 85% quality |

---

## Sources

- `/lancedb/lancedb` (Context7, HIGH) — hybrid search, FTS, RRF reranker, sentence-transformer integration verified
- `/asg017/sqlite-vec` (Context7, HIGH) — installation, KNN API, alpha status confirmed
- `/modelcontextprotocol/python-sdk` (Context7, HIGH) — FastMCP API, transports, stdio integration verified
- `/chroma-core/chroma` (Context7, HIGH) — PersistentClient mode, embedding functions verified
- https://pypi.org/project/lancedb/ — v0.29.2 confirmed as latest (HIGH)
- https://pypi.org/project/mcp/ — v1.26.0 confirmed as latest (HIGH)
- https://pypi.org/project/bm25s/ — v0.3.0 confirmed as latest (HIGH)
- https://pypi.org/project/sentence-transformers/ — v5.2.3 confirmed as latest (HIGH)
- https://pypi.org/project/sqlite-vec/ — v0.1.6 confirmed as latest; alpha status (HIGH)
- https://pypi.org/project/tantivy/ — v0.25.1 confirmed as latest (HIGH)
- https://github.com/lancedb/lancedb/blob/main/docs/src/fts_tantivy.md — tantivy dependency for LanceDB FTS confirmed (MEDIUM, GitHub source)
- https://gofastmcp.com/integrations/claude-code — stdio transport for Claude Code confirmed (MEDIUM, official FastMCP site)
- https://ollama.com/blog/embedding-models — nomic-embed-text, mxbai-embed-large models confirmed (HIGH, official Ollama)
- https://huggingface.co/blog/xhluca/bm25s — BM25S performance claims (500x vs rank-bm25) (MEDIUM, HuggingFace blog)
- https://bm25s.github.io/ — bm25s capabilities (MEDIUM, project site)
- https://www.sbert.net/ — sentence-transformers models and CPU performance (HIGH, official SBERT docs)

---

*Stack research for: Corpus — local semantic search engine for AI agent libraries*
*Researched: 2026-02-23*

# Milestones

## v1.0 MVP (Shipped: 2026-02-23)

**Phases completed:** 4 phases, 15 plans
**Timeline:** 2026-01-13 → 2026-02-23 (41 days)
**Python LOC:** ~6,100

**Delivered:** A semantic search engine for AI agent libraries — index local skills, workflows, and code; query via CLI, MCP, or Python API with sub-second hybrid BM25+vector retrieval.

**Key accomplishments:**
- LanceDB embedding pipeline: ChunkRecord schema, deterministic sha256 chunk IDs, OllamaEmbedder integration
- Full ingestion CLI (`corpus add`, `corpus index`) with incremental re-indexing and XDG Base Directory compliance
- Hybrid BM25+vector search engine with RRF fusion, filterable by source, file type, and construct type
- Agent construct classifier (rule-based + LLM fallback) and AI summarizer per indexed file
- FastMCP server with pre-warmed embeddings and `from corpus import search` Python API
- Safety hardening: CLI KeyError fix, indexer warning logs, MCP `content_error` signaling

**Archive:** `.planning/milestones/v1.0-ROADMAP.md`

---


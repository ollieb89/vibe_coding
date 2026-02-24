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


## v1.1 Search Quality (Shipped: 2026-02-23)

**Phases completed:** 2 phases, 4 plans
**Timeline:** 2026-02-23 (1 day)
**Python LOC:** ~6,248

**Delivered:** Eliminated index noise via per-source extension allowlists and lifted `--construct` filtering accuracy from heuristic to 0.95-confidence via YAML frontmatter signals.

**Key accomplishments:**
- Per-source extension allowlist (`SourceConfig.extensions`) with sensible defaults — excludes `.sh`, `.html`, `.json`, `.lock`, binaries automatically
- Extension filtering wired end-to-end: corpus.toml → walk_source → indexer → CLI warning on file removal
- `ClassificationResult` dataclass with confidence + source tracking (frontmatter/rule_based/llm)
- Frontmatter-first classifier: `type:` / `component_type:` → 0.95 confidence; `tags:` → 0.70 confidence
- LanceDB schema v3 with `classification_source` + `classification_confidence` fields; idempotent in-place migration
- `--construct` filter now leverages high-confidence frontmatter classifications persisted in LanceDB

**Archive:** `.planning/milestones/v1.1-ROADMAP.md`

---


## v1.2 Graph Linker (Shipped: 2026-02-24)

**Phases completed:** 2 phases (7–8), 1 GSD plan
**Timeline:** 2026-02-24 (1 day)
**Python LOC:** ~7,300

**Delivered:** Added a directed relationship graph to the indexing pipeline — `corpus index` now auto-extracts `## Related Skills` / `## Related Files` links from Markdown and persists them as queryable graph edges, while dead API surface was removed.

**Key accomplishments:**
- `corpus index` auto-extracts `## Related Skills` / `## Related Files` edges into `graph.sqlite` with no extra commands
- `corpus graph <slug>` exposes upstream (←) and downstream (→) neighbours for any indexed file
- Closest-prefix ambiguity resolution picks the nearest-path candidate when multiple files share a slug
- `corpus index` warns on duplicate slug collisions in yellow at index time
- `corpus graph --show-duplicates` lists all slug collisions and the paths involved
- Removed dead `use_llm_classification` parameter from `index_source()` / `SourceConfig`, shrinking the API surface

**Archive:** `.planning/milestones/v1.2-ROADMAP.md`

---


## v1.3 Code Quality (Shipped: 2026-02-24)

**Phases completed:** 4 phases, 11 plans, 0 tasks

**Key accomplishments:**
- (none recorded)

---


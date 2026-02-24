# Corpus

## What This Is

Corpus is a local semantic search engine for AI agent libraries. It indexes agent skills, workflows, prompts, and code across configured directories and local repos, then makes them instantly queryable via CLI, MCP server, and Python API. Built for developers who maintain collections of agent skills and need to surface relevant files without grepping.

v1.0 ships as a CLI tool (`corpus add`, `corpus index`, `corpus search`, `corpus status`) backed by LanceDB with hybrid BM25+vector retrieval. An MCP server (`corpus mcp serve`) exposes search to Claude Code and other agents. A Python API (`from corpus import search`) enables programmatic access.

v1.1 adds configurable extension allowlists per source (no more config files polluting results) and frontmatter-aware construct classification — YAML `type:` and `component_type:` fields are classified at 0.95 confidence, making `--construct` filtering reliably accurate.

v1.2 adds a relationship graph layer: `corpus index` now extracts `## Related Skills` / `## Related Files` links from indexed Markdown and persists them as a directed graph, queryable via `corpus graph <slug>`.

## Core Value

Surface relevant agent files instantly — query an entire local agent library and get ranked, relevant results in under a second.

## Requirements

### Validated

- ✓ LanceDB embedding pipeline with deterministic chunk IDs — v1.0
- ✓ Source config via `corpus.toml` (CONF-01–CONF-04) — v1.0
- ✓ `corpus add <dir>` CLI command (CONF-05) — v1.0
- ✓ `corpus index` with incremental re-indexing and ghost document removal (INGEST-01–INGEST-07) — v1.0
- ✓ Structure-aware chunking: heading-based (`.md`), AST-based (`.py`), line-based fallback — v1.0
- ✓ `corpus search` with hybrid BM25+vector+RRF ranking (SEARCH-01, SEARCH-02) — v1.0
- ✓ Search filters: `--source`, `--type`, `--construct`, `--limit` (SEARCH-03, SEARCH-04, SEARCH-05) — v1.0
- ✓ Agent construct classifier: skill/prompt/workflow/agent_config/code/documentation (CLASS-01–CLASS-03) — v1.0
- ✓ AI summarizer per indexed file with Ollama, config-gated (SUMM-01–SUMM-03) — v1.0
- ✓ `corpus status` with file count, chunk count, last indexed, model (CLI-04) — v1.0
- ✓ FastMCP server with pre-warmed embeddings, `corpus_search` tool (MCP-01–MCP-06) — v1.0
- ✓ Python API: `search()`, `index()`, `SearchResult` dataclass (API-01–API-03) — v1.0
- ✓ Safety: no CLI KeyErrors, no silent exception swallowing, MCP `content_error` signaling — v1.0
- ✓ Per-source extension allowlist in corpus.toml; default covers doc/code types, excludes junk (CONF-06, CONF-07, CONF-08) — v1.1
- ✓ Frontmatter-aware construct classifier: `type:`, `component_type:`, `tags` at 0.95/0.95/0.70 confidence (CLASS-04, CLASS-05) — v1.1
- ✓ `classification_source` + `classification_confidence` persisted in LanceDB; schema v3 in-place migration — v1.1

### Active

- [ ] Relationship graph: extract + persist `## Related Skills` / `## Related Files` links during `corpus index` (GRAPH-01–GRAPH-05)
- [ ] Remove dead `use_llm_classification` parameter from `index_source()` (CLEAN-01)

### Out of Scope

- Hosted/cloud index — local-only (privacy, simplicity)
- Real-time file watching — manual index refresh only; daemon complexity not justified yet
- Web UI — CLI + MCP sufficient for target users
- LLM rewriting (corpus-analyzer original feature) — retained but not the focus
- Chunk-level results (CHUNK-01–CHUNK-03) — v2 candidate
- TypeScript/JS AST chunking (IDX-01) — v2 candidate

## Context

**v1.2 in progress (started 2026-02-24). v1.1 shipped 2026-02-23.**

- ~6,248 lines Python source (graph module adds ~300 lines)
- Tech stack: LanceDB, FastMCP, Pydantic, Typer, Rich, OllamaEmbedder (nomic-embed-text); graph layer uses SQLite
- 282 tests passing (pytest)
- XDG Base Directory compliant: config in `~/.config/corpus/`, data in `~/.local/share/corpus/`
- Single-user local tool; no daemon, no cloud dependency

Graph layer uses a separate `graph.sqlite` file (not LanceDB) to store directed edges; keeps concerns cleanly separated.

Known limitations heading into v2 planning:
- Search returns file-level results; chunk-level line ranges would improve precision
- TypeScript/JS files use line-based chunking (no AST awareness)
- Cold-start on first index after KEEP_ALIVE expiry still possible (pre-warm only covers MCP startup)

## Constraints

- **Runtime**: Python 3.12, managed with `uv`
- **Package manager**: `uv` only (no pip/poetry)
- **Embeddings**: Must support offline (Ollama) — cloud providers optional
- **Storage**: LanceDB for vector+metadata; FTS via tantivy (built into LanceDB)
- **Existing tests**: Test suite must stay green

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Pivot corpus-analyzer rather than start fresh | Extraction, models, DB, CLI already built | ✓ Good — saved ~2 phases of setup work |
| LanceDB over sqlite-vec | Embedded, ships hybrid search + BM25 + RRF natively | ✓ Good — no external service, fast queries |
| Hybrid search (vector + BM25 via RRF) | Better recall than pure vector; handles exact name matches | ✓ Good — validated in UAT |
| Protocol-based embedding abstraction | Offline-first (Ollama) with optional cloud providers | ✓ Good — clean swap if needed |
| Store embedding model name in schema | Cannot be retrofitted after first embed | ✓ Good — enforced at query time |
| AST-aware chunking for `.py`, heading-based for `.md` | Better chunk coherence vs line-based | ✓ Good — search quality improved |
| Rule-based classifier first, LLM fallback | Cost-conscious; LLM gate via `use_llm_classification` | ✓ Good — zero LLM cost by default |
| Default `use_llm_classification = False` | Avoid unexpected Ollama API costs | ✓ Good — explicit opt-in |
| `needs_reindex()` removed entirely | Hash-based change detection makes it redundant | ✓ Good — dead code eliminated |
| FTS rebuild only in `index_source()` | Redundant rebuild in `CorpusSearch.__init__` was wasteful | ✓ Good — ~20% faster search init |
| MCP `content_error` field vs exception | Avoids breaking existing clients; explicit error signal | ✓ Good — graceful degradation |
| Path constants in `config/schema.py` | Avoid circular imports from dual definitions | ✓ Good — single source of truth |
| `ClassificationResult` dataclass (not raw string) | Structured data enables confidence + source tracking | ✓ Good — clean extension point for LLM/rule/frontmatter sources |
| Frontmatter priority > rule-based | Explicit declaration is higher signal than heuristics | ✓ Good — 0.95 vs 0.60 confidence gap makes priority clear |
| `type:` confidence 0.95, `tags:` confidence 0.70 | Explicit type is direct match; tags are softer signal | ✓ Good — appropriate weighting |
| `ensure_schema_v3()` in-place migration | Existing users don't rebuild index on upgrade | ✓ Good — idempotent, zero data loss |
| Extension allowlist default includes doc/code types | Sensible out-of-box behavior without requiring config | ✓ Good — excludes `.sh`, `.html`, `.json`, `.lock`, binaries automatically |

| SQLite for graph store (not LanceDB) | Graph edges are relational; SQLite is simpler and avoids LanceDB schema overhead | — Pending |
| Closest-prefix ambiguity resolution for slugs | Context-aware: picks the candidate closest in filesystem path to the referencing file | — Pending |

---
*Last updated: 2026-02-24 after v1.2 milestone started*

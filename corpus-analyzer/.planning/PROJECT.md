# Corpus

## What This Is

Corpus is a semantic search engine for AI agent libraries. It indexes agent skills, workflows, prompts, and code across local collections of cloned repos and arbitrary directories, then makes them queryable via CLI, MCP server (for Claude Code and other agent integration), and Python API. When building a new agent or workflow, you query the index to surface relevant files instantly.

This is a pivot of the existing corpus-analyzer codebase — the extraction, classification, and persistence infrastructure is retained; the primary output becomes a searchable index rather than a rewriting tool.

## Core Value

Surface relevant agent files instantly — a developer building a new workflow should be able to query their entire local agent library and get ranked, relevant results in under a second.

## Requirements

### Validated

<!-- Existing capabilities in corpus-analyzer — these work and will be retained/extended. -->

- ✓ File scanning and extraction (markdown, Python, .txt, .rst) — existing
- ✓ Document model with metadata (headings, links, code blocks, symbols) — existing
- ✓ SQLite persistence layer (`CorpusDatabase`) — existing
- ✓ CLI interface (Typer) — existing
- ✓ Document type classification (persona, howto, runbook, etc.) — existing
- ✓ Domain tag classification (backend, frontend, ai, etc.) — existing
- ✓ Ollama integration for LLM operations — existing

### Active

<!-- What Corpus v1 is building toward. -->

- [ ] Hybrid search: vector similarity + BM25/keyword ranked results
- [ ] Embedding generation: configurable provider (Ollama local or cloud API: OpenAI/Cohere)
- [ ] Source management: config file defining permanent source directories + ad-hoc `corpus add <dir>` CLI
- [ ] Incremental indexing: re-index only changed/new files
- [ ] MCP server exposing search as a tool for Claude Code and other agents
- [ ] Python API for programmatic search access
- [ ] CLI search command returning ranked files with snippets and similarity scores
- [ ] Index all file types: `.md`, `.py`, `.json`, `.yaml`, `.ts`, `.js`, and other code files

### Out of Scope

- Hosted/cloud index — local-only for v1 (privacy, simplicity)
- Real-time file watching — manual index refresh only in v1
- Web UI — CLI + MCP sufficient for v1 target users
- LLM rewriting (corpus-analyzer original feature) — retained but not the focus

## Context

The corpus-analyzer codebase provides a strong foundation:
- `core/scanner.py` walks directories and yields file paths
- `extractors/` converts files to `Document` models (already handles markdown, Python)
- `core/database.py` is a SQLite wrapper via `sqlite-utils`
- `core/models.py` has `Document`, `Chunk`, and supporting models
- `classifiers/` provides metadata enrichment useful for filtering search results
- Ollama is already wired in for LLM calls

New work centers on: embedding pipeline, vector storage, hybrid search ranking, MCP server, and source config management.

## Constraints

- **Runtime**: Python 3.12, managed with `uv`
- **Package manager**: `uv` only (no pip/poetry)
- **Embeddings**: Must support offline (Ollama) — cloud providers optional
- **Storage**: SQLite for metadata; vector store TBD (sqlite-vec or ChromaDB)
- **Existing tests**: Existing test suite must stay green through the pivot

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Pivot corpus-analyzer rather than start fresh | Extraction, models, DB, CLI already built | — Pending |
| Hybrid search (vector + BM25) | Better recall than pure vector; handles exact name matches | — Pending |
| Configurable embedding provider | Developers may be offline or prefer quality of cloud models | — Pending |
| Vector storage backend | sqlite-vec vs ChromaDB vs hnswlib TBD | — Pending |

---
*Last updated: 2026-02-23 after initialization*

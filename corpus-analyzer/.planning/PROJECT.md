# Corpus

## What This Is

Corpus is a local semantic search engine for AI agent libraries. It indexes agent skills, workflows, prompts, and code across configured directories and local repos, then makes them instantly queryable via CLI, MCP server, and Python API. Built for developers who maintain collections of agent skills and need to surface relevant files without grepping.

v1.0 ships as a CLI tool (`corpus add`, `corpus index`, `corpus search`, `corpus status`) backed by LanceDB with hybrid BM25+vector retrieval. An MCP server (`corpus mcp serve`) exposes search to Claude Code and other agents. A Python API (`from corpus import search`) enables programmatic access.

v1.1 adds configurable extension allowlists per source (no more config files polluting results) and frontmatter-aware construct classification — YAML `type:` and `component_type:` fields are classified at 0.95 confidence, making `--construct` filtering reliably accurate.

v1.2 adds a relationship graph layer: `corpus index` now extracts `## Related Skills` / `## Related Files` links from indexed Markdown and persists them as a directed graph, queryable via `corpus graph <slug>`.

v1.3 achieves a clean linting baseline across the entire codebase: zero mypy errors (`uv run mypy src/` exits 0 across 53 files) and zero ruff violations (`uv run ruff check .` exits 0). Per-file line-length override (120 chars) suppresses E501 in `llm/*.py`; B006 suppressed for Typer list defaults in `cli.py`.

v1.4 gives users full control over search output: `--min-score <float>` filters results below the RRF threshold (0.009–0.033 range documented in help text); `--sort-by score|date|title` orders results; a contextual FILT-03 hint fires when filtering eliminates all results. Python API and MCP are at parity — `search()` accepts `sort_by` and `min_score`; `corpus_search()` MCP tool accepts `min_score: Optional[float]`.

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
- ✓ Relationship graph: `corpus index` extracts + persists `## Related Skills` / `## Related Files` edges; `corpus graph <slug>` queries upstream/downstream neighbours; closest-prefix ambiguity resolution; `--show-duplicates` (GRAPH-01–GRAPH-05) — v1.2
- ✓ Dead `use_llm_classification` parameter removed from `index_source()` and `SourceConfig` (CLEAN-01) — v1.2
- ✓ `pyproject.toml` surgical ruff/mypy config: `extend-exclude`, `per-file-ignores`, `[[tool.mypy.overrides]]` (CONF-01–CONF-04, RUFF-01, RUFF-02) — v1.3
- ✓ `ruff --fix` sweep eliminated ~370 auto-fixable violations across 37 files (RUFF-01, RUFF-02) — v1.3
- ✓ Manual E741/E402/B017/B023/B904/E501 fixes across leaf modules, database hub, and cli.py (RUFF-03–RUFF-07) — v1.3
- ✓ `cast(Table, ...)` pattern at all sqlite-utils call sites; parameterised generics; float() guards (MYPY-01) — v1.3
- ✓ `Atom` promoted to module level; nested functions fully annotated in `chunked_processor.py` (MYPY-02) — v1.3
- ✓ `DEFAULT_SYSTEM_PROMPT` trailing comma bug fixed (was `tuple[str]`, now `str`) (MYPY-05) — v1.3
- ✓ `uv run ruff check .` → 0 violations; `uv run mypy src/` → 0 errors; 281 tests green (VALID-01–VALID-03) — v1.3

### Validated

- ✓ `--min-score <float>` CLI flag filters results below RRF threshold; help text documents 0.009–0.033 range (FILT-01, FILT-02) — v1.4
- ✓ FILT-03 contextual hint when `--min-score` filters all results — v1.4
- ✓ `--sort-by score|date|title` CLI flag with engine vocabulary translation — v1.4
- ✓ Python `search()` API accepts `sort_by` and `min_score` with `ValueError` validation (PARITY-01, PARITY-02) — v1.4
- ✓ MCP `corpus_search()` accepts `min_score: Optional[float]` with `None`→`0.0` + `filtered_by_min_score` signal (PARITY-03) — v1.4

## Current Milestone: v1.5 TypeScript AST Chunking

**Goal:** Replace line-based chunking for TypeScript and JavaScript with tree-sitter AST-aware chunking, matching the precision and parity of the existing Python AST chunker.

**Target features:**
- tree-sitter based AST chunker for `.ts`, `.tsx`, `.js`, `.jsx`
- Chunk types: functions/methods, classes, interfaces/types, top-level constants
- Silent line-based fallback on parse failure
- Full test coverage at parity with the Python AST chunker

### Active

- [ ] tree-sitter AST chunker for `.ts`, `.tsx`, `.js`, `.jsx` (IDX-01)
- [ ] Chunk granularity: functions, methods, classes, interfaces/types, top-level constants (IDX-02)
- [ ] Silent line-based fallback when tree-sitter cannot parse a file (IDX-03)
- [ ] Test suite at full parity with Python AST chunker coverage (TEST-01)
- [ ] Integration: new chunker wired into indexer dispatch for TS/JS extensions (IDX-04)

### Out of Scope

- Hosted/cloud index — local-only (privacy, simplicity)
- Real-time file watching — manual index refresh only; daemon complexity not justified yet
- Web UI — CLI + MCP sufficient for target users
- LLM rewriting (corpus-analyzer original feature) — retained but not the focus
- Chunk-level results (CHUNK-01–CHUNK-03) — v2 candidate

## Context

**v1.4 shipped 2026-02-24. All v1.4 requirements complete. Search output is now user-controllable across all three interfaces.**

- ~7,513 lines Python source across 53 files (23 files touched in v1.4: +2,566 / -48 lines)
- Tech stack: LanceDB, FastMCP, Pydantic, Typer, Rich, OllamaEmbedder (nomic-embed-text); graph layer uses SQLite (`graph.sqlite`)
- 293 tests passing (pytest) — 8 new tests added in v1.4 (4 engine, 3 CLI, 2 MCP + 1 API updated)
- XDG Base Directory compliant: config in `~/.config/corpus/`, data in `~/.local/share/corpus/`
- Single-user local tool; no daemon, no cloud dependency
- Zero mypy errors, zero ruff violations — maintained clean linting baseline through v1.4

Known limitations heading into v2 planning:
- Search returns file-level results; chunk-level line ranges would improve precision
- TypeScript/JS files use line-based chunking (no AST awareness)
- Cold-start on first index after KEEP_ALIVE expiry still possible (pre-warm only covers MCP startup)
- FILT-04 (MCP sort_by) and FILT-05 (score normalisation) explicitly deferred to v2

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

| SQLite for graph store (not LanceDB) | Graph edges are relational; SQLite is simpler and avoids LanceDB schema overhead | ✓ Good — separate `graph.sqlite` keeps concerns cleanly separated |
| Closest-prefix ambiguity resolution for slugs | Context-aware: picks the candidate closest in filesystem path to the referencing file | ✓ Good — handles multi-repo agent libraries without false matches |
| Hardcode `use_llm=False` at call site (not remove arg) | `classify_file` defaults to `use_llm=True`; removing kwarg would silently switch to LLM classification | ✓ Good — preserved rule-based classification behaviour |
| `extend-exclude` over `exclude` in ruff config | Preserves ruff defaults (`.venv`, `.git`) while adding `.windsurf/`, `.planning/` | ✓ Good — no accidental exclusion of user dirs |
| `cast(Table, ...)` per call site (not `# type: ignore`) | Explicit and refactor-safe; grep-able pattern | ✓ Good — all 8 sqlite-utils call sites annotated cleanly |
| `DEFAULT_SYSTEM_PROMPT` trailing comma removed (not cast away) | Was a real `tuple[str]` runtime bug — `+=` on a tuple would raise `TypeError` at runtime | ✓ Good — genuine bug fixed, not suppressed |
| `Atom` promoted to module level (not type: ignore on nested) | Nested dataclasses prevent typed annotations on helper closures | ✓ Good — cleaner module structure, zero mypy errors |
| `OllamaClient.db: CorpusDatabase \| None = None` added | `advanced_rewriter.py` uses `client.db`; TYPE_CHECKING guard avoids circular import | ✓ Good — optional field, no runtime impact if unused |
| Post-retrieval Python filter for `min_score` (not LanceDB `.where()`) | RRF scores aren't stored as a native LanceDB column; filtering in-process is simpler and correct | ✓ Good — 4 tests confirm behaviour; no schema change needed |
| `_CLI_SORT_BY_MAP` + `_API_SORT_MAP` translation dicts | CLI/API vocabulary (`score/date/title`) decoupled from engine vocabulary (`relevance/date/path`) | ✓ Good — user-facing names are stable even if engine internals change |
| MCP `min_score: Optional[float]` with `None`→`0.0` guard | MCP schema requires Optional for backward-compat; explicit guard makes the no-op intent clear | ✓ Good — tested with both `None` and `0.02` cases |
| FILT-03 branch checks `min_score > 0.0` before generic no-results | Contextual hint only fires when the user deliberately filtered; doesn't appear on regular empty results | ✓ Good — tested by asserting absence of generic message alongside presence of hint |

---
*Last updated: 2026-02-24 after v1.5 milestone start*

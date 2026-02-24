# Corpus

## What This Is

Corpus is a local semantic search engine for AI agent libraries. It indexes agent skills, workflows, prompts, and code across configured directories and local repos, then makes them instantly queryable via CLI, MCP server, and Python API. Built for developers who maintain collections of agent skills and need to surface relevant files without grepping.

v1.0 ships as a CLI tool (`corpus add`, `corpus index`, `corpus search`, `corpus status`) backed by LanceDB with hybrid BM25+vector retrieval. An MCP server (`corpus mcp serve`) exposes search to Claude Code and other agents. A Python API (`from corpus import search`) enables programmatic access.

v1.1 adds configurable extension allowlists per source (no more config files polluting results) and frontmatter-aware construct classification — YAML `type:` and `component_type:` fields are classified at 0.95 confidence, making `--construct` filtering reliably accurate.

v1.2 adds a relationship graph layer: `corpus index` now extracts `## Related Skills` / `## Related Files` links from indexed Markdown and persists them as a directed graph, queryable via `corpus graph <slug>`.

v1.3 achieves a clean linting baseline across the entire codebase: zero mypy errors (`uv run mypy src/` exits 0 across 53 files) and zero ruff violations (`uv run ruff check .` exits 0). Per-file line-length override (120 chars) suppresses E501 in `llm/*.py`; B006 suppressed for Typer list defaults in `cli.py`.

v1.4 gives users full control over search output: `--min-score <float>` filters results below the RRF threshold (0.009–0.033 range documented in help text); `--sort-by score|date|title` orders results; a contextual FILT-03 hint fires when filtering eliminates all results. Python API and MCP are at parity — `search()` accepts `sort_by` and `min_score`; `corpus_search()` MCP tool accepts `min_score: Optional[float]`.

v1.5 replaces line-based chunking for TypeScript and JavaScript with tree-sitter AST-aware chunking. `.ts`, `.tsx`, `.js`, `.jsx` files now index at construct-level precision — functions, classes, interfaces, type aliases, enums, and generators extracted as separate chunks with correct line boundaries. Production-safe: 50K+ char files fall back to line chunking; missing tree-sitter is caught at call site with graceful fallback.

v2 exposes chunk-level search results across all surfaces. CLI output switches to grep/compiler-error format (`path/to/file.md:42-67 [skill] score:0.021`) — IDE-clickable with exact line ranges. MCP `corpus_search` response becomes self-contained: each result carries `start_line`, `end_line`, and full chunk `text`. Python and TypeScript class bodies are sub-chunked at method level (`ClassName.method_name`). A new `--name` CLI flag and MCP `name` parameter filter by chunk name. MCP gains `sort_by` support and 0–1 normalised scores. A `corpus search --output json` flag enables shell piping. A new `corpus_graph` MCP tool allows LLM clients to walk codebase dependency graphs.

## Core Value

Surface relevant agent files instantly — query an entire local agent library and get ranked, relevant results in under a second.

## Current Milestone: v2.1 Result Quality

**Goal:** Complete the chunk-level search experience — MCP self-contained chunks, method sub-chunking, name filtering, normalised scores, JSON output, and graph MCP.

**Target features:**
- MCP `corpus_search` response includes `start_line`, `end_line`, `text` per result (CHUNK-03)
- Python + TypeScript method sub-chunking: `ClassName.method_name` naming (SUB-01–03)
- `corpus search --name <fragment>` and MCP `name` parameter (NAME-01–03)
- MCP `sort_by` + 0–1 normalised scores (SORT-01, NORM-01)
- `corpus search --output json` for shell piping (JSON-01)
- `corpus_graph` MCP tool for LLM graph traversal (GRAPH-01)
- 85%+ branch coverage on chunking modules; zero-hallucination line-range contract (QUAL-01–02)

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
- ✓ `--min-score <float>` CLI flag filters results below RRF threshold; help text documents 0.009–0.033 range (FILT-01, FILT-02) — v1.4
- ✓ FILT-03 contextual hint when `--min-score` filters all results — v1.4
- ✓ `--sort-by score|date|title` CLI flag with engine vocabulary translation — v1.4
- ✓ Python `search()` API accepts `sort_by` and `min_score` with `ValueError` validation (PARITY-01, PARITY-02) — v1.4
- ✓ MCP `corpus_search()` accepts `min_score: Optional[float]` with `None`→`0.0` + `filtered_by_min_score` signal (PARITY-03) — v1.4
- ✓ `pyproject.toml` updated with `tree-sitter>=0.25.0` and `tree-sitter-language-pack>=0.13.0`; `uv sync` succeeds with pre-compiled wheels (DEP-01) — v1.5
- ✓ `chunk_file()` dispatch routes `.ts`, `.tsx`, `.js`, `.jsx` to `chunk_typescript()` (IDX-01) — v1.5
- ✓ `chunk_typescript()` extracts 8 top-level node types with correct 1-indexed line boundaries (IDX-02) — v1.5
- ✓ `export_statement` unwrapping: `export function foo()` and `export class Bar` produce correctly-named chunks (IDX-03) — v1.5
- ✓ Grammar dispatched by extension: TypeScript/TSX/JavaScript; `@lru_cache` grammar loader (IDX-04, IDX-07) — v1.5
- ✓ Silent fallback to `chunk_lines()` on exception or zero constructs; no fallback on `has_error` alone (IDX-05) — v1.5
- ✓ `chunk_name` field in returned chunk dict (IDX-06) — v1.5
- ✓ Size guard: files >50,000 chars fall back to `chunk_lines()` before AST parse (IDX-08) — v1.5
- ✓ `ImportError` guard in `chunk_file()` — missing tree-sitter falls back to line chunking (IDX-09) — v1.5
- ✓ `TestChunkTypeScript` at full parity with `TestChunkPython` — 21 test methods (TEST-01) — v1.5
- ✓ `TestChunkFile` dispatch assertions for all four TS/JS extensions (TEST-02) — v1.5
- ✓ `ruff check .` exits 0, `mypy src/` exits 0, 320 tests passing (QUAL-01) — v1.5
- ✓ LanceDB schema v4: `start_line`, `end_line`, `chunk_name`, `chunk_text` persisted per chunk; `ensure_schema_v4()` idempotent migration; all chunkers emit v4 fields (CHUNK-01) — v2.0
- ✓ CLI `corpus search` output: grep/IDE-clickable format `path:start-end [construct] score:X.XXX` with 200-char indented chunk text preview; Rich markup escaped (CHUNK-02) — v2.0

### Active (v2.1 — current milestone)

- [ ] MCP `corpus_search` response includes `start_line`, `end_line`, `text` per result — self-contained unit of knowledge (CHUNK-03)
- [ ] Python AST chunker: class header chunk (`ClassName`) + per-method chunks (`ClassName.method_name`) (SUB-01, SUB-02)
- [ ] TypeScript AST chunker: per-method chunks for class bodies using `ClassName.method_name` naming (SUB-03)
- [ ] `corpus search --name <fragment>` CLI flag; MCP `name` parameter — case-insensitive substring filter on `chunk_name` (NAME-01, NAME-02, NAME-03)
- [ ] MCP `corpus_search` accepts `sort_by` parameter (same vocabulary as CLI); scores normalised to 0–1 per query (SORT-01, NORM-01)
- [ ] `corpus search --output json` — JSON array to stdout for shell piping (JSON-01)
- [ ] MCP `corpus_graph` tool: accepts `slug`, returns upstream/downstream neighbour lists (GRAPH-01)
- [ ] 85%+ branch coverage on chunking modules; zero-hallucination parametrised integration test for line ranges (QUAL-01, QUAL-02)

### Planned (v3)

- [ ] MMR-style result diversity: near-duplicate/same-file chunks penalized; architectural spread ensured (RANK-01)
- [ ] Contiguous sub-chunk merging: adjacent method chunks from same file merged into single display entry (RANK-02)
- [ ] Optional `--rerank` flag: two-stage cross-encoder/LLM re-ranking of top-20 results (RANK-03)
- [ ] `corpus search --expand-graph`: results include immediate graph neighbors labeled `[Depends On]` / `[Imported By]` (GEXP-01)
- [ ] `corpus graph --depth N`: recursive N-hop walk (default 2); hub nodes (high indegree) labeled with count (GWALK-01, GWALK-02)
- [ ] Centrality scoring: `corpus index` computes indegree centrality; high-centrality files receive score multiplier in search (GCENT-01)
- [ ] `corpus search --within-graph <slug>`: +20% score boost for results in same graph component (soft filter) (GSCOPE-01)
- [ ] Multiple `--query` flags: AND-intersection of semantic spaces (MULTI-01)
- [ ] `--exclude-path <glob>`: structural negative filter on file path (MULTI-02)
- [ ] Source labeling: CLI results display source name prefix; MCP `corpus_search` includes `source` field (XSRC-01, XSRC-02)

### Out of Scope

- Hosted/cloud index — local-only (privacy, simplicity)
- Real-time file watching — manual index refresh only; daemon complexity not justified yet
- Web UI — CLI + MCP sufficient for target users
- LLM rewriting (corpus-analyzer original feature) — retained but not the focus
- Chunk-level results (CHUNK-01–CHUNK-03) — addressed in v2

## Context

**v2.0 shipped 2026-02-24. Chunk data layer and IDE-clickable CLI display complete. v2.1 roadmap: Phases 19–25 (MCP chunk response, method sub-chunking, name filtering, score normalisation, JSON output, graph MCP).**

- ~7,926 lines Python source across 54 files
- Tech stack: LanceDB, FastMCP, Pydantic, Typer, Rich, OllamaEmbedder (nomic-embed-text), tree-sitter + tree-sitter-language-pack; graph layer uses SQLite (`graph.sqlite`)
- 340 tests passing (pytest) — 10 new format_result tests added in v2.0
- XDG Base Directory compliant: config in `~/.config/corpus/`, data in `~/.local/share/corpus/`
- Single-user local tool; no daemon, no cloud dependency
- Zero mypy errors, zero ruff violations — clean linting baseline maintained through v2.0

Shipped in v2.0 (Phases 17–18):
- CLI output is now grep/IDE-clickable: `path:start-end [construct] score:X.XXX` with chunk text preview
- LanceDB stores exact line boundaries and full chunk text per chunk (schema v4)

Known limitations addressed in v2.1:
- MCP `corpus_search` still returns file-level results — CHUNK-03 (Phase 19)
- No method sub-chunking yet — SUB-01–SUB-03 (Phases 20–21)
- No `--name` filter yet — NAME-01–NAME-03 (Phase 22)
- `--min-score` help text references raw RRF range — will update after NORM-01 (Phase 23)

Remaining known limitations (deferred):
- Cold-start on first index after KEEP_ALIVE expiry still possible (pre-warm only covers MCP startup)
- `.d.ts` ambient declarations excluded at scanner level — niche use case, deferred indefinitely

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
| `get_parser(dialect)` from `tree_sitter_language_pack` with `@lru_cache` | Simpler than module-level globals; one Parser per dialect per process | ✓ Good — prevents 30s overhead on 500+ TS file corpora |
| `.tsx` and `.jsx` both use TSX grammar | TypeScript grammar produces ERROR nodes on JSX elements | ✓ Good — all JSX cases handled cleanly |
| Fall back only on exception or zero constructs, NOT on `has_error` | tree-sitter is error-tolerant; partial trees still yield good constructs | ✓ Good — no unnecessary fallback on syntax errors |
| `export default function(){}` → detect 'default' child, emit full export_statement | `declaration` field is `None` for anonymous default exports; special-case required | ✓ Good — `test_export_default_function` passes |
| Lazy import of `ts_chunker` inside `chunk_file` elif branch | Avoids circular import (`ts_chunker` imports from `chunker`) | ✓ Good — clean module boundary, no import side-effects |
| Separate `except ImportError:` before `except Exception:` (not merged) | Explicit over broad; ImportError is a distinct, expected failure mode | ✓ Good — IDX-09 contract clear and testable |
| Size guard before parser call (not after) | Minified files exit early with zero AST overhead | ✓ Good — 50K char threshold validated by test |
| Smoke test via Python API (`chunk_file`) not CLI (`corpus index`) | `corpus index` requires configured LanceDB sources; API call confirms dispatch wiring without external config | ✓ Good — clean, hermetic validation |

| CLI format: `file:start-end [construct] score:X.XXX` (grep/compiler-error pattern) | IDE-clickable natively in VSCode/IntelliJ; parseable by shell scripts; matches developer muscle memory | ✓ Good — shipped v2.0 |
| MCP returns full `text` (untruncated); CLI truncates to 200 chars | MCP callers are LLMs — self-contained chunk avoids follow-up file-read; CLI is human-readable terminal output | — Pending (CHUNK-03 v2.1) |
| `start_line`/`end_line` are 1-indexed, inclusive | Matches existing chunker convention (tree-sitter 0-indexed → +1); matches editor conventions | ✓ Good — shipped v2.0 |
| `ensure_schema_v4()` adds columns with defaults, does not rebuild | Same pattern as v3 migration (v1.1); users re-index to backfill; idempotent | ✓ Good — shipped v2.0 |
| `format_result` returns `(primary, preview \| None)` tuple — pure function | Console.print() owns rendering; testable without output side effects | ✓ Good — shipped v2.0 |
| `ClassName.method_name` dot notation for method sub-chunks | Unambiguous; matches Python attribute access syntax; makes `--name` filtering readable | — Pending (SUB-01–03 v2.1) |
| Class header chunk = docstring + `__init__` up to first non-assignment | Makes class purpose searchable independently from methods; bounded and deterministic | — Pending (v2.1) |
| `--name foo` flag (not `--construct name:foo`) | `--construct` already has a fixed meaning (agent construct type); separate flag is cleaner UX | — Pending (NAME-02 v2.1) |
| Case-insensitive substring match for `--name` | Most useful for exploratory search; exact match would require knowing the precise chunk name | — Pending (v2.1) |
| Per-query min-max normalisation (not global baseline) | Cross-query normalisation is misleading for hybrid scores; within-query is correct and simple | — Pending (NORM-01 v2.1) |
| Normalisation inside search engine (not display layer) | API, CLI, and MCP all receive same normalised value; existing score-range tests must be updated | — Pending (v2.1) |
| `--output json` flag (not separate subcommand) | Composable with all existing filter flags; keeps CLI surface small | — Pending (JSON-01 v2.1/v2.2) |
| `corpus_graph` MCP returns upstream/downstream lists (not graph object) | LLMs iterate with follow-up calls; flat lists are simpler to consume than nested structures | — Pending (GRAPH-01 v2.2) |
| `corpus_graph` MCP reuses `GraphStore` (no new storage) | Graph layer complete since v1.2; MCP tool is a thin wrapper; zero schema changes required | — Pending (v2.2) |

---
*Last updated: 2026-02-24 after v2.1 milestone started*

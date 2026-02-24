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

**Phases completed:** 4 phases, 11 plans
**Timeline:** 2026-02-24 (1 day)

**Delivered:** Achieved a zero-violation linting baseline across all 53 source files — `ruff check .` and `mypy src/` both exit 0 — via surgical config, auto-fix sweeps, and targeted manual fixes.

**Key accomplishments:**
- `pyproject.toml` surgical ruff/mypy config: `extend-exclude` for `.planning/`, per-file-ignores for E501 and B006
- `ruff --fix` sweep eliminated ~370 auto-fixable violations across 37 files
- Manual E741/E402/B017/B023/B904/E501 fixes across leaf modules, database hub, and cli.py
- `cast(Table, ...)` pattern at all 8 sqlite-utils call sites — grep-able and refactor-safe
- `DEFAULT_SYSTEM_PROMPT` trailing comma bug fixed (was `tuple[str]` at runtime, now `str`)
- `Atom` dataclass promoted to module level; nested closures fully annotated in chunked_processor.py

**Archive:** `.planning/milestones/v1.3-ROADMAP.md`

---


## v1.4 Search Precision (Shipped: 2026-02-24)

**Phases completed:** 2 phases, 3 plans
**Timeline:** 2026-02-24 (1 day)
**Files modified:** 23 (+2,566 / -48 lines)

**Delivered:** Gave users full control over search output quality — minimum-score filtering and sort-order control are now available across CLI, Python API, and MCP with RRF score guidance and a contextual hint when filtering eliminates all results.

**Key accomplishments:**
- `min_score: float = 0.0` parameter added to `hybrid_search()` with post-retrieval RRF score filtering (FILT-01)
- `--min-score` CLI option with RRF range help text (0.009–0.033) so users can calibrate thresholds (FILT-02)
- FILT-03 contextual hint: "No results above X.xxx. Run without --min-score to see available scores." on filtered-all
- `--sort-by score|date|title` CLI option with `_CLI_SORT_BY_MAP` translation to engine vocabulary
- Python `search()` API gains `sort_by` + `min_score` with `ValueError` on invalid sort values (PARITY-01/02)
- MCP `corpus_search()` gains `min_score: Optional[float]` with `None`→`0.0` + `filtered_by_min_score` signal (PARITY-03)

**Archive:** `.planning/milestones/v1.4-ROADMAP.md`

---


## v2 Chunk-Level Precision (Planned: 2026-02-24)

**Phases:** 9 phases (17–25), 17 plans
**Status:** Planning complete — not started

**Goal:** Expose chunk-level search results with exact line ranges and full text across CLI, MCP, and Python API. Add method-level sub-chunking for Python and TypeScript classes. Enable name-based filtering. Normalise scores to 0–1. Expose graph traversal via MCP. Add JSON output.

**Key outcomes (planned):**
- CLI output: `path/to/file.md:42-67 [skill] score:0.021` — IDE-clickable grep format with chunk text on second line
- MCP `corpus_search`: self-contained results with `start_line`, `end_line`, `text` per chunk
- Python and TypeScript classes sub-chunked at method level: `ClassName.method_name` naming
- `corpus search --name foo` and MCP `name` parameter for construct-name filtering
- MCP `sort_by` support; 0–1 normalised scores replace raw RRF values
- `corpus search --output json` for shell piping
- `corpus_graph` MCP tool for LLM graph traversal
- 85%+ branch coverage on chunking modules; zero-hallucination line-range contract validated

**Archive:** `.planning/milestones/v2-ROADMAP.md`

---


## v1.5 TypeScript AST Chunking (Shipped: 2026-02-24)

**Phases completed:** 2 phases (15–16), 5 plans
**Timeline:** 2026-02-24 (1 day)
**Python LOC:** ~7,811

**Delivered:** Replaced line-based chunking for TypeScript and JavaScript with tree-sitter AST-aware chunking — `.ts`, `.tsx`, `.js`, `.jsx` files now index at construct-level precision matching the existing Python AST chunker, with production safeguards for minified files and optional-dependency environments.

**Key accomplishments:**
- `chunk_typescript()` extracts 8 top-level node types (function, generator, class, abstract class, interface, type alias, lexical declaration, enum) with correct 1-indexed line boundaries and export-unwrapping
- Grammar dispatched by extension: TypeScript for `.ts`, TSX for `.tsx`/`.jsx`, JavaScript for `.js`; `@lru_cache` grammar loader prevents re-parsing on 500+ file corpora
- TDD RED→GREEN: 21-method `TestChunkTypeScript` class at full parity with `TestChunkPython` (all node types, non-ASCII identifiers, JSX parse, partial-error tree, catastrophic failure fallback)
- IDX-08 size guard: files >50,000 chars bypass AST parse entirely — safe for minified and generated files
- IDX-09 `ImportError` fallback: `chunk_file()` catches missing tree-sitter at call site; import of `ts_chunker` no longer raises in optional-dependency environments
- Zero-violation quality gate: ruff 0 violations, mypy 0 errors, 320 tests passing across 54 source files

**Archive:** `.planning/milestones/v1.5-ROADMAP.md`

---


## v2.0 Chunk Foundation (Shipped: 2026-02-24)

**Phases completed:** 2 phases (17–18), 4 plans
**Timeline:** 2026-02-24 (1 day)
**Python LOC:** ~7,926
**Files modified:** 26 (+3,540 / -986 lines)

**Delivered:** Established the chunk data foundation — every indexed chunk now carries exact line boundaries and full text in LanceDB; `corpus search` output switched to grep/IDE-clickable format with chunk text preview.

**Key accomplishments:**
- LanceDB schema v4: `ChunkRecord` gains `chunk_name`, `chunk_text`, `start_line`, `end_line` with idempotent `ensure_schema_v4()` migration (CHUNK-01)
- All three chunkers (Markdown, Python, TypeScript) emit v4 fields; `_enforce_char_limit` carries fields through all sub-chunk split paths
- Zero-hallucination line-range contract verified via parametrised round-trip test across `.md`/`.py`/`.ts` fixtures
- `format_result(result, cwd)` implemented with grep-style `path:start-end [type] score:X.XXX` output and 200-char indented chunk text preview (CHUNK-02)
- `search_command` render loop replaced — CLI output is now IDE-clickable in VSCode/IntelliJ
- Rich markup escaping on path, construct_type, and preview — no MarkupError on special chars; 340 tests passing

**Archive:** `.planning/milestones/v2.0-ROADMAP.md`

---


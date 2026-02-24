# Requirements: v2 Chunk-Level Precision

**Defined:** 2026-02-24
**Status:** PLANNING
**Milestone:** v2 Chunk-Level Precision
**Depends on:** v1.5 (shipped 2026-02-24)

---

## Milestone Goal

Expose chunk-level search results across CLI, Python API, and MCP — with exact line ranges, full chunk text, and construct names — while adding method-level sub-chunking for Python and TypeScript classes, a `chunk_name` persistence layer enabling name-based filtering, MCP sort/score normalisation, and two new surface features: JSON output and a graph MCP tool.

---

## Cluster A — Chunk-Level Display (HIGHEST PRIORITY)

These three requirements are a single cohesive unit: the data layer must land first (CHUNK-01), then CLI display (CHUNK-02) and MCP exposure (CHUNK-03) build on top.

- [ ] **CHUNK-01**: `ChunkRecord` schema updated to `v4`: `start_line: int`, `end_line: int`, `chunk_name: str`, and `chunk_text: str` persisted in LanceDB; `ensure_schema_v4()` idempotent migration adds columns to existing tables without data loss; existing rows default to `start_line=0`, `end_line=0`, `chunk_name=""`, `chunk_text=""`
- [x] **CHUNK-02**: `corpus search` CLI output changed from 3-line snippet format to grep/compiler-error format: `path/to/file.md:42-67 [skill] score:0.021` on the primary line; chunk text (truncated to 200 chars) on the next line; format is IDE-clickable (VSCode, IntelliJ parse `file:line` natively)
- [ ] **CHUNK-03**: MCP `corpus_search` tool response includes `start_line`, `end_line`, and `text` (full chunk text, untruncated) in each result object; response is a self-contained unit of knowledge — the LLM caller does not need to open the file to understand the chunk

---

## Cluster C — Method-Level Sub-Chunking (SECOND PRIORITY)

Depends on CHUNK-01 (line ranges must be persisted before method chunks are useful to display).

- [ ] **SUB-01**: Python AST chunker produces a "header chunk" for each class containing the class docstring and attribute definitions (`__init__` body up to first non-assignment statement); header chunk uses `chunk_name = "ClassName"` and correct line boundaries
- [ ] **SUB-02**: Python AST chunker produces a separate chunk for each method on a class; chunk name uses `ClassName.method_name` format; line boundaries are the method's `def` line to the last line of its body
- [ ] **SUB-03**: TypeScript/JavaScript AST chunker produces per-method chunks for class bodies (both Python classes and TS/JS classes follow the same `ClassName.method_name` naming convention)
- [ ] **SUB-04**: 85%+ branch coverage on both `py_chunker` (or equivalent Python chunking module) and `ts_chunker` chunking logic — measured via `pytest --cov` with branch coverage enabled

---

## Cluster B — `chunk_name` Persistence and Filtering (THIRD PRIORITY)

Depends on CHUNK-01 (schema v4 persists `chunk_name`).

- [ ] **NAME-01**: All three chunkers (Markdown heading-based, Python AST, TypeScript AST) populate `chunk_name` in returned chunk dicts; Markdown uses the heading text; Python uses function/class name; TypeScript uses existing construct name
- [ ] **NAME-02**: `corpus search --name <fragment>` CLI flag filters results to chunks whose `chunk_name` contains `<fragment>` (case-insensitive substring match); does not conflict with existing `--construct` flag
- [ ] **NAME-03**: MCP `corpus_search` tool accepts an optional `name: str` parameter that applies the same case-insensitive substring filter on `chunk_name`

---

## Cluster D — MCP Sort + Score Normalisation (THIRD PRIORITY)

Parallel to Cluster B — no ordering dependency between B and D.

- [ ] **SORT-01**: MCP `corpus_search` tool accepts `sort_by` parameter using the same vocabulary as the CLI: `relevance | construct | confidence | date | path`; default is `relevance`
- [ ] **NORM-01**: RRF scores are normalised to 0–1 range within each result set before returning from the search engine; normalisation uses per-query min-max rescaling; `min_score` threshold is applied after normalisation; CLI and MCP both receive normalised scores; Python API `SearchResult.score` is also normalised

---

## Cluster E — New Features

Depends on Clusters A–D being substantially complete (JSON output needs chunk fields; graph MCP is independent).

- [ ] **JSON-01**: `corpus search --output json` emits a JSON array to stdout where each object includes: `path`, `start_line`, `end_line`, `chunk_name`, `score`, `construct`, `confidence`, `text`; designed for shell piping (`corpus search "foo" --output json | jq '.[] | .path'`)
- [ ] **GRAPH-01**: MCP server exposes a `corpus_graph` tool accepting a `slug: str` parameter; returns upstream neighbours (files that link to the slug) and downstream neighbours (files the slug links to); response format mirrors `corpus graph <slug>` CLI output

---

## Quality Requirements

- [ ] **QUAL-01**: 85%+ branch coverage on all chunking modules (`py_chunker`, `ts_chunker`, and Markdown heading chunker) — measured with `pytest --cov --cov-branch`
- [ ] **QUAL-02**: "Zero hallucination" on line ranges — if `corpus search` reports `file.md:42-67`, the text at lines 42–67 of `file.md` must match the chunk text; validated by a parametrised integration test that cross-checks stored `start_line`/`end_line` against the actual file on disk
- [ ] **QUAL-03**: `uv run ruff check .` exits 0 and `uv run mypy src/` exits 0 after all v2 changes
- [ ] **QUAL-04**: All 320 existing tests continue to pass alongside all new v2 tests

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| `--construct name:foo` syntax (old deferred idea) | Superseded by `--name foo` flag — cleaner UX |
| Per-query min-max normalisation across multiple queries | Misleading for cross-query `min_score` comparisons; within-query normalisation is the correct scope |
| Real-time file watching | Manual index refresh only; daemon complexity not justified |
| Web UI | CLI + MCP sufficient for target users |
| Cloud/hosted index | Local-only (privacy, simplicity) |
| `.d.ts` ambient declaration indexing | Excluded at scanner level; niche use case, defer indefinitely |
| Import statement chunks | Near-zero standalone search value; inflates chunk count and BM25 noise |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CHUNK-01 | Phase 17 | Complete |
| CHUNK-02 | Phase 18 | Complete |
| CHUNK-03 | Phase 19 | Planned |
| SUB-01 | Phase 20 | Planned |
| SUB-02 | Phase 20 | Planned |
| SUB-03 | Phase 21 | Planned |
| SUB-04 | Phase 25 | Planned |
| NAME-01 | Phase 22 | Planned |
| NAME-02 | Phase 22 | Planned |
| NAME-03 | Phase 22 | Planned |
| SORT-01 | Phase 23 | Planned |
| NORM-01 | Phase 23 | Planned |
| JSON-01 | Phase 24 | Planned |
| GRAPH-01 | Phase 24 | Planned |
| QUAL-01 | Phase 25 | Planned |
| QUAL-02 | Phase 25 | Planned |
| QUAL-03 | Phase 25 | Planned |
| QUAL-04 | Phase 25 | Planned |

**Coverage:**
- v2 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-24*

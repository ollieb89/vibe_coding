# Roadmap: v2 Chunk-Level Precision

## Milestones

- ✅ **v1.0 MVP** — Phases 1–4 (shipped 2026-02-23)
- ✅ **v1.1 Search Quality** — Phases 5–6 (shipped 2026-02-23)
- ✅ **v1.2 Graph Linker** — Phases 7–8 (shipped 2026-02-24)
- ✅ **v1.3 Code Quality** — Phases 9–12 (shipped 2026-02-24)
- ✅ **v1.4 Search Precision** — Phases 13–14 (shipped 2026-02-24)
- ✅ **v1.5 TypeScript AST Chunking** — Phases 15–16 (shipped 2026-02-24)
- 🚧 **v2 Chunk-Level Precision** — Phases 17–25 (in progress)

---

## Phases

<details>
<summary>✅ v1.0–v1.5 (Phases 1–16) — SHIPPED</summary>

Full details: `.planning/milestones/v1.5-ROADMAP.md` and earlier milestone ROADMAP files.

</details>

---

### 🚧 v2 Chunk-Level Precision (In Progress)

**Milestone Goal:** Surface chunk-level search results with exact line ranges, full chunk text, and construct names across CLI, MCP, and Python API. Add method-level sub-chunking for Python and TypeScript classes. Enable name-based filtering. Normalise MCP scores. Expose graph traversal via MCP. Add JSON output.

**Priority order:** Cluster A (chunk display) → Cluster C (method sub-chunking) → Clusters B+D (chunk_name + MCP sort/normalise) → Cluster E (JSON output, graph MCP)

---

#### Phase 17: Schema v4 — Chunk Data Layer
**Goal**: LanceDB stores `start_line`, `end_line`, `chunk_name`, and `chunk_text` per chunk; existing data migrates cleanly without re-indexing; all chunkers populate these fields
**Depends on**: Phase 16 (v1.5 complete)
**Requirements**: CHUNK-01
**Success Criteria** (what must be TRUE):
  1. `ensure_schema_v4()` runs idempotently: adds `start_line`, `end_line`, `chunk_name`, `chunk_text` columns to existing LanceDB tables; re-running on an already-migrated table is a no-op
  2. `ChunkRecord` dataclass includes all four new fields with correct types; existing rows default to `start_line=0, end_line=0, chunk_name="", chunk_text=""`
  3. `corpus index` on a fresh source populates all four fields correctly for Markdown (heading text as `chunk_name`), Python (function/class name), and TypeScript (construct name) chunks
  4. A round-trip test: index a known file, query LanceDB directly, assert `start_line` and `end_line` match the actual source line numbers (zero-hallucination contract established at schema level)
  5. All 320 existing tests remain green
**Plans**: 2 plans

Plans:
- [x] 17-01-PLAN.md — TDD RED: write failing tests for `ChunkRecord` v4 fields and `ensure_schema_v4()` migration
- [x] 17-02-PLAN.md — GREEN: implement `ensure_schema_v4()`, update `ChunkRecord`, wire all chunkers to populate new fields

---

#### Phase 18: CLI Chunk Display
**Goal**: `corpus search` output switches to grep/compiler-error format showing exact line ranges — IDE-clickable and human-readable
**Depends on**: Phase 17 (chunk fields in schema)
**Requirements**: CHUNK-02
**Success Criteria** (what must be TRUE):
  1. `corpus search <query>` prints results in the format `path/to/file.md:42-67 [skill] score:0.021` on the primary line
  2. A second line shows the chunk text truncated to 200 characters with a trailing ellipsis if truncated
  3. The path is relative to the current working directory (shorter, more readable) — absolute path available via `--output json`
  4. Format is parseable by VSCode and IntelliJ problem matchers (file:line pattern)
  5. Existing `--limit`, `--min-score`, `--sort-by`, `--source`, `--type`, `--construct` flags all continue to work correctly with the new display format
  6. All 320+ existing tests remain green; new display format tests added for the formatter function
**Plans**: 2 plans

Plans:
- [ ] 18-01-PLAN.md — TDD RED: write failing tests for new result formatter (grep-style output, truncation, path format)
- [ ] 18-02-PLAN.md — GREEN: implement new formatter, wire into CLI search command, update any snapshot tests

---

#### Phase 19: MCP Chunk Response
**Goal**: MCP `corpus_search` returns self-contained chunk results — LLM callers receive `start_line`, `end_line`, and full `text` without needing to open the source file
**Depends on**: Phase 17 (chunk fields in schema)
**Requirements**: CHUNK-03
**Success Criteria** (what must be TRUE):
  1. Each result object in `corpus_search` response includes `start_line: int`, `end_line: int`, and `text: str` fields
  2. `text` is the full chunk text — untruncated — so the LLM receives a complete, self-contained unit of knowledge
  3. `start_line` and `end_line` match the values stored in LanceDB (zero-hallucination enforced at the response layer)
  4. Existing MCP result fields (`path`, `score`, `construct`, `confidence`, `summary`, `filtered_by_min_score`) are preserved unchanged
  5. MCP schema is backward-compatible: old clients that ignore unknown fields continue to work
  6. Integration test: call `corpus_search` via the MCP tool interface, assert new fields are present and non-empty for a freshly-indexed source
**Plans**: 2 plans

Plans:
- [ ] 19-01-PLAN.md — TDD RED: write failing MCP response tests asserting `start_line`, `end_line`, `text` fields
- [ ] 19-02-PLAN.md — GREEN: update MCP tool handler to include chunk fields in response; update `SearchResult` or intermediate dict as needed

---

#### Phase 20: Python Method Sub-Chunking
**Goal**: Python classes produce a header chunk (docstring + attributes) plus one chunk per method, using `ClassName.method_name` naming — enabling precise method-level retrieval
**Depends on**: Phase 17 (line ranges are persisted; method chunks are worth storing)
**Requirements**: SUB-01, SUB-02
**Success Criteria** (what must be TRUE):
  1. Given a class with a docstring, `__init__`, and two methods, the Python chunker produces: one header chunk (`ClassName`, lines covering docstring + `__init__` up to first non-assignment), one chunk per method (`ClassName.method_one`, `ClassName.method_two`)
  2. Header chunk contains the class docstring and `__init__` body; it does NOT contain method bodies
  3. Method chunks use `chunk_name = "ClassName.method_name"` format; `start_line` and `end_line` are the method's `def` line to the last line of its body
  4. Standalone functions (not inside a class) are unchanged — still extracted as top-level chunks
  5. `TestChunkPython` suite updated: existing class-level tests updated to reflect new header+method structure; new tests cover header chunk content, method chunk naming, and line boundary accuracy
  6. `corpus index` on a Python file with classes produces the new sub-chunks in LanceDB; a `corpus search "method_name"` query returns the method chunk, not the whole class
**Plans**: 2 plans

Plans:
- [ ] 20-01-PLAN.md — TDD RED: update `TestChunkPython` class tests to expect header+method structure; add new method-level test cases
- [ ] 20-02-PLAN.md — GREEN: refactor Python AST chunker to emit header chunk + per-method chunks for class nodes

---

#### Phase 21: TypeScript Method Sub-Chunking
**Goal**: TypeScript/JavaScript class bodies are sub-chunked at method level with the same `ClassName.method_name` naming as Python — consistent cross-language behaviour
**Depends on**: Phase 20 (Python sub-chunking establishes the pattern)
**Requirements**: SUB-03
**Success Criteria** (what must be TRUE):
  1. Given a TypeScript class with a constructor and two methods, `chunk_typescript()` produces a header chunk (`ClassName`) and one chunk per method (`ClassName.constructor`, `ClassName.method_one`, `ClassName.method_two`)
  2. Header chunk covers the class declaration line and any class-level properties; method chunks cover each `method_definition` node
  3. Abstract classes and exported classes follow the same sub-chunking pattern
  4. `TestChunkTypeScript` suite updated with method sub-chunking cases mirroring the new Python tests
  5. Integration: `corpus index` on a TypeScript file with classes produces method-level chunks in LanceDB; a `corpus search "method_name"` query returns the method chunk
**Plans**: 2 plans

Plans:
- [ ] 21-01-PLAN.md — TDD RED: add TypeScript method sub-chunking tests to `TestChunkTypeScript`
- [ ] 21-02-PLAN.md — GREEN: refactor `chunk_typescript()` to emit header + per-method chunks for class_declaration nodes

---

#### Phase 22: `chunk_name` Filtering — CLI and MCP
**Goal**: Users can filter search results by chunk name via `--name` on the CLI and `name` on the MCP tool — enables targeting a specific function or method by name
**Depends on**: Phase 17 (chunk_name stored in schema), Phase 20–21 (method names populated)
**Requirements**: NAME-01, NAME-02, NAME-03
**Success Criteria** (what must be TRUE):
  1. All three chunkers (Markdown, Python, TypeScript) consistently populate `chunk_name` in returned chunk dicts: Markdown uses heading text, Python uses `function_name` or `ClassName` / `ClassName.method_name`, TypeScript uses construct name or `ClassName.method_name`
  2. `corpus search "query" --name foo` returns only results where `chunk_name` contains `"foo"` (case-insensitive substring); `--name` is combinable with all existing filters
  3. `corpus search --name foo` with no query string is valid and returns all chunks matching the name filter (ordered by relevance against empty query, or by `--sort-by` flag)
  4. MCP `corpus_search` tool accepts `name: Optional[str]` parameter and applies the same substring filter
  5. `--name` help text explains it filters by construct name (function, class, method, or heading)
**Plans**: 2 plans

Plans:
- [ ] 22-01-PLAN.md — TDD RED: write failing tests for `--name` CLI flag and MCP `name` parameter
- [ ] 22-02-PLAN.md — GREEN: add name filter to search engine post-retrieval step; wire `--name` CLI flag and MCP parameter

---

#### Phase 23: MCP Sort + Score Normalisation
**Goal**: MCP clients can sort results and use intuitive 0–1 score thresholds — normalised scores make `min_score` calibration straightforward without per-session score range discovery
**Depends on**: Phase 17 (scores are well-defined; normalisation is meaningful with chunk-level results)
**Requirements**: SORT-01, NORM-01
**Success Criteria** (what must be TRUE):
  1. MCP `corpus_search` tool accepts `sort_by: Optional[str]` using vocabulary `relevance | construct | confidence | date | path`; default is `relevance`; invalid values return a clear error message
  2. All scores returned by CLI, Python API, and MCP are normalised to [0.0, 1.0] per query using min-max rescaling; a single result always scores 1.0; ties are handled without division by zero
  3. `min_score` threshold is applied after normalisation; a threshold of `0.5` reliably filters the lower half of results regardless of the raw RRF range
  4. CLI `--min-score` help text updated to reflect the 0–1 normalised range (removes the 0.009–0.033 RRF guidance, which is now stale)
  5. Python API `SearchResult.score` is the normalised value; existing tests that assert on score ranges are updated
  6. `filtered_by_min_score` MCP field continues to work correctly after normalisation
**Plans**: 2 plans

Plans:
- [ ] 23-01-PLAN.md — TDD RED: write failing tests for normalised scores (single result = 1.0, two-result ordering preserved, `min_score=0.5` bisects correctly)
- [ ] 23-02-PLAN.md — GREEN: implement per-query min-max normalisation in search engine; add `sort_by` to MCP tool; update CLI help text

---

#### Phase 24: JSON Output + Graph MCP Tool
**Goal**: Shell-pipeble JSON output from `corpus search` and graph traversal via MCP — two independent new surfaces
**Depends on**: Phase 17–23 (JSON output uses chunk fields; graph MCP is independent of chunk work)
**Requirements**: JSON-01, GRAPH-01
**Success Criteria** (what must be TRUE):
  1. `corpus search "query" --output json` emits a JSON array to stdout; each object includes: `path`, `start_line`, `end_line`, `chunk_name`, `score`, `construct`, `confidence`, `text`; rich formatting is suppressed when `--output json` is active
  2. `corpus search "query" --output json | jq '.[] | .path'` works correctly in a standard shell pipeline
  3. `--output json` is combinable with all existing filter flags (`--limit`, `--min-score`, `--sort-by`, `--source`, `--type`, `--construct`, `--name`)
  4. MCP server exposes a `corpus_graph` tool accepting `slug: str`; returns `upstream: list[str]` (files that link to the slug) and `downstream: list[str]` (files the slug links to); empty lists (not errors) when no edges exist
  5. `corpus_graph` calls the existing `GraphStore.search_paths()` and adjacency query logic — no new storage layer required
  6. MCP `corpus_graph` tool is listed in the MCP server's tool manifest so LLM clients can discover and invoke it
**Plans**: 2 plans

Plans:
- [ ] 24-01-PLAN.md — TDD RED: write failing tests for `--output json` formatter and `corpus_graph` MCP tool
- [ ] 24-02-PLAN.md — GREEN: implement JSON output mode in CLI search; implement `corpus_graph` MCP tool wired to `GraphStore`

---

#### Phase 25: Quality Gate
**Goal**: v2 milestone meets the "Zero Hallucination" line-range contract and 85%+ branch coverage quality bar; codebase stays clean
**Depends on**: Phases 17–24
**Requirements**: SUB-04, QUAL-01, QUAL-02, QUAL-03, QUAL-04
**Success Criteria** (what must be TRUE):
  1. `pytest --cov=corpus_analyzer --cov-branch --cov-report=term-missing` reports 85%+ branch coverage for `ingest/py_chunker.py` (or equivalent Python chunking module) and `ingest/ts_chunker.py`
  2. A parametrised integration test cross-checks every `start_line`/`end_line` stored in LanceDB against the actual file on disk for a set of reference fixtures — zero mismatches
  3. `uv run ruff check .` exits 0 across all v2 changes
  4. `uv run mypy src/` exits 0 across all v2 changes
  5. All v1.5 tests (320) plus all new v2 tests pass without modification to existing test logic
  6. `PROJECT.md` and `MILESTONES.md` updated to record v2 milestone as complete
**Plans**: 1 plan

Plans:
- [ ] 25-01-PLAN.md — Coverage measurement, zero-hallucination parametrised test, ruff + mypy gate, milestone documentation update

---

## Phase Summary

| Phase | Name | Cluster | Requirements | Plans |
|-------|------|---------|--------------|-------|
| 17 | Schema v4 — Chunk Data Layer | A | CHUNK-01 | 2 |
| 18 | CLI Chunk Display | A | CHUNK-02 | 2 |
| 19 | MCP Chunk Response | A | CHUNK-03 | 2 |
| 20 | Python Method Sub-Chunking | C | SUB-01, SUB-02 | 2 |
| 21 | TypeScript Method Sub-Chunking | C | SUB-03 | 2 |
| 22 | `chunk_name` Filtering — CLI and MCP | B | NAME-01, NAME-02, NAME-03 | 2 |
| 23 | MCP Sort + Score Normalisation | D | SORT-01, NORM-01 | 2 |
| 24 | JSON Output + Graph MCP Tool | E | JSON-01, GRAPH-01 | 2 |
| 25 | Quality Gate | — | SUB-04, QUAL-01–04 | 1 |

**Total:** 9 phases, 17 plans

---

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 5/5 | Complete | 2026-02-23 |
| 2. Search Core | v1.0 | 5/5 | Complete | 2026-02-23 |
| 3. Agent Interfaces | v1.0 | 3/3 | Complete | 2026-02-23 |
| 4. Defensive Hardening | v1.0 | 2/2 | Complete | 2026-02-23 |
| 5. Extension Filtering | v1.1 | 2/2 | Complete | 2026-02-23 |
| 6. Frontmatter Classification | v1.1 | 2/2 | Complete | 2026-02-23 |
| 7. Graph Layer | v1.2 | —/— | Complete | 2026-02-24 |
| 8. Cleanup | v1.2 | 1/1 | Complete | 2026-02-24 |
| 9. Config and Auto-Fix | v1.3 | 2/2 | Complete | 2026-02-24 |
| 10. Manual Ruff — Leaf to Hub | v1.3 | 3/3 | Complete | 2026-02-24 |
| 11. Manual Ruff — CLI + Mypy | v1.3 | 5/5 | Complete | 2026-02-24 |
| 12. Validation Gate | v1.3 | 1/1 | Complete | 2026-02-24 |
| 13. Engine Min-Score Filter | v1.4 | 1/1 | Complete | 2026-02-24 |
| 14. API / MCP / CLI Parity | v1.4 | 2/2 | Complete | 2026-02-24 |
| 15. Core AST Chunker | v1.5 | 2/2 | Complete | 2026-02-24 |
| 16. Integration Hardening | v1.5 | 3/3 | Complete | 2026-02-24 |
| 17. Schema v4 — Chunk Data Layer | v2 | 2/2 | Complete | 2026-02-24 |
| 18. CLI Chunk Display | v2 | 0/2 | Planned | — |
| 19. MCP Chunk Response | v2 | 0/2 | Planned | — |
| 20. Python Method Sub-Chunking | v2 | 0/2 | Planned | — |
| 21. TypeScript Method Sub-Chunking | v2 | 0/2 | Planned | — |
| 22. chunk_name Filtering | v2 | 0/2 | Planned | — |
| 23. MCP Sort + Score Normalisation | v2 | 0/2 | Planned | — |
| 24. JSON Output + Graph MCP Tool | v2 | 0/2 | Planned | — |
| 25. Quality Gate | v2 | 0/1 | Planned | — |

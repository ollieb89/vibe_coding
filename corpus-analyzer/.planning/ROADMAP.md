# Roadmap: Corpus v2.1 Result Quality

## Milestones

- ✅ **v1.0 MVP** - Phases 1–4 (shipped 2026-02-23)
- ✅ **v1.1 Search Quality** - Phases 5–6 (shipped 2026-02-23)
- ✅ **v1.2 Graph Linker** - Phases 7–8 (shipped 2026-02-24)
- ✅ **v1.3 Code Quality** - Phases 9–12 (shipped 2026-02-24)
- ✅ **v1.4 Search Precision** - Phases 13–14 (shipped 2026-02-24)
- ✅ **v1.5 TypeScript AST Chunking** - Phases 15–16 (shipped 2026-02-24)
- ✅ **v2.0 Chunk Foundation** - Phases 17–18 (shipped 2026-02-24)
- 🚧 **v2.1 Result Quality** - Phases 19–25 (in progress)

## Phases

<details>
<summary>✅ v1.0–v2.0 (Phases 1–18) — SHIPPED 2026-02-24</summary>

See archived milestone files in `.planning/milestones/`.

</details>

### 🚧 v2.1 Result Quality (Phases 19–25)

**Milestone Goal:** Complete the chunk-level search experience — MCP self-contained chunks, method sub-chunking, name filtering, normalised scores, JSON output, and graph MCP.

#### Phase 19: MCP Chunk Response

**Goal**: MCP `corpus_search` results become self-contained units of knowledge with exact line boundaries and full chunk text
**Depends on**: Phase 18 (CLI chunk display complete; v4 schema with `start_line`, `end_line`, `chunk_text` in LanceDB)
**Requirements**: CHUNK-03
**Success Criteria** (what must be TRUE):
  1. MCP `corpus_search` result objects include `start_line`, `end_line`, and `text` fields alongside existing fields
  2. The `text` field contains the full untruncated chunk text (not the 200-char preview used by CLI)
  3. An LLM caller receives everything needed to understand a result without a follow-up file-read tool call
  4. Legacy rows (where `chunk_text` is empty) return empty string for `text` rather than erroring
**Plans**: 1 plan

Plans:
- [ ] 19-01-PLAN.md — TDD: self-contained MCP response (text, start_line, end_line; remove snippet/full_content)

---

#### Phase 20: Python Method Sub-Chunking

**Goal**: Python classes are indexed at method granularity — each method becomes a separately searchable chunk named `ClassName.method_name`
**Depends on**: Phase 19
**Requirements**: SUB-01, SUB-02
**Success Criteria** (what must be TRUE):
  1. Indexing a Python file with a class produces a `ClassName` header chunk containing the docstring and `__init__` body up to the first non-assignment statement
  2. Each method in the class produces a separate `ClassName.method_name` chunk with correct `start_line`/`end_line`
  3. Special methods (`__init__`, `__str__`, `__repr__`) follow the same dot-notation naming
  4. The monolithic class chunk no longer appears — it is replaced by the header + per-method chunks
  5. Re-indexing an already-indexed Python file produces the same chunks deterministically
**Plans**: TBD

Plans:
- [ ] 20-01: TBD

---

#### Phase 21: TypeScript Method Sub-Chunking

**Goal**: TypeScript classes are indexed at method granularity — each method becomes a separately searchable chunk named `ClassName.method_name`
**Depends on**: Phase 20
**Requirements**: SUB-03
**Success Criteria** (what must be TRUE):
  1. Indexing a TypeScript file with a class produces per-method chunks for each `method_definition` node
  2. Each method chunk is named `ClassName.method_name` with correct `start_line`/`end_line`
  3. The constructor becomes `ClassName.constructor`
  4. Top-level functions and non-class constructs are unaffected and continue to index as before
**Plans**: TBD

Plans:
- [ ] 21-01: TBD

---

#### Phase 22: Name Filtering

**Goal**: Users can filter search results by chunk name on both CLI and MCP, enabling targeted lookup of specific methods or constructs
**Depends on**: Phase 21
**Requirements**: NAME-01, NAME-02, NAME-03
**Success Criteria** (what must be TRUE):
  1. `corpus search --name foo` returns only results whose `chunk_name` contains `foo` (case-insensitive substring match)
  2. `--name` composes with all existing filter flags (`--source`, `--type`, `--construct`, `--min-score`, `--sort-by`, `--limit`)
  3. `corpus search --name foo` with no positional query argument is valid and lists matching chunks ordered by `--sort-by` (default: relevance)
  4. MCP `corpus_search` accepts a `name: Optional[str]` parameter applying the same case-insensitive substring semantics
  5. `corpus search --name ClassName.method` narrows results to that specific method chunk
**Plans**: TBD

Plans:
- [ ] 22-01: TBD

---

#### Phase 23: Score Normalisation and MCP Sort

**Goal**: All search surfaces return scores in a consistent 0–1 range; MCP gains `sort_by` parameter parity with CLI
**Depends on**: Phase 22
**Requirements**: NORM-01, SORT-01
**Success Criteria** (what must be TRUE):
  1. `corpus search` displays scores in 0–1 range; no result shows a raw RRF value (0.009–0.033 range gone from output)
  2. Python API `SearchResult.score` values are in 0–1 range for all returned results
  3. MCP `corpus_search` result scores are in 0–1 range
  4. MCP `corpus_search` accepts `sort_by` with the same vocabulary as CLI (`relevance | construct | confidence | date | path`)
  5. `--min-score` help text is updated to reference the 0–1 normalised range (old RRF range documentation removed)
**Plans**: TBD

Plans:
- [ ] 23-01: TBD

---

#### Phase 24: JSON Output

**Goal**: `corpus search` results can be piped to other tools via a machine-readable JSON format
**Depends on**: Phase 23
**Requirements**: JSON-01
**Success Criteria** (what must be TRUE):
  1. `corpus search --output json` emits a valid JSON array to stdout with no Rich formatting characters
  2. Each JSON object contains the same fields as a `SearchResult` (path, score, construct_type, chunk_name, start_line, end_line, text, etc.)
  3. `--output json` composes with all existing filter flags including `--name`, `--min-score`, `--sort-by`, `--limit`
  4. The output is valid JSON parseable by `jq` and Python `json.loads()`
**Plans**: TBD

Plans:
- [ ] 24-01: TBD

---

#### Phase 25: Graph MCP and Quality Gate

**Goal**: LLM clients can traverse the codebase dependency graph via MCP; chunking module coverage meets the 85% branch target with a zero-hallucination line-range contract
**Depends on**: Phase 24
**Requirements**: GRAPH-01, QUAL-01, QUAL-02
**Success Criteria** (what must be TRUE):
  1. MCP exposes a `corpus_graph` tool that accepts `slug: str` and returns `upstream` and `downstream` neighbour path lists
  2. `corpus_graph` reuses the existing `GraphStore` with zero new storage — no schema changes required
  3. `pytest --cov --cov-branch` reports 85%+ branch coverage on `chunking/chunker.py`, `chunking/py_chunker.py`, and `chunking/ts_chunker.py`
  4. A parametrised integration test verifies that every stored `start_line`/`end_line` matches actual file content for `.md`, `.py`, and `.ts` fixtures (zero hallucination)
**Plans**: TBD

Plans:
- [ ] 25-01: TBD

---

## Phase Details

### Phase 19: MCP Chunk Response
**Goal**: MCP `corpus_search` results become self-contained units of knowledge with exact line boundaries and full chunk text
**Depends on**: Phase 18
**Requirements**: CHUNK-03
**Success Criteria** (what must be TRUE):
  1. MCP `corpus_search` result objects include `start_line`, `end_line`, and `text` fields alongside existing fields
  2. The `text` field contains the full untruncated chunk text (not the 200-char preview used by CLI)
  3. An LLM caller receives everything needed to understand a result without a follow-up file-read tool call
  4. Legacy rows (where `chunk_text` is empty) return empty string for `text` rather than erroring
**Plans**: 1 plan

### Phase 20: Python Method Sub-Chunking
**Goal**: Python classes are indexed at method granularity — each method becomes a separately searchable chunk named `ClassName.method_name`
**Depends on**: Phase 19
**Requirements**: SUB-01, SUB-02
**Success Criteria** (what must be TRUE):
  1. Indexing a Python file with a class produces a `ClassName` header chunk containing the docstring and `__init__` body up to the first non-assignment statement
  2. Each method in the class produces a separate `ClassName.method_name` chunk with correct `start_line`/`end_line`
  3. Special methods (`__init__`, `__str__`, `__repr__`) follow the same dot-notation naming
  4. The monolithic class chunk no longer appears — it is replaced by the header + per-method chunks
  5. Re-indexing an already-indexed Python file produces the same chunks deterministically
**Plans**: TBD

### Phase 21: TypeScript Method Sub-Chunking
**Goal**: TypeScript classes are indexed at method granularity — each method becomes a separately searchable chunk named `ClassName.method_name`
**Depends on**: Phase 20
**Requirements**: SUB-03
**Success Criteria** (what must be TRUE):
  1. Indexing a TypeScript file with a class produces per-method chunks for each `method_definition` node
  2. Each method chunk is named `ClassName.method_name` with correct `start_line`/`end_line`
  3. The constructor becomes `ClassName.constructor`
  4. Top-level functions and non-class constructs are unaffected and continue to index as before
**Plans**: TBD

### Phase 22: Name Filtering
**Goal**: Users can filter search results by chunk name on both CLI and MCP, enabling targeted lookup of specific methods or constructs
**Depends on**: Phase 21
**Requirements**: NAME-01, NAME-02, NAME-03
**Success Criteria** (what must be TRUE):
  1. `corpus search --name foo` returns only results whose `chunk_name` contains `foo` (case-insensitive substring match)
  2. `--name` composes with all existing filter flags (`--source`, `--type`, `--construct`, `--min-score`, `--sort-by`, `--limit`)
  3. `corpus search --name foo` with no positional query argument is valid and lists matching chunks ordered by `--sort-by` (default: relevance)
  4. MCP `corpus_search` accepts a `name: Optional[str]` parameter applying the same case-insensitive substring semantics
  5. `corpus search --name ClassName.method` narrows results to that specific method chunk
**Plans**: TBD

### Phase 23: Score Normalisation and MCP Sort
**Goal**: All search surfaces return scores in a consistent 0–1 range; MCP gains `sort_by` parameter parity with CLI
**Depends on**: Phase 22
**Requirements**: NORM-01, SORT-01
**Success Criteria** (what must be TRUE):
  1. `corpus search` displays scores in 0–1 range; no result shows a raw RRF value (0.009–0.033 range gone from output)
  2. Python API `SearchResult.score` values are in 0–1 range for all returned results
  3. MCP `corpus_search` result scores are in 0–1 range
  4. MCP `corpus_search` accepts `sort_by` with the same vocabulary as CLI (`relevance | construct | confidence | date | path`)
  5. `--min-score` help text is updated to reference the 0–1 normalised range (old RRF range documentation removed)
**Plans**: TBD

### Phase 24: JSON Output
**Goal**: `corpus search` results can be piped to other tools via a machine-readable JSON format
**Depends on**: Phase 23
**Requirements**: JSON-01
**Success Criteria** (what must be TRUE):
  1. `corpus search --output json` emits a valid JSON array to stdout with no Rich formatting characters
  2. Each JSON object contains the same fields as a `SearchResult` (path, score, construct_type, chunk_name, start_line, end_line, text, etc.)
  3. `--output json` composes with all existing filter flags including `--name`, `--min-score`, `--sort-by`, `--limit`
  4. The output is valid JSON parseable by `jq` and Python `json.loads()`
**Plans**: TBD

### Phase 25: Graph MCP and Quality Gate
**Goal**: LLM clients can traverse the codebase dependency graph via MCP; chunking module coverage meets the 85% branch target with a zero-hallucination line-range contract
**Depends on**: Phase 24
**Requirements**: GRAPH-01, QUAL-01, QUAL-02
**Success Criteria** (what must be TRUE):
  1. MCP exposes a `corpus_graph` tool that accepts `slug: str` and returns `upstream` and `downstream` neighbour path lists
  2. `corpus_graph` reuses the existing `GraphStore` with zero new storage — no schema changes required
  3. `pytest --cov --cov-branch` reports 85%+ branch coverage on `chunking/chunker.py`, `chunking/py_chunker.py`, and `chunking/ts_chunker.py`
  4. A parametrised integration test verifies that every stored `start_line`/`end_line` matches actual file content for `.md`, `.py`, and `.ts` fixtures (zero hallucination)
**Plans**: TBD

## Progress

**Execution Order:** 19 → 20 → 21 → 22 → 23 → 24 → 25

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1–4. MVP | v1.0 | 15/15 | Complete | 2026-02-23 |
| 5–6. Search Quality | v1.1 | 4/4 | Complete | 2026-02-23 |
| 7–8. Graph Linker | v1.2 | 1/1 | Complete | 2026-02-24 |
| 9–12. Code Quality | v1.3 | 11/11 | Complete | 2026-02-24 |
| 13–14. Search Precision | v1.4 | 3/3 | Complete | 2026-02-24 |
| 15–16. TS AST Chunking | v1.5 | 5/5 | Complete | 2026-02-24 |
| 17–18. Chunk Foundation | v2.0 | 4/4 | Complete | 2026-02-24 |
| 19. MCP Chunk Response | 1/1 | Complete    | 2026-02-24 | - |
| 20. Python Sub-Chunking | v2.1 | 0/TBD | Not started | - |
| 21. TypeScript Sub-Chunking | v2.1 | 0/TBD | Not started | - |
| 22. Name Filtering | v2.1 | 0/TBD | Not started | - |
| 23. Score Normalisation + MCP Sort | v2.1 | 0/TBD | Not started | - |
| 24. JSON Output | v2.1 | 0/TBD | Not started | - |
| 25. Graph MCP + Quality Gate | v2.1 | 0/TBD | Not started | - |

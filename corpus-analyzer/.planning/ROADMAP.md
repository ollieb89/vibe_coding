# Roadmap: Corpus

## Milestones

- ✅ **v1.0 MVP** — Phases 1–4 (shipped 2026-02-23)
- ✅ **v1.1 Search Quality** — Phases 5–6 (shipped 2026-02-23)
- ✅ **v1.2 Graph Linker** — Phases 7–8 (shipped 2026-02-24)
- ✅ **v1.3 Code Quality** — Phases 9–12 (shipped 2026-02-24)
- 🚧 **v1.4 Search Precision** — Phases 13–14 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1–4) — SHIPPED 2026-02-23</summary>

- [x] Phase 1: Foundation (5/5 plans) — completed 2026-02-23
- [x] Phase 2: Search Core (5/5 plans) — completed 2026-02-23
- [x] Phase 3: Agent Interfaces (3/3 plans) — completed 2026-02-23
- [x] Phase 4: Defensive Hardening (2/2 plans) — completed 2026-02-23

Full details: `.planning/milestones/v1.0-ROADMAP.md`

</details>

<details>
<summary>✅ v1.1 Search Quality (Phases 5–6) — SHIPPED 2026-02-23</summary>

- [x] Phase 5: Extension Filtering (2/2 plans) — completed 2026-02-23
- [x] Phase 6: Frontmatter Classification (2/2 plans) — completed 2026-02-23

Full details: `.planning/milestones/v1.1-ROADMAP.md`

</details>

<details>
<summary>✅ v1.2 Graph Linker (Phases 7–8) — SHIPPED 2026-02-24</summary>

- [x] Phase 7: Graph Layer — Relationship extraction, storage, and CLI query command (COMPLETE)
- [x] Phase 8: Cleanup — Remove dead `use_llm_classification` parameter (completed 2026-02-24)

Full details: `.planning/milestones/v1.2-ROADMAP.md`

</details>

<details>
<summary>✅ v1.3 Code Quality (Phases 9–12) — SHIPPED 2026-02-24</summary>

- [x] Phase 9: Config and Auto-Fix (2/2 plans) — completed 2026-02-24
- [x] Phase 10: Manual Ruff — Leaf to Hub (3/3 plans) — completed 2026-02-24
- [x] Phase 11: Manual Ruff — CLI + Mypy (5/5 plans) — completed 2026-02-24
- [x] Phase 12: Validation Gate (1/1 plan) — completed 2026-02-24

Full details: `.planning/milestones/v1.3-ROADMAP.md`

</details>

### 🚧 v1.4 Search Precision (In Progress)

**Milestone Goal:** Give users control over search output — expose relevance scores, add sorting, and filter noise via a minimum-score threshold — across CLI, Python API, and MCP.

- [x] **Phase 13: Engine Min-Score Filter** - Add `min_score` parameter to `hybrid_search()` with post-retrieval Python filtering — **1 plan** (completed 2026-02-24)
- [ ] **Phase 14: API / MCP / CLI Parity** - Wire `min_score` and `sort_by` through all three caller surfaces with help text and empty-result hint

## Phase Details

### Phase 13: Engine Min-Score Filter
**Goal**: Users can filter `corpus search` results by a minimum relevance score via a parameter built into the search engine
**Depends on**: Phase 12 (clean codebase baseline)
**Requirements**: FILT-01
**Success Criteria** (what must be TRUE):
  1. `hybrid_search()` accepts a `min_score: float = 0.0` parameter and returns only results at or above that threshold
  2. Passing `min_score=0.0` (the default) returns identical results to the current v1.3 behaviour — zero regression
  3. Passing `min_score=99.0` returns an empty list regardless of query
  4. All 281 existing tests remain green after the engine change
**Plans**: 1 plan

Plans:
- [ ] 13-01-PLAN.md — TDD: write failing min_score tests (RED) then implement engine filter (GREEN)

### Phase 14: API / MCP / CLI Parity
**Goal**: Users can control min-score filtering and result sort order through all three interfaces — CLI, Python API, and MCP — with a contextual hint when filtering eliminates all results
**Depends on**: Phase 13
**Requirements**: FILT-02, FILT-03, PARITY-01, PARITY-02, PARITY-03
**Success Criteria** (what must be TRUE):
  1. `corpus search --min-score 0.02` filters results below 0.02 and `--min-score` help text documents the RRF score range (~0.009–0.033)
  2. When `--min-score` filters all results, the CLI prints: "No results above X.xxx. Run without --min-score to see available scores."
  3. `from corpus import search` accepts `sort_by` and `min_score` keyword arguments and forwards them to the engine
  4. MCP `corpus_search` tool accepts a `min_score` parameter and passes it to the engine
  5. `uv run ruff check .` and `uv run mypy src/` both exit 0 after all changes
**Plans**: 2 plans

Plans:
- [ ] 14-01-PLAN.md — TDD: add --min-score (FILT-02), FILT-03 hint, and --sort-by to CLI search command
- [ ] 14-02-PLAN.md — TDD: add sort_by + min_score to Python API and min_score to MCP corpus_search

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
| 13. Engine Min-Score Filter | 1/1 | Complete    | 2026-02-24 | - |
| 14. API / MCP / CLI Parity | v1.4 | 0/? | Not started | - |

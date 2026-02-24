# Roadmap: Corpus

## Milestones

- ✅ **v1.0 MVP** — Phases 1–4 (shipped 2026-02-23)
- ✅ **v1.1 Search Quality** — Phases 5–6 (shipped 2026-02-23)
- 🔄 **v1.2 Graph Linker** — Phases 7–8 (in progress 2026-02-24)

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

### v1.2 Graph Linker (Phases 7–8)

- [x] **Phase 7: Graph Layer** — Relationship extraction, storage, and CLI query command (COMPLETE)
- [ ] **Phase 8: Cleanup** — Remove dead `use_llm_classification` parameter

## Phase Details

### Phase 7: Graph Layer
**Goal**: Developers can explore file relationships extracted automatically during indexing
**Depends on**: Phase 6 (indexing pipeline in place)
**Requirements**: GRAPH-01, GRAPH-02, GRAPH-03, GRAPH-04, GRAPH-05
**Status**: COMPLETE (merged to main 2026-02-24)
**Success Criteria** (what must be TRUE):
  1. Running `corpus graph <slug>` shows all files that reference that file (upstream neighbors)
  2. Running `corpus graph <slug>` shows all files that file references (downstream neighbors)
  3. Running `corpus index` automatically populates graph edges from `## Related Skills` / `## Related Files` sections with no extra commands
  4. When multiple files share the same slug, `corpus index` prints a warning and resolves the reference to the candidate closest in filesystem path to the referencing file
  5. Running `corpus graph --show-duplicates` lists every slug collision and the paths involved
**Plans**: TBD

### Phase 8: Cleanup
**Goal**: The `index_source()` function signature no longer carries the dead `use_llm_classification` parameter
**Depends on**: Phase 7
**Requirements**: CLEAN-01
**Success Criteria** (what must be TRUE):
  1. `index_source()` has no `use_llm_classification` parameter in its signature or any call sites
  2. All existing tests pass with no regressions after the removal
**Plans**: 1 plan

Plans:
- [ ] 08-01-PLAN.md — Remove use_llm_classification from indexer, config, and tests

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
| 8. Cleanup | v1.2 | 0/1 | Not started | — |

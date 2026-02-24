# Roadmap: Corpus

## Milestones

- ✅ **v1.0 MVP** — Phases 1–4 (shipped 2026-02-23)
- ✅ **v1.1 Search Quality** — Phases 5–6 (shipped 2026-02-23)
- ✅ **v1.2 Graph Linker** — Phases 7–8 (shipped 2026-02-24)
- ✅ **v1.3 Code Quality** — Phases 9–12 (shipped 2026-02-24)
- ✅ **v1.4 Search Precision** — Phases 13–14 (shipped 2026-02-24)
- 🚧 **v1.5 TypeScript AST Chunking** — Phases 15–16 (in progress)

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

<details>
<summary>✅ v1.4 Search Precision (Phases 13–14) — SHIPPED 2026-02-24</summary>

- [x] Phase 13: Engine Min-Score Filter (1/1 plan) — completed 2026-02-24
- [x] Phase 14: API / MCP / CLI Parity (2/2 plans) — completed 2026-02-24

Full details: `.planning/milestones/v1.4-ROADMAP.md`

</details>

### 🚧 v1.5 TypeScript AST Chunking (In Progress)

**Milestone Goal:** Replace line-based chunking for `.ts`, `.tsx`, `.js`, `.jsx` with tree-sitter AST-aware chunking, matching the precision and test coverage of the existing Python AST chunker.

- [x] **Phase 15: Core AST Chunker** — Install deps, implement `chunk_typescript()` TDD-style, wire dispatch, full test suite green (**2 plans**) (completed 2026-02-24)
- [ ] **Phase 16: Integration Hardening** — Size guard, ImportError fallback, ruff/mypy/all-tests validation gate

## Phase Details

### Phase 15: Core AST Chunker
**Goal**: Users can index `.ts`, `.tsx`, `.js`, and `.jsx` files with AST-aware chunking that extracts named top-level constructs at the same precision as the Python chunker
**Depends on**: Phase 14 (v1.4 complete, clean linting baseline)
**Requirements**: DEP-01, IDX-01, IDX-02, IDX-03, IDX-04, IDX-05, IDX-06, IDX-07, TEST-01, TEST-02
**Success Criteria** (what must be TRUE):
  1. `uv sync` succeeds after adding `tree-sitter>=0.25.0` and `tree-sitter-language-pack>=0.13.0` to `pyproject.toml` with no C toolchain required
  2. `chunk_typescript()` extracts all eight target node types (function, generator, class, abstract class, interface, type alias, lexical declaration, enum) as separate chunks with correct 1-indexed line boundaries
  3. `export function foo()` and `export class Bar` produce chunks with the full exported text — export-unwrapping is verified by test assertion
  4. `.tsx` and `.jsx` files parse JSX syntax without fallback; `.ts` uses the TypeScript grammar; `.js` uses the JavaScript grammar
  5. `TestChunkTypeScript` passes with all cases from `TestChunkPython` adapted: all node types, line-range accuracy, non-ASCII identifiers, JSX parse, `has_error` partial tree does NOT fall back, deliberate catastrophic parse failure DOES fall back; `TestChunkFile` dispatch assertions cover all four extensions
**Plans**: 2 plans

Plans:
- [ ] 15-01-PLAN.md — TDD RED: write failing TestChunkTypeScript tests + update TestChunkFile dispatch
- [ ] 15-02-PLAN.md — GREEN: add deps, implement ts_chunker.py, wire chunk_file() dispatch

### Phase 16: Integration Hardening
**Goal**: The TypeScript chunker is production-safe under adversarial inputs (minified files, missing package install) and the full codebase passes the zero-violation quality gate
**Depends on**: Phase 15
**Requirements**: IDX-08, IDX-09, QUAL-01
**Success Criteria** (what must be TRUE):
  1. A TypeScript file exceeding 50,000 characters falls back to `chunk_lines()` without attempting AST parse — verified by test assertion on the size guard branch
  2. `corpus index` completes normally when `tree-sitter` is not installed — `chunk_file()` catches `ImportError` and returns `chunk_lines()` output rather than raising
  3. `uv run ruff check .` exits 0 and `uv run mypy src/` exits 0 after all v1.5 changes
  4. All 293+ existing tests continue to pass alongside the new `TestChunkTypeScript` and updated `TestChunkFile` tests
**Plans**: TBD

Plans:
- [ ] 16-01: TBD

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
| 15. Core AST Chunker | 2/2 | Complete    | 2026-02-24 | - |
| 16. Integration Hardening | v1.5 | 0/? | Not started | - |

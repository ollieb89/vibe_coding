# Roadmap: Corpus

## Milestones

- ✅ **v1.0 MVP** — Phases 1–4 (shipped 2026-02-23)
- ✅ **v1.1 Search Quality** — Phases 5–6 (shipped 2026-02-23)
- ✅ **v1.2 Graph Linker** — Phases 7–8 (shipped 2026-02-24)
- 🚧 **v1.3 Code Quality** — Phases 9–12 (in progress)

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

### 🚧 v1.3 Code Quality (In Progress)

**Milestone Goal:** Achieve a clean, zero-error linting baseline — `uv run ruff check .` and `uv run mypy src/` both exit zero, all 281 tests green.

- [x] **Phase 9: Config and Auto-Fix** — pyproject.toml surgical additions + ruff auto-fix eliminating ~282 violations (2 plans) (completed 2026-02-24)
- [ ] **Phase 10: Manual Ruff — Leaf to Hub** — Fix all remaining ruff violations in leaf modules through the core database hub
- [ ] **Phase 11: Manual Ruff — CLI + Mypy** — Fix CLI and legacy rewriter ruff violations; fix all 42 mypy errors across 9 files
- [ ] **Phase 12: Validation Gate** — Confirm zero ruff violations, zero mypy errors, all tests green

## Phase Details

### Phase 9: Config and Auto-Fix
**Goal**: pyproject.toml is configured with all necessary suppressions and ruff auto-fix has eliminated all auto-fixable violations
**Depends on**: Phase 8 (v1.2 complete)
**Requirements**: CONF-01, CONF-02, CONF-03, CONF-04, RUFF-01, RUFF-02
**Success Criteria** (what must be TRUE):
  1. `pyproject.toml` has `per-file-ignores` suppressing E501 for `llm/*.py` and B006 for `cli.py`
  2. `pyproject.toml` has a `[[tool.mypy.overrides]]` block disabling strict checks for `python-frontmatter` imports
  3. `pyproject.toml` excludes `.windsurf/` and `.planning/` from ruff scope
  4. Running `ruff check --fix` eliminates all W293/W291/I001/F401/UP045/F541/W605 violations with no manual edits
  5. All `__init__.py` re-exports remain importable after auto-fix (smoke-test passes)
**Plans**: 2 plans

Plans:
- [ ] 09-01-PLAN.md — Add ruff/mypy config stanzas to pyproject.toml (Commit 1)
- [ ] 09-02-PLAN.md — Run ruff --fix, audit changes, smoke-test, full pytest, commit (Commit 2)

### Phase 10: Manual Ruff — Leaf to Hub
**Goal**: All ruff violations in leaf modules and the core database hub are resolved — no B-series, F841/E741, E501, or E402 violations remain outside `cli.py`
**Depends on**: Phase 9
**Requirements**: RUFF-03, RUFF-04, RUFF-05, RUFF-06
**Success Criteria** (what must be TRUE):
  1. All E501 line-length violations in leaf modules are fixed by wrapping (no content changes)
  2. All B-series violations (B905/B007/B017/B023/B904/B008) are resolved without breaking behaviour
  3. All F841/E741 violations (unused variables, ambiguous names) are eliminated
  4. All E402 import ordering violations in `llm/rewriter.py` are fixed
**Plans**: TBD

### Phase 11: Manual Ruff — CLI + Mypy
**Goal**: `cli.py` is ruff-clean and all 42 mypy errors across 9 files are resolved — the codebase is type-correct under `--strict`
**Depends on**: Phase 10
**Requirements**: RUFF-07, MYPY-01, MYPY-02, MYPY-03, MYPY-04, MYPY-05, MYPY-06
**Success Criteria** (what must be TRUE):
  1. All 45 E501 violations in `cli.py` are wrapped; B006 Typer list defaults are suppressed with `# noqa: B006` (not broken)
  2. `core/database.py` has zero mypy errors — `cast(Table, ...)` applied at all sqlite-utils call sites
  3. `llm/chunked_processor.py` has zero mypy errors — nested function types annotated, `Atom` promoted to module level
  4. All remaining single-file mypy errors are resolved (`utils/ui.py`, `extractors/`, `llm/ollama_client.py`, `llm/rewriter.py`, `ingest/chunker.py`, `analyzers/shape.py`)
  5. The `llm/rewriter.py` line 406 operator bug is investigated and fixed (not cast away)
**Plans**: TBD

### Phase 12: Validation Gate
**Goal**: The codebase has a confirmed zero-error linting baseline — ruff clean, mypy clean, tests green
**Depends on**: Phase 11
**Requirements**: VALID-01, VALID-02, VALID-03
**Success Criteria** (what must be TRUE):
  1. `uv run ruff check .` exits 0 with zero violations printed
  2. `uv run mypy src/` exits 0 with zero errors printed
  3. `uv run pytest -v` exits 0 with all 281 tests passing
**Plans**: TBD

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
| 9. Config and Auto-Fix | 2/2 | Complete   | 2026-02-24 | - |
| 10. Manual Ruff — Leaf to Hub | v1.3 | 0/TBD | Not started | - |
| 11. Manual Ruff — CLI + Mypy | v1.3 | 0/TBD | Not started | - |
| 12. Validation Gate | v1.3 | 0/TBD | Not started | - |

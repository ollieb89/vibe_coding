# Roadmap: Corpus

## Milestones

- ✅ **v1.0 MVP** — Phases 1–4 (shipped 2026-02-23)
- 🚧 **v1.1 Search Quality** — Phases 5–6 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1–4) — SHIPPED 2026-02-23</summary>

- [x] Phase 1: Foundation (5/5 plans) — completed 2026-02-23
- [x] Phase 2: Search Core (5/5 plans) — completed 2026-02-23
- [x] Phase 3: Agent Interfaces (3/3 plans) — completed 2026-02-23
- [x] Phase 4: Defensive Hardening (2/2 plans) — completed 2026-02-23

Full details: `.planning/milestones/v1.0-ROADMAP.md`

</details>

### 🚧 v1.1 Search Quality (In Progress)

**Milestone Goal:** Eliminate noise from search results by controlling which files get indexed and improving construct classification accuracy via frontmatter signals.

- [ ] **Phase 5: Extension Filtering** - User-configurable and default extension allowlist controls which files are indexed per source
- [ ] **Phase 6: Frontmatter Classification** - Classifier reads YAML frontmatter as a high-confidence classification signal

## Phase Details

### Phase 5: Extension Filtering
**Goal**: Users control exactly which file types get indexed per source, and the indexer silently skips non-allowlisted files using a sensible default when no extensions are configured
**Depends on**: Phase 4
**Requirements**: CONF-06, CONF-07, CONF-08
**Success Criteria** (what must be TRUE):
  1. User can add `extensions = [".md", ".py"]` to a source block in `corpus.toml` and only those file types are indexed for that source
  2. Running `corpus index` on a source with an allowlist skips `.sh`, `.html`, `.json`, `.lock`, and binary files without error or warning
  3. A source with no `extensions` key automatically applies a default allowlist covering `.md`, `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.yaml`, `.yml`, `.txt`
  4. The default allowlist excludes `.sh`, `.html`, `.json`, `.lock`, and binary files even with no user configuration
**Plans**: 2 plans

Plans:
- [ ] 05-01-PLAN.md — TDD: SourceConfig.extensions field + walk_source extension filtering
- [ ] 05-02-PLAN.md — Integrate extensions into indexer, reconcile stale chunks, CLI output

### Phase 6: Frontmatter Classification
**Goal**: The construct classifier reads YAML frontmatter from markdown files as a high-confidence signal, making `--construct` filtering reliably accurate
**Depends on**: Phase 5
**Requirements**: CLASS-04, CLASS-05
**Success Criteria** (what must be TRUE):
  1. Running `corpus search --construct skill` returns files whose frontmatter declares `type: skill` or `component_type: skill` at or near the top of results
  2. A markdown file with a recognized frontmatter type declaration is classified with confidence >= 0.9
  3. Frontmatter `tags` field values are surfaced as classification signals alongside `type` and `component_type`
  4. Files without frontmatter continue to be classified using existing rule-based signals with no regression in test suite
**Plans**: 2 plans

Plans:
- [ ] 06-01-PLAN.md — TDD: ClassificationResult datatype + classify_by_frontmatter() + confidence scores
- [ ] 06-02-PLAN.md — Schema evolution (classification_source/confidence fields) + indexer wiring

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 5/5 | Complete | 2026-02-23 |
| 2. Search Core | v1.0 | 5/5 | Complete | 2026-02-23 |
| 3. Agent Interfaces | v1.0 | 3/3 | Complete | 2026-02-23 |
| 4. Defensive Hardening | v1.0 | 2/2 | Complete | 2026-02-23 |
| 5. Extension Filtering | v1.1 | 0/2 | Not started | - |
| 6. Frontmatter Classification | v1.1 | 0/2 | Not started | - |

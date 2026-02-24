# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-24 — v3.0 Intelligent Search milestone planned)

**Core value:** Surface relevant agent files instantly — query your entire local agent library and get ranked results in under a second
**Current focus:** v2 Chunk-Level Precision (Phases 17–25) — Phase 17 complete; v3.0 roadmap created

## Current Position

Phase: 17 complete (v2 in progress); v3 roadmap written
Plan: —
Status: v2 Phase 17 done (330 tests green); v3.0 roadmap created — ready to continue v2 at Phase 18
Last activity: 2026-02-24 — v3.0 Intelligent Search roadmap created (Phases 26–32)

Progress: [██░░░░░░░░] 20% of v2 (Phase 17 complete — 2 of 2 plans done); v3 planning complete

## Performance Metrics

**v1.0 Summary:**
- Total plans completed: 15
- Phases: 4
- Timeline: 41 days (2026-01-13 → 2026-02-23)

**v1.1 Summary:**
- Total plans completed: 4
- Phases: 2
- Timeline: 1 day (2026-02-23)

**v1.2 Summary:**
- Total plans completed: 1
- Phases: 2 (7–8)
- Timeline: 1 day (2026-02-24)

**v1.3 Summary:**
- Total plans completed: 11
- Phases: 4 (9–12)
- Timeline: 1 day (2026-02-24)

**v1.4 Complete:**
- Plans completed: 3 (13-01, 14-02, 14-01)
- Phases: 2 (13, 14)
- Timeline: 1 day (2026-02-24)

**v1.5 Complete:**
- Plans completed: 5 (15-01, 15-02, 16-01, 16-02, 16-03)
- Phases: 2 complete (15, 16)
- Timeline: 1 day (2026-02-24)

## Accumulated Context

### Decisions

Key v3 planning decisions:
- SearchCoordinator is the single composition point for CLI, MCP, and Python API — all three call coordinator.search(), not engine.hybrid_search() directly
- MULTI-01 uses overfetch+score-sum (file-level AND), NOT hard set intersection on chunk IDs — hard intersection reliably returns zero on sparse corpora
- GCENT-01 centrality is computed from the FULL relationships table at the END of index_source() — not per-file during the walk — because centrality is a global graph property
- GWALK-01 requires a visited: set[str] for cycle detection before any recursive graph walk ships; A→B→A cycle test is mandatory
- RERANK-02 sentence-transformers is an optional extra ([rerank]) — never a core dep; lazy-import only inside --rerank branch
- Phase 32 score range docs must be updated for post-NORM-01 normalised 0–1 scores; no doc or test should reference raw RRF range (0.009–0.033) as output

Key 17-02 decisions:
- chunk_text read via chunk.get("chunk_text", "") in indexer — safe because summary prepend mutates chunk["text"] only
- Test fixtures that directly insert LanceDB rows auto-fixed with chunk_name="" and chunk_text="" defaults
- ensure_schema_v2 → ensure_schema_v3 → ensure_schema_v4 call order preserved in CorpusIndex.open()

### Pending Todos

None.

### Blockers/Concerns

- Phase 27 (RANK-02 contiguous merge) depends on v2 Phase 17 being complete — Phase 17 is done, so this is unblocked
- Phase 32 success criteria explicitly require updating --min-score help text and FILT-03 for normalised scores — depends on v2 NORM-01 (Phase 23) shipping before v3 Phase 32

## Session Continuity

Last session: 2026-02-24
Stopped at: v3.0 roadmap written — Phases 26–32 defined, requirements traceability updated
Resume file: None
Next step: Resume v2 at Phase 18

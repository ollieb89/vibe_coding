# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-24 after v1.4 milestone start)

**Core value:** Surface relevant agent files instantly — query your entire local agent library and get ranked results in under a second
**Current focus:** v1.4 Search Precision — Phase 14: API/MCP/CLI Parity

## Current Position

Phase: 14 of 14 (API/MCP/CLI Parity)
Plan: 3 of 3 complete (13-01, 14-02, 14-01 — all surfaces done)
Status: Phase 14 complete — CLI, API, and MCP parity delivered
Last activity: 2026-02-24 — Completed 14-01: CLI --min-score, --sort-by, FILT-03 hint

Progress: [██████████] 100% (v1.4)

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

## Accumulated Context

### Decisions

Recent decisions affecting current work:

- [v1.4 research]: Post-retrieval Python list comprehension is the only correct approach for `min_score` filtering — `_relevance_score` is injected by RRFReranker after retrieval, not a stored LanceDB column; `.where()` predicate will fail
- [v1.4 research]: All three caller surfaces (CLI, API, MCP) must ship in one atomic phase — partial parity is an incomplete milestone
- [v1.4 research]: FastMCP `Optional[float]` parameters require `# noqa: UP045` comment to pass ruff — copy existing `corpus_search()` parameter pattern exactly
- [v1.4 research]: `tests/api/test_public.py:18` uses exact-set `==` for `SearchResult` fields — no new fields may be added; existing `score` field covers v1.4 needs
- [13-01]: min_score=0.0 is a no-op via `if min_score > 0.0:` guard; filter uses inclusive >= on _relevance_score; applied post-text-gate pre-sort
- [14-02]: _API_SORT_MAP dict translates user-facing sort vocabulary (score/date/title) to engine vocabulary (relevance/date/path) at API boundary — keeps layer naming conventions independent
- [14-02]: MCP min_score None->0.0 conversion is explicit in function body; empty results with non-zero min_score include filtered_by_min_score: True signal for MCP clients
- [14-01]: sort_by uses None sentinel default so CLI detects user-provided --sort-by vs fallback to --sort; Rich wraps help text across lines so tests assert tokens individually

### Pending Todos

None.

### Blockers/Concerns

None — 293 tests passing (3 new in 14-01). Ruff-clean, mypy-clean. v1.4 complete.

## Session Continuity

Last session: 2026-02-24
Stopped at: Completed 14-01 (CLI --min-score, --sort-by, FILT-03 hint). Phase 14 complete. v1.4 milestone done.
Resume file: None

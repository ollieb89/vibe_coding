# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-24 after v2.1 milestone started)

**Core value:** Surface relevant agent files instantly — query your entire local agent library and get ranked results in under a second
**Current focus:** v2.1 Result Quality (Phases 19–25) — roadmap defined, ready for Phase 19

## Current Position

Phase: 20 (Python Method Sub-Chunking)
Plan: 01 complete
Status: Phase 20 in progress — 1/? plans done
Last activity: 2026-02-24 — 20-01 SUB-01 class header chunk

Progress: [=         ] 1/7 phases — v2.1 in progress

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

**v2.0 Complete:**
- Plans completed: 4 (17-01, 17-02, 18-01, 18-02)
- Phases: 2 (17, 18)
- Timeline: 1 day (2026-02-24)

**v2.1 In Progress:**
- Plans completed: 2 (19-01, 20-01)
- Phases: 1/7 complete (19–25)
- Timeline: started 2026-02-24

## Accumulated Context

### Decisions

Key v3 planning decisions:
- SearchCoordinator is the single composition point for CLI, MCP, and Python API — all three call coordinator.search(), not engine.hybrid_search() directly
- MULTI-01 uses overfetch+score-sum (file-level AND), NOT hard set intersection on chunk IDs — hard intersection reliably returns zero on sparse corpora
- GCENT-01 centrality is computed from the FULL relationships table at the END of index_source() — not per-file during the walk — because centrality is a global graph property
- GWALK-01 requires a visited: set[str] for cycle detection before any recursive graph walk ships; A→B→A cycle test is mandatory
- RERANK-02 sentence-transformers is an optional extra ([rerank]) — never a core dep; lazy-import only inside --rerank branch
- Phase 32 score range docs must be updated for post-NORM-01 normalised 0–1 scores; no doc or test should reference raw RRF range (0.009–0.033) as output

Key 19-01 decisions:
- MCP corpus_search result_dict uses content-first ordering: text is the first key so LLM callers see chunk body immediately
- Legacy rows (chunk_text empty/missing) use str(row.get("chunk_text", "") or "") and int(row.get("start_line", 0) or 0) for safe fallback
- Path, extract_snippet, and full OSError/content_error block removed from server.py — no file reads in MCP hot path

Key 18-02 decisions:
- extract_snippet removed from cli.py import after render loop replacement (F401 — unused); still exported from module
- SIM108 ternary style enforced by ruff for construct_part and preview assignments in format_result()
- format_result returns (primary, preview | None) tuple — pure function; Console.print() owns rendering

Key 18-01 decisions:
- format_result() RED tests import at module level — single ImportError is the RED signal for all 10 tests
- test_format_result_rich_markup_escape_in_path checks '[deprecated]' in primary (escaped string), not Rich internals
- test_format_result_no_ellipsis_at_exactly_200_chars: len(preview)==204 (4 indent + 200 chars)

Key 17-02 decisions:
- chunk_text read via chunk.get("chunk_text", "") in indexer — safe because summary prepend mutates chunk["text"] only
- Test fixtures that directly insert LanceDB rows auto-fixed with chunk_name="" and chunk_text="" defaults
- ensure_schema_v2 → ensure_schema_v3 → ensure_schema_v4 call order preserved in CorpusIndex.open()
- [Phase 20-01]: _chunk_class() returns list[dict] to allow Plan 02 method chunk additions without signature change
- [Phase 20-01]: init body traversal uses direct iteration over init_node.body (not ast.walk) to preserve linear order for truncation logic

### v2.1 Roadmap Notes

- Phase 19 (CHUNK-03): MCP `corpus_search` already has all v4 fields in LanceDB — this is a thin addition to the MCP response schema
- Phase 20–21 (SUB-01–03): Sub-chunking changes the output of `py_chunker.py` and `ts_chunker.py`; will cause re-indexing behaviour changes; all tests for monolithic class chunks will need updating
- Phase 22 (NAME-01–03): `--name` with no positional query requires making the query argument Optional in the CLI command signature
- Phase 23 (NORM-01): Normalisation inside the search engine means all existing score-range tests (e.g. FILT-01 threshold tests) must be updated to expect 0–1 values
- Phase 23 (SORT-01): MCP sort_by uses the existing `_API_SORT_MAP` translation — minimal wiring required
- Phase 24 (JSON-01): Rich must be fully suppressed when `--output json`; use `print()` not `Console.print()`
- Phase 25 (GRAPH-01): `corpus_graph` MCP tool is a thin wrapper around existing `GraphStore.search_paths()` and `get_neighbours()` — no new storage

### Pending Todos

None.

### Blockers/Concerns

- Phase 27 (RANK-02 contiguous merge) depends on v2 Phase 17 being complete — Phase 17 is done, so this is unblocked
- Phase 32 success criteria explicitly require updating --min-score help text and FILT-03 for normalised scores — depends on v2 NORM-01 (Phase 23) shipping before v3 Phase 32

## Session Continuity

Last session: 2026-02-24
Stopped at: Completed 20-01-PLAN.md (SUB-01 class header chunk)
Resume file: None
Next step: Phase 20 Plan 02 — method sub-chunks (SUB-02)

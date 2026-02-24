# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-24 — v2 milestone planned)

**Core value:** Surface relevant agent files instantly — query your entire local agent library and get ranked results in under a second
**Current focus:** v2 Chunk-Level Precision — planning complete, Phase 17 next

## Current Position

Phase: 17 in progress (Schema v4 — Chunk Data Layer)
Plan: 1 of 2 in Phase 17 complete (17-01 RED tests done)
Status: Phase 17 active — 17-01 RED state committed, 17-02 GREEN implementation next
Last activity: 2026-02-24 — 17-01 RED tests committed (11 new failing tests)

Progress: [█░░░░░░░░░] 10% of v2 (Phase 17 Plan 1 of 2 complete)

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

Key v1.5 decisions:
- Use `get_parser(dialect)` from `tree_sitter_language_pack` with `@lru_cache` (simpler than module-level globals)
- `.tsx` and `.jsx` both use TSX grammar (TypeScript grammar produces ERROR nodes on JSX elements)
- Fall back only on uncaught exception or zero constructs — NOT on `root_node.has_error` alone
- `export default function(): void {}` requires special-case: declaration field is None; detect 'default' child and emit full export_statement as chunk_name='default'
- Lazy import of ts_chunker inside chunk_file elif branch avoids circular import

Key 15-01 decisions:
- Module-level import of ts_chunker in test file ensures clean RED state (ModuleNotFoundError at collection)
- test_dispatches_other_to_chunk_lines renamed to test_dispatches_ts_to_chunk_typescript (correctly reflects new intent)

Key 16-01 decisions:
- RED state acknowledged as pre-passing for test_import_error_falls_back_to_chunk_lines — current except Exception catches ImportError; 16-02 creates explicit separate branch
- RED state for test_large_file_falls_back_to_chunk_lines confirmed — 50,001-char 'x' file falls back via no-named-constructs path; 16-02 adds explicit size guard before parse

Key 16-02 decisions:
- Lazy import of get_parser inside _get_cached_parser body allows ImportError to be caught in chunk_typescript's try/except
- Separate except ImportError and except Exception clauses preserved (not merged) per locked CONTEXT.md decision
- Removed quotes from Parser return type annotation — ruff UP037 requires unquoted form when from __future__ import annotations is present; TYPE_CHECKING guard is sufficient for mypy

Key 16-03 decisions:
- Smoke test used Python API (chunk_file dispatch) rather than corpus index CLI — direct API call confirms dispatch wiring cleanly without requiring LanceDB configured sources
- v1.5 milestone declared complete after all quality gates confirmed: ruff 0 violations, mypy 0 errors, 320 tests passing

### 17-01 Decisions

- Deferred import of ensure_schema_v4 inside test methods (not module level) keeps pre-existing schema tests collectable and GREEN while ensure_schema_v4 tests fail with ImportError
- MockEmbedder in test_round_trip.py uses model="test-model" with zero vectors to avoid model-mismatch guard in CorpusIndex.open()
- Round-trip assertions use index._table.search().limit(20).to_list() — full-table dump, no vector similarity needed

### v2 Planning Decisions

- CLI format: `file:start-end [construct] score:X.XXX` (grep/compiler-error pattern, IDE-clickable)
- MCP returns full chunk `text` untruncated; CLI truncates to 200 chars for display
- Schema v4 adds columns with defaults — users re-index to backfill; migration is idempotent
- `ClassName.method_name` dot notation for method sub-chunks (Python and TypeScript)
- `--name foo` flag (not `--construct name:foo`) — separate flag, case-insensitive substring match
- Per-query min-max score normalisation inside the search engine (not at display layer)
- `corpus_graph` MCP reuses existing `GraphStore` — no new storage layer

### Pending Todos

None — v2 planning complete, ready to start Phase 17.

### Blockers/Concerns

None — 320 tests passing. Ruff-clean. Mypy-clean. v2 planning documentation written.

## Session Continuity

Last session: 2026-02-24
Stopped at: 17-01-PLAN.md complete — RED test suite committed (3be5ace)
Resume file: None
Next step: Phase 17-02-PLAN.md — TDD GREEN for schema v4 (implement ChunkRecord v4 fields, ensure_schema_v4(), chunker v4 emission)

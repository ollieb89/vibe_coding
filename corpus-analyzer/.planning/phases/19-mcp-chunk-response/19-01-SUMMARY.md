---
phase: 19-mcp-chunk-response
plan: "01"
subsystem: api
tags: [mcp, fastmcp, lancedb, chunk_text, corpus_search]

# Dependency graph
requires:
  - phase: 17-chunk-store
    provides: chunk_text, start_line, end_line fields stored in LanceDB v4 schema
  - phase: 18-search-formatter
    provides: CorpusSearch engine and hybrid_search()
provides:
  - MCP corpus_search tool returns self-contained chunk content (text, start_line, end_line)
  - Regression guards: tests assert snippet and full_content absent from results
  - No whole-file reads in MCP response path
affects: [25-graph-mcp, phase-32-score-docs]

# Tech tracking
tech-stack:
  added: []
  patterns: [content-first result dict ordering (text key first), chunk-level MCP response]

key-files:
  created: []
  modified:
    - src/corpus_analyzer/mcp/server.py
    - tests/mcp/test_server.py

key-decisions:
  - "MCP result_dict uses content-first ordering: text is the first key so LLM callers see chunk body immediately"
  - "Legacy rows (chunk_text empty/missing) return text='' without raising — int(row.get('start_line', 0) or 0) pattern handles None"
  - "Path, extract_snippet, and full OSError/content_error block removed — no file reads in MCP hot path"

patterns-established:
  - "content-first dict: text key first so LLM tool consumers see the content before metadata"
  - "safe int coerce: int(row.get('field', 0) or 0) pattern for nullable int fields from LanceDB"

requirements-completed: [CHUNK-03]

# Metrics
duration: 8min
completed: 2026-02-24
---

# Phase 19 Plan 01: MCP Chunk Response Summary

**MCP corpus_search now returns full chunk body (text), start_line, end_line from LanceDB — removing snippet truncation and whole-file reads**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-24T16:06:12Z
- **Completed:** 2026-02-24T16:14:00Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- MCP corpus_search results now include `text` (full untruncated chunk_text), `start_line`, and `end_line` — each result is self-contained
- Removed `snippet` (truncated preview) and `full_content` (whole-file read) from the response entirely
- Added 7 new tests including regression guards asserting `snippet` and `full_content` absent
- Removed `Path.read_text()` call and OSError/content_error code path from the MCP hot path
- 345 tests pass, ruff and mypy clean

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests for new response shape** - `55e9acd` (test)
2. **Task 2 GREEN: Implement self-contained chunk response** - `7b8ab08` (feat)
3. **Task 3: Full regression check + E501 fix** - `d37ad78` (refactor)

_Note: TDD tasks follow test → feat → refactor commit sequence_

## Files Created/Modified

- `src/corpus_analyzer/mcp/server.py` — Replaced snippet+full_content result fields with text/start_line/end_line; removed Path, extract_snippet imports and file-read block
- `tests/mcp/test_server.py` — Added 7 new CHUNK-03 tests; removed 2 OSError file-read tests; updated shape test for new contract

## Decisions Made

- MCP result dict uses content-first ordering: `text` is the first key so LLM callers see chunk body immediately without scanning metadata
- Legacy rows (chunk_text empty or missing) return `text=""` without raising — `str(row.get("chunk_text", "") or "")` and `int(row.get("start_line", 0) or 0)` handle None/empty safely
- `Path`, `extract_snippet` removed entirely — no file reads in the MCP response path improves reliability (no OSError on moved files)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed E501 line-too-long in test docstring**
- **Found during:** Task 3 (Full regression check)
- **Issue:** `test_corpus_search_no_snippet_field` docstring was 101 chars, exceeding the 100-char limit (ruff E501)
- **Fix:** Shortened docstring from "old truncated preview removed" to "old truncated preview"
- **Files modified:** tests/mcp/test_server.py
- **Verification:** `uv run ruff check .` reports clean
- **Committed in:** d37ad78 (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 line length)
**Impact on plan:** Trivial style fix. No scope creep.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- CHUNK-03 satisfied: MCP corpus_search now provides self-contained chunk results
- Phase 20 (SUB-01: sub-chunking) can proceed — MCP layer is ready to expose sub-chunks once they are stored
- No blockers

---
*Phase: 19-mcp-chunk-response*
*Completed: 2026-02-24*

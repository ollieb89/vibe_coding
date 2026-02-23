---
phase: 04-hardening
plan: 01
subsystem: safety
tags: [cli, ingest, mcp, error-handling, safety]

# Dependency graph
requires:
  - phase: 03-agent-interfaces
    provides: MCP server implementation and CLI search
provides:
  - CLI safe score access to prevent KeyErrors
  - Ingest warning logs for stale chunks and existing files query failures
  - MCP server `content_error` reporting for post-indexing file read failures
affects: [04-hardening]

# Tech tracking
tech-stack:
  added: []
  patterns: [Safe dict access with .get(), Explicit exception logging, Explicit error signaling in API responses]

key-files:
  created: []
  modified: 
    - src/corpus_analyzer/cli.py
    - src/corpus_analyzer/ingest/indexer.py
    - src/corpus_analyzer/mcp/server.py

key-decisions:
  - "Used safe `.get('_relevance_score', 0.0)` in CLI to match API and MCP patterns"
  - "Used `%`-style formatting in indexer warning logs for consistency and performance"
  - "Added `content_error` string to MCP responses instead of failing silently or changing `full_content` type"

patterns-established:
  - "Error Handling: Never swallow exceptions silently; surface as warnings if non-critical or errors in API responses"

requirements-completed: [CLI-02, INGEST-07, MCP-02]

# Metrics
duration: 15min
completed: 2026-02-23
---

# Phase 04: Hardening (Safety Gaps) Summary

**Closed critical safety gaps by preventing CLI KeyErrors on missing scores, logging indexer exceptions instead of silent swallows, and surfacing file read OSErrors as `content_error` in MCP responses.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-02-23T20:03:00Z
- **Completed:** 2026-02-23T20:18:00Z
- **Tasks:** 3
- **Files modified:** 6 (including tests)

## Accomplishments
- Prevented CLI crashes when search results omit the `_relevance_score` field.
- Eliminated silent data loss risks in the indexer by logging warnings when chunk deletion or file queries fail.
- Improved MCP client experience by explicitly signaling when a file cannot be read after it was indexed, rather than returning an empty string silently.

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix CLI-02 KeyError with TDD** - `f10812b` (fix)
2. **Task 2: Fix INGEST-07 silent swallows with TDD** - `4b1e3e4` (fix)
3. **Task 3: Fix MCP-02 silent OSError with TDD** - `9732bf8` (fix)

**Plan metadata:** `24f60dd` (docs: create phase plan)

## Files Created/Modified
- `src/corpus_analyzer/cli.py` - Updated search command to use `.get('_relevance_score', 0.0)`
- `tests/cli/test_search_status.py` - Added test for missing relevance score
- `src/corpus_analyzer/ingest/indexer.py` - Replaced bare excepts with exception logging
- `tests/ingest/test_indexer.py` - Added tests verifying warning logs
- `src/corpus_analyzer/mcp/server.py` - Caught OSError on file read to populate `content_error`
- `tests/mcp/test_server.py` - Added tests for `content_error` presence/absence

## Decisions Made
- Maintained `full_content = ""` behavior on OSError in MCP server to avoid breaking existing clients that expect a string, while adding the new `content_error` field for explicit error signaling.
- Used `.get('_relevance_score', 0.0)` in CLI to match the exact pattern already established in `mcp/server.py` and `api/public.py`.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## Next Phase Readiness
- Core safety gaps identified in v1.0 audit are closed.
- System is more robust against unexpected data shapes and filesystem errors.
- Ready for next hardening phase focusing on UX (UX-03, UX-04).

---
*Phase: 04-hardening*
*Completed: 2026-02-23*

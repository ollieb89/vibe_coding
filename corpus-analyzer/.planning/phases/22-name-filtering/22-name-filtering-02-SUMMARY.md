---
phase: 22-name-filtering
plan: 02
subsystem: search
tags: [cli, mcp, typer, fastmcp, name-filter, hybrid-search]

# Dependency graph
requires:
  - phase: 22-01
    provides: name parameter in CorpusSearch.hybrid_search() and empty-query support
provides:
  - "--name/-N CLI option in corpus search command"
  - "query argument made Optional in CLI search_command"
  - "name: Optional[str] parameter in MCP corpus_search tool"
  - "name forwarded to hybrid_search() from both CLI and MCP"
affects: [23-score-norm, 24-json-output, 25-graph-mcp]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Optional CLI argument pattern: Annotated[str | None, typer.Argument(...)] = None"
    - "Guard clause before embedder setup: check required arg combos early, exit(1) with message"
    - "effective_query pattern: derive from optional arg before passing to downstream calls"

key-files:
  created: []
  modified:
    - src/corpus_analyzer/cli.py
    - src/corpus_analyzer/mcp/server.py
    - tests/cli/test_search_status.py
    - tests/mcp/test_server.py

key-decisions:
  - "name_filter guard placed before embedder/index setup to avoid connection overhead on bad input"
  - "effective_query = query if query is not None else '' — empty string is the empty-query signal to the engine (established in 22-01)"
  - "name_filter always passed as keyword arg to hybrid_search (name=name_filter) so None is explicit"
  - "Existing test test_corpus_search_passes_filters_to_hybrid_search updated to include name=None (Rule 1 auto-fix)"

patterns-established:
  - "Optional Typer argument: Annotated[T | None, typer.Argument(...)] = None for optional positional args"
  - "Early guard for mutual exclusion: check required combinations before I/O setup"

requirements-completed: [NAME-01, NAME-02, NAME-03]

# Metrics
duration: 3min
completed: 2026-02-24
---

# Phase 22 Plan 02: Name Filtering CLI+MCP Wiring Summary

**`--name` CLI flag and MCP `name` parameter wired to hybrid_search; query made Optional with name-only mode passing `query=""` to the engine**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-24T17:26:01Z
- **Completed:** 2026-02-24T17:28:34Z
- **Tasks:** 2 (TDD: RED + GREEN)
- **Files modified:** 4

## Accomplishments
- CLI `search` command gains `--name/-N` option; query argument becomes Optional
- Guard clause ensures `corpus search` (no query, no --name) exits 1 with helpful message
- Name-only mode (`corpus search --name foo`) valid; passes `query=""` to engine
- MCP `corpus_search` gains `name: Optional[str]` parameter forwarded to hybrid_search
- Full test suite green (398 tests); ruff and mypy clean on modified files

## Task Commits

1. **Task 1: RED — failing tests for CLI --name and MCP name parameter** - `159ee84` (test)
2. **Task 2: GREEN — wire --name into CLI and name into MCP server** - `c4d802f` (feat)

**Plan metadata:** (docs commit follows)

_Note: TDD tasks have two commits: failing tests then implementation_

## Files Created/Modified
- `src/corpus_analyzer/cli.py` - query made Optional; --name/-N option added; guard clause; effective_query; name=name_filter in hybrid_search call; updated no-results message
- `src/corpus_analyzer/mcp/server.py` - name: Optional[str] = None added to corpus_search(); name=name forwarded to hybrid_search(); docstring updated
- `tests/cli/test_search_status.py` - 6 new tests: help shows --name, filter passed, name-only valid, name-only empty query, no query+no name error, name+source compose
- `tests/mcp/test_server.py` - 3 new tests: name accepted, name forwarded, name=None forwarded; existing filter test updated to include name=None

## Decisions Made
- Guard placed before embedder/index setup to avoid Ollama connection overhead on invalid input
- `effective_query = query if query is not None else ""` — empty string signals engine to use name-only mode (pattern from 22-01)
- `name_filter` always passed as explicit keyword arg so None is forwarded explicitly (not omitted)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated existing MCP filter test to include name=None**
- **Found during:** Task 2 (GREEN — wire --name into CLI and name into MCP server)
- **Issue:** `test_corpus_search_passes_filters_to_hybrid_search` used `assert_called_once_with` without `name=None`; failed after new parameter always passed
- **Fix:** Added `name=None` to the expected call in assert_called_once_with
- **Files modified:** `tests/mcp/test_server.py`
- **Verification:** Full suite runs 398 passed
- **Committed in:** `c4d802f` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Necessary correctness fix; no scope creep.

## Issues Encountered
None beyond the Rule 1 auto-fix above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- NAME-01, NAME-02, NAME-03 complete; phase 22 fully done
- Phase 23 (NORM-01 score normalisation) is next; score range tests will need updating
- `hybrid_search()` signature now includes `name=` keyword — downstream phases should be aware

---
*Phase: 22-name-filtering*
*Completed: 2026-02-24*

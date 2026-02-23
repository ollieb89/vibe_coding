---
phase: 04-hardening
plan: 02
subsystem: cleanup
tags: [config, scanner, search, tech-debt, verification]

# Dependency graph
requires:
  - phase: 04-hardening
    plan: 01
    provides: Safety gap fixes that this cleanup builds upon
provides:
  - Single-source-of-truth for DATA_DIR and CONFIG_PATH
  - SourceConfig.use_llm_classification configuration field
  - Cleaner scanner without dead code
  - Faster CorpusSearch without redundant FTS rebuild
  - Retroactive verification documents for phases 1-3
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: [Single source of truth for constants, Config-driven feature flags, Dead code elimination]

key-files:
  created:
    - .planning/phases/01-foundation/01-VERIFICATION.md
    - .planning/phases/02-search-core/02-VERIFICATION.md
    - .planning/phases/03-agent-interfaces/03-VERIFICATION.md
  modified:
    - src/corpus_analyzer/config/schema.py
    - src/corpus_analyzer/config/__init__.py
    - src/corpus_analyzer/cli.py
    - src/corpus_analyzer/api/public.py
    - src/corpus_analyzer/mcp/server.py
    - src/corpus_analyzer/ingest/indexer.py
    - src/corpus_analyzer/ingest/scanner.py
    - src/corpus_analyzer/search/engine.py

key-decisions:
  - "Moved path constants to config/schema.py to avoid circular imports and dual definitions"
  - "Set use_llm_classification default to False for cost-conscious default behavior"
  - "Removed needs_reindex entirely as the indexer uses hash-based change detection"
  - "Removed FTS rebuild from CorpusSearch.__init__ since indexer already builds it"

patterns-established:
  - "Configuration as Single Source of Truth: All path constants live in config/schema.py"
  - "Feature Flags in Config: LLM classification controlled via SourceConfig field"

requirements-completed: []

# Metrics
duration: 12min
completed: 2026-02-23
---

# Phase 04: Hardening (Tech Debt & Cleanup) Summary

**Eliminated accumulated tech debt by consolidating path definitions, exposing LLM classification as a config field, removing dead code, and creating retroactive verification audit trail.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-23T20:12:00Z
- **Completed:** 2026-02-23T20:24:00Z
- **Tasks:** 3
- **Files modified:** 13 (including verification docs)

## Accomplishments
- Established single source of truth for DATA_DIR and CONFIG_PATH in config/schema.py.
- Added use_llm_classification field to SourceConfig for explicit control over LLM-based classification.
- Removed needs_reindex() dead code from scanner module.
- Eliminated redundant FTS index rebuild from CorpusSearch.__init__ (saving time on every search invocation).
- Created retroactive VERIFICATION.md files for phases 1, 2, and 3 to complete the audit trail.

## Task Commits

Each task was committed atomically:

1. **Task 1: Consolidate paths and expose use_llm_classification** - `6c03fc2` (refactor)
2. **Task 2: Remove dead code and redundant FTS rebuild** - `c6423ab` (refactor)
3. **Task 3: Write retroactive VERIFICATION.md files** - `7d6c0f9` (docs)

**Plan metadata:** `24f60dd` (docs: create phase plan)

## Files Created/Modified
- `src/corpus_analyzer/config/schema.py` - Added CONFIG_PATH, DATA_DIR constants and use_llm_classification field
- `src/corpus_analyzer/config/__init__.py` - Updated exports
- `src/corpus_analyzer/cli.py` - Import paths from config.schema
- `src/corpus_analyzer/api/public.py` - Import DATA_DIR from config.schema
- `src/corpus_analyzer/mcp/server.py` - Import paths from config.schema (not cli)
- `src/corpus_analyzer/ingest/indexer.py` - Wired source.use_llm_classification to classify_file()
- `src/corpus_analyzer/ingest/scanner.py` - Removed needs_reindex() dead code
- `src/corpus_analyzer/ingest/__init__.py` - Removed needs_reindex from exports
- `src/corpus_analyzer/search/engine.py` - Removed FTS rebuild from __init__
- `tests/config/test_schema.py` - Added test for use_llm_classification
- `tests/ingest/test_scanner.py` - Removed TestNeedsReindex tests
- `tests/search/test_engine.py` - Added manual FTS index creation to fixture
- `.planning/phases/01-foundation/01-VERIFICATION.md` - Retroactive verification
- `.planning/phases/02-search-core/02-VERIFICATION.md` - Retroactive verification
- `.planning/phases/03-agent-interfaces/03-VERIFICATION.md` - Retroactive verification

## Decisions Made
- Chose to default use_llm_classification to False to avoid unexpected Ollama API costs.
- Removed the needs_reindex() function entirely rather than deprecating it since no callers existed.
- Removed FTS rebuild from CorpusSearch.__init__ because index_source() already creates it, making the __init__ call redundant and wasteful.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## Next Phase Readiness
- Tech debt cleared, codebase is cleaner and more maintainable.
- Single source of truth established for configuration constants.
- Audit trail complete with retroactive verification documents.
- Ready for v1.0 milestone archival.

---
*Phase: 04-hardening*
*Completed: 2026-02-23*

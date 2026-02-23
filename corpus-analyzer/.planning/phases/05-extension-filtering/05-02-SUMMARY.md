# Phase 05-02 Summary: Extension Filtering Indexer Integration

## What Was Built

Wired `SourceConfig.extensions` into the indexer pipeline and CLI output.

1. **Indexer Integration** — `src/corpus_analyzer/ingest/indexer.py`
   - Passed `extensions=source.extensions` to `walk_source()` during indexing
   - Tracked files removed (either stale or extension-excluded) by diffing existing index files vs current files
   - Updated `IndexResult` dataclass to include `files_removed` attribute
   - Fixed a bug where `_delete_stale_chunks` was called twice

2. **CLI Enhancements** — `src/corpus_analyzer/cli.py`
   - Added `extensions=source.extensions` to the `walk_source()` call for the `total` file count progress calculation
   - Display active extensions on the first index run of a source
   - Print a yellow warning message showing the number of removed files when `files_removed > 0`

## Test Coverage

- Added `test_indexer_extension_filtering_and_removal` to `tests/ingest/test_indexer.py`
  - Tests that files are indexed based on the extension allowlist
  - Tests that restricting the allowlist on a subsequent run correctly calculates `files_removed`

All 179 tests pass. ruff and mypy clean.

## Commits

1. `feat(05-02): wire extensions into indexer and track removed files`

## Next Steps

This successfully integrates the extension filtering feature introduced in plan 05-01 into the core indexing pipeline and user interface.

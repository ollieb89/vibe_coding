# Phase 05-01 Summary: Extension Filtering Implementation

## What Was Built

Per-source extension allowlist feature for the corpus-analyzer:

1. **SourceConfig.extensions field** — `src/corpus_analyzer/config/schema.py`
   - `DEFAULT_EXTENSIONS` constant with common doc/code types
   - `extensions` field on `SourceConfig` with sensible defaults
   - Pydantic `field_validator` that normalizes values (lowercase, leading dot)

2. **walk_source extension filtering** — `src/corpus_analyzer/ingest/scanner.py`
   - Added `extensions` parameter to `walk_source()`
   - Extension filter applied after include/exclude matching
   - Case-insensitive suffix comparison
   - `None` means no filtering (backward compatible)
   - Empty list `[]` yields no files

## Test Coverage

Added 11 new tests across both modules:
- `tests/config/test_schema.py`: 6 tests for `SourceConfig.extensions`
- `tests/ingest/test_scanner.py`: 5 tests for `walk_source` extension filtering

All 178 tests pass. ruff and mypy clean.

## Commits

1. `test(05-01): add failing tests for SourceConfig.extensions and walk_source filtering`
2. `feat(05-01): add SourceConfig.extensions field and walk_source extension filtering`
3. `refactor(05-01): clean up extensions field docs and type annotations`

## Next Steps

This foundation enables Phase 02 (indexer integration) to consume the extension filtering contract.

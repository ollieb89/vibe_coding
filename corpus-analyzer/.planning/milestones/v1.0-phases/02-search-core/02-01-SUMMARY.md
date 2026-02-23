# Phase 02 Search Core — 02-01 Summary

## Schema changes

- **`src/corpus_analyzer/store/schema.py`**
  - Added `ChunkRecord.construct_type: str | None = None`
  - Added `ChunkRecord.summary: str | None = None`
  - Added `ensure_schema_v2(table: lancedb.table.Table) -> None` (in-place LanceDB schema evolution via `add_columns()`)

- **`src/corpus_analyzer/config/schema.py`**
  - Added `SourceConfig.summarize: bool = True`

- **`src/corpus_analyzer/search/__init__.py`**
  - Added search package initializer (module docstring)

## Test scaffolds created (Wave 0 / RED)

New `tests/search/` package:

- `tests/search/__init__.py`
  - **Test count**: 0

- `tests/search/test_engine.py`
  - **Test count**: 11 (all `xfail(strict=True)` stubs)

- `tests/search/test_classifier.py`
  - **Test count**: 8 (all `xfail(strict=True)` stubs)

- `tests/search/test_summarizer.py`
  - **Test count**: 4 (all `xfail(strict=True)` stubs)

- `tests/search/test_formatter.py`
  - **Test count**: 4 (all `xfail(strict=True)` stubs)

Extended existing Phase 1 tests:

- `tests/ingest/test_indexer.py`
  - **Added test count**: 2 (both `xfail(strict=True)` stubs)

## Deviations from plan

- Updated **`tests/store/test_schema.py`** to include the two new `ChunkRecord` fields so existing schema tests continue to pass.
- Updated **`src/corpus_analyzer/config/__init__.py`** to fix mypy errors and satisfy Ruff import sorting.

## Import paths for downstream plans

- `ensure_schema_v2`:
  - `from corpus_analyzer.store.schema import ensure_schema_v2`

- `ConstructClassifier` (to be implemented in Phase 02-03; import path reserved):
  - `from corpus_analyzer.search.classifier import ConstructClassifier`

- `Summarizer` (to be implemented in Phase 02-04; import path reserved):
  - `from corpus_analyzer.search.summarizer import Summarizer`

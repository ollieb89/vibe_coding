# Phase 02 Search Core — 02-05 Summary

## New CLI commands

Added to `src/corpus_analyzer/cli.py`:

- `search_command(query, --source/-s, --type/-t, --construct/-c, --limit/-n)`
- `status_command()`

### `corpus search` behavior

- Loads config and validates Ollama embedder connection.
- Opens index via `CorpusIndex.open(DATA_DIR, embedder)`.
- Executes `CorpusSearch.hybrid_search(...)` with optional filters.
- Prints ranked results with:
  - highlighted file path
  - construct type fallback (`documentation`)
  - dimmed relevance score
  - optional italic summary
  - snippet via `extract_snippet(...)`
- On no results, prints `No results for "<query>"`.
- On invalid filter values (`ValueError`), exits with code 1 and prints the validation error.

### `corpus status` behavior

- Loads config and opens the index/search stack.
- Uses `CorpusSearch.status(...)` to retrieve:
  - files
  - chunks
  - last indexed
  - model
- Renders a Rich table titled `Index Status`.
- If index open/status retrieval fails, prints `Index not found. Run 'corpus index' first.` and exits 0.

## FTS index integration point

Added to `src/corpus_analyzer/ingest/indexer.py` in `CorpusIndex.index_source()`:

- `self._table.create_fts_index("text", replace=True)`

This is executed after `self._table.optimize()` to keep BM25/FTS search synchronized with newly indexed content.

## Test and validation updates

### Added tests

- `tests/cli/test_search_status.py`
  - help output for `search`/`status`
  - no-result message path
  - invalid filter path (non-zero exit)
  - status metrics rendering
  - missing-index message path

- `tests/ingest/test_indexer.py`
  - `test_index_rebuilds_fts_index` to assert `create_fts_index("text", replace=True)` is called.

### Executed checks

- `uv run pytest tests/ingest/test_indexer.py -x -q` ✅
- `uv run pytest tests/cli/test_search_status.py -x -q` ✅
- `uv run pytest tests/search/ tests/ingest/ tests/store/ tests/config/ -v --no-header` ✅
- `uv run mypy src/corpus_analyzer/cli.py src/corpus_analyzer/ingest/indexer.py` ✅
- `uv run corpus-analyzer search --help && uv run corpus-analyzer status --help` ✅

## Phase 2 requirement status for this wave

- CLI-01: ✅ FTS rebuild now runs at end of indexing.
- CLI-02: ✅ `corpus search` implemented.
- CLI-03: ✅ `--source`, `--type`, `--construct`, `--limit` supported.
- CLI-04: ✅ `corpus status` implemented.
- CLI-05: ✅ `corpus add` unchanged.
- SEARCH-01..SEARCH-05 (wave-relevant integration points): ✅ validated through existing search tests plus CLI behavior tests.

## Known follow-up

- Repository-wide `ruff check src/corpus_analyzer/cli.py` still reports pre-existing E501 line-length issues outside the new 02-05 scope.

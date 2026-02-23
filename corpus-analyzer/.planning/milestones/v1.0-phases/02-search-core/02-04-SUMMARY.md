# Phase 02 Search Core — 02-04 Summary

## Import paths

- Summarizer APIs:
  - `from corpus_analyzer.search.summarizer import generate_summary, should_summarize`
- Indexer integrations:
  - `from corpus_analyzer.search.classifier import classify_file`
  - `from corpus_analyzer.store.schema import ensure_schema_v2`

## ensure_schema_v2 wiring confirmation

`CorpusIndex.open()` now calls `ensure_schema_v2(table)` after opening/creating the `chunks` table and before returning the `CorpusIndex` instance.

## Stored summary lookup

Indexer now includes:

- `_get_stored_summaries(self, source_name: str) -> dict[str, str | None]`

This method retrieves existing summary values per `file_path` for a source and is used by `index_source()` to decide whether summary generation should run.

## Indexer extension behavior implemented

- `index_source()` now accepts:
  - `use_llm_classification: bool = True`
- For changed/new files, indexer now:
  1. Reads `full_text` from disk.
  2. Calls `classify_file(...)` once per file.
  3. Uses `should_summarize(...)` with source flag + stored summary + change status.
  4. Calls `generate_summary(...)` only when needed.
  5. Prepends summary to first chunk text before embedding (SUMM-02).
  6. Stores `construct_type` and `summary` on every chunk dict.
- Unchanged files remain skipped by hash check, so summary generation is not repeated.

## Behavior deviations from plan

- `generate_summary()` uses `ollama.Client(host=host).generate(...)` (still `ollama.generate` semantics, but explicit host-aware client for correctness with configured host).
- No functional deviation to required outcomes; tests validate the same contract.

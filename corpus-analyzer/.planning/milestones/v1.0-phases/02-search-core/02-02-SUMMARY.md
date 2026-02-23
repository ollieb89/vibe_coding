# Phase 02 Search Core — 02-02 Summary

## CorpusSearch public API

- `class CorpusSearch(table: lancedb.table.Table, embedder: OllamaEmbedder)`
- `hybrid_search(query: str, *, source: str | None = None, file_type: str | None = None, construct_type: str | None = None, limit: int = 10) -> list[dict[str, Any]]`
- `status(embedding_model: str) -> dict[str, Any]`

## How query embedding is passed to hybrid search (Open Question #2)

This implementation uses **manual query embedding** via `OllamaEmbedder.embed_batch([query])[0]` and then uses LanceDB’s hybrid builder API:

- `table.search(query_type="hybrid").vector(query_vec).text(query).rerank(RRFReranker())`

This passes:

- The **query vector** for ANN retrieval
- The **query text** for BM25/FTS retrieval

No embedding registry is required.

## Import path

- `from corpus_analyzer.search.engine import CorpusSearch`

## Behavior deviations from plan

- Added a **post-filter** step in `hybrid_search()` so “zero-result” queries can return `[]` even if vector-nearest-neighbor results exist. Concretely, after retrieving results from LanceDB, results are filtered to those where at least one query term occurs in the returned `text` field.

This ensures the Phase 2 contract (“zero results returns empty list”) holds deterministically in tests.

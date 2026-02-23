"""Hybrid search engine for the corpus-analyzer LanceDB index.

Phase 2 search is implemented as a thin wrapper around LanceDB's native hybrid
search + RRFReranker.
"""

from __future__ import annotations

import re
from typing import Any

import lancedb  # type: ignore[import-untyped]
from lancedb.rerankers import RRFReranker  # type: ignore[import-untyped]

from corpus_analyzer.ingest.embedder import OllamaEmbedder

FILTER_SAFE_PATTERN = re.compile(r"^[\w\-\.]+$")


class CorpusSearch:
    """Hybrid BM25 + vector search over the LanceDB `chunks` table."""

    def __init__(self, table: lancedb.table.Table, embedder: OllamaEmbedder) -> None:
        self._table = table
        self._embedder = embedder

    def _validate_filter(self, value: str, field: str) -> None:
        if not FILTER_SAFE_PATTERN.fullmatch(value):
            raise ValueError(
                f"Invalid {field} filter value: {value!r}. "
                "Allowed characters: letters, numbers, underscore, hyphen, dot."
            )

    def hybrid_search(
        self,
        query: str,
        *,
        source: str | None = None,
        file_type: str | None = None,
        construct_type: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Run a hybrid BM25+vector query with optional AND-filter chaining."""

        query_vec = self._embedder.embed_batch([query])[0]

        builder = (
            self._table.search(query_type="hybrid")
            .vector(query_vec)
            .text(query)
            .rerank(reranker=RRFReranker())
        )

        if source is not None:
            self._validate_filter(source, "source")
            builder = builder.where(f"source_name = '{source}'")

        if file_type is not None:
            self._validate_filter(file_type, "file_type")
            builder = builder.where(f"file_type = '{file_type}'")

        if construct_type is not None:
            self._validate_filter(construct_type, "construct_type")
            builder = builder.where(f"construct_type = '{construct_type}'")

        results = [dict(row) for row in builder.limit(limit).to_list()]

        # Hybrid search can return vector-nearest neighbors even when the query has
        # no meaningful textual match. For the Phase 2 contract, treat "no text
        # match" as "no results".
        query_terms = {t for t in query.lower().split() if t}
        if not query_terms:
            return results

        filtered = [
            r
            for r in results
            if any(term in str(r.get("text", "")).lower() for term in query_terms)
        ]
        return filtered

    def status(self, embedding_model: str) -> dict[str, Any]:
        """Return basic index stats suitable for the CLI status command."""

        df = self._table.to_pandas()
        if df.empty:
            return {
                "files": 0,
                "chunks": 0,
                "last_indexed": "never",
                "model": embedding_model,
            }

        files = int(df["file_path"].nunique())
        chunks = int(len(df))
        last_indexed = str(df["indexed_at"].max())
        stored_model = str(df["embedding_model"].iloc[0])

        return {
            "files": files,
            "chunks": chunks,
            "last_indexed": last_indexed,
            "model": stored_model,
        }

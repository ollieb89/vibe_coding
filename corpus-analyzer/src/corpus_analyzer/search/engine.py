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

CONSTRUCT_PRIORITY: dict[str, int] = {
    "agent": 1,
    "skill": 2,
    "workflow": 3,
    "command": 4,
    "rule": 5,
    "prompt": 6,
    "code": 7,
    "documentation": 8,
}

_VALID_SORT_VALUES = frozenset({"relevance", "construct", "confidence", "date", "path"})


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
        sort_by: str = "relevance",
        min_score: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Run a hybrid BM25+vector query with optional AND-filter chaining.

        Args:
            sort_by: Post-retrieval sort order. One of:
                "relevance" (default, RRF order), "construct" (CONSTRUCT_PRIORITY),
                "confidence" (descending), "date" (descending), "path" (ascending).
            min_score: Minimum _relevance_score threshold (inclusive). Results
                below this score are excluded. Default 0.0 keeps all results
                (all real RRF scores are positive). RRF scores range approximately
                0.009–0.033 for K=60. Negative values behave the same as 0.0.
        """
        if sort_by not in _VALID_SORT_VALUES:
            raise ValueError(
                f"Invalid sort_by value: {sort_by!r}. "
                f"Allowed values: {sorted(_VALID_SORT_VALUES)}"
            )

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

        # RRF scores range ~0.009–0.033 for K=60; min_score=0.0 is a no-op.
        if min_score > 0.0:
            filtered = [
                r for r in filtered
                if float(r.get("_relevance_score", 0.0)) >= min_score
            ]

        if sort_by == "construct":
            filtered.sort(
                key=lambda r: (
                    CONSTRUCT_PRIORITY.get(str(r.get("construct_type") or ""), 99),
                    -float(r.get("classification_confidence") or 0.0),
                )
            )
        elif sort_by == "confidence":
            filtered.sort(
                key=lambda r: float(r.get("classification_confidence") or 0.0), reverse=True
            )
        elif sort_by == "date":
            filtered.sort(key=lambda r: str(r.get("indexed_at") or ""), reverse=True)
        elif sort_by == "path":
            filtered.sort(key=lambda r: str(r.get("file_path") or ""))

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

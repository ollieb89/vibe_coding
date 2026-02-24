"""FastMCP server exposing corpus_search tool for Claude Code and other agents."""

import logging
import sys
from typing import Any, Optional

logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

from fastmcp import Context, FastMCP  # noqa: E402,I001
from fastmcp.server.lifespan import lifespan  # noqa: E402,I001

from corpus_analyzer.config import load_config  # noqa: E402,I001
from corpus_analyzer.ingest.embedder import OllamaEmbedder  # noqa: E402,I001
from corpus_analyzer.ingest.indexer import CorpusIndex  # noqa: E402,I001
from corpus_analyzer.search.engine import CorpusSearch  # noqa: E402,I001
from corpus_analyzer.config.schema import CONFIG_PATH, DATA_DIR  # noqa: E402,I001


@lifespan
async def corpus_lifespan(server: FastMCP) -> Any:
    """Pre-warm embedding model and open index at startup."""
    config = load_config(CONFIG_PATH)
    embedder = OllamaEmbedder(model=config.embedding.model, host=config.embedding.host)
    try:
        embedder.embed_batch(["warmup"])
    except Exception as exc:
        logging.warning("Pre-warm failed: %s — first query may be slow", exc)
    try:
        index = CorpusIndex.open(DATA_DIR, embedder)
        engine: CorpusSearch | None = CorpusSearch(index.table, embedder)
    except Exception as exc:
        logging.error("Index open failed: %s", exc)
        engine = None
    yield {"engine": engine, "config": config}


mcp = FastMCP("corpus", lifespan=corpus_lifespan)


@mcp.tool
async def corpus_search(
    query: str,
    source: Optional[str] = None,  # noqa: UP045
    type: Optional[str] = None,  # noqa: UP045
    construct: Optional[str] = None,  # noqa: UP045
    top_k: Optional[int] = 5,  # noqa: UP045
    min_score: Optional[float] = None,  # noqa: UP045
    name: Optional[str] = None,  # noqa: UP045
    ctx: Context = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """Search the corpus index with a natural language query.

    Each result is a self-contained unit of knowledge with the full chunk body
    and precise source line boundaries — no follow-up file reads needed.

    Result fields:
      - text: full untruncated chunk body (empty string for legacy rows where
              chunk_text is empty or missing)
      - start_line: 1-indexed start line in the source file (0 for legacy rows)
      - end_line: 1-indexed end line in the source file (0 for legacy rows)
      - path: absolute path to the source file
      - score: relevance score
      - construct_type: type of code/doc construct (function, class, documentation, …)
      - chunk_name: name of the chunk (function name, heading, etc.)
      - summary: brief LLM-generated summary of the chunk (may be empty)
      - file_type: file extension (e.g. ".py", ".md")

    Use 'source', 'type', 'construct' for filtering; 'top_k' for result count.
    'min_score' filters out results below the given relevance threshold (0.0 means no filter).
    'name' is an optional case-insensitive substring filter on chunk_name.
    Use to narrow results to a specific method or construct (e.g. 'ClassName.method').
    """
    engine_or_none: CorpusSearch | None = ctx.lifespan_context.get("engine")
    if engine_or_none is None:
        raise ValueError(
            "Index not found or embedding model unreachable. "
            "Run 'corpus index' first and ensure Ollama is running."
        )
    engine = engine_or_none

    limit = top_k if top_k is not None else 5

    effective_min_score = min_score if min_score is not None else 0.0

    try:
        raw_results = engine.hybrid_search(
            query,
            source=source,
            file_type=type,
            construct_type=construct,
            limit=limit,
            min_score=effective_min_score,
            name=name,
        )
    except Exception as exc:
        raise ValueError(
            f"Search failed: {exc}. Ensure 'corpus index' has been run."
        ) from exc

    if not raw_results:
        empty_response: dict[str, Any] = {
            "results": [],
            "message": f"No results found for query: {query}",
        }
        if min_score:
            empty_response["filtered_by_min_score"] = True
        return empty_response

    results = []
    for row in raw_results:
        result_dict: dict[str, Any] = {
            "text": str(row.get("chunk_text", "") or ""),
            "start_line": int(row.get("start_line", 0) or 0),
            "end_line": int(row.get("end_line", 0) or 0),
            "path": str(row.get("file_path", "")),
            "score": float(row.get("_relevance_score", 0.0)),
            "construct_type": str(row.get("construct_type") or "documentation"),
            "chunk_name": str(row.get("chunk_name", "") or ""),
            "summary": str(row.get("summary") or ""),
            "file_type": str(row.get("file_type", "")),
        }
        results.append(result_dict)

    return {"results": results}

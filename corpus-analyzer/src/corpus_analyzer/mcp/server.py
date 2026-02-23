"""FastMCP server exposing corpus_search tool for Claude Code and other agents."""

import logging
import sys
from pathlib import Path
from typing import Any, Optional

logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

from fastmcp import Context, FastMCP  # noqa: E402,I001
from fastmcp.server.lifespan import lifespan  # noqa: E402,I001

from corpus_analyzer.config import load_config  # noqa: E402,I001
from corpus_analyzer.ingest.embedder import OllamaEmbedder  # noqa: E402,I001
from corpus_analyzer.ingest.indexer import CorpusIndex  # noqa: E402,I001
from corpus_analyzer.search.engine import CorpusSearch  # noqa: E402,I001
from corpus_analyzer.search.formatter import extract_snippet  # noqa: E402,I001
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
    ctx: Context = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """Search the corpus index with a natural language query.

    Returns full file content for top matching files plus metadata.
    Use 'source', 'type', 'construct' for filtering; 'top_k' for result count.
    """
    engine_or_none: CorpusSearch | None = ctx.lifespan_context.get("engine")
    if engine_or_none is None:
        raise ValueError(
            "Index not found or embedding model unreachable. "
            "Run 'corpus index' first and ensure Ollama is running."
        )
    engine = engine_or_none

    limit = top_k if top_k is not None else 5

    try:
        raw_results = engine.hybrid_search(
            query,
            source=source,
            file_type=type,
            construct_type=construct,
            limit=limit,
        )
    except Exception as exc:
        raise ValueError(
            f"Search failed: {exc}. Ensure 'corpus index' has been run."
        ) from exc

    if not raw_results:
        return {"results": [], "message": f"No results found for query: {query}"}

    results = []
    for row in raw_results:
        file_path = str(row.get("file_path", ""))
        content_error: str | None = None
        try:
            full_content = Path(file_path).read_text(errors="replace")
        except OSError as exc:
            logging.warning("Cannot read file after indexing: %s — %s", file_path, exc)
            full_content = ""
            content_error = f"File not found: {file_path}"

        result_dict: dict[str, Any] = {
            "path": file_path,
            "score": float(row.get("_relevance_score", 0.0)),
            "snippet": extract_snippet(str(row.get("text", "")), query),
            "full_content": full_content,
            "construct_type": str(row.get("construct_type") or "documentation"),
            "summary": str(row.get("summary") or ""),
            "file_type": str(row.get("file_type", "")),
        }

        if content_error is not None:
            result_dict["content_error"] = content_error

        results.append(result_dict)

    return {"results": results}

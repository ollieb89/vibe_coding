"""Unit tests for the corpus MCP server (corpus_analyzer.mcp.server)."""

from __future__ import annotations

import asyncio
import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

def _make_ctx(engine: Any) -> MagicMock:
    """Create a mock FastMCP Context with a populated lifespan_context."""
    ctx = MagicMock()
    ctx.lifespan_context = {"engine": engine, "config": MagicMock()}
    ctx.info = AsyncMock(return_value=None)
    return ctx


def _make_engine(raw_results: list[dict[str, Any]]) -> MagicMock:
    """Create a mock CorpusSearch engine returning the provided raw results."""
    engine = MagicMock()
    engine.hybrid_search.return_value = raw_results
    return engine


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------


def test_corpus_search_returns_results_shape() -> None:
    """Tool returns list of result dicts with all required fields."""
    from corpus_analyzer.mcp.server import corpus_search

    raw = [
        {
            "file_path": "/some/file.md",
            "_relevance_score": 0.9,
            "text": "hello world",
            "construct_type": "skill",
            "summary": "A skill file",
            "file_type": ".md",
        }
    ]
    engine = _make_engine(raw)
    ctx = _make_ctx(engine)

    async def _run_test() -> dict[str, Any]:
        return await corpus_search(query="hello", ctx=ctx)

    result = asyncio.run(_run_test())

    assert "results" in result
    assert len(result["results"]) == 1
    r = result["results"][0]
    assert r["path"] == "/some/file.md"
    assert r["score"] == pytest.approx(0.9)
    assert r["construct_type"] == "skill"
    assert r["summary"] == "A skill file"
    assert r["file_type"] == ".md"
    assert "snippet" in r
    assert "full_content" in r


def test_corpus_search_empty_results() -> None:
    """Empty result set returns {results: [], message: 'No results found for query: X'}."""
    from corpus_analyzer.mcp.server import corpus_search

    engine = _make_engine([])
    ctx = _make_ctx(engine)

    async def _run_test() -> dict[str, Any]:
        return await corpus_search(query="nonexistent", ctx=ctx)

    result = asyncio.run(_run_test())

    assert result == {"results": [], "message": "No results found for query: nonexistent"}


def test_corpus_search_engine_none_raises_value_error() -> None:
    """When engine is None (startup failed), tool raises ValueError with actionable message."""
    from corpus_analyzer.mcp.server import corpus_search

    ctx = MagicMock()
    ctx.lifespan_context = {"engine": None, "config": MagicMock()}

    async def _run_test() -> None:
        await corpus_search(query="hello", ctx=ctx)

    with pytest.raises(ValueError, match="corpus index"):
        asyncio.run(_run_test())


def test_corpus_search_passes_filters_to_hybrid_search() -> None:
    """Tool passes source, file_type, construct_type, and limit through to hybrid_search."""
    from corpus_analyzer.mcp.server import corpus_search

    engine = _make_engine([])
    ctx = _make_ctx(engine)

    async def _run_test() -> None:
        await corpus_search(
            query="test",
            source="my-source",
            type=".py",
            construct="skill",
            top_k=3,
            ctx=ctx,
        )

    asyncio.run(_run_test())

    engine.hybrid_search.assert_called_once_with(
        "test",
        source="my-source",
        file_type=".py",
        construct_type="skill",
        limit=3,
    )


def test_server_module_does_not_write_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    """Importing and using the server module must not write anything to stdout (MCP-04)."""
    import corpus_analyzer.mcp.server  # noqa: F401 (import for side effects check)

    captured = capsys.readouterr()
    assert captured.out == "", f"Unexpected stdout output: {captured.out!r}"

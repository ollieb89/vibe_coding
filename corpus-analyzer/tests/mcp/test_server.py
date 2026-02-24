"""Unit tests for the corpus MCP server (corpus_analyzer.mcp.server)."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock

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
# Tests — existing shape / filter tests
# -----------------------------------------------------------------------------


def test_corpus_search_returns_results_shape() -> None:
    """Tool returns list of result dicts with all required CHUNK-03 fields."""
    from corpus_analyzer.mcp.server import corpus_search

    raw = [
        {
            "file_path": "/some/file.md",
            "_relevance_score": 0.9,
            "chunk_text": "hello world",
            "start_line": 1,
            "end_line": 3,
            "construct_type": "skill",
            "chunk_name": "intro",
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
    assert "text" in r
    assert "start_line" in r
    assert "end_line" in r
    assert "chunk_name" in r


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
        min_score=0.0,
    )


def test_corpus_search_min_score_forwarded() -> None:
    """corpus_search() forwards non-None min_score to hybrid_search() unchanged."""
    from corpus_analyzer.mcp.server import corpus_search

    engine = _make_engine([])
    ctx = _make_ctx(engine)

    async def _run_test() -> None:
        await corpus_search(query="q", min_score=0.015, ctx=ctx)

    asyncio.run(_run_test())

    call_kwargs = engine.hybrid_search.call_args[1]
    assert call_kwargs["min_score"] == pytest.approx(0.015)


def test_corpus_search_min_score_none_uses_zero() -> None:
    """corpus_search() converts None min_score to 0.0 before forwarding."""
    from corpus_analyzer.mcp.server import corpus_search

    engine = _make_engine([])
    ctx = _make_ctx(engine)

    async def _run_test() -> None:
        await corpus_search(query="q", min_score=None, ctx=ctx)

    asyncio.run(_run_test())

    call_kwargs = engine.hybrid_search.call_args[1]
    assert call_kwargs["min_score"] == pytest.approx(0.0)


def test_server_module_does_not_write_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    """Importing and using the server module must not write anything to stdout (MCP-04)."""
    import corpus_analyzer.mcp.server  # noqa: F401 (import for side effects check)

    captured = capsys.readouterr()
    assert captured.out == "", f"Unexpected stdout output: {captured.out!r}"


# -----------------------------------------------------------------------------
# Tests — CHUNK-03 new response shape (RED phase)
# -----------------------------------------------------------------------------


def test_corpus_search_text_field_present() -> None:
    """Result dict includes 'text' field with full untruncated chunk_text content."""
    from corpus_analyzer.mcp.server import corpus_search

    raw = [
        {
            "file_path": "/some/file.py",
            "_relevance_score": 0.8,
            "chunk_text": "def foo():\n    pass",
            "start_line": 10,
            "end_line": 12,
            "construct_type": "function",
            "chunk_name": "foo",
            "summary": "",
            "file_type": ".py",
        }
    ]
    engine = _make_engine(raw)
    ctx = _make_ctx(engine)

    async def _run_test() -> dict[str, Any]:
        return await corpus_search(query="foo", ctx=ctx)

    result = asyncio.run(_run_test())
    r = result["results"][0]
    assert r["text"] == "def foo():\n    pass"


def test_corpus_search_line_bounds_present() -> None:
    """Result dict includes correct start_line and end_line from the row."""
    from corpus_analyzer.mcp.server import corpus_search

    raw = [
        {
            "file_path": "/some/file.py",
            "_relevance_score": 0.8,
            "chunk_text": "def foo():\n    pass",
            "start_line": 10,
            "end_line": 12,
            "construct_type": "function",
            "chunk_name": "foo",
            "summary": "",
            "file_type": ".py",
        }
    ]
    engine = _make_engine(raw)
    ctx = _make_ctx(engine)

    async def _run_test() -> dict[str, Any]:
        return await corpus_search(query="foo", ctx=ctx)

    result = asyncio.run(_run_test())
    r = result["results"][0]
    assert r["start_line"] == 10
    assert r["end_line"] == 12


def test_corpus_search_legacy_row_empty_text() -> None:
    """Legacy row with empty chunk_text and zero line bounds returns text='' without raising."""
    from corpus_analyzer.mcp.server import corpus_search

    raw = [
        {
            "file_path": "/legacy/file.md",
            "_relevance_score": 0.5,
            "chunk_text": "",
            "start_line": 0,
            "end_line": 0,
            "construct_type": "documentation",
            "chunk_name": "",
            "summary": "",
            "file_type": ".md",
        }
    ]
    engine = _make_engine(raw)
    ctx = _make_ctx(engine)

    async def _run_test() -> dict[str, Any]:
        return await corpus_search(query="legacy", ctx=ctx)

    result = asyncio.run(_run_test())
    r = result["results"][0]
    assert r["text"] == ""
    assert r["start_line"] == 0
    assert r["end_line"] == 0


def test_corpus_search_no_snippet_field() -> None:
    """Regression guard: 'snippet' must NOT appear in result dict (old truncated preview removed)."""
    from corpus_analyzer.mcp.server import corpus_search

    raw = [
        {
            "file_path": "/some/file.md",
            "_relevance_score": 0.7,
            "chunk_text": "Some content here",
            "start_line": 5,
            "end_line": 7,
            "construct_type": "documentation",
            "chunk_name": "intro",
            "summary": "",
            "file_type": ".md",
        }
    ]
    engine = _make_engine(raw)
    ctx = _make_ctx(engine)

    async def _run_test() -> dict[str, Any]:
        return await corpus_search(query="content", ctx=ctx)

    result = asyncio.run(_run_test())
    r = result["results"][0]
    assert "snippet" not in r


def test_corpus_search_no_full_content_field() -> None:
    """Regression guard: 'full_content' must NOT appear in result dict (whole-file read removed)."""
    from corpus_analyzer.mcp.server import corpus_search

    raw = [
        {
            "file_path": "/some/file.md",
            "_relevance_score": 0.7,
            "chunk_text": "Some content here",
            "start_line": 5,
            "end_line": 7,
            "construct_type": "documentation",
            "chunk_name": "intro",
            "summary": "",
            "file_type": ".md",
        }
    ]
    engine = _make_engine(raw)
    ctx = _make_ctx(engine)

    async def _run_test() -> dict[str, Any]:
        return await corpus_search(query="content", ctx=ctx)

    result = asyncio.run(_run_test())
    r = result["results"][0]
    assert "full_content" not in r


def test_corpus_search_text_field_is_first_key() -> None:
    """Content-first ordering: 'text' must be the first key in result dict."""
    from corpus_analyzer.mcp.server import corpus_search

    raw = [
        {
            "file_path": "/some/file.py",
            "_relevance_score": 0.9,
            "chunk_text": "class Foo:\n    pass",
            "start_line": 1,
            "end_line": 2,
            "construct_type": "class",
            "chunk_name": "Foo",
            "summary": "A class",
            "file_type": ".py",
        }
    ]
    engine = _make_engine(raw)
    ctx = _make_ctx(engine)

    async def _run_test() -> dict[str, Any]:
        return await corpus_search(query="Foo", ctx=ctx)

    result = asyncio.run(_run_test())
    r = result["results"][0]
    assert list(r.keys())[0] == "text"


def test_corpus_search_no_content_error_field() -> None:
    """No file-read means no OSError path: 'content_error' must NOT appear in result dict."""
    from corpus_analyzer.mcp.server import corpus_search

    raw = [
        {
            "file_path": "/some/file.md",
            "_relevance_score": 0.6,
            "chunk_text": "Content here",
            "start_line": 1,
            "end_line": 3,
            "construct_type": "documentation",
            "chunk_name": "sec",
            "summary": "",
            "file_type": ".md",
        }
    ]
    engine = _make_engine(raw)
    ctx = _make_ctx(engine)

    async def _run_test() -> dict[str, Any]:
        return await corpus_search(query="content", ctx=ctx)

    result = asyncio.run(_run_test())
    r = result["results"][0]
    assert "content_error" not in r

"""Unit tests for the corpus Python public API (corpus_analyzer.api.public)."""

from __future__ import annotations

import os
from dataclasses import fields
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def test_search_result_has_required_fields() -> None:
    """SearchResult dataclass must have all 6 fields from API-01."""
    from corpus_analyzer.api.public import SearchResult

    field_names = {f.name for f in fields(SearchResult)}
    assert field_names == {"path", "file_type", "construct_type", "summary", "score", "snippet"}


def test_search_result_instantiation() -> None:
    """SearchResult can be instantiated with positional args and accessed by attribute."""
    from corpus_analyzer.api.public import SearchResult

    r = SearchResult(
        path="/foo/bar.md",
        file_type=".md",
        construct_type="skill",
        summary="A skill",
        score=0.85,
        snippet="hello world",
    )
    assert r.path == "/foo/bar.md"
    assert r.score == pytest.approx(0.85)


def test_search_calls_hybrid_search_and_maps_to_dataclasses() -> None:
    """search() delegates to CorpusSearch.hybrid_search() and maps results to SearchResult."""
    from corpus_analyzer.api.public import search

    mock_engine = MagicMock()
    mock_engine.hybrid_search.return_value = [
        {
            "file_path": "/x/y.md",
            "file_type": ".md",
            "construct_type": "prompt",
            "summary": "A prompt",
            "_relevance_score": 0.7,
            "text": "some prompt text",
        }
    ]

    with patch("corpus_analyzer.api.public._open_engine", return_value=(mock_engine, MagicMock())):
        results = search("test query")

    assert len(results) == 1
    assert results[0].path == "/x/y.md"
    assert results[0].construct_type == "prompt"
    assert results[0].score == pytest.approx(0.7)
    mock_engine.hybrid_search.assert_called_once_with(
        "test query",
        source=None,
        file_type=None,
        construct_type=None,
        limit=10,
        sort_by="relevance",
        min_score=0.0,
    )


def test_search_passes_filters_to_hybrid_search() -> None:
    """search() passes keyword arguments through to hybrid_search filters."""
    from corpus_analyzer.api.public import search

    mock_engine = MagicMock()
    mock_engine.hybrid_search.return_value = []

    with patch("corpus_analyzer.api.public._open_engine", return_value=(mock_engine, MagicMock())):
        results = search("q", source="my-source", file_type=".py", construct_type="code", limit=5)

    assert results == []
    mock_engine.hybrid_search.assert_called_once_with(
        "q",
        source="my-source",
        file_type=".py",
        construct_type="code",
        limit=5,
        sort_by="relevance",
        min_score=0.0,
    )


def test_index_calls_index_source_for_each_source() -> None:
    """index() calls CorpusIndex.index_source() once per configured source."""
    from corpus_analyzer.api.public import index

    mock_result = MagicMock()
    mock_result.files_indexed = 3
    mock_result.chunks_written = 12
    mock_result.files_skipped = 1
    mock_result.elapsed = 0.5

    mock_index = MagicMock()
    mock_index.index_source.return_value = mock_result

    mock_config = MagicMock()
    source_a = MagicMock()
    source_a.name = "source-a"
    source_b = MagicMock()
    source_b.name = "source-b"
    mock_config.sources = [source_a, source_b]

    with (
        patch("corpus_analyzer.api.public._find_config", return_value=Path("/fake/corpus.toml")),
        patch("corpus_analyzer.api.public.load_config", return_value=mock_config),
        patch("corpus_analyzer.api.public.OllamaEmbedder"),
        patch("corpus_analyzer.api.public.CorpusIndex") as mock_ci_class,
    ):
        mock_ci_class.open.return_value = mock_index
        results = index()

    assert len(results) == 2
    assert mock_index.index_source.call_count == 2
    assert results[0]["source_name"] == "source-a"
    assert results[0]["files_indexed"] == 3


def test_search_sort_by_translates_and_forwards() -> None:
    """search() translates API sort_by vocabulary to engine vocabulary before forwarding."""
    from corpus_analyzer.api.public import search

    mock_engine = MagicMock()
    mock_engine.hybrid_search.return_value = []

    with patch("corpus_analyzer.api.public._open_engine", return_value=(mock_engine, MagicMock())):
        search("q", sort_by="title")

    call_kwargs = mock_engine.hybrid_search.call_args[1]
    assert call_kwargs["sort_by"] == "path"

    mock_engine.reset_mock()
    mock_engine.hybrid_search.return_value = []

    with patch("corpus_analyzer.api.public._open_engine", return_value=(mock_engine, MagicMock())):
        search("q", sort_by="date")

    call_kwargs = mock_engine.hybrid_search.call_args[1]
    assert call_kwargs["sort_by"] == "date"


def test_search_invalid_sort_by_raises_value_error() -> None:
    """search() raises ValueError with message containing 'Invalid sort_by' for bad values."""
    from corpus_analyzer.api.public import search

    mock_engine = MagicMock()
    mock_engine.hybrid_search.return_value = []

    with (
        patch("corpus_analyzer.api.public._open_engine", return_value=(mock_engine, MagicMock())),
        pytest.raises(ValueError, match="Invalid sort_by"),
    ):
        search("q", sort_by="invalid")


def test_search_min_score_forwarded() -> None:
    """search() forwards min_score to hybrid_search() unchanged."""
    from corpus_analyzer.api.public import search

    mock_engine = MagicMock()
    mock_engine.hybrid_search.return_value = []

    with patch("corpus_analyzer.api.public._open_engine", return_value=(mock_engine, MagicMock())):
        search("q", min_score=0.02)

    call_kwargs = mock_engine.hybrid_search.call_args[1]
    assert call_kwargs["min_score"] == pytest.approx(0.02)


def test_find_config_walks_up_from_cwd(tmp_path: Path) -> None:
    """_find_config() finds corpus.toml in a parent directory above CWD."""
    from corpus_analyzer.api.public import _find_config

    # Create corpus.toml in tmp_path/project/ and CWD at tmp_path/project/src/
    (tmp_path / "project").mkdir()
    config_file = tmp_path / "project" / "corpus.toml"
    config_file.write_text("")
    subdir = tmp_path / "project" / "src"
    subdir.mkdir()
    # Add .git sentinel to stop the walk
    (tmp_path / "project" / ".git").mkdir()

    original_cwd = os.getcwd()
    try:
        os.chdir(subdir)
        found = _find_config()
        # corpus.toml exists in parent of .git dir, so it should be found first
        assert found == config_file
    finally:
        os.chdir(original_cwd)

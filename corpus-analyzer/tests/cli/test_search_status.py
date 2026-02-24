"""CLI tests for search and status commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from corpus_analyzer.cli import app
from corpus_analyzer.config.schema import CorpusConfig, EmbeddingConfig

runner = CliRunner()


def _config() -> CorpusConfig:
    return CorpusConfig(embedding=EmbeddingConfig(model="nomic-embed-text", host="http://localhost:11434"))


def test_search_help_shows_expected_flags() -> None:
    result = runner.invoke(app, ["search", "--help"])
    assert result.exit_code == 0
    assert "--source" in result.stdout
    assert "--type" in result.stdout
    assert "--construct" in result.stdout
    assert "--limit" in result.stdout


def test_status_help_is_available() -> None:
    result = runner.invoke(app, ["status", "--help"])
    assert result.exit_code == 0
    assert "Show index health" in result.stdout


def test_search_no_results_message() -> None:
    with (
        patch("corpus_analyzer.cli.load_config", return_value=_config()),
        patch("corpus_analyzer.cli.OllamaEmbedder") as mock_embedder_cls,
        patch("corpus_analyzer.cli.CorpusIndex.open") as mock_open,
        patch("corpus_analyzer.cli.CorpusSearch") as mock_search_cls,
    ):
        mock_embedder = MagicMock()
        mock_embedder.validate_connection.return_value = None
        mock_embedder_cls.return_value = mock_embedder

        mock_open.return_value = MagicMock(table=MagicMock())

        mock_search = MagicMock()
        mock_search.hybrid_search.return_value = []
        mock_search_cls.return_value = mock_search

        result = runner.invoke(app, ["search", "systematic debugging"])

    assert result.exit_code == 0
    assert 'No results for "systematic debugging"' in result.stdout


def test_search_invalid_filter_exits_non_zero() -> None:
    with (
        patch("corpus_analyzer.cli.load_config", return_value=_config()),
        patch("corpus_analyzer.cli.OllamaEmbedder") as mock_embedder_cls,
        patch("corpus_analyzer.cli.CorpusIndex.open") as mock_open,
        patch("corpus_analyzer.cli.CorpusSearch") as mock_search_cls,
    ):
        mock_embedder = MagicMock()
        mock_embedder.validate_connection.return_value = None
        mock_embedder_cls.return_value = mock_embedder

        mock_open.return_value = MagicMock(table=MagicMock())

        mock_search = MagicMock()
        mock_search.hybrid_search.side_effect = ValueError("Invalid source filter value")
        mock_search_cls.return_value = mock_search

        result = runner.invoke(app, ["search", "query", "--source", "bad value"])

    assert result.exit_code == 1
    assert "Invalid source filter value" in result.stdout


def test_search_result_missing_relevance_score_does_not_raise() -> None:
    with (
        patch("corpus_analyzer.cli.load_config", return_value=_config()),
        patch("corpus_analyzer.cli.OllamaEmbedder") as mock_embedder_cls,
        patch("corpus_analyzer.cli.CorpusIndex.open") as mock_open,
        patch("corpus_analyzer.cli.CorpusSearch") as mock_search_cls,
    ):
        mock_embedder = MagicMock()
        mock_embedder_cls.return_value = mock_embedder
        mock_open.return_value = MagicMock(table=MagicMock())

        mock_search = MagicMock()
        mock_search.hybrid_search.return_value = [
            {
                "file_path": "/fake/path.md",
                "text": "fake content",
                "construct_type": "documentation",
                # _relevance_score intentionally missing
            }
        ]
        mock_search_cls.return_value = mock_search

        result = runner.invoke(app, ["search", "query"])

    assert result.exit_code == 0


def test_search_construct_sort_note_when_redundant() -> None:
    """CLI prints a dim note when --construct and --sort construct are used together."""
    with (
        patch("corpus_analyzer.cli.load_config", return_value=_config()),
        patch("corpus_analyzer.cli.OllamaEmbedder") as mock_embedder_cls,
        patch("corpus_analyzer.cli.CorpusIndex.open") as mock_open,
        patch("corpus_analyzer.cli.CorpusSearch") as mock_search_cls,
    ):
        mock_embedder = MagicMock()
        mock_embedder.validate_connection.return_value = None
        mock_embedder_cls.return_value = mock_embedder
        mock_open.return_value = MagicMock(table=MagicMock())

        mock_search = MagicMock()
        mock_search.hybrid_search.return_value = [
            {"file_path": "/fake/agent.md", "text": "agent content", "construct_type": "agent"}
        ]
        mock_search_cls.return_value = mock_search

        result = runner.invoke(
            app, ["search", "query", "--construct", "agent", "--sort", "construct"]
        )

    assert result.exit_code == 0
    assert "sorting by priority is implicit" in result.stdout


def test_search_no_construct_sort_note_without_redundancy() -> None:
    """CLI does NOT print the redundancy note when --construct is absent."""
    with (
        patch("corpus_analyzer.cli.load_config", return_value=_config()),
        patch("corpus_analyzer.cli.OllamaEmbedder") as mock_embedder_cls,
        patch("corpus_analyzer.cli.CorpusIndex.open") as mock_open,
        patch("corpus_analyzer.cli.CorpusSearch") as mock_search_cls,
    ):
        mock_embedder = MagicMock()
        mock_embedder.validate_connection.return_value = None
        mock_embedder_cls.return_value = mock_embedder
        mock_open.return_value = MagicMock(table=MagicMock())

        mock_search = MagicMock()
        mock_search.hybrid_search.return_value = [
            {"file_path": "/fake/agent.md", "text": "agent content", "construct_type": "agent"}
        ]
        mock_search_cls.return_value = mock_search

        result = runner.invoke(app, ["search", "query", "--sort", "construct"])

    assert result.exit_code == 0
    assert "sorting by priority is implicit" not in result.stdout


def test_status_outputs_expected_metrics() -> None:
    with (
        patch("corpus_analyzer.cli.load_config", return_value=_config()),
        patch("corpus_analyzer.cli.OllamaEmbedder") as mock_embedder_cls,
        patch("corpus_analyzer.cli.CorpusIndex.open") as mock_open,
        patch("corpus_analyzer.cli.CorpusSearch") as mock_search_cls,
    ):
        mock_embedder = MagicMock()
        mock_embedder_cls.return_value = mock_embedder
        mock_open.return_value = MagicMock(table=MagicMock())

        mock_search = MagicMock()
        mock_search.status.return_value = {
            "files": 42,
            "chunks": 187,
            "last_indexed": "2026-02-23T14:30:00+00:00",
            "model": "nomic-embed-text",
        }
        mock_search_cls.return_value = mock_search

        result = runner.invoke(app, ["status"])

    assert result.exit_code == 0
    assert "Index Status" in result.stdout
    assert "Files" in result.stdout
    assert "Chunks" in result.stdout
    assert "Last indexed" in result.stdout
    assert "nomic-embed-text" in result.stdout


def test_status_missing_index_message() -> None:
    with (
        patch("corpus_analyzer.cli.load_config", return_value=_config()),
        patch("corpus_analyzer.cli.OllamaEmbedder") as mock_embedder_cls,
        patch("corpus_analyzer.cli.CorpusIndex.open", side_effect=RuntimeError("missing")),
    ):
        mock_embedder_cls.return_value = MagicMock()
        result = runner.invoke(app, ["status"])

    assert result.exit_code == 0
    assert "Index not found. Run 'corpus index' first." in result.stdout


def test_min_score_option_help_text() -> None:
    """FILT-02: --min-score help text documents the score range.

    Rich wraps long help text across lines with padding, so we assert
    each token appears somewhere in the output rather than as a contiguous
    substring.
    """
    result = runner.invoke(app, ["search", "--help"])
    assert result.exit_code == 0
    assert "--min-score" in result.stdout
    assert "Scores are normalised to 0–1 range" in result.stdout
    assert "0.0 keeps" in result.stdout


def test_min_score_filters_all_prints_hint() -> None:
    """FILT-03: when --min-score filters all results, print the contextual hint."""
    with (
        patch("corpus_analyzer.cli.load_config", return_value=_config()),
        patch("corpus_analyzer.cli.OllamaEmbedder") as mock_embedder_cls,
        patch("corpus_analyzer.cli.CorpusIndex.open") as mock_open,
        patch("corpus_analyzer.cli.CorpusSearch") as mock_search_cls,
    ):
        mock_embedder = MagicMock()
        mock_embedder.validate_connection.return_value = None
        mock_embedder_cls.return_value = mock_embedder
        mock_open.return_value = MagicMock(table=MagicMock())

        mock_search = MagicMock()
        mock_search.hybrid_search.return_value = []
        mock_search_cls.return_value = mock_search

        result = runner.invoke(app, ["search", "anything", "--min-score", "0.999"])

    assert result.exit_code == 0
    assert "No results above 0.999" in result.stdout
    assert "Run without --min-score to see available scores." in result.stdout
    assert 'No results for "anything"' not in result.stdout


def test_sort_by_option_forwards_to_engine() -> None:
    """--sort-by translates API vocabulary to engine vocabulary before forwarding."""
    with (
        patch("corpus_analyzer.cli.load_config", return_value=_config()),
        patch("corpus_analyzer.cli.OllamaEmbedder") as mock_embedder_cls,
        patch("corpus_analyzer.cli.CorpusIndex.open") as mock_open,
        patch("corpus_analyzer.cli.CorpusSearch") as mock_search_cls,
    ):
        mock_embedder = MagicMock()
        mock_embedder.validate_connection.return_value = None
        mock_embedder_cls.return_value = mock_embedder
        mock_open.return_value = MagicMock(table=MagicMock())

        mock_engine = MagicMock()
        mock_engine.hybrid_search.return_value = [
            {"file_path": "/fake/path.md", "text": "content", "construct_type": "agent"}
        ]
        mock_search_cls.return_value = mock_engine

        # score -> relevance
        runner.invoke(app, ["search", "q", "--sort-by", "score"])
        assert mock_engine.hybrid_search.call_args.kwargs["sort_by"] == "relevance"

        # title -> path
        runner.invoke(app, ["search", "q", "--sort-by", "title"])
        assert mock_engine.hybrid_search.call_args.kwargs["sort_by"] == "path"


def test_search_name_flag_in_help() -> None:
    """NAME-01: --name option appears in corpus search --help output."""
    result = runner.invoke(app, ["search", "--help"])
    assert result.exit_code == 0
    assert "--name" in result.stdout


def test_search_name_filter_passed_to_engine() -> None:
    """NAME-01: --name value is passed as name= keyword to hybrid_search()."""
    with (
        patch("corpus_analyzer.cli.load_config", return_value=_config()),
        patch("corpus_analyzer.cli.OllamaEmbedder") as mock_embedder_cls,
        patch("corpus_analyzer.cli.CorpusIndex.open") as mock_open,
        patch("corpus_analyzer.cli.CorpusSearch") as mock_search_cls,
    ):
        mock_embedder = MagicMock()
        mock_embedder.validate_connection.return_value = None
        mock_embedder_cls.return_value = mock_embedder
        mock_open.return_value = MagicMock(table=MagicMock())

        mock_search = MagicMock()
        mock_search.hybrid_search.return_value = []
        mock_search_cls.return_value = mock_search

        runner.invoke(app, ["search", "myquery", "--name", "SearchEngine.search"])

    call_kwargs = mock_search.hybrid_search.call_args.kwargs
    assert call_kwargs.get("name") == "SearchEngine.search"


def test_search_name_only_no_query_is_valid() -> None:
    """NAME-03: corpus search --name foo (no positional query) exits 0."""
    with (
        patch("corpus_analyzer.cli.load_config", return_value=_config()),
        patch("corpus_analyzer.cli.OllamaEmbedder") as mock_embedder_cls,
        patch("corpus_analyzer.cli.CorpusIndex.open") as mock_open,
        patch("corpus_analyzer.cli.CorpusSearch") as mock_search_cls,
    ):
        mock_embedder = MagicMock()
        mock_embedder.validate_connection.return_value = None
        mock_embedder_cls.return_value = mock_embedder
        mock_open.return_value = MagicMock(table=MagicMock())

        mock_search = MagicMock()
        mock_search.hybrid_search.return_value = []
        mock_search_cls.return_value = mock_search

        result = runner.invoke(app, ["search", "--name", "foo"])

    assert result.exit_code == 0


def test_search_name_only_passes_empty_query_to_engine() -> None:
    """NAME-03: --name only (no query) passes query='' to hybrid_search."""
    with (
        patch("corpus_analyzer.cli.load_config", return_value=_config()),
        patch("corpus_analyzer.cli.OllamaEmbedder") as mock_embedder_cls,
        patch("corpus_analyzer.cli.CorpusIndex.open") as mock_open,
        patch("corpus_analyzer.cli.CorpusSearch") as mock_search_cls,
    ):
        mock_embedder = MagicMock()
        mock_embedder.validate_connection.return_value = None
        mock_embedder_cls.return_value = mock_embedder
        mock_open.return_value = MagicMock(table=MagicMock())

        mock_search = MagicMock()
        mock_search.hybrid_search.return_value = []
        mock_search_cls.return_value = mock_search

        runner.invoke(app, ["search", "--name", "foo"])

    positional_query = mock_search.hybrid_search.call_args.args[0]
    assert positional_query == ""


def test_search_no_query_no_name_exits_error() -> None:
    """NAME-03: corpus search with no query and no --name prints error and exits 1."""
    result = runner.invoke(app, ["search"])
    assert result.exit_code == 1
    assert "Provide a query or --name" in result.stdout


def test_search_name_composes_with_source_filter() -> None:
    """NAME-01: --name composes with --source as AND predicate passed to engine."""
    with (
        patch("corpus_analyzer.cli.load_config", return_value=_config()),
        patch("corpus_analyzer.cli.OllamaEmbedder") as mock_embedder_cls,
        patch("corpus_analyzer.cli.CorpusIndex.open") as mock_open,
        patch("corpus_analyzer.cli.CorpusSearch") as mock_search_cls,
    ):
        mock_embedder = MagicMock()
        mock_embedder.validate_connection.return_value = None
        mock_embedder_cls.return_value = mock_embedder
        mock_open.return_value = MagicMock(table=MagicMock())

        mock_search = MagicMock()
        mock_search.hybrid_search.return_value = []
        mock_search_cls.return_value = mock_search

        runner.invoke(app, ["search", "q", "--name", "foo", "--source", "my-src"])

    call_kwargs = mock_search.hybrid_search.call_args.kwargs
    assert call_kwargs.get("name") == "foo"
    assert call_kwargs.get("source") == "my-src"

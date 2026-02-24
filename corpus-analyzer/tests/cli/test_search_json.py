import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from corpus_analyzer.cli import app
from corpus_analyzer.config.schema import CorpusConfig, EmbeddingConfig

runner = CliRunner()


def _config() -> CorpusConfig:
    return CorpusConfig(embedding=EmbeddingConfig(model="nomic-embed-text", host="http://localhost:11434"))


def test_search_json_output() -> None:
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
            {
                "file_path": "/test/path.md",
                "_relevance_score": 0.95,
                "construct_type": "skill",
                "chunk_name": "Test Skill",
                "start_line": 10,
                "end_line": 20,
                "chunk_text": "This is a test chunk",
            }
        ]
        mock_search_cls.return_value = mock_search

        result = runner.invoke(app, ["search", "--output", "json", "test"])

    assert result.exit_code == 0
    
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    assert len(data) == 1
    
    first = data[0]
    assert first["path"] == "/test/path.md"
    assert first["score"] == 0.95
    assert first["construct_type"] == "skill"
    assert first["chunk_name"] == "Test Skill"
    assert first["start_line"] == 10
    assert first["end_line"] == 20
    assert first["text"] == "This is a test chunk"


def test_search_json_empty_results() -> None:
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

        result = runner.invoke(app, ["search", "this-will-not-match", "--output", "json"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "[]"
    
    data = json.loads(result.stdout)
    assert data == []


def test_search_json_error_results() -> None:
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

        result = runner.invoke(app, ["search", "query", "--source", "bad value", "--output", "json"])

    assert result.exit_code == 1
    
    data = json.loads(result.stdout)
    assert "error" in data
    assert "Invalid source filter value" in data["error"]


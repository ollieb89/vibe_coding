"""CLI tests for the index command — graph.sqlite creation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from corpus_analyzer.cli import app
from corpus_analyzer.config.schema import CorpusConfig, EmbeddingConfig, SourceConfig

runner = CliRunner()


def _config(source_path: Path) -> CorpusConfig:
    """Build a minimal CorpusConfig pointing at *source_path*."""
    return CorpusConfig(
        embedding=EmbeddingConfig(model="nomic-embed-text", host="http://localhost:11434"),
        sources=[
            SourceConfig(
                name="test-source",
                path=str(source_path),
                extensions=[".md"],
            )
        ],
    )


@pytest.fixture()
def source_dir(tmp_path: Path) -> Path:
    """Create a tiny source directory with one markdown file."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "skill-a" / "SKILL.md").parent.mkdir(parents=True, exist_ok=True)
    (src / "skill-a" / "SKILL.md").write_text(
        "# Skill A\n\n## Related Skills\n\n- `skill-b`\n"
    )
    return src


def test_index_command_builds_graph_sqlite(tmp_path: Path, source_dir: Path) -> None:
    """Running `corpus index` creates graph.sqlite alongside the LanceDB index."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    config = _config(source_dir)

    mock_index_result = MagicMock()
    mock_index_result.files_indexed = 1
    mock_index_result.chunks_written = 2
    mock_index_result.files_skipped = 0
    mock_index_result.files_removed = 0
    mock_index_result.elapsed = 0.1

    mock_index = MagicMock()
    mock_index.check_source_status.return_value = MagicMock(
        needs_indexing=True,
        reason="new source",
    )
    mock_index.index_source.return_value = mock_index_result

    with (
        patch("corpus_analyzer.cli.load_config", return_value=config),
        patch("corpus_analyzer.cli.OllamaEmbedder") as mock_embedder_cls,
        patch("corpus_analyzer.cli.CorpusIndex.open", return_value=mock_index),
        patch("corpus_analyzer.cli.DATA_DIR", data_dir),
        patch("corpus_analyzer.cli.walk_source") as mock_walk,
    ):
        mock_embedder = MagicMock()
        mock_embedder.validate_connection.return_value = None
        mock_embedder_cls.return_value = mock_embedder

        # Return one file so the progress bar fires and index_source() is called
        mock_walk.return_value = [source_dir / "skill-a" / "SKILL.md"]

        result = runner.invoke(app, ["index"])

    assert result.exit_code == 0, result.output
    assert (data_dir / "graph.sqlite").exists(), (
        "graph.sqlite was not created in DATA_DIR after running 'corpus index'"
    )

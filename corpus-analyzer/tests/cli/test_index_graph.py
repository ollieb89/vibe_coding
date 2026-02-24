"""CLI tests for the index command — graph.sqlite creation and duplicate warnings."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from corpus_analyzer.cli import app
from corpus_analyzer.config.schema import CorpusConfig, EmbeddingConfig, SourceConfig
from corpus_analyzer.graph.registry import SlugRegistry

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


# ---------------------------------------------------------------------------
# Helpers for duplicate-warning tests
# ---------------------------------------------------------------------------

def _run_index_with_duplicates(
    tmp_path: Path,
    source_dir: Path,
    structural: dict[str, list[Path]],
    cross_source: dict[str, list[Path]],
) -> str:
    """Run `corpus index` with a mocked SlugRegistry whose classify() returns the given split.

    Returns the CLI output string.
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    config = _config(source_dir)

    mock_index_result = MagicMock()
    mock_index_result.files_indexed = 0
    mock_index_result.chunks_written = 0
    mock_index_result.files_skipped = 1
    mock_index_result.files_removed = 0
    mock_index_result.elapsed = 0.0

    mock_index = MagicMock()
    mock_index.check_source_status.return_value = MagicMock(
        needs_indexing=False,
        reason="up to date",
    )
    mock_index.index_source.return_value = mock_index_result

    fake_registry = MagicMock(spec=SlugRegistry)
    fake_registry.__len__ = MagicMock(return_value=len(structural) + len(cross_source) + 1)
    fake_registry.classify.return_value = (structural, cross_source)

    with (
        patch("corpus_analyzer.cli.load_config", return_value=config),
        patch("corpus_analyzer.cli.OllamaEmbedder") as mock_embedder_cls,
        patch("corpus_analyzer.cli.CorpusIndex.open", return_value=mock_index),
        patch("corpus_analyzer.cli.DATA_DIR", data_dir),
        patch("corpus_analyzer.cli.walk_source", return_value=[]),
        patch("corpus_analyzer.cli.SlugRegistry") as mock_registry_cls,
    ):
        mock_embedder = MagicMock()
        mock_embedder.validate_connection.return_value = None
        mock_embedder_cls.return_value = mock_embedder
        mock_registry_cls.build.return_value = fake_registry

        result = runner.invoke(app, ["index"])

    assert result.exit_code == 0, result.output
    return result.output


def test_cross_source_duplicates_are_suppressed(tmp_path: Path, source_dir: Path) -> None:
    """Cross-source duplicates (same skill in multiple sources) must not show a warning."""
    cross: dict[str, list[Path]] = {
        "git": [Path(f"/source{i}/git/SKILL.md") for i in range(4)],
        "brainstorming": [Path(f"/source{i}/brainstorming/SKILL.md") for i in range(3)],
    }
    output = _run_index_with_duplicates(tmp_path, source_dir, {}, cross)
    assert "⚠️" not in output, f"Expected no warning for cross-source duplicates, got:\n{output}"


def test_within_source_duplicates_shown_as_summary(tmp_path: Path, source_dir: Path) -> None:
    """Within-source duplicates must appear in a single summary warning line."""
    within: dict[str, list[Path]] = {
        "writing-skills": [Path(f"/repo/v{i}/writing-skills/SKILL.md") for i in range(3)],
        "clerk-auth": [Path(f"/repo/v{i}/clerk-auth/SKILL.md") for i in range(2)],
    }
    output = _run_index_with_duplicates(tmp_path, source_dir, within, {})
    assert "⚠️" in output, f"Expected a warning for within-source collisions, got:\n{output}"
    warning_lines = [ln for ln in output.splitlines() if "⚠️" in ln]
    assert len(warning_lines) == 1, (
        f"Expected exactly one summary warning line, got {len(warning_lines)}:\n{output}"
    )
    assert "writing-skills" in output
    assert "clerk-auth" in output


def test_mixed_within_and_cross_source(tmp_path: Path, source_dir: Path) -> None:
    """Cross-source slugs must not appear in the warning; within-source ones must."""
    cross: dict[str, list[Path]] = {
        "git": [Path(f"/source{i}/git/SKILL.md") for i in range(4)],
    }
    within: dict[str, list[Path]] = {
        "rag-engineer": [Path(f"/repo/v{i}/rag-engineer/SKILL.md") for i in range(2)],
    }
    output = _run_index_with_duplicates(tmp_path, source_dir, within, cross)
    assert "⚠️" in output, f"Expected warning for within-source collision, got:\n{output}"
    assert "git" not in output, "Cross-source slug 'git' must be excluded from warning"
    assert "rag-engineer" in output

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
    duplicates: dict[str, list[Path]],
) -> str:
    """Run `corpus index` with a mocked SlugRegistry that exposes *duplicates*.

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
    fake_registry.__len__ = MagicMock(return_value=len(duplicates) + 1)
    fake_registry.duplicates = duplicates

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


def test_high_cardinality_duplicates_are_suppressed(tmp_path: Path, source_dir: Path) -> None:
    """Duplicate slugs with > 8 candidates must not appear in the warning output."""
    big_dup: dict[str, list[Path]] = {
        "references": [Path(f"/repo{i}/references/README.md") for i in range(30)],
        "agents": [Path(f"/repo{i}/agents/README.md") for i in range(76)],
    }
    output = _run_index_with_duplicates(tmp_path, source_dir, big_dup)
    assert "⚠️" not in output, f"Expected no warning for high-cardinality duplicates, got:\n{output}"


def test_low_cardinality_duplicates_shown_as_summary(tmp_path: Path, source_dir: Path) -> None:
    """2–3 real collisions must appear in a single summary line, not individual lines per slug."""
    real_dups: dict[str, list[Path]] = {
        "writing-skills": [Path(f"/repo{i}/writing-skills/SKILL.md") for i in range(3)],
        "clerk-auth": [Path(f"/repo{i}/clerk-auth/SKILL.md") for i in range(2)],
    }
    output = _run_index_with_duplicates(tmp_path, source_dir, real_dups)
    assert "⚠️" in output, f"Expected a warning for real collisions, got:\n{output}"
    # Summary should mention both slugs on a single line, not emit one line per slug
    warning_lines = [ln for ln in output.splitlines() if "⚠️" in ln]
    assert len(warning_lines) == 1, (
        f"Expected exactly one summary warning line, got {len(warning_lines)}:\n{output}"
    )
    assert "writing-skills" in output
    assert "clerk-auth" in output


def test_mixed_cardinality_summary_excludes_high_count(tmp_path: Path, source_dir: Path) -> None:
    """High-cardinality structural slugs must be excluded from the summary even when real collisions exist."""
    mixed_dups: dict[str, list[Path]] = {
        "references": [Path(f"/repo{i}/references/README.md") for i in range(30)],
        "rag-engineer": [Path(f"/repo{i}/rag-engineer/SKILL.md") for i in range(2)],
    }
    output = _run_index_with_duplicates(tmp_path, source_dir, mixed_dups)
    assert "⚠️" in output, f"Expected warning for real collision, got:\n{output}"
    assert "references" not in output, (
        "High-cardinality slug 'references' must be excluded from warning"
    )
    assert "rag-engineer" in output

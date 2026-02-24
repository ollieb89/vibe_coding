# tests/cli/test_graph_command.py
"""CLI tests for the `corpus graph` command."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from corpus_analyzer.cli import app

runner = CliRunner()


def test_graph_help_available() -> None:
    """corpus graph --help exits cleanly and shows the depth option."""
    result = runner.invoke(app, ["graph", "--help"])
    assert result.exit_code == 0
    assert "--depth" in result.stdout or "depth" in result.stdout.lower()


def test_graph_no_results_message(tmp_path: Path) -> None:
    """corpus graph with an unknown slug prints a friendly 'not found' message."""
    graph_db = tmp_path / "graph.sqlite"
    from corpus_analyzer.graph.store import GraphStore

    GraphStore(graph_db)  # init empty db
    with patch("corpus_analyzer.cli.DATA_DIR", tmp_path):
        result = runner.invoke(app, ["graph", "no-such-skill"])
    assert result.exit_code == 0
    assert "no relationships" in result.stdout.lower() or "not found" in result.stdout.lower()


def test_graph_shows_downstream(tmp_path: Path) -> None:
    """corpus graph <slug> shows downstream (outgoing) edges for a matched path."""
    from corpus_analyzer.graph.store import GraphStore

    store = GraphStore(tmp_path / "graph.sqlite")
    store.write_edges("/skills/alpha/SKILL.md", [("/skills/beta/SKILL.md", True, "related_skill")])
    with patch("corpus_analyzer.cli.DATA_DIR", tmp_path):
        result = runner.invoke(app, ["graph", "alpha"])
    assert result.exit_code == 0
    assert "beta" in result.stdout


def test_graph_shows_upstream(tmp_path: Path) -> None:
    """corpus graph <slug> shows upstream (incoming) edges when the slug matches a target."""
    from corpus_analyzer.graph.store import GraphStore

    store = GraphStore(tmp_path / "graph.sqlite")
    store.write_edges("/skills/alpha/SKILL.md", [("/skills/beta/SKILL.md", True, "related_skill")])
    with patch("corpus_analyzer.cli.DATA_DIR", tmp_path):
        result = runner.invoke(app, ["graph", "beta"])
    assert result.exit_code == 0
    assert "alpha" in result.stdout


# ---------------------------------------------------------------------------
# --show-duplicates tests
# ---------------------------------------------------------------------------

def _make_config(source_path: Path) -> object:
    """Build a minimal CorpusConfig pointing at *source_path*."""
    from corpus_analyzer.config.schema import CorpusConfig, EmbeddingConfig, SourceConfig

    return CorpusConfig(
        embedding=EmbeddingConfig(model="nomic-embed-text", host="http://localhost:11434"),
        sources=[SourceConfig(name="test-source", path=str(source_path), extensions=[".md"])],
    )


def test_show_duplicates_exits_cleanly_with_no_collisions(tmp_path: Path) -> None:
    """corpus graph --show-duplicates exits 0 and says no duplicates when registry is clean."""
    from corpus_analyzer.graph.registry import SlugRegistry

    empty_registry = SlugRegistry({}, {})
    config = _make_config(tmp_path / "src")
    (tmp_path / "graph.sqlite")  # not needed — command must not require it for this flag

    with (
        patch("corpus_analyzer.cli.load_config", return_value=config),
        patch("corpus_analyzer.cli.SlugRegistry") as mock_registry_cls,
        patch("corpus_analyzer.cli.DATA_DIR", tmp_path),
    ):
        mock_registry_cls.build.return_value = empty_registry
        result = runner.invoke(app, ["graph", "--show-duplicates"])

    assert result.exit_code == 0, result.output
    assert "no duplicate" in result.stdout.lower() or "0 duplicate" in result.stdout.lower()


def test_show_duplicates_lists_all_collisions(tmp_path: Path) -> None:
    """corpus graph --show-duplicates prints every duplicate slug and its candidate paths."""
    from corpus_analyzer.graph.registry import SlugRegistry

    dup_registry = SlugRegistry(
        {
            "git": Path("/source1/git/SKILL.md"),
            "brainstorm": Path("/source1/brainstorm/SKILL.md"),
        },
        {
            "git": [Path("/source1/git/SKILL.md"), Path("/source2/git/SKILL.md")],
            "brainstorm": [
                Path("/source1/brainstorm/SKILL.md"),
                Path("/source2/brainstorm/SKILL.md"),
            ],
        },
    )
    config = _make_config(tmp_path / "src")

    with (
        patch("corpus_analyzer.cli.load_config", return_value=config),
        patch("corpus_analyzer.cli.SlugRegistry") as mock_registry_cls,
        patch("corpus_analyzer.cli.DATA_DIR", tmp_path),
    ):
        mock_registry_cls.build.return_value = dup_registry
        result = runner.invoke(app, ["graph", "--show-duplicates"])

    assert result.exit_code == 0, result.output
    assert "git" in result.stdout
    assert "brainstorm" in result.stdout
    # Each candidate path should appear
    assert "source1" in result.stdout
    assert "source2" in result.stdout


def test_show_duplicates_shown_in_help(tmp_path: Path) -> None:
    """corpus graph --help lists the --show-duplicates option."""
    result = runner.invoke(app, ["graph", "--help"])
    assert result.exit_code == 0
    assert "--show-duplicates" in result.stdout


def test_graph_no_slug_without_show_duplicates_errors(tmp_path: Path) -> None:
    """corpus graph with no slug and no --show-duplicates should exit non-zero."""
    graph_db = tmp_path / "graph.sqlite"
    from corpus_analyzer.graph.store import GraphStore

    GraphStore(graph_db)
    with patch("corpus_analyzer.cli.DATA_DIR", tmp_path):
        result = runner.invoke(app, ["graph"])
    assert result.exit_code != 0

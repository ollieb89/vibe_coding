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

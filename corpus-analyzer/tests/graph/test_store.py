"""Tests for GraphStore SQLite adjacency table."""
from __future__ import annotations

from pathlib import Path

from corpus_analyzer.graph.store import GraphStore


def test_write_and_read_edge(tmp_path: Path) -> None:
    store = GraphStore(tmp_path / "graph.sqlite")
    store.write_edges("/skills/a/SKILL.md", [("/skills/b/SKILL.md", True, "related_skill")])
    edges = store.edges_from("/skills/a/SKILL.md")
    assert len(edges) == 1
    assert edges[0]["target_path"] == "/skills/b/SKILL.md"
    assert edges[0]["resolved"] is True


def test_edges_to_returns_upstream(tmp_path: Path) -> None:
    store = GraphStore(tmp_path / "graph.sqlite")
    store.write_edges("/a.md", [("/b.md", True, "related_skill")])
    upstream = store.edges_to("/b.md")
    assert len(upstream) == 1
    assert upstream[0]["source_path"] == "/a.md"


def test_write_edges_is_idempotent(tmp_path: Path) -> None:
    store = GraphStore(tmp_path / "graph.sqlite")
    store.write_edges("/a.md", [("/b.md", True, "related_skill")])
    store.write_edges("/a.md", [("/b.md", True, "related_skill")])
    assert len(store.edges_from("/a.md")) == 1


def test_clear_edges_for_source(tmp_path: Path) -> None:
    store = GraphStore(tmp_path / "graph.sqlite")
    store.write_edges(
        "/a.md", [("/b.md", True, "related_skill"), ("/c.md", False, "related_skill")]
    )
    store.clear_edges_for("/a.md")
    assert store.edges_from("/a.md") == []


def test_unresolved_edge_stores_slug(tmp_path: Path) -> None:
    store = GraphStore(tmp_path / "graph.sqlite")
    store.write_edges("/a.md", [("unknown-slug", False, "related_skill")])
    edges = store.edges_from("/a.md")
    assert edges[0]["target_path"] == "unknown-slug"
    assert edges[0]["resolved"] is False

"""Tests for CorpusSearch hybrid search engine.

Tests cover: hybrid search returns results, RRF fusion, filters by source/type/construct,
snippet extraction integration, construct_type stored per chunk, summary in results,
end-to-end search, all filter flags, and status command.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import lancedb  # type: ignore[import-untyped]
import pytest

from corpus_analyzer.search.engine import CorpusSearch
from corpus_analyzer.store.schema import ChunkRecord, ensure_schema_v2


class MockEmbedder:
    def __init__(self, model: str = "nomic-embed-text") -> None:
        self.model = model

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 768 for _ in texts]


@pytest.fixture
def seeded_table(tmp_path: Path):
    db = lancedb.connect(str(tmp_path / "index"))
    table = db.create_table("chunks", schema=ChunkRecord, mode="overwrite")
    ensure_schema_v2(table)

    now = datetime.now(UTC).isoformat()
    rows: list[dict[str, object]] = [
        {
            "chunk_id": "c1",
            "file_path": "/repo/skills/foo.md",
            "source_name": "test-src",
            "text": "This is a skill about hybrid search and LanceDB.",
            "vector": [0.1] * 768,
            "start_line": 1,
            "end_line": 10,
            "file_type": ".md",
            "content_hash": "h1",
            "embedding_model": "nomic-embed-text",
            "indexed_at": now,
            "construct_type": "skill",
            "summary": "Hybrid search skill summary.",
        },
        {
            "chunk_id": "c2",
            "file_path": "/repo/workflows/bar.md",
            "source_name": "test-src",
            "text": "Workflow steps for indexing and search.",
            "vector": [0.2] * 768,
            "start_line": 1,
            "end_line": 8,
            "file_type": ".md",
            "content_hash": "h2",
            "embedding_model": "nomic-embed-text",
            "indexed_at": now,
            "construct_type": "workflow",
            "summary": None,
        },
        {
            "chunk_id": "c3",
            "file_path": "/repo/src/app.py",
            "source_name": "other-src",
            "text": "Python code for embedding and table search.",
            "vector": [0.3] * 768,
            "start_line": 1,
            "end_line": 20,
            "file_type": ".py",
            "content_hash": "h3",
            "embedding_model": "nomic-embed-text",
            "indexed_at": now,
            "construct_type": "code",
            "summary": "Code summary.",
        },
        {
            "chunk_id": "c4",
            "file_path": "/repo/docs/readme.md",
            "source_name": "other-src",
            "text": "Documentation about something else.",
            "vector": [0.4] * 768,
            "start_line": 1,
            "end_line": 5,
            "file_type": ".md",
            "content_hash": "h4",
            "embedding_model": "nomic-embed-text",
            "indexed_at": now,
            "construct_type": None,
            "summary": None,
        },
    ]
    table.add(rows)
    table.create_fts_index("text", replace=True)
    return table


@pytest.fixture
def search(seeded_table):
    return CorpusSearch(seeded_table, MockEmbedder())


def test_hybrid_search_returns_results(search: CorpusSearch) -> None:
    """SEARCH-01: hybrid_search() returns a non-empty list for a matching query."""
    results = search.hybrid_search("skill")
    assert isinstance(results, list)
    assert len(results) > 0


def test_hybrid_uses_rrf(search: CorpusSearch) -> None:
    """SEARCH-02: hybrid_search() uses RRFReranker (_relevance_score present in results)."""
    results = search.hybrid_search("search")
    assert results
    assert all("_relevance_score" in r for r in results)


def test_filter_by_source(search: CorpusSearch) -> None:
    """SEARCH-03: source filter limits results to chunks with matching source_name."""
    results = search.hybrid_search("search", source="test-src")
    assert results
    assert {r["source_name"] for r in results} == {"test-src"}


def test_filter_by_file_type(search: CorpusSearch) -> None:
    """SEARCH-04: file_type filter limits results to chunks with matching file_type."""
    results = search.hybrid_search("search", file_type=".py")
    assert results
    assert {r["file_type"] for r in results} == {".py"}


def test_construct_type_stored(search: CorpusSearch) -> None:
    """CLASS-02: construct_type field is present in search results."""
    results = search.hybrid_search("search")
    assert results
    assert all("construct_type" in r for r in results)
    assert any(r.get("construct_type") is not None for r in results)


def test_filter_by_construct(search: CorpusSearch) -> None:
    """CLASS-03: construct filter limits results to chunks with matching construct_type."""
    results = search.hybrid_search("search", construct_type="skill")
    assert results
    assert {r["construct_type"] for r in results} == {"skill"}


def test_summary_in_results(search: CorpusSearch) -> None:
    """SUMM-02: summary field is present and non-empty in search results for indexed file."""
    results = search.hybrid_search("search")
    assert results
    assert any(isinstance(r.get("summary"), str) and r["summary"] for r in results)


def test_search_end_to_end(search: CorpusSearch) -> None:
    """CLI-02: hybrid_search() returns list of dicts with file_path, text, _relevance_score."""
    results = search.hybrid_search("search", limit=10)
    assert results
    r0 = results[0]
    assert "file_path" in r0
    assert "text" in r0
    assert "_relevance_score" in r0


def test_all_filters(search: CorpusSearch) -> None:
    """CLI-03: source + file_type + construct filters chain as AND predicates."""
    results = search.hybrid_search(
        "search", source="test-src", file_type=".md", construct_type="skill"
    )
    assert results
    assert {r["source_name"] for r in results} == {"test-src"}
    assert {r["file_type"] for r in results} == {".md"}
    assert {r["construct_type"] for r in results} == {"skill"}


def test_status_returns_stats(seeded_table) -> None:
    """CLI-04: status() returns dict with files, chunks, last_indexed, model keys."""
    search = CorpusSearch(seeded_table, MockEmbedder())
    status = search.status(embedding_model="nomic-embed-text")
    assert set(status.keys()) == {"files", "chunks", "last_indexed", "model"}
    assert status["files"] > 0
    assert status["chunks"] > 0
    assert status["last_indexed"] != "never"
    assert status["model"] == "nomic-embed-text"


def test_status_empty_table(tmp_path: Path) -> None:
    embedder = MockEmbedder()
    db = lancedb.connect(str(tmp_path / "empty"))
    table = db.create_table("chunks", schema=ChunkRecord, mode="overwrite")
    ensure_schema_v2(table)
    search = CorpusSearch(table, embedder)
    status = search.status(embedding_model=embedder.model)
    assert status == {
        "files": 0,
        "chunks": 0,
        "last_indexed": "never",
        "model": embedder.model,
    }


def test_zero_results_no_crash(search: CorpusSearch) -> None:
    """SEARCH-01: hybrid_search() with no matching query returns empty list (not error)."""
    results = search.hybrid_search("zzzznosuchthing")
    assert results == []


def test_rejects_unsafe_filter_value(search: CorpusSearch) -> None:
    with pytest.raises(ValueError):
        search.hybrid_search("search", source="bad value")

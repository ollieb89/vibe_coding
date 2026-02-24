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

from corpus_analyzer.search.engine import CONSTRUCT_PRIORITY, RRF_SCORE_CEILING, CorpusSearch
from corpus_analyzer.store.schema import ChunkRecord, ensure_schema_v2, ensure_schema_v3


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
            "chunk_name": "",
            "chunk_text": "",
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
            "chunk_name": "",
            "chunk_text": "",
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
            "chunk_name": "",
            "chunk_text": "",
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
            "chunk_name": "",
            "chunk_text": "",
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


# --- Sort tests ---

@pytest.fixture
def sortable_table(tmp_path: Path):
    """Table seeded with three rows of different construct types and confidence scores."""
    db = lancedb.connect(str(tmp_path / "sort_idx"))
    table = db.create_table("chunks", schema=ChunkRecord, mode="overwrite")
    ensure_schema_v2(table)
    ensure_schema_v3(table)

    rows: list[dict[str, object]] = [
        {
            "chunk_id": "r1",
            "file_path": "/z/skill.md",
            "source_name": "src",
            "text": "search content skill text",
            "vector": [0.1] * 768,
            "start_line": 1, "end_line": 2,
            "file_type": ".md",
            "content_hash": "h1",
            "embedding_model": "nomic-embed-text",
            "indexed_at": "2024-01-01T00:00:00",
            "construct_type": "skill",
            "classification_confidence": 0.6,
            "summary": None,
            "chunk_name": "",
            "chunk_text": "",
        },
        {
            "chunk_id": "r2",
            "file_path": "/a/agent.md",
            "source_name": "src",
            "text": "search content agent text",
            "vector": [0.2] * 768,
            "start_line": 1, "end_line": 2,
            "file_type": ".md",
            "content_hash": "h2",
            "embedding_model": "nomic-embed-text",
            "indexed_at": "2024-01-03T00:00:00",
            "construct_type": "agent",
            "classification_confidence": 0.9,
            "summary": None,
            "chunk_name": "",
            "chunk_text": "",
        },
        {
            "chunk_id": "r3",
            "file_path": "/m/rule.md",
            "source_name": "src",
            "text": "search content rule text",
            "vector": [0.3] * 768,
            "start_line": 1, "end_line": 2,
            "file_type": ".md",
            "content_hash": "h3",
            "embedding_model": "nomic-embed-text",
            "indexed_at": "2024-01-02T00:00:00",
            "construct_type": "rule",
            "classification_confidence": 0.7,
            "summary": None,
            "chunk_name": "",
            "chunk_text": "",
        },
    ]
    table.add(rows)
    table.create_fts_index("text", replace=True)
    return table


@pytest.fixture
def sortable_search(sortable_table):
    return CorpusSearch(sortable_table, MockEmbedder())


class TestHybridSearchSort:
    """Tests for the sort_by parameter of hybrid_search()."""

    def test_sort_by_construct_uses_priority_order(
        self, sortable_search: CorpusSearch
    ) -> None:
        """sort_by='construct' orders results by CONSTRUCT_PRIORITY.

        Order: agent before skill before rule.
        """
        results = sortable_search.hybrid_search("search content", sort_by="construct")
        construct_types = [r["construct_type"] for r in results if r.get("construct_type")]
        priorities = [CONSTRUCT_PRIORITY.get(ct, 99) for ct in construct_types]
        assert priorities == sorted(priorities)

    def test_sort_by_confidence_descending(self, sortable_search: CorpusSearch) -> None:
        """sort_by='confidence' orders results highest confidence first."""
        results = sortable_search.hybrid_search("search content", sort_by="confidence")
        confidences = [r.get("classification_confidence") or 0.0 for r in results]
        assert confidences == sorted(confidences, reverse=True)

    def test_sort_by_date_descending(self, sortable_search: CorpusSearch) -> None:
        """sort_by='date' orders results most recently indexed first."""
        results = sortable_search.hybrid_search("search content", sort_by="date")
        dates = [r["indexed_at"] for r in results]
        assert dates == sorted(dates, reverse=True)

    def test_sort_by_path_ascending(self, sortable_search: CorpusSearch) -> None:
        """sort_by='path' orders results alphabetically by file_path."""
        results = sortable_search.hybrid_search("search content", sort_by="path")
        paths = [r["file_path"] for r in results]
        assert paths == sorted(paths)

    def test_invalid_sort_raises_value_error(self, sortable_search: CorpusSearch) -> None:
        """Unknown sort_by value raises ValueError."""
        with pytest.raises(ValueError, match="sort_by"):
            sortable_search.hybrid_search("search content", sort_by="invalid")

    def test_sort_by_construct_uses_confidence_as_tiebreaker(self, tmp_path: Path) -> None:
        """sort_by='construct' uses confidence descending as secondary key for equal-priority rows.

        Equal-priority construct types are broken by confidence descending.
        """
        from corpus_analyzer.store.schema import ensure_schema_v3

        db = lancedb.connect(str(tmp_path / "tie_idx"))
        table = db.create_table("chunks", schema=ChunkRecord, mode="overwrite")
        ensure_schema_v2(table)
        ensure_schema_v3(table)

        now = datetime.now(UTC).isoformat()
        rows: list[dict[str, object]] = [
            {
                "chunk_id": "t1",
                "file_path": "/low/agent.md",
                "source_name": "src",
                "text": "search agent low confidence",
                "vector": [0.1] * 768,
                "start_line": 1, "end_line": 2,
                "file_type": ".md",
                "content_hash": "h1",
                "embedding_model": "nomic-embed-text",
                "indexed_at": now,
                "construct_type": "agent",
                "classification_confidence": 0.3,
                "summary": None,
                "chunk_name": "",
                "chunk_text": "",
            },
            {
                "chunk_id": "t2",
                "file_path": "/high/agent.md",
                "source_name": "src",
                "text": "search agent high confidence",
                "vector": [0.2] * 768,
                "start_line": 1, "end_line": 2,
                "file_type": ".md",
                "content_hash": "h2",
                "embedding_model": "nomic-embed-text",
                "indexed_at": now,
                "construct_type": "agent",
                "classification_confidence": 0.9,
                "summary": None,
                "chunk_name": "",
                "chunk_text": "",
            },
        ]
        table.add(rows)
        table.create_fts_index("text", replace=True)

        search = CorpusSearch(table, MockEmbedder())
        results = search.hybrid_search("search agent", sort_by="construct")
        agents = [r for r in results if r.get("construct_type") == "agent"]
        assert len(agents) == 2
        confidences = [float(r.get("classification_confidence") or 0.0) for r in agents]
        assert confidences == sorted(confidences, reverse=True), (
            "Within the same construct type, higher confidence should rank first"
        )


def test_min_score_zero_is_noop(search: CorpusSearch) -> None:
    """FILT-01: min_score=0.0 returns identical results to no filter."""
    without_filter = search.hybrid_search("search")
    with_zero = search.hybrid_search("search", min_score=0.0)
    assert with_zero == without_filter


def test_min_score_above_max_returns_empty(search: CorpusSearch) -> None:
    """FILT-01: min_score=99.0 exceeds any real RRF score — must return []."""
    results = search.hybrid_search("search", min_score=99.0)
    assert results == []


def test_min_score_parameter_accepted(search: CorpusSearch) -> None:
    """FILT-01: hybrid_search() must accept min_score without TypeError."""
    # Raises TypeError if parameter does not exist
    _ = search.hybrid_search("search", min_score=0.0)


def test_min_score_filters_below_threshold(search: CorpusSearch) -> None:
    """FILT-01: results passing the filter all have _relevance_score >= threshold."""
    baseline = search.hybrid_search("search")
    if not baseline:
        pytest.skip("no results in seeded table for this query")
    max_score = max(float(r.get("_relevance_score", 0.0)) for r in baseline)
    # Threshold == max_score keeps at least one result (inclusive >=)
    results = search.hybrid_search("search", min_score=max_score)
    assert len(results) >= 1
    assert all(float(r.get("_relevance_score", 0.0)) >= max_score for r in results)


# --- Name filter tests ---

@pytest.fixture
def named_table(tmp_path: Path):
    """Table seeded with rows that have distinct chunk_names for name-filter tests."""
    db = lancedb.connect(str(tmp_path / "named_idx"))
    table = db.create_table("chunks", schema=ChunkRecord, mode="overwrite")
    ensure_schema_v2(table)
    now = datetime.now(UTC).isoformat()
    rows: list[dict[str, object]] = [
        {
            "chunk_id": "n1",
            "file_path": "/repo/src/search.py",
            "source_name": "src",
            "text": "def search foo bar baz",
            "vector": [0.1] * 768,
            "start_line": 1, "end_line": 5,
            "file_type": ".py",
            "content_hash": "h1",
            "embedding_model": "nomic-embed-text",
            "indexed_at": now,
            "construct_type": "function",
            "summary": None,
            "chunk_name": "SearchEngine.search",
            "chunk_text": "def search(self): ...",
        },
        {
            "chunk_id": "n2",
            "file_path": "/repo/src/index.py",
            "source_name": "src",
            "text": "def index foo bar baz",
            "vector": [0.2] * 768,
            "start_line": 10, "end_line": 20,
            "file_type": ".py",
            "content_hash": "h2",
            "embedding_model": "nomic-embed-text",
            "indexed_at": now,
            "construct_type": "function",
            "summary": None,
            "chunk_name": "SearchEngine.index",
            "chunk_text": "def index(self): ...",
        },
        {
            "chunk_id": "n3",
            "file_path": "/repo/src/util.py",
            "source_name": "src",
            "text": "def helper foo bar baz",
            "vector": [0.3] * 768,
            "start_line": 1, "end_line": 5,
            "file_type": ".py",
            "content_hash": "h3",
            "embedding_model": "nomic-embed-text",
            "indexed_at": now,
            "construct_type": "function",
            "summary": None,
            "chunk_name": "HelperClass.run",
            "chunk_text": "def run(self): ...",
        },
    ]
    table.add(rows)
    table.create_fts_index("text", replace=True)
    return table


class TestHybridSearchNameFilter:
    """NAME-01/NAME-03: Tests for the name= filter and empty-query name-only search."""

    def test_name_filter_returns_matching_chunks(self, named_table) -> None:
        """NAME-01: name='search' returns only chunks whose chunk_name contains 'search' (ci)."""
        search = CorpusSearch(named_table, MockEmbedder())
        results = search.hybrid_search("foo", name="search")
        assert results
        assert all("search" in str(r.get("chunk_name", "")).lower() for r in results)

    def test_name_filter_case_insensitive(self, named_table) -> None:
        """NAME-01: name filter is case-insensitive ('SEARCH' matches 'SearchEngine.search')."""
        search = CorpusSearch(named_table, MockEmbedder())
        results = search.hybrid_search("foo", name="SEARCH")
        assert results
        assert all("search" in str(r.get("chunk_name", "")).lower() for r in results)

    def test_name_filter_dot_notation(self, named_table) -> None:
        """NAME-01: name='SearchEngine.search' narrows to that specific method chunk."""
        search = CorpusSearch(named_table, MockEmbedder())
        results = search.hybrid_search("foo", name="SearchEngine.search")
        assert len(results) == 1
        assert results[0]["chunk_name"] == "SearchEngine.search"

    def test_name_filter_no_match_returns_empty(self, named_table) -> None:
        """NAME-01: name filter with no matching chunk_name returns empty list."""
        search = CorpusSearch(named_table, MockEmbedder())
        results = search.hybrid_search("foo", name="NonExistentClass.method")
        assert results == []

    def test_name_none_is_noop(self, named_table) -> None:
        """NAME-01: name=None behaves identically to omitting the parameter."""
        search = CorpusSearch(named_table, MockEmbedder())
        without_name = search.hybrid_search("foo")
        with_none = search.hybrid_search("foo", name=None)
        assert with_none == without_name

    def test_empty_query_with_name_skips_text_filter(self, named_table) -> None:
        """NAME-03: empty query + name filter returns name-matching chunks without text match."""
        search = CorpusSearch(named_table, MockEmbedder())
        results = search.hybrid_search("", name="helper")
        assert results
        assert all("helper" in str(r.get("chunk_name", "")).lower() for r in results)

    def test_name_composes_with_construct_filter(self, named_table) -> None:
        """NAME-01: name filter composes with construct_type filter as AND predicate."""
        search = CorpusSearch(named_table, MockEmbedder())
        results = search.hybrid_search("foo", name="search", construct_type="function")
        assert results
        assert all("search" in str(r.get("chunk_name", "")).lower() for r in results)
        assert all(r.get("construct_type") == "function" for r in results)


class TestScoreNormalisation:
    """NORM-01: Scores returned by hybrid_search() must be in [0.0, 1.0] range."""

    def test_scores_normalised_to_unit_range(self, search: CorpusSearch) -> None:
        """All _relevance_score values in results are in [0.0, 1.0]."""
        results = search.hybrid_search("search")
        assert results, "Need results to test normalisation"
        for r in results:
            score = float(r["_relevance_score"])
            assert 0.0 <= score <= 1.0, f"Score {score} is outside [0, 1]"

    def test_score_ceiling_constant_matches_rrf_k(self) -> None:
        """RRF_SCORE_CEILING equals 1/K + 1/K for the two-list fusion with K=60."""
        assert pytest.approx(1.0 / 60 + 1.0 / 60) == RRF_SCORE_CEILING

    def test_empty_query_scan_scores_zero(self, named_table) -> None:
        """Empty-query scan path (no RRF) returns _relevance_score 0.0 per row."""
        search_obj = CorpusSearch(named_table, MockEmbedder())
        results = search_obj.hybrid_search("")
        for r in results:
            assert float(r.get("_relevance_score", 0.0)) == pytest.approx(0.0)

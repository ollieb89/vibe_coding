"""Tests for corpus_analyzer.ingest.indexer — CorpusIndex.

Uses real LanceDB in tmp_path with mocked OllamaEmbedder.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from corpus_analyzer.config.schema import SourceConfig
from corpus_analyzer.ingest.indexer import (  # type: ignore[attr-defined]
    CorpusIndex,
    IndexResult,
    SourceStatus,
)
from corpus_analyzer.search.classifier import ClassificationResult


class MockEmbedder:
    """Mock OllamaEmbedder for testing."""

    def __init__(self, model: str = "nomic-embed-text"):
        self.model = model
        self.host = "http://localhost:11434"

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return fake 768-dim vectors."""
        return [[0.1] * 768 for _ in texts]


def test_indexer_extension_filtering_and_removal(tmp_path: Path):
    """Extension changes correctly filter files and remove stale chunks."""
    from corpus_analyzer.config.schema import SourceConfig

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "file1.md").write_text("Markdown content")
    (source_dir / "file2.py").write_text("print('Python content')")

    embedder = MockEmbedder()
    index = CorpusIndex.open(tmp_path, embedder)

    # First index: allow both
    source1 = SourceConfig(name="test", path=str(source_dir), extensions=[".md", ".py"])
    res1 = index.index_source(source1)

    assert res1.files_indexed == 2
    assert getattr(res1, "files_removed", 0) == 0

    # Second index: allow only .md
    source2 = SourceConfig(name="test", path=str(source_dir), extensions=[".md"])
    res2 = index.index_source(source2)

    assert res2.files_indexed == 0  # .md is skipped because it's unchanged
    assert getattr(res2, "files_removed", 0) == 1  # .py was removed


class TestCorpusIndexOpen:
    """Tests for CorpusIndex.open() classmethod."""

    def test_creates_table_when_not_exists(self, tmp_path) -> None:
        """open() creates 'chunks' table when it doesn't exist."""
        embedder = MockEmbedder()

        index = CorpusIndex.open(tmp_path, embedder)

        assert index.table is not None
        assert index._embedder.model == "nomic-embed-text"
        cols = {field.name for field in index.table.schema}
        assert "construct_type" in cols
        assert "summary" in cols

    def test_opens_existing_table(self, tmp_path) -> None:
        """open() opens existing table without error."""
        embedder = MockEmbedder()

        # First call creates table
        index1 = CorpusIndex.open(tmp_path, embedder)
        assert index1.table is not None

        # Second call opens existing
        index2 = CorpusIndex.open(tmp_path, embedder)
        assert index2.table is not None

    def test_raises_on_model_mismatch(self, tmp_path) -> None:
        """open() raises RuntimeError when stored model differs."""
        # Create with first model
        embedder1 = MockEmbedder(model="model-a")
        index1 = CorpusIndex.open(tmp_path, embedder1)

        # Insert a dummy record to set the model
        index1.table.add([{
            "chunk_id": "test-1",
            "file_path": "/test.txt",
            "source_name": "test",
            "text": "test",
            "vector": [0.1] * 768,
            "start_line": 1,
            "end_line": 1,
            "file_type": ".txt",
            "content_hash": "abc",
            "embedding_model": "model-a",
            "indexed_at": "2024-01-01T00:00:00Z",
            "chunk_name": "",
            "chunk_text": "",
        }])

        # Try to open with different model
        embedder2 = MockEmbedder(model="model-b")
        with pytest.raises(RuntimeError) as exc_info:
            CorpusIndex.open(tmp_path, embedder2)

        assert "model mismatch" in str(exc_info.value).lower()
        assert "model-a" in str(exc_info.value)
        assert "model-b" in str(exc_info.value)


class TestCorpusIndexSource:
    """Tests for CorpusIndex.index_source() method."""

    @pytest.fixture
    def index(self, tmp_path):
        """Create a CorpusIndex fixture."""
        embedder = MockEmbedder()
        return CorpusIndex.open(tmp_path, embedder)

    def test_indexes_files_and_returns_counts(self, index, tmp_path) -> None:
        """index_source() indexes files and returns correct counts."""
        # Create source directory with files
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.md").write_text("# Heading\nContent here.")
        (source_dir / "file2.md").write_text("## Another\nMore content.")

        source = SourceConfig(name="my-source", path=str(source_dir))

        result = index.index_source(source)

        assert isinstance(result, IndexResult)
        assert result.source_name == "my-source"
        assert result.files_indexed == 2
        assert result.chunks_written > 0
        assert result.files_skipped == 0
        assert result.elapsed > 0

    def test_skips_unchanged_files_on_second_run(self, index, tmp_path) -> None:
        """index_source() skips unchanged files on second run."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file.md").write_text("# Heading\nContent here.")

        source = SourceConfig(name="my-source", path=str(source_dir))

        # First run - indexes file
        result1 = index.index_source(source)
        assert result1.files_indexed == 1
        assert result1.files_skipped == 0

        # Second run - skips unchanged file
        result2 = index.index_source(source)
        assert result2.files_indexed == 0
        assert result2.files_skipped == 1

    def test_reindexes_changed_files(self, index, tmp_path) -> None:
        """index_source() reindexes files that have changed."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        file_path = source_dir / "file.md"
        file_path.write_text("# Original\nOriginal content.")

        source = SourceConfig(name="my-source", path=str(source_dir))

        # First run
        result1 = index.index_source(source)
        assert result1.files_indexed == 1

        # Change file
        file_path.write_text("# Changed\nNew content here.")

        # Second run - should reindex
        result2 = index.index_source(source)
        assert result2.files_indexed == 1
        assert result2.files_skipped == 0

    def test_removes_stale_chunks_when_file_deleted(self, index, tmp_path) -> None:
        """index_source() removes chunks for deleted files."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        file1 = source_dir / "file1.md"
        file2 = source_dir / "file2.md"
        file1.write_text("# File 1\nContent 1.")
        file2.write_text("# File 2\nContent 2.")

        source = SourceConfig(name="my-source", path=str(source_dir))

        # First run - index both files
        result1 = index.index_source(source)
        assert result1.files_indexed == 2

        # Get chunk count after first run
        chunks_after_first = len(index.table.to_pandas())

        # Delete one file
        file1.unlink()

        # Second run - should remove stale chunks
        result2 = index.index_source(source)
        assert result2.files_indexed == 0  # file2 unchanged (skipped)
        assert result2.files_skipped == 1
        # Verify chunks for deleted file were removed
        chunks_after_second = len(index.table.to_pandas())
        assert chunks_after_second < chunks_after_first

    def test_does_not_delete_chunks_from_other_sources(self, index, tmp_path) -> None:
        """index_source() does not affect chunks from other sources."""
        # Create two source directories
        source1_dir = tmp_path / "source1"
        source2_dir = tmp_path / "source2"
        source1_dir.mkdir()
        source2_dir.mkdir()

        (source1_dir / "file.md").write_text("# Source 1\nContent 1.")
        (source2_dir / "file.md").write_text("# Source 2\nContent 2.")

        source1 = SourceConfig(name="source-1", path=str(source1_dir))
        source2 = SourceConfig(name="source-2", path=str(source2_dir))

        # Index both sources
        index.index_source(source1)
        index.index_source(source2)

        # Delete file from source1
        (source1_dir / "file.md").unlink()

        # Reindex source1 (this should only delete source1 chunks)
        index.index_source(source1)

        # Verify source2 chunks still exist
        chunks = index.table.to_pandas()
        source2_chunks = chunks[chunks["source_name"] == "source-2"]
        assert len(source2_chunks) > 0

    def test_handles_empty_source(self, index, tmp_path) -> None:
        """index_source() handles empty source directory."""
        source_dir = tmp_path / "empty_source"
        source_dir.mkdir()

        source = SourceConfig(name="empty", path=str(source_dir))

        result = index.index_source(source)

        assert result.files_indexed == 0
        assert result.files_skipped == 0
        assert result.chunks_written == 0

    def test_progress_callback_called(self, index, tmp_path) -> None:
        """index_source() calls progress_callback with file count."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.md").write_text("# A\nContent.")
        (source_dir / "file2.md").write_text("# B\nContent.")

        source = SourceConfig(name="my-source", path=str(source_dir))

        progress_calls = []

        def callback(n: int) -> None:
            progress_calls.append(n)

        index.index_source(source, progress_callback=callback)

        assert len(progress_calls) == 2  # Called for each file

    def test_respects_include_exclude_patterns(self, index, tmp_path) -> None:
        """index_source() respects source include/exclude patterns."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "include.md").write_text("# Include\nContent.")
        (source_dir / "exclude.txt").write_text("exclude")

        source = SourceConfig(
            name="my-source",
            path=str(source_dir),
            include=["*.md"],  # Only .md files
            exclude=[],
        )

        result = index.index_source(source)

        assert result.files_indexed == 1  # Only .md file


def test_get_existing_files_logs_warning_on_exception(tmp_path, caplog) -> None:
    import logging
    caplog.set_level(logging.WARNING)
    embedder = MockEmbedder()
    index = CorpusIndex.open(tmp_path, embedder)

    with patch.object(index._table, "search", side_effect=RuntimeError("db error")):
        index._get_existing_files("my-source")

    assert "my-source" in caplog.text


def test_delete_stale_chunks_logs_warning_on_exception(tmp_path, caplog) -> None:
    import logging
    caplog.set_level(logging.WARNING)
    embedder = MockEmbedder()
    index = CorpusIndex.open(tmp_path, embedder)

    with patch.object(index._table, "search", side_effect=RuntimeError("db error")):
        index._delete_stale_chunks("my-source", set())

    assert "my-source" in caplog.text


# --- Phase 2 extension tests ---


def test_index_adds_construct_type(tmp_path) -> None:
    """CLI-01: After index_source(), chunks have a non-None construct_type value."""
    embedder = MockEmbedder()
    index = CorpusIndex.open(tmp_path, embedder)

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "file.md").write_text("# Heading\nContent here.")

    source = SourceConfig(name="my-source", path=str(source_dir), summarize=True)

    with (
        patch(
            "corpus_analyzer.ingest.indexer.classify_file",
            return_value=ClassificationResult("skill", 0.6, "rule_based"),
        ) as mock_classify,
        patch(
            "corpus_analyzer.ingest.indexer.generate_summary",
            return_value="Summary text.",
        ) as mock_summary,
    ):
        index.index_source(source)

    df = index.table.to_pandas()
    assert len(df) > 0
    assert "construct_type" in df.columns
    assert "summary" in df.columns
    assert set(df["construct_type"].dropna().tolist()) == {"skill"}
    assert set(df["summary"].dropna().tolist()) == {"Summary text."}
    assert any(str(t).startswith("Summary text.\n\n") for t in df["text"].tolist())
    mock_classify.assert_called_once()
    mock_summary.assert_called_once()


def test_index_skips_summary_on_unchanged_file(tmp_path) -> None:
    """CLI-01: Second index_source() call on unchanged file does not re-generate summary."""
    embedder = MockEmbedder()
    index = CorpusIndex.open(tmp_path, embedder)

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "file.md").write_text("# Heading\nContent here.")

    source = SourceConfig(name="my-source", path=str(source_dir), summarize=True)

    with (
        patch(
            "corpus_analyzer.ingest.indexer.classify_file",
            return_value=ClassificationResult("skill", 0.6, "rule_based"),
        ),
        patch(
            "corpus_analyzer.ingest.indexer.generate_summary",
            return_value="Summary text.",
        ) as mock_summary,
    ):
        index.index_source(source)
        index.index_source(source)

    assert mock_summary.call_count == 1


def test_indexer_stores_frontmatter_classification(tmp_path: Path) -> None:
    """CLASS-04: Indexer stores classification_source and classification_confidence."""
    embedder = MockEmbedder()
    index = CorpusIndex.open(tmp_path, embedder)

    source_dir = tmp_path / "source"
    source_dir.mkdir()

    file_content = "---\ntype: skill\n---\n# My Skill\nContent."
    (source_dir / "skill.md").write_text(file_content)

    source = SourceConfig(
        name="my-source",
        path=str(source_dir),
        summarize=False,
    )

    index.index_source(source)

    df = index.table.to_pandas()
    assert len(df) > 0
    row = df.iloc[0]

    assert row["construct_type"] == "skill"
    assert row["classification_source"] == "frontmatter"
    assert abs(row["classification_confidence"] - 0.95) < 0.01


def test_index_rebuilds_fts_index(tmp_path) -> None:
    """CLI-01: index_source() rebuilds FTS index with replace=True after optimize."""
    embedder = MockEmbedder()
    index = CorpusIndex.open(tmp_path, embedder)

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "file.md").write_text("# Heading\nContent here.")

    source = SourceConfig(name="my-source", path=str(source_dir), summarize=False)

    with patch.object(type(index.table), "create_fts_index", autospec=True) as mock_fts:
        index.index_source(source)

    mock_fts.assert_called_once_with(index.table, "text", replace=True)


# --- Source-level change detection tests ---


class TestSourceLevelChangeDetection:
    """Source-level fast-path: skip expensive LanceDB ops when nothing has changed."""

    def test_clean_source_skips_lancedb_query_on_second_run(self, tmp_path: Path) -> None:
        """Second run on unchanged source never queries LanceDB (table.search not called)."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "a.md").write_text("# A\nContent A.")
        (source_dir / "b.md").write_text("# B\nContent B.")

        index = CorpusIndex.open(tmp_path, MockEmbedder())
        source = SourceConfig(name="my-source", path=str(source_dir))

        index.index_source(source)  # first run — writes manifest

        # Second run: table.search should never be called (source-level skip)
        with patch.object(index._table, "search") as mock_search:
            result2 = index.index_source(source)

        mock_search.assert_not_called()
        assert result2.files_indexed == 0
        assert result2.files_skipped == 2

    def test_clean_source_skips_optimize_on_second_run(self, tmp_path: Path) -> None:
        """Second run on unchanged source skips table.optimize() (no work done)."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "a.md").write_text("# A\nContent A.")

        index = CorpusIndex.open(tmp_path, MockEmbedder())
        source = SourceConfig(name="my-source", path=str(source_dir))

        index.index_source(source)

        with patch.object(index._table, "optimize") as mock_optimize:
            index.index_source(source)

        mock_optimize.assert_not_called()

    def test_modified_file_still_queries_lancedb(self, tmp_path: Path) -> None:
        """Modified file triggers full reindex path (table.search IS called)."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        file_path = source_dir / "a.md"
        file_path.write_text("# Original\nContent.")

        index = CorpusIndex.open(tmp_path, MockEmbedder())
        source = SourceConfig(name="my-source", path=str(source_dir))

        index.index_source(source)
        file_path.write_text("# Changed\nNew content.")

        with patch.object(index._table, "search", wraps=index._table.search) as mock_search:
            result2 = index.index_source(source)

        mock_search.assert_called()
        assert result2.files_indexed == 1

    def test_added_file_triggers_full_reindex(self, tmp_path: Path) -> None:
        """New file in source triggers full reindex (file count changed)."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "a.md").write_text("# A\nContent.")

        index = CorpusIndex.open(tmp_path, MockEmbedder())
        source = SourceConfig(name="my-source", path=str(source_dir))

        index.index_source(source)
        (source_dir / "b.md").write_text("# B\nNew file.")

        with patch.object(index._table, "search", wraps=index._table.search) as mock_search:
            result2 = index.index_source(source)

        mock_search.assert_called()
        assert result2.files_indexed >= 1

    def test_deleted_file_triggers_full_reindex(self, tmp_path: Path) -> None:
        """Deleted file triggers full reindex (file count changed)."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "a.md").write_text("# A\nContent A.")
        (source_dir / "b.md").write_text("# B\nContent B.")

        index = CorpusIndex.open(tmp_path, MockEmbedder())
        source = SourceConfig(name="my-source", path=str(source_dir))

        index.index_source(source)
        (source_dir / "b.md").unlink()

        with patch.object(index._table, "search", wraps=index._table.search) as mock_search:
            index.index_source(source)

        mock_search.assert_called()


# --- check_source_status tests ---


class TestCheckSourceStatus:
    """Tests for CorpusIndex.check_source_status() — public pre-index check."""

    @pytest.fixture
    def index(self, tmp_path: Path) -> CorpusIndex:
        """Create a CorpusIndex fixture."""
        return CorpusIndex.open(tmp_path, MockEmbedder())

    def test_new_source_needs_indexing(self, index: CorpusIndex, tmp_path: Path) -> None:
        """check_source_status() reports needs_indexing=True for a never-indexed source."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file.md").write_text("# Content")

        source = SourceConfig(name="new-source", path=str(source_dir))
        status = index.check_source_status(source)

        assert isinstance(status, SourceStatus)
        assert status.needs_indexing is True
        assert status.reason == "new source"
        assert status.last_indexed_at is None
        assert status.source_name == "new-source"

    def test_up_to_date_source_does_not_need_indexing(
        self, index: CorpusIndex, tmp_path: Path
    ) -> None:
        """check_source_status() reports needs_indexing=False when source is unchanged."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file.md").write_text("# Content")

        source = SourceConfig(name="my-source", path=str(source_dir))
        index.index_source(source)

        status = index.check_source_status(source)

        assert status.needs_indexing is False
        assert status.reason == "up to date"
        assert status.last_indexed_at is not None

    def test_modified_file_needs_indexing(self, index: CorpusIndex, tmp_path: Path) -> None:
        """check_source_status() reports needs_indexing=True when a file has been modified."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        file_path = source_dir / "file.md"
        file_path.write_text("# Original")

        source = SourceConfig(name="my-source", path=str(source_dir))
        index.index_source(source)

        # Modify the file so its mtime advances past last_indexed_at
        file_path.write_text("# Changed")

        status = index.check_source_status(source)

        assert status.needs_indexing is True
        assert status.last_indexed_at is not None

    def test_added_file_needs_indexing(self, index: CorpusIndex, tmp_path: Path) -> None:
        """check_source_status() reports needs_indexing=True when a file has been added."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file.md").write_text("# Original")

        source = SourceConfig(name="my-source", path=str(source_dir))
        index.index_source(source)

        (source_dir / "new_file.md").write_text("# New file")

        status = index.check_source_status(source)

        assert status.needs_indexing is True

    def test_source_status_includes_file_count(
        self, index: CorpusIndex, tmp_path: Path
    ) -> None:
        """check_source_status() includes the file_count recorded at last index."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.md").write_text("# A")
        (source_dir / "file2.md").write_text("# B")

        source = SourceConfig(name="my-source", path=str(source_dir))
        index.index_source(source)

        status = index.check_source_status(source)

        assert status.file_count == 2

    def test_new_source_has_zero_file_count(self, index: CorpusIndex, tmp_path: Path) -> None:
        """check_source_status() reports file_count=0 for a never-indexed source."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file.md").write_text("# Content")

        source = SourceConfig(name="never-indexed", path=str(source_dir))
        status = index.check_source_status(source)

        assert status.file_count == 0

    def test_check_does_not_modify_manifest(
        self, index: CorpusIndex, tmp_path: Path
    ) -> None:
        """check_source_status() is read-only — does not update the manifest."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file.md").write_text("# Content")

        source = SourceConfig(name="my-source", path=str(source_dir))
        # Never indexed — manifest has no entry for this source
        index.check_source_status(source)

        # Manifest should still be empty (check is side-effect-free)
        manifest = index._load_manifest()
        assert "my-source" not in manifest


def test_index_writes_relationship_edges(tmp_path: Path) -> None:
    """Indexer writes graph edges when ## Related Skills section is present."""
    from corpus_analyzer.graph.registry import SlugRegistry
    from corpus_analyzer.graph.store import GraphStore

    embedder = MockEmbedder()
    index = CorpusIndex.open(tmp_path, embedder)

    source_dir = tmp_path / "source"
    source_dir.mkdir()

    # alpha.md references beta via ## Related Skills
    alpha_path = source_dir / "alpha.md"
    alpha_path.write_text("# Alpha\n\n## Related Skills\n\n- `beta`\n")

    # beta.md is a plain file (the target)
    beta_path = source_dir / "beta.md"
    beta_path.write_text("# Beta\nPlain content.\n")

    source = SourceConfig(name="my-source", path=str(source_dir), summarize=False)

    # Build a SlugRegistry that knows about the beta directory.
    # beta.md is a top-level file so we register it directly via a mapping.
    registry = SlugRegistry({"beta": beta_path.resolve()})

    graph_db_path = tmp_path / "graph.db"
    graph_store = GraphStore(graph_db_path)

    with (
        patch(
            "corpus_analyzer.ingest.indexer.classify_file",
            return_value=ClassificationResult("skill", 0.6, "rule_based"),
        ),
        patch(
            "corpus_analyzer.ingest.indexer.generate_summary",
            return_value="",
        ),
    ):
        index.index_source(source, graph_store=graph_store, registry=registry)

    edges = graph_store.edges_from(str(alpha_path.resolve()))
    assert len(edges) == 1, f"Expected 1 edge, got {len(edges)}: {edges}"
    assert edges[0]["target_path"] == str(beta_path.resolve())
    assert edges[0]["resolved"] is True


def test_open_migrates_agent_config_to_agent(tmp_path: Path) -> None:
    """CorpusIndex.open() renames stored 'agent_config' rows to 'agent'."""
    embedder = MockEmbedder()
    index = CorpusIndex.open(tmp_path, embedder)

    # Manually insert a legacy agent_config row
    index.table.add([{
        "chunk_id": "legacy-1",
        "file_path": "/agents/old.md",
        "source_name": "test",
        "text": "old agent config",
        "vector": [0.1] * 768,
        "start_line": 1, "end_line": 1,
        "file_type": ".md",
        "content_hash": "abc",
        "embedding_model": "nomic-embed-text",
        "indexed_at": "2024-01-01T00:00:00",
        "construct_type": "agent_config",
        "chunk_name": "",
        "chunk_text": "",
    }])

    # Re-open triggers migration
    index2 = CorpusIndex.open(tmp_path, embedder)
    df = index2.table.to_pandas()
    row = df[df["chunk_id"] == "legacy-1"].iloc[0]
    assert row["construct_type"] == "agent"

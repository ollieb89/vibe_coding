"""Tests for corpus_analyzer.ingest.indexer — CorpusIndex.

Uses real LanceDB in tmp_path with mocked OllamaEmbedder.
"""

from unittest.mock import MagicMock, patch

import pytest

from corpus_analyzer.config.schema import SourceConfig
from corpus_analyzer.ingest.indexer import CorpusIndex, IndexResult  # type: ignore[attr-defined]


class MockEmbedder:
    """Mock OllamaEmbedder for testing."""

    def __init__(self, model: str = "nomic-embed-text"):
        self.model = model

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return fake 768-dim vectors."""
        return [[0.1] * 768 for _ in texts]


class TestCorpusIndexOpen:
    """Tests for CorpusIndex.open() classmethod."""

    def test_creates_table_when_not_exists(self, tmp_path) -> None:
        """open() creates 'chunks' table when it doesn't exist."""
        embedder = MockEmbedder()

        index = CorpusIndex.open(tmp_path, embedder)

        assert index.table is not None
        assert index._embedder.model == "nomic-embed-text"

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

        # Get total chunks
        total_chunks = len(index.table.to_pandas())

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

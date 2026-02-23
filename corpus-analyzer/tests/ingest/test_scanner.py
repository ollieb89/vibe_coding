"""Tests for corpus_analyzer.ingest.scanner — File scanning and change detection.

Follows RED-GREEN-REFACTOR TDD cycle.
All file operations use pytest tmp_path fixture.
"""

from pathlib import Path

import pytest

from corpus_analyzer.ingest.scanner import (
    file_content_hash,
    needs_reindex,
    walk_source,
)


# ---------------------------------------------------------------------------
# file_content_hash tests
# ---------------------------------------------------------------------------


class TestFileContentHash:
    """Tests for file_content_hash function."""

    def test_same_content_same_hash(self, tmp_path: Path) -> None:
        """Same file content produces the same hash."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("Hello, World!")

        hash1 = file_content_hash(file1)
        hash2 = file_content_hash(file1)

        assert hash1 == hash2
        assert len(hash1) == 64  # sha256 hex digest length

    def test_different_content_different_hash(self, tmp_path: Path) -> None:
        """Different content produces different hashes."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content A")
        file2.write_text("Content B")

        hash1 = file_content_hash(file1)
        hash2 = file_content_hash(file2)

        assert hash1 != hash2

    def test_binary_content(self, tmp_path: Path) -> None:
        """Binary files can be hashed."""
        binary_file = tmp_path / "data.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd\xfc")

        hash_result = file_content_hash(binary_file)

        assert len(hash_result) == 64
        assert all(c in "0123456789abcdef" for c in hash_result)


# ---------------------------------------------------------------------------
# needs_reindex tests
# ---------------------------------------------------------------------------


class TestNeedsReindex:
    """Tests for needs_reindex function."""

    def test_same_mtime_returns_false(self, tmp_path: Path) -> None:
        """Same mtime returns False (fast path, no hash check)."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("content")

        mtime = file_path.stat().st_mtime
        stored_hash = "anything"  # Won't be checked

        result = needs_reindex(file_path, mtime, stored_hash)

        assert result is False

    def test_different_mtime_different_content_returns_true(self, tmp_path: Path) -> None:
        """Different mtime and different content returns True."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("original content")

        old_mtime = 0.0  # Different from current
        old_hash = file_content_hash(file_path)

        # Change content
        file_path.write_text("changed content")

        result = needs_reindex(file_path, old_mtime, old_hash)

        assert result is True

    def test_different_mtime_same_content_returns_false(self, tmp_path: Path) -> None:
        """Different mtime but same content returns False (touch without change)."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("unchanged content")

        old_mtime = 0.0  # Different from current
        old_hash = file_content_hash(file_path)

        # Touch file without changing content
        file_path.touch()

        result = needs_reindex(file_path, old_mtime, old_hash)

        assert result is False


# ---------------------------------------------------------------------------
# walk_source tests
# ---------------------------------------------------------------------------


class TestWalkSource:
    """Tests for walk_source function."""

    def test_yields_all_files_by_default(self, tmp_path: Path) -> None:
        """Default include ['**/*'] yields all files."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("1")
        (source_dir / "file2.md").write_text("2")
        subdir = source_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.py").write_text("3")

        files = list(walk_source(source_dir, include=["**/*"], exclude=[]))

        assert len(files) == 3
        assert all(isinstance(f, Path) for f in files)

    def test_include_pattern_filters(self, tmp_path: Path) -> None:
        """Include pattern ['*.md'] only yields .md files."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "readme.md").write_text("md")
        (source_dir / "script.py").write_text("py")
        (source_dir / "config.yaml").write_text("yaml")

        files = list(walk_source(source_dir, include=["*.md"], exclude=[]))

        assert len(files) == 1
        assert files[0].name == "readme.md"

    def test_exclude_pattern_skips(self, tmp_path: Path) -> None:
        """Exclude pattern skips matching files."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "keep.txt").write_text("keep")
        node_modules = source_dir / "node_modules"
        node_modules.mkdir()
        (node_modules / "package.json").write_text("skip")

        files = list(walk_source(
            source_dir,
            include=["**/*"],
            exclude=["**/node_modules/**"],
        ))

        assert len(files) == 1
        assert files[0].name == "keep.txt"

    def test_multiple_include_patterns(self, tmp_path: Path) -> None:
        """Multiple include patterns match union of files."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file.md").write_text("md")
        (source_dir / "file.py").write_text("py")
        (source_dir / "file.txt").write_text("txt")

        files = list(walk_source(
            source_dir,
            include=["*.md", "*.py"],
            exclude=[],
        ))

        assert len(files) == 2
        names = {f.name for f in files}
        assert names == {"file.md", "file.py"}

    def test_empty_directory_yields_nothing(self, tmp_path: Path) -> None:
        """Empty directory yields no files."""
        source_dir = tmp_path / "empty"
        source_dir.mkdir()

        files = list(walk_source(source_dir, include=["**/*"], exclude=[]))

        assert files == []

    def test_respects_path_match_semantics(self, tmp_path: Path) -> None:
        """Pattern matching follows Path.match() semantics."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        subdir = source_dir / "docs"
        subdir.mkdir()
        (subdir / "guide.md").write_text("guide")

        files = list(walk_source(source_dir, include=["docs/*.md"], exclude=[]))

        assert len(files) == 1
        assert files[0].name == "guide.md"

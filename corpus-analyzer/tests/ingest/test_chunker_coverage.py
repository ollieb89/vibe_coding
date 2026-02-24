"""Additional chunker tests for branch coverage.

These tests target specific branches in chunker.py to improve coverage to 85%+.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from corpus_analyzer.ingest.chunker import (
    chunk_file,
    chunk_lines,
    chunk_markdown,
    chunk_python,
    _enforce_char_limit,
)


class TestChunkLinesEdgeCases:
    """Tests for chunk_lines edge cases."""

    def test_empty_file_returns_empty(self, tmp_path: Path) -> None:
        """Empty file should return empty chunks list."""
        txt_file = tmp_path / "empty.txt"
        txt_file.write_text("")
        chunks = chunk_lines(txt_file)
        assert chunks == []

    def test_single_line_file(self, tmp_path: Path) -> None:
        """Single line file produces single chunk."""
        txt_file = tmp_path / "single.txt"
        txt_file.write_text("single line")
        chunks = chunk_lines(txt_file)
        assert len(chunks) == 1
        assert chunks[0]["text"] == "single line"
        assert chunks[0]["start_line"] == 1
        assert chunks[0]["end_line"] == 1

    def test_trailing_newline_removed(self, tmp_path: Path) -> None:
        """Trailing newline on last line is removed."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("line1\nline2\n")
        chunks = chunk_lines(txt_file, window=10, overlap=0)
        # Last line should not have trailing newline
        assert not chunks[0]["text"].endswith("\n")


class TestEnforceCharLimit:
    """Tests for _enforce_char_limit function branches."""

    def test_chunk_under_limit_preserved(self) -> None:
        """Chunks under char limit are preserved as-is."""
        chunks = [
            {
                "text": "short text",
                "start_line": 1,
                "end_line": 1,
                "chunk_name": "test",
                "chunk_text": "short text",
            }
        ]
        result = _enforce_char_limit(chunks, max_chars=100)
        assert len(result) == 1
        assert result[0]["text"] == "short text"

    def test_oversized_chunk_split(self) -> None:
        """Oversized chunk is split into smaller pieces."""
        long_text = "x" * 100
        chunks = [
            {
                "text": long_text,
                "start_line": 1,
                "end_line": 1,
                "chunk_name": "test",
                "chunk_text": long_text,
            }
        ]
        result = _enforce_char_limit(chunks, max_chars=50)
        # Should be split into multiple chunks
        assert len(result) > 1
        # Each chunk should be within limit
        for chunk in result:
            assert len(chunk["text"]) <= 50

    def test_extremely_long_line_split(self) -> None:
        """Extremely long single line is split into char chunks."""
        long_line = "x" * 200
        chunks = [
            {
                "text": long_line,
                "start_line": 1,
                "end_line": 1,
                "chunk_name": "test",
                "chunk_text": long_line,
            }
        ]
        result = _enforce_char_limit(chunks, max_chars=50)
        # Long line should be split into 50-char chunks
        assert len(result) == 4
        for chunk in result:
            assert len(chunk["text"]) <= 50
            assert chunk["start_line"] == 1
            assert chunk["end_line"] == 1

    def test_empty_chunk_preserved(self) -> None:
        """Empty chunks are preserved (not filtered) during char limit enforcement."""
        chunks = [
            {
                "text": "",
                "start_line": 1,
                "end_line": 1,
                "chunk_name": "test",
                "chunk_text": "",
            }
        ]
        result = _enforce_char_limit(chunks, max_chars=100)
        # Empty chunks are preserved (not filtered out)
        assert len(result) == 1
        assert result[0]["text"] == ""

    def test_multiline_chunk_split(self) -> None:
        """Multi-line chunk exceeding limit is split at line boundaries."""
        lines = [f"line {i}" for i in range(10)]
        text = "\n".join(lines)
        chunks = [
            {
                "text": text,
                "start_line": 1,
                "end_line": 10,
                "chunk_name": "test",
                "chunk_text": text,
            }
        ]
        result = _enforce_char_limit(chunks, max_chars=30)
        # Should be split preserving line boundaries where possible
        assert len(result) > 1
        for chunk in result:
            assert len(chunk["text"]) <= 30


class TestChunkFileEdgeCases:
    """Tests for chunk_file dispatcher edge cases."""

    def test_binary_file_returns_empty(self, tmp_path: Path) -> None:
        """Binary files should return empty list."""
        bin_file = tmp_path / "test.png"
        bin_file.write_bytes(b"\x89PNG\r\n\x1a\n")
        chunks = chunk_file(bin_file)
        assert chunks == []

    def test_unknown_extension_uses_chunk_lines(self, tmp_path: Path) -> None:
        """Unknown extension falls back to chunk_lines."""
        weird_file = tmp_path / "test.xyz"
        weird_file.write_text("line1\nline2\nline3\n")
        chunks = chunk_file(weird_file)
        # Should use chunk_lines fallback
        assert len(chunks) >= 1
        assert "start_line" in chunks[0]

    def test_json_file_chunked(self, tmp_path: Path) -> None:
        """JSON files are chunked using chunk_lines."""
        json_file = tmp_path / "test.json"
        json_file.write_text('{"key": "value",\n"list": [1, 2, 3]}\n')
        chunks = chunk_file(json_file)
        assert len(chunks) >= 1
        assert '"key": "value"' in chunks[0]["text"]

    def test_unicode_decode_error_handled(self, tmp_path: Path) -> None:
        """Files with invalid UTF-8 are handled gracefully."""
        bad_file = tmp_path / "test.txt"
        bad_file.write_bytes(b"\xff\xfe\x00\x01 invalid utf-8")
        chunks = chunk_file(bad_file)
        assert chunks == []


class TestChunkMarkdownEdgeCases:
    """Tests for chunk_markdown edge cases."""

    def test_no_headings_single_chunk(self, tmp_path: Path) -> None:
        """Markdown without headings returns single chunk."""
        md_file = tmp_path / "test.md"
        md_file.write_text("Just some text.\nMore text.\n")
        chunks = chunk_markdown(md_file)
        assert len(chunks) == 1
        assert chunks[0]["start_line"] == 1
        assert "Just some text" in chunks[0]["text"]

    def test_empty_section_filtered(self, tmp_path: Path) -> None:
        """Empty sections are filtered out."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Heading\n\n## Next\nContent\n")
        chunks = chunk_markdown(md_file)
        # Empty section should be filtered
        assert all(len(c["text"].strip()) > 0 for c in chunks)

    def test_large_section_subsplit(self, tmp_path: Path) -> None:
        """Large sections exceeding word count are sub-split."""
        md_file = tmp_path / "test.md"
        # Create content with many words (each word on separate line to exceed count)
        content = "# Large\n" + "word\n" * 300
        md_file.write_text(content)
        chunks = chunk_markdown(md_file, max_words=100)
        # Should be sub-split into multiple chunks
        assert len(chunks) > 1


class TestChunkPythonEdgeCases:
    """Tests for chunk_python edge cases."""

    def test_syntax_error_falls_back(self, tmp_path: Path) -> None:
        """Syntax errors cause fallback to chunk_lines."""
        py_file = tmp_path / "bad.py"
        py_file.write_text("def foo(:\n    pass\n")
        chunks = chunk_python(py_file)
        # Should fall back to chunk_lines
        assert len(chunks) >= 1
        assert "start_line" in chunks[0]

    def test_empty_file_returns_empty(self, tmp_path: Path) -> None:
        """Empty Python file returns empty list."""
        py_file = tmp_path / "empty.py"
        py_file.write_text("   \n   \n")
        chunks = chunk_python(py_file)
        assert chunks == []

    def test_only_comments_no_defs(self, tmp_path: Path) -> None:
        """File with only comments falls back to chunk_lines."""
        py_file = tmp_path / "comments.py"
        py_file.write_text("# Comment 1\n# Comment 2\nx = 1\n")
        chunks = chunk_python(py_file)
        # Should fall back to chunk_lines since no top-level defs
        assert len(chunks) >= 1

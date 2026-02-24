"""Tests for snippet extraction and Rich result formatting."""

from __future__ import annotations

from pathlib import Path

from corpus_analyzer.search.formatter import extract_snippet, format_result


def test_extract_snippet_short_text() -> None:
    """SEARCH-05: text with <= max_lines lines is returned in full."""
    text = "line 1\nline 2"
    assert extract_snippet(text, query="line", max_lines=3) == text


def test_extract_snippet_finds_best_line() -> None:
    """SEARCH-05: snippet window centers around the line containing the most query terms."""
    text = "\n".join(
        [
            "alpha",
            "beta",
            "gamma",
            "context before",
            "search term search term appears here",
            "context after",
        ]
    )
    snippet = extract_snippet(text, query="search term", max_lines=3)
    assert snippet == "context before\nsearch term search term appears here\ncontext after"


def test_extract_snippet_truncates_at_word_boundary() -> None:
    """SEARCH-05: snippet longer than 200 chars is truncated at word boundary with ellipsis."""
    long_line = "word " * 80
    snippet = extract_snippet(long_line, query="word", max_lines=3)
    assert snippet.endswith("…")
    assert len(snippet) <= 201


def test_extract_snippet_empty_query() -> None:
    """SEARCH-05: empty query falls back to first max_lines lines without error."""
    text = "line 1\nline 2\nline 3\nline 4"
    snippet = extract_snippet(text, query="", max_lines=3)
    assert snippet == "line 1\nline 2\nline 3"


# ---------------------------------------------------------------------------
# format_result() RED tests — CHUNK-02
# All tests below MUST fail until Plan 02 ships the implementation.
# ---------------------------------------------------------------------------


def test_format_result_with_line_range() -> None:
    """CHUNK-02: full result with line range produces path:start-end, score, bracket tag, preview."""
    result = {
        "file_path": "/cwd/skills/foo.md",
        "start_line": 42,
        "end_line": 67,
        "construct_type": "skill",
        "_relevance_score": 0.021,
        "chunk_text": "Some chunk content",
    }
    primary, preview = format_result(result, cwd=Path("/cwd"))
    assert "skills/foo.md:42-67" in primary
    assert "score:0.021" in primary
    assert "[skill]" in primary
    assert preview == "    Some chunk content"


def test_format_result_legacy_row_no_line_range() -> None:
    """CHUNK-02: legacy row with start_line=0 and end_line=0 omits :0-0 and returns None preview."""
    result = {
        "file_path": "/cwd/skills/foo.md",
        "start_line": 0,
        "end_line": 0,
        "construct_type": "skill",
        "_relevance_score": 0.5,
        "chunk_text": "",
    }
    primary, preview = format_result(result, cwd=Path("/cwd"))
    assert ":0-0" not in primary
    assert preview is None


def test_format_result_empty_construct_omits_brackets() -> None:
    """CHUNK-02: empty or None construct_type produces no brackets in primary line."""
    result_none = {
        "file_path": "/cwd/skills/foo.md",
        "start_line": 1,
        "end_line": 5,
        "construct_type": None,
        "_relevance_score": 0.5,
        "chunk_text": "content",
    }
    primary_none, _ = format_result(result_none, cwd=Path("/cwd"))
    assert "[]" not in primary_none
    assert "[None]" not in primary_none

    result_empty = dict(result_none)
    result_empty["construct_type"] = ""
    primary_empty, _ = format_result(result_empty, cwd=Path("/cwd"))
    assert "[]" not in primary_empty
    assert "[None]" not in primary_empty


def test_format_result_chunk_text_newline_takes_first_line() -> None:
    """CHUNK-02: multi-line chunk_text — preview shows only the first line, indented."""
    result = {
        "file_path": "/cwd/skills/foo.md",
        "start_line": 1,
        "end_line": 5,
        "construct_type": "skill",
        "_relevance_score": 0.5,
        "chunk_text": "first line\nsecond line\nthird line",
    }
    _, preview = format_result(result, cwd=Path("/cwd"))
    assert preview == "    first line"


def test_format_result_truncates_at_200_chars() -> None:
    """CHUNK-02: chunk_text > 200 chars is truncated to 200 chars + '...' (207 total with indent)."""
    result = {
        "file_path": "/cwd/skills/foo.md",
        "start_line": 1,
        "end_line": 5,
        "construct_type": "skill",
        "_relevance_score": 0.5,
        "chunk_text": "x" * 250,
    }
    _, preview = format_result(result, cwd=Path("/cwd"))
    assert preview is not None
    assert preview.endswith("...")
    assert len(preview) == 207  # 4 spaces + 200 chars + 3 dots


def test_format_result_no_ellipsis_at_exactly_200_chars() -> None:
    """CHUNK-02: chunk_text exactly 200 chars — no truncation ellipsis."""
    result = {
        "file_path": "/cwd/skills/foo.md",
        "start_line": 1,
        "end_line": 5,
        "construct_type": "skill",
        "_relevance_score": 0.5,
        "chunk_text": "y" * 200,
    }
    _, preview = format_result(result, cwd=Path("/cwd"))
    assert preview is not None
    assert not preview.endswith("...")
    assert len(preview) == 204  # 4 spaces + 200 chars


def test_format_result_path_outside_cwd_uses_absolute() -> None:
    """CHUNK-02: file_path outside cwd falls back to absolute path in primary."""
    result = {
        "file_path": "/other/project/file.md",
        "start_line": 1,
        "end_line": 5,
        "construct_type": "skill",
        "_relevance_score": 0.5,
        "chunk_text": "content",
    }
    primary, _ = format_result(result, cwd=Path("/home/user/project"))
    assert "/other/project/file.md" in primary


def test_format_result_score_always_3_decimal_places() -> None:
    """CHUNK-02: _relevance_score is always formatted to 3 decimal places."""
    result = {
        "file_path": "/cwd/skills/foo.md",
        "start_line": 1,
        "end_line": 5,
        "construct_type": "skill",
        "_relevance_score": 0.1,
        "chunk_text": "content",
    }
    primary, _ = format_result(result, cwd=Path("/cwd"))
    assert "score:0.100" in primary


def test_format_result_rich_markup_escape_in_path() -> None:
    """CHUNK-02: path containing Rich markup brackets is escaped — no MarkupError raised."""
    result = {
        "file_path": "/cwd/[deprecated]/foo.md",
        "start_line": 1,
        "end_line": 5,
        "construct_type": "skill",
        "_relevance_score": 0.5,
        "chunk_text": "content",
    }
    primary, _ = format_result(result, cwd=Path("/cwd"))
    # Should not raise; escaped form of [deprecated] must appear in primary
    assert "[deprecated]" in primary


def test_format_result_start_line_nonzero_end_line_zero_shows_range() -> None:
    """CHUNK-02: start_line > 0 with end_line == 0 is not a legacy row — range is shown."""
    result = {
        "file_path": "/cwd/skills/foo.md",
        "start_line": 5,
        "end_line": 0,
        "construct_type": "skill",
        "_relevance_score": 0.5,
        "chunk_text": "content",
    }
    primary, _ = format_result(result, cwd=Path("/cwd"))
    assert ":5-0" in primary

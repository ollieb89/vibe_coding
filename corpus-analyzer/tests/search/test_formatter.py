"""Tests for snippet extraction and Rich result formatting."""

from __future__ import annotations

from corpus_analyzer.search.formatter import extract_snippet


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

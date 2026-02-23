"""Tests for Summarizer AI summary generation."""

from __future__ import annotations

from unittest.mock import patch

from corpus_analyzer.search.summarizer import generate_summary, should_summarize


def test_generate_summary() -> None:
    """SUMM-01: generate_summary() returns a non-empty string (mock ollama.generate)."""
    with patch("corpus_analyzer.search.summarizer.ollama.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.generate.return_value.response = "  This file defines indexing rules.  "

        result = generate_summary(
            filename="rules.md",
            content="A" * 20,
            model="mistral",
            host="http://localhost:11434",
        )

    assert result == "This file defines indexing rules."
    mock_client.generate.assert_called_once()


def test_summary_is_one_or_two_sentences() -> None:
    """SUMM-01: generate_summary() returns empty string when ollama.generate raises."""
    with patch("corpus_analyzer.search.summarizer.ollama.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.generate.side_effect = ConnectionError("offline")

        result = generate_summary(
            filename="rules.md",
            content="A" * 20,
            model="mistral",
            host="http://localhost:11434",
        )

    assert result == ""


def test_skip_when_summarize_false() -> None:
    """SUMM-03: should_summarize=False when source summarize is disabled."""
    assert (
        should_summarize(
            source_summarize=False,
            stored_summary=None,
            content_hash_changed=True,
        )
        is False
    )


def test_skip_when_content_unchanged() -> None:
    """SUMM-01/SUMM-03: unchanged file with existing summary is skipped."""
    assert (
        should_summarize(
            source_summarize=True,
            stored_summary=None,
            content_hash_changed=True,
        )
        is True
    )
    assert (
        should_summarize(
            source_summarize=True,
            stored_summary="already summarized",
            content_hash_changed=False,
        )
        is False
    )

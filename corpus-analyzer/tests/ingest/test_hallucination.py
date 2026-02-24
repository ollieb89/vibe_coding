"""Zero-hallucination line-range integration tests.

QUAL-02: A parametrised integration test verifies that every stored
start_line/end_line matches actual file content for .md, .py, and .ts fixtures.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from corpus_analyzer.ingest.chunker import chunk_markdown, chunk_python
from corpus_analyzer.ingest.ts_chunker import chunk_typescript


@pytest.mark.parametrize(
    "filename,chunker",
    [
        ("sample.md", chunk_markdown),
        ("sample.py", chunk_python),
        ("sample.ts", chunk_typescript),
    ],
)
def test_zero_hallucination_line_ranges(filename: str, chunker: callable) -> None:
    """Verify chunk line ranges exactly match file content.

    This test ensures that the chunker's reported start_line and end_line
    values correspond exactly to the actual content in the file, with no
    hallucination or extra/missing characters.
    """
    fixture_dir = Path(__file__).parent.parent / "fixtures" / "hallucination"
    fixture_path = fixture_dir / filename

    # Read the file content
    content = fixture_path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=False)  # Don't keep line endings

    # Get chunks from the chunker
    chunks = chunker(fixture_path)

    assert len(chunks) > 0, f"Expected at least one chunk for {filename}"

    for chunk in chunks:
        start_line = chunk["start_line"]
        end_line = chunk["end_line"]
        chunk_text = chunk["text"]

        # Validate line numbers are 1-indexed and within bounds
        assert start_line >= 1, f"start_line must be >= 1, got {start_line}"
        assert end_line >= start_line, f"end_line must be >= start_line, got {end_line} < {start_line}"
        assert end_line <= len(lines), f"end_line {end_line} exceeds file length {len(lines)}"

        # Extract expected text from file
        # Lines are 1-indexed in chunks, 0-indexed in Python list
        expected_lines = lines[start_line - 1 : end_line]
        expected_text = "\n".join(expected_lines)

        # Compare chunk text with expected text
        # Normalize both by stripping trailing whitespace for comparison
        normalized_chunk = chunk_text.rstrip()
        normalized_expected = expected_text.rstrip()

        assert normalized_chunk == normalized_expected, (
            f"Hallucination detected in {filename} lines {start_line}-{end_line}:\n"
            f"  Expected ({len(normalized_expected)} chars): {repr(normalized_expected[:100])}...\n"
            f"  Got ({len(normalized_chunk)} chars): {repr(normalized_chunk[:100])}..."
        )


def test_line_numbers_are_one_indexed() -> None:
    """Verify that chunk line numbers are 1-indexed (not 0-indexed)."""
    fixture_dir = Path(__file__).parent.parent / "fixtures" / "hallucination"
    fixture_path = fixture_dir / "sample.md"

    chunks = chunk_markdown(fixture_path)

    # The first chunk should start at line 1 (not 0)
    assert chunks[0]["start_line"] == 1, "First chunk should start at line 1 (1-indexed)"


def test_chunk_text_matches_exact_content() -> None:
    """Verify chunk text is exactly the file content without modification."""
    fixture_dir = Path(__file__).parent.parent / "fixtures" / "hallucination"
    fixture_path = fixture_dir / "sample.py"

    content = fixture_path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=False)

    chunks = chunk_python(fixture_path)

    # Verify each chunk's text is a substring of the original content
    for chunk in chunks:
        chunk_text = chunk["text"]
        # The chunk text should appear exactly in the original content
        assert chunk_text in content or chunk_text.rstrip() in content.rstrip(), (
            f"Chunk text not found in original content: {repr(chunk_text[:50])}..."
        )

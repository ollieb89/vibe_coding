"""Tests for Markdown extractor."""

from pathlib import Path

from corpus_analyzer.extractors.markdown import MarkdownExtractor


def test_extract_title_from_frontmatter(sample_markdown: Path, temp_dir: Path):
    """Test title extraction from frontmatter."""
    extractor = MarkdownExtractor()
    doc = extractor.extract(sample_markdown, temp_dir)
    assert doc.title == "Sample Document"


def test_extract_headings(sample_markdown: Path, temp_dir: Path):
    """Test heading extraction."""
    extractor = MarkdownExtractor()
    doc = extractor.extract(sample_markdown, temp_dir)

    assert len(doc.headings) == 4
    assert doc.headings[0].text == "Sample Document"
    assert doc.headings[0].level == 1
    assert doc.headings[1].text == "Overview"
    assert doc.headings[1].level == 2


def test_extract_code_blocks(sample_markdown: Path, temp_dir: Path):
    """Test code block extraction."""
    extractor = MarkdownExtractor()
    doc = extractor.extract(sample_markdown, temp_dir)

    assert len(doc.code_blocks) == 1
    assert doc.code_blocks[0].language == "python"
    assert "hello" in doc.code_blocks[0].content


def test_extract_links(sample_markdown: Path, temp_dir: Path):
    """Test link extraction."""
    extractor = MarkdownExtractor()
    doc = extractor.extract(sample_markdown, temp_dir)

    assert len(doc.links) == 1
    assert doc.links[0].text == "Link to docs"
    assert doc.links[0].url == "https://example.com"


def test_token_estimation(sample_markdown: Path, temp_dir: Path):
    """Test token estimation."""
    extractor = MarkdownExtractor()
    doc = extractor.extract(sample_markdown, temp_dir)

    assert doc.token_estimate > 0

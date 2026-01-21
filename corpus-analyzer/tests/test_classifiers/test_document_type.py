"""Tests for document type classifier."""

from datetime import datetime
from pathlib import Path

from corpus_analyzer.classifiers.document_type import classify_document
from corpus_analyzer.core.models import Document, DocumentCategory, Heading


def test_classify_howto():
    """Test classification of how-to documents."""
    doc = Document(
        path=Path("/test/howto.md"),
        relative_path="howto.md",
        file_type="md",
        title="How to Set Up Development Environment",
        mtime=datetime.now(),
        size_bytes=1000,
        headings=[
            Heading(level=1, text="How to Set Up Development Environment", line_number=1),
            Heading(level=2, text="Steps", line_number=5),
            Heading(level=2, text="Prerequisites", line_number=10),
        ],
    )

    result = classify_document(doc)
    assert result.category == DocumentCategory.HOWTO
    assert result.confidence > 0.3  # Category detected correctly


def test_classify_adr():
    """Test classification of ADR documents."""
    doc = Document(
        path=Path("/test/adr-001.md"),
        relative_path="adr-001.md",
        file_type="md",
        title="ADR-001: Use PostgreSQL for Data Storage",
        mtime=datetime.now(),
        size_bytes=800,
        headings=[
            Heading(level=1, text="ADR-001: Use PostgreSQL", line_number=1),
            Heading(level=2, text="Status", line_number=3),
            Heading(level=2, text="Context", line_number=5),
            Heading(level=2, text="Decision", line_number=10),
            Heading(level=2, text="Consequences", line_number=15),
        ],
    )

    result = classify_document(doc)
    assert result.category == DocumentCategory.ADR
    assert result.confidence > 0.5


def test_classify_runbook():
    """Test classification of runbook documents."""
    doc = Document(
        path=Path("/test/runbook.md"),
        relative_path="runbook.md",
        file_type="md",
        title="Database Recovery Runbook",
        mtime=datetime.now(),
        size_bytes=1500,
        headings=[
            Heading(level=1, text="Database Recovery Runbook", line_number=1),
            Heading(level=2, text="Troubleshooting", line_number=5),
            Heading(level=2, text="Recovery Steps", line_number=15),
            Heading(level=2, text="Alert Response", line_number=25),
        ],
    )

    result = classify_document(doc)
    assert result.category == DocumentCategory.RUNBOOK
    assert result.confidence > 0.5


def test_classify_unknown():
    """Test classification of unclassifiable documents."""
    doc = Document(
        path=Path("/test/notes.md"),
        relative_path="notes.md",
        file_type="md",
        title="Random Notes",
        mtime=datetime.now(),
        size_bytes=200,
        headings=[],
    )

    result = classify_document(doc)
    assert result.category == DocumentCategory.UNKNOWN

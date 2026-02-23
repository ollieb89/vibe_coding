"""Ingest package for corpus-analyzer.

Provides file chunking and scanning functionality for document ingestion.
"""

from corpus_analyzer.ingest.chunker import (
    chunk_file,
    chunk_lines,
    chunk_markdown,
    chunk_python,
)
from corpus_analyzer.ingest.scanner import (
    file_content_hash,
    needs_reindex,
    walk_source,
)

__all__ = [
    "chunk_file",
    "chunk_lines",
    "chunk_markdown",
    "chunk_python",
    "file_content_hash",
    "needs_reindex",
    "walk_source",
]

"""Document extractors package."""

from pathlib import Path
from typing import Optional

from corpus_analyzer.core.models import Document


def extract_document(file_path: Path, root: Path) -> Optional[Document]:
    """
    Extract a document based on its file type.

    Args:
        file_path: Absolute path to the file
        root: Root directory for relative path calculation

    Returns:
        Extracted Document or None if extraction fails
    """
    from corpus_analyzer.extractors.markdown import MarkdownExtractor
    from corpus_analyzer.extractors.python import PythonExtractor

    suffix = file_path.suffix.lower()

    extractors = {
        ".md": MarkdownExtractor,
        ".py": PythonExtractor,
        ".txt": MarkdownExtractor,  # Treat as plain text markdown
        ".rst": MarkdownExtractor,  # Basic handling
    }

    extractor_class = extractors.get(suffix)
    if extractor_class:
        extractor = extractor_class()
        return extractor.extract(file_path, root)

    return None


__all__ = ["extract_document"]

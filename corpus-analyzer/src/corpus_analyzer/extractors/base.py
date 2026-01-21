"""Base extractor interface."""

from abc import ABC, abstractmethod
from pathlib import Path

from corpus_analyzer.core.models import Document


class BaseExtractor(ABC):
    """Abstract base class for document extractors."""

    @abstractmethod
    def extract(self, file_path: Path, root: Path) -> Document:
        """
        Extract document metadata and content.

        Args:
            file_path: Absolute path to the file
            root: Root directory for relative path calculation

        Returns:
            Extracted Document model
        """
        pass

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Simple estimation: ~4 characters per token on average.
        """
        return len(text) // 4

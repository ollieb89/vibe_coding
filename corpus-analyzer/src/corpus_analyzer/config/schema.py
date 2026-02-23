"""Configuration schema for corpus-analyzer.

This module defines the Pydantic models for the corpus.toml configuration file,
including embedding settings and source definitions.
"""

from __future__ import annotations

from pathlib import Path
from platformdirs import user_config_dir, user_data_dir

from pydantic import BaseModel, Field, field_validator

CONFIG_PATH = Path(user_config_dir("corpus")) / "corpus.toml"
DATA_DIR = Path(user_data_dir("corpus"))

DEFAULT_EXTENSIONS: list[str] = [
    ".md", ".py", ".ts", ".tsx", ".js", ".jsx", ".yaml", ".yml", ".txt"
]
"""Default file extensions to index for documentation and code types."""


class EmbeddingConfig(BaseModel):
    """Configuration for the embedding model used to generate vectors.

    Attributes:
        model: Name of the embedding model (e.g., "nomic-embed-text").
        provider: Embedding provider service (Phase 1: always "ollama").
        host: URL of the Ollama server.
    """

    model: str = "nomic-embed-text"
    """Name of the embedding model."""

    provider: str = "ollama"
    """Embedding provider service."""

    host: str = "http://localhost:11434"
    """URL of the Ollama server."""


class SourceConfig(BaseModel):
    """Configuration for a single document source.

    A source is a directory of documents to be indexed, with optional
    include/exclude glob patterns for filtering.

    Attributes:
        name: Unique identifier for this source.
        path: Directory path to the source documents (may use ~ expansion).
        include: Glob patterns for files to include.
        exclude: Glob patterns for files to exclude.
    """

    name: str
    """Unique identifier for this source."""

    path: str
    """Directory path to the source documents (may use ~ expansion)."""

    include: list[str] = Field(default_factory=lambda: ["**/*"])
    """Glob patterns for files to include."""

    exclude: list[str] = Field(default_factory=list)
    """Glob patterns for files to exclude."""

    summarize: bool = False
    """Whether to generate and embed AI summaries for chunks in this source."""

    use_llm_classification: bool = False
    """Whether to use LLM-based classification for construct type detection.

    When True, Ollama is called to classify each changed file during indexing.
    When False (default), rule-based classification is used.
    Set to True per source for richer classification when LLM cost is acceptable.
    """

    extensions: list[str] = Field(default_factory=lambda: list(DEFAULT_EXTENSIONS))
    """File extensions to index for this source (e.g. [".md", ".py"]).

    Defaults to common documentation and code types. Set to an empty list to skip
    all files in this source. The leading dot is required but normalized automatically.
    """

    @field_validator("extensions", mode="before")
    @classmethod
    def normalize_extensions(cls, v: object) -> list[str]:
        """Normalize extension strings: lowercase, ensure leading dot."""
        if not isinstance(v, list):
            raise ValueError("extensions must be a list of strings")
        result: list[str] = []
        for raw in v:
            ext = str(raw).strip().lower()
            if ext and not ext.startswith("."):
                ext = f".{ext}"
            result.append(ext)
        return result


class CorpusConfig(BaseModel):
    """Root configuration model for corpus-analyzer.

    This is the top-level configuration that contains embedding settings
    and a list of document sources to index.

    Attributes:
        embedding: Embedding model configuration.
        sources: List of document sources to index.
    """

    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    """Embedding model configuration."""

    sources: list[SourceConfig] = Field(default_factory=list)
    """List of document sources to index."""

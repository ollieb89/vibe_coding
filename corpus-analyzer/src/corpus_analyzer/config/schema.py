"""Configuration schema for corpus-analyzer.

This module defines the Pydantic models for the corpus.toml configuration file,
including embedding settings and source definitions.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


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

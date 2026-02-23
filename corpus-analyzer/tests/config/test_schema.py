"""Tests for corpus_analyzer.config.schema — Config model validation.

Follows RED-GREEN-REFACTOR TDD cycle.
"""

import pytest
from pydantic import ValidationError

from corpus_analyzer.config.schema import CorpusConfig, EmbeddingConfig, SourceConfig


# ---------------------------------------------------------------------------
# EmbeddingConfig tests
# ---------------------------------------------------------------------------


class TestEmbeddingConfig:
    """Tests for EmbeddingConfig model with defaults."""

    def test_instantiates_with_defaults(self) -> None:
        """EmbeddingConfig() instantiates with default values."""
        config = EmbeddingConfig()
        assert config.model == "nomic-embed-text"
        assert config.provider == "ollama"
        assert config.host == "http://localhost:11434"

    def test_custom_values(self) -> None:
        """EmbeddingConfig accepts custom values."""
        config = EmbeddingConfig(model="other-model", provider="other", host="http://other:8080")
        assert config.model == "other-model"
        assert config.provider == "other"
        assert config.host == "http://other:8080"


# ---------------------------------------------------------------------------
# SourceConfig tests
# ---------------------------------------------------------------------------


class TestSourceConfig:
    """Tests for SourceConfig model validation."""

    def test_instantiates_with_required_fields(self) -> None:
        """SourceConfig with name and path instantiates with defaults."""
        source = SourceConfig(name="my-skills", path="/home/user/skills")
        assert source.name == "my-skills"
        assert source.path == "/home/user/skills"
        assert source.include == ["**/*"]
        assert source.exclude == []

    def test_custom_include_exclude(self) -> None:
        """SourceConfig accepts custom include/exclude patterns."""
        source = SourceConfig(
            name="docs",
            path="/docs",
            include=["**/*.md", "**/*.py"],
            exclude=["**/node_modules/**", "**/.git/**"],
        )
        assert source.include == ["**/*.md", "**/*.py"]
        assert source.exclude == ["**/node_modules/**", "**/.git/**"]

    def test_missing_name_raises_validation_error(self) -> None:
        """SourceConfig without name raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            SourceConfig(path="/some/path")  # type: ignore[call-arg]
        assert "name" in str(exc_info.value)

    def test_missing_path_raises_validation_error(self) -> None:
        """SourceConfig without path raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            SourceConfig(name="some-name")  # type: ignore[call-arg]
        assert "path" in str(exc_info.value)


# ---------------------------------------------------------------------------
# CorpusConfig tests
# ---------------------------------------------------------------------------


class TestCorpusConfig:
    """Tests for CorpusConfig model validation."""

    def test_instantiates_with_defaults(self) -> None:
        """CorpusConfig() instantiates with default embedding and empty sources."""
        config = CorpusConfig()
        assert isinstance(config.embedding, EmbeddingConfig)
        assert config.embedding.model == "nomic-embed-text"
        assert config.sources == []

    def test_with_single_source(self) -> None:
        """CorpusConfig with one source appears in sources list."""
        source = SourceConfig(name="skills", path="/skills")
        config = CorpusConfig(sources=[source])
        assert len(config.sources) == 1
        assert config.sources[0].name == "skills"
        assert config.sources[0].path == "/skills"

    def test_with_multiple_sources(self) -> None:
        """CorpusConfig with multiple sources preserves all."""
        sources = [
            SourceConfig(name="skills", path="/skills"),
            SourceConfig(name="docs", path="/docs"),
        ]
        config = CorpusConfig(sources=sources)
        assert len(config.sources) == 2
        assert config.sources[0].name == "skills"
        assert config.sources[1].name == "docs"

    def test_custom_embedding(self) -> None:
        """CorpusConfig accepts custom embedding config."""
        embedding = EmbeddingConfig(model="custom-model", provider="custom")
        config = CorpusConfig(embedding=embedding)
        assert config.embedding.model == "custom-model"
        assert config.embedding.provider == "custom"

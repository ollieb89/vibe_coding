"""Tests for corpus_analyzer.config.io — TOML load/save functions.

Follows RED-GREEN-REFACTOR TDD cycle.
Uses pytest tmp_path fixture for file operations.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from corpus_analyzer.config.io import load_config, save_config
from corpus_analyzer.config.schema import CorpusConfig, EmbeddingConfig, SourceConfig

# ---------------------------------------------------------------------------
# load_config tests
# ---------------------------------------------------------------------------


class TestLoadConfig:
    """Tests for load_config() function."""

    def test_non_existent_file_returns_defaults(self, tmp_path: Path) -> None:
        """load_config() returns CorpusConfig with defaults when file doesn't exist."""
        non_existent = tmp_path / "non_existent.toml"
        config = load_config(non_existent)
        assert isinstance(config, CorpusConfig)
        assert config.sources == []
        assert config.embedding.model == "nomic-embed-text"

    def test_loads_valid_toml(self, tmp_path: Path) -> None:
        """load_config() reads and validates a valid corpus.toml file."""
        config_path = tmp_path / "corpus.toml"
        config_path.write_text("""
[embedding]
model = "nomic-embed-text"
provider = "ollama"
host = "http://localhost:11434"

[[sources]]
name = "my-skills"
path = "/home/user/skills"
include = ["**/*.md"]
exclude = ["**/node_modules/**"]
""")
        config = load_config(config_path)
        assert config.embedding.model == "nomic-embed-text"
        assert config.embedding.provider == "ollama"
        assert len(config.sources) == 1
        assert config.sources[0].name == "my-skills"
        assert config.sources[0].path == "/home/user/skills"
        assert config.sources[0].include == ["**/*.md"]
        assert config.sources[0].exclude == ["**/node_modules/**"]

    def test_loads_minimal_toml_with_defaults(self, tmp_path: Path) -> None:
        """load_config() applies defaults for missing optional fields."""
        config_path = tmp_path / "corpus.toml"
        config_path.write_text("""
[[sources]]
name = "docs"
path = "/docs"
""")
        config = load_config(config_path)
        assert len(config.sources) == 1
        assert config.sources[0].name == "docs"
        assert config.sources[0].path == "/docs"
        assert config.sources[0].include == ["**/*"]  # default
        assert config.sources[0].exclude == []  # default
        assert config.embedding.model == "nomic-embed-text"  # default

    def test_invalid_toml_raises_validation_error(self, tmp_path: Path) -> None:
        """load_config() raises ValidationError for invalid TOML content."""
        config_path = tmp_path / "corpus.toml"
        # Missing required 'path' field in source
        config_path.write_text("""
[[sources]]
name = "invalid-source"
""")
        with pytest.raises(ValidationError) as exc_info:
            load_config(config_path)
        assert "path" in str(exc_info.value)


# ---------------------------------------------------------------------------
# save_config tests
# ---------------------------------------------------------------------------


class TestSaveConfig:
    """Tests for save_config() function."""

    def test_saves_config_to_file(self, tmp_path: Path) -> None:
        """save_config() writes a valid TOML file."""
        config_path = tmp_path / "corpus.toml"
        config = CorpusConfig(
            embedding=EmbeddingConfig(model="test-model"),
            sources=[SourceConfig(name="test", path="/test")],
        )
        save_config(config_path, config)
        assert config_path.exists()
        content = config_path.read_text()
        assert "model = \"test-model\"" in content
        assert "name = \"test\"" in content
        assert "path = \"/test\"" in content

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """save_config() creates parent directories if they don't exist."""
        nested_path = tmp_path / "nested" / "deep" / "corpus.toml"
        config = CorpusConfig()
        save_config(nested_path, config)
        assert nested_path.exists()

    def test_round_trip_preserves_data(self, tmp_path: Path) -> None:
        """save_config + load_config round-trip preserves all data."""
        config_path = tmp_path / "corpus.toml"
        original = CorpusConfig(
            embedding=EmbeddingConfig(
                model="custom-model",
                provider="custom-provider",
                host="http://custom:8080",
            ),
            sources=[
                SourceConfig(
                    name="src1",
                    path="/path/one",
                    include=["**/*.md", "**/*.py"],
                    exclude=["**/node_modules/**"],
                ),
                SourceConfig(
                    name="src2",
                    path="/path/two",
                    include=["**/*.toml"],
                    exclude=["**/.git/**", "**/.venv/**"],
                ),
            ],
        )
        save_config(config_path, original)
        loaded = load_config(config_path)

        # Check embedding
        assert loaded.embedding.model == "custom-model"
        assert loaded.embedding.provider == "custom-provider"
        assert loaded.embedding.host == "http://custom:8080"

        # Check sources count
        assert len(loaded.sources) == 2

        # Check first source
        assert loaded.sources[0].name == "src1"
        assert loaded.sources[0].path == "/path/one"
        assert loaded.sources[0].include == ["**/*.md", "**/*.py"]
        assert loaded.sources[0].exclude == ["**/node_modules/**"]

        # Check second source
        assert loaded.sources[1].name == "src2"
        assert loaded.sources[1].path == "/path/two"
        assert loaded.sources[1].include == ["**/*.toml"]
        assert loaded.sources[1].exclude == ["**/.git/**", "**/.venv/**"]

    def test_round_trip_empty_sources(self, tmp_path: Path) -> None:
        """save_config + load_config round-trip works with empty sources."""
        config_path = tmp_path / "corpus.toml"
        original = CorpusConfig(sources=[])
        save_config(config_path, original)
        loaded = load_config(config_path)
        assert loaded.sources == []
        assert loaded.embedding.model == "nomic-embed-text"

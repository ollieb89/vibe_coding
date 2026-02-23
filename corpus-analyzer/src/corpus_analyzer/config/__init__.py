"""Configuration package for corpus-analyzer.

Provides Pydantic models for corpus.toml configuration and I/O functions
for loading and saving configuration files.
"""

from pathlib import Path

# Import settings from the renamed settings module
settings_module_path = Path(__file__).parent.parent / "settings.py"
if settings_module_path.exists():
    from corpus_analyzer.settings import settings
else:
    settings = None  # type: ignore[misc]

from corpus_analyzer.config.io import load_config, save_config
from corpus_analyzer.config.schema import CorpusConfig, EmbeddingConfig, SourceConfig

__all__ = [
    "CorpusConfig",
    "EmbeddingConfig",
    "SourceConfig",
    "load_config",
    "save_config",
    "settings",
]

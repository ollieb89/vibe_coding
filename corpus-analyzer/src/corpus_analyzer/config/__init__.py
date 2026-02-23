"""Configuration package for corpus-analyzer."""

from corpus_analyzer.config.io import load_config, save_config
from corpus_analyzer.config.schema import (
    CONFIG_PATH,
    DATA_DIR,
    CorpusConfig,
    EmbeddingConfig,
    SourceConfig,
)
from corpus_analyzer.settings import settings

__all__ = [
    "CONFIG_PATH",
    "DATA_DIR",
    "CorpusConfig",
    "EmbeddingConfig",
    "SourceConfig",
    "load_config",
    "save_config",
    "settings",
]

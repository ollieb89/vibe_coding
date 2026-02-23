"""Configuration I/O for corpus-analyzer.

This module provides functions to load and save the corpus.toml configuration file.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import tomli_w

from corpus_analyzer.config.schema import CorpusConfig


def load_config(path: Path) -> CorpusConfig:
    """Load and validate a corpus.toml configuration file.

    If the file does not exist, returns a CorpusConfig with default values
    and an empty sources list.

    Args:
        path: Path to the corpus.toml file.

    Returns:
        A validated CorpusConfig instance.

    Raises:
        pydantic.ValidationError: If the TOML file contains invalid configuration.
    """
    if not path.exists():
        return CorpusConfig()

    with open(path, "rb") as f:
        data: dict[str, Any] = tomllib.load(f)

    return CorpusConfig.model_validate(data)


def save_config(path: Path, config: CorpusConfig) -> None:
    """Save a CorpusConfig to a TOML file.

    Creates parent directories if they do not exist.

    Args:
        path: Path where the corpus.toml file should be written.
        config: The CorpusConfig instance to save.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    data = config.model_dump()
    with open(path, "wb") as f:
        tomli_w.dump(data, f)

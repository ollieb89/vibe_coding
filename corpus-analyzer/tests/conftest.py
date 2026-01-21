"""Pytest configuration and fixtures."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from corpus_analyzer.core.database import CorpusDatabase


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def sample_markdown(temp_dir: Path) -> Path:
    """Create a sample markdown file."""
    md_file = temp_dir / "sample.md"
    md_file.write_text("""---
title: Sample Document
---

# Sample Document

This is a sample document for testing.

## Overview

Some overview text.

## Steps

1. First step
2. Second step

## Code Example

```python
def hello():
    print("Hello, world!")
```

[Link to docs](https://example.com)
""")
    return md_file


@pytest.fixture
def sample_python(temp_dir: Path) -> Path:
    """Create a sample Python file."""
    py_file = temp_dir / "sample.py"
    py_file.write_text('''"""Sample module for testing."""

import os
from pathlib import Path

import typer


class SampleClass:
    """A sample class."""

    def method(self):
        """A sample method."""
        pass


def sample_function(arg: str) -> str:
    """A sample function."""
    return arg.upper()
''')
    return py_file


@pytest.fixture
def test_db(temp_dir: Path) -> CorpusDatabase:
    """Create a test database."""
    db = CorpusDatabase(temp_dir / "test.sqlite")
    db.initialize()
    return db

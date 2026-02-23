# Coding Conventions

**Analysis Date:** 2026-02-23

## Naming Patterns

**Files:**
- Python modules: `snake_case.py`
  - Examples: `document_type.py`, `domain_tags.py`, `chunked_processor.py`
- Test files: `test_*.py`
  - Examples: `test_document_type.py`, `test_extractors/test_python.py`
- Package directories: `snake_case/`
  - Examples: `classifiers/`, `extractors/`, `core/`

**Functions:**
- Module-level functions: `snake_case`
  - Examples: `extract_document_features()`, `classify_document()`, `detect_domain_tags()`
  - Private functions: prefix with `_`
  - Examples: `_extract_imports()`, `_extract_symbols()`, `_generate_title()`

**Variables:**
- Local variables: `snake_case`
  - Examples: `doc_path`, `content_hash`, `category_patterns`, `token_estimate`
- Constants: `UPPER_CASE`
  - Examples: `CLASSIFICATION_RULES`, `DOMAIN_PATTERNS`, `CLI_INDICATORS`
- Instance variables: `snake_case`
  - Examples: `self.path`, `self.db`, `self.content`

**Types:**
- Classes: `PascalCase`
  - Examples: `Document`, `DocumentCategory`, `ClassificationResult`, `BaseExtractor`
- Enums: `PascalCase` with `UPPER_CASE` members
  - Example: `class DocumentCategory(str, Enum)` with members like `PERSONA = "persona"`
- NamedTuple: `PascalCase`
  - Example: `class ClassificationResult(NamedTuple)`

## Code Style

**Formatting:**
- Tool: `ruff` (integrated linter/formatter)
- Line length: 100 characters
- Python version: 3.12 (strict)

**Linting:**
- Tool: `ruff` with strict configuration
- Active rule sets:
  - `E` (Pycodestyle errors)
  - `F` (Pyflakes)
  - `I` (isort import sorting)
  - `N` (Pep8 naming)
  - `W` (Pycodestyle warnings)
  - `UP` (Pyupgrade)
  - `B` (Flake8 bugbear)
  - `C4` (Flake8 comprehensions)
  - `SIM` (Flake8 simplify)
- Config: `pyproject.toml` [tool.ruff] and [tool.ruff.lint]

**Type Checking:**
- Tool: `mypy` with strict mode enabled
- Python version: 3.12
- Strict settings: All files subject to strict type checking
- Warnings enforced:
  - `warn_return_any = true` - Catches untyped returns
  - `warn_unused_ignores = true` - Prevents orphaned type ignores

## Import Organization

**Order:**
1. Standard library imports (`pathlib`, `datetime`, `json`, `logging`, etc.)
2. Third-party imports (`pydantic`, `typer`, `rich`, `sqlite_utils`, etc.)
3. Local application imports (from `corpus_analyzer.*`)

**Examples from codebase:**
```python
# Standard library first
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Iterator

# Third-party
import sqlite_utils
from pydantic import BaseModel, Field
from rich.console import Console

# Local imports
from corpus_analyzer.core.database import CorpusDatabase
from corpus_analyzer.core.models import Document, DocumentCategory
```

**Path Aliases:**
- No path aliases configured (absolute imports only)
- All imports use `corpus_analyzer.*` prefix from `src/` location

**Import Rules:**
- Use `from module import specific_name` for clarity
- Avoid wildcard imports (`import *`)
- Import classes/functions, not modules when possible
- Example: `from corpus_analyzer.core.models import Document` not `from corpus_analyzer.core import models`

## Error Handling

**Patterns:**
- Graceful fallback on exceptions, not re-raise
  - Example in `src/corpus_analyzer/classifiers/document_type.py:290-295`:
    ```python
    def read_document_content(doc_path: Path) -> str:
        """Read full document content for enhanced analysis."""
        try:
            return doc_path.read_text(encoding="utf-8")
        except Exception:
            return ""
    ```
  - Example in `src/corpus_analyzer/extractors/python.py:30-42`: Returns minimal Document on SyntaxError
- Generic `Exception` catching for non-critical operations
- Specific exception handling for CLI operations (e.g., `FileNotFoundError`, `typer.Exit()`)
- Logging exceptions with `logger.exception()` for important operations

## Logging

**Framework:** Python standard `logging` module

**Patterns:**
- Module-level logger: `logger = logging.getLogger(__name__)`
- Used in: `src/corpus_analyzer/generators/advanced_rewriter.py`, `src/corpus_analyzer/llm/unified_rewriter.py`, `src/corpus_analyzer/analyzers/quality.py`
- Log levels used:
  - `logger.info()` - Informational messages (e.g., "Marked X as gold standard")
  - `logger.exception()` - Error with traceback (e.g., "Failed to rewrite document X")
- No custom logging configuration; relies on application setup

## Comments

**When to Comment:**
- Comments explain "why", not "what" the code does
- Docstrings required for all public functions/classes
- Inline comments for complex logic sections
- TODO/FIXME used sparingly (found 2 instances in codebase):
  - `src/corpus_analyzer/generators/advanced_rewriter.py`: `# TODO: Add timestamp`
  - `src/corpus_analyzer/generators/templates.py`: `<!-- TODO: Add {section_title} content -->`

**JSDoc/TSDoc:**
- Using Python docstrings (not JSDoc)
- Style: Triple-quoted docstrings at function/class start
- Content: Brief description, Args section, Returns section
- Examples:
  ```python
  def extract(self, file_path: Path, root: Path) -> Document:
      """
      Extract document metadata and content.

      Args:
          file_path: Absolute path to the file
          root: Root directory for relative path calculation

      Returns:
          Extracted Document model
      """
  ```

## Function Design

**Size:** Functions generally 20-50 lines
- Shorter functions for extractors and filters
- Longer functions (80+ lines) reserved for complex classification logic with multiple passes
- Example: `classify_document()` at 95 lines handles multi-stage scoring

**Parameters:**
- Use type hints on all parameters: `param_name: Type`
- Use `Optional[Type]` for nullable parameters
- Use `|` union syntax for Python 3.12+: `Type1 | Type2`
- Avoid mutable defaults; use `field(default_factory=...)` for dataclasses

**Return Values:**
- Always include return type hint: `-> Type`
- Return `None` explicitly: `-> None`
- Prefer returning data models (Pydantic models, NamedTuples) over dicts
- Examples:
  - `compute_tfidf_similarity() -> dict[DocumentCategory, float]`
  - `classify_document() -> ClassificationResult` (NamedTuple)
  - `detect_domain_tags() -> list[DomainTag]`

## Module Design

**Exports:**
- Explicit imports, no barrel files for private modules
- Public APIs exposed through `__init__.py` files
- Example: `src/corpus_analyzer/core/__init__.py`:
  ```python
  from corpus_analyzer.core.database import CorpusDatabase
  from corpus_analyzer.core.models import Chunk, Document, DocumentCategory, DomainTag
  from corpus_analyzer.core.scanner import scan_directory
  ```

**Barrel Files:**
- Used selectively for public module groups
- Location: `src/corpus_analyzer/core/__init__.py`, `src/corpus_analyzer/extractors/__init__.py`, etc.
- Purpose: Expose main classes/functions for easier imports

**Dataclass vs Pydantic:**
- Pydantic `BaseModel` for data validation: `Document`, `DocumentCategory`, `CodeBlock`, `Heading`
- `@dataclass` for internal structures with no validation: `DocumentFeatures`
- `NamedTuple` for immutable result objects: `ClassificationResult`

**Type Hints:**
- Mandatory on all functions (enforced by mypy strict mode)
- Use `Optional[T]` or `T | None` for nullable types
- Collection types with type parameters: `list[Type]`, `dict[Key, Value]`
- Generic type aliases used: `Iterator[Type]`

---

*Convention analysis: 2026-02-23*

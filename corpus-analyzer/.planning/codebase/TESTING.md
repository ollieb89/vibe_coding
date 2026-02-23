# Testing Patterns

**Analysis Date:** 2026-02-23

## Test Framework

**Runner:**
- `pytest` 8.0.0+ (defined in `pyproject.toml`)
- Config: `pyproject.toml` [tool.pytest.ini_options]
- Test discovery: searches `tests/` directory
- Python path setup: `pythonpath = ["src"]` for imports

**Assertion Library:**
- Standard `assert` statements (no custom assertion library)
- Examples: `assert result.category == DocumentCategory.HOWTO`, `assert result.confidence > 0.3`

**Run Commands:**
```bash
pytest tests/                          # Run all tests
pytest tests/ -v                       # Verbose output
pytest tests/ --cov                    # Run with coverage report
pytest tests/ -k test_name             # Run specific test by name
pytest tests/test_classifiers/ -v      # Run tests in specific directory
```

## Test File Organization

**Location:**
- Parallel structure: `/tests/` mirrors `/src/corpus_analyzer/`
- Directory structure:
  ```
  tests/
  ├── conftest.py                  # Shared fixtures
  ├── test_classifiers/            # Tests for classifiers module
  ├── test_extractors/             # Tests for extractors module
  ├── test_core/                   # Tests for core module
  ├── llm/                         # Tests for llm module
  ├── test_analyzers/              # Tests for analyzers module
  ```

**Naming:**
- Test files: `test_*.py` prefix
- Test functions: `test_` prefix
- Test classes: `Test` prefix (if grouping tests in classes, though not common in codebase)

**Structure:**
- One test file per module being tested
- Examples:
  - `tests/test_classifiers/test_document_type.py` → tests `src/corpus_analyzer/classifiers/document_type.py`
  - `tests/test_extractors/test_python.py` → tests `src/corpus_analyzer/extractors/python.py`
  - `tests/llm/test_chunking.py` → tests `src/corpus_analyzer/llm/chunked_processor.py`

## Test Structure

**Suite Organization:**
```python
"""Tests for document type classifier."""

from datetime import datetime
from pathlib import Path

from corpus_analyzer.classifiers.document_type import classify_document
from corpus_analyzer.core.models import Document, DocumentCategory, Heading


def test_classify_howto():
    """Test classification of how-to documents."""
    # Setup
    doc = Document(
        path=Path("/test/howto.md"),
        relative_path="howto.md",
        file_type="md",
        title="How to Set Up Development Environment",
        mtime=datetime.now(),
        size_bytes=1000,
        headings=[
            Heading(level=1, text="How to Set Up Development Environment", line_number=1),
            Heading(level=2, text="Steps", line_number=5),
            Heading(level=2, text="Prerequisites", line_number=10),
        ],
    )

    # Execute
    result = classify_document(doc)

    # Assert
    assert result.category == DocumentCategory.HOWTO
    assert result.confidence > 0.3
```

**Patterns:**
- **Setup pattern:** Create test data in test function (no complex setup methods)
  - Use fixtures from `conftest.py` for common data
  - Example: `sample_markdown`, `sample_python`, `test_db`, `temp_dir`
- **Teardown pattern:** Automatic via pytest fixtures with context managers
  - Example: `TemporaryDirectory` in `temp_dir` fixture auto-cleans up
- **Assertion pattern:** Direct assertions with comparison operators
  - Assert expected value: `assert result.category == DocumentCategory.HOWTO`
  - Assert numeric ranges: `assert result.confidence > 0.3`
  - Assert collection contents: `assert "os" in doc.imports`
  - Assert existence: `assert len(doc.headings) == 4`

## Mocking

**Framework:** Not actively used in current codebase
- Tests use real objects created inline
- No `unittest.mock` imports found in test files
- Real file I/O used with `TemporaryDirectory` fixture

**Patterns:**
- Create test fixtures with actual data structures
- Example from `tests/conftest.py`:
  ```python
  @pytest.fixture
  def sample_markdown(temp_dir: Path) -> Path:
      """Create a sample markdown file."""
      md_file = temp_dir / "sample.md"
      md_file.write_text("""---
  title: Sample Document
  ---

  # Sample Document
  ...
  """)
      return md_file
  ```

**What to Mock:**
- Nothing currently mocked; real objects preferred
- Tests create minimal Document/Document models with only required fields

**What NOT to Mock:**
- File I/O (use `TemporaryDirectory` instead)
- Model instantiation (create real Pydantic models)
- Database operations (use in-memory test database)

## Fixtures and Factories

**Test Data:**
Located in `tests/conftest.py`:

```python
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
...
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
```

**Location:**
- Centralized in `tests/conftest.py`
- Fixtures available to all test modules
- Scoped appropriately (function scope by default)

**Fixture Patterns:**
- Use `@pytest.fixture` decorator
- Return concrete objects, not factories
- Example: `sample_markdown` returns `Path` to created file
- Clean up via context managers: `with TemporaryDirectory() as tmp: yield Path(tmp)`

## Coverage

**Requirements:** Not explicitly enforced
- Coverage tool available: `pytest-cov>=4.1.0`
- No minimum coverage threshold configured in `pyproject.toml`
- Config supports coverage but not strictly required

**View Coverage:**
```bash
pytest tests/ --cov=corpus_analyzer --cov-report=html
pytest tests/ --cov=corpus_analyzer --cov-report=term
```

## Test Types

**Unit Tests:**
- **Scope:** Individual functions/classes in isolation
- **Approach:** Create minimal test data, call function, assert output
- **Examples:**
  - `tests/test_classifiers/test_document_type.py`: Tests classification logic
  - `tests/test_extractors/test_python.py`: Tests Python AST extraction
  - `tests/test_extractors/test_markdown.py`: Tests markdown parsing
- **Pattern:**
  ```python
  def test_extract_module_docstring(sample_python: Path, temp_dir: Path):
      """Test module docstring extraction."""
      extractor = PythonExtractor()
      doc = extractor.extract(sample_python, temp_dir)
      assert doc.module_docstring == "Sample module for testing."
  ```

**Integration Tests:**
- **Scope:** Multiple components working together
- **Examples:**
  - `tests/test_core/test_db_migration.py`: Tests database operations
  - `tests/test_core/test_enhanced_db.py`: Tests database with document insertion
  - `tests/llm/test_rewriter_quality.py`: Tests LLM processing pipeline
- **Pattern:** Involves real database, extractors, and classifiers in sequence

**E2E Tests:**
- **Framework:** Not currently implemented
- **Status:** Not required for this codebase
- **Potential candidate:** CLI testing with real file system operations

## Common Patterns

**Async Testing:**
- Not currently used in tests
- No async functions in test suite
- All operations are synchronous

**Error Testing:**
```python
def test_classify_unknown():
    """Test classification of unclassifiable documents."""
    doc = Document(
        path=Path("/test/notes.md"),
        relative_path="notes.md",
        file_type="md",
        title="Random Notes",
        mtime=datetime.now(),
        size_bytes=200,
        headings=[],
    )

    result = classify_document(doc)
    assert result.category == DocumentCategory.UNKNOWN
```

**Parameterized Tests:**
- Not currently used
- Could use `@pytest.mark.parametrize()` for testing multiple inputs
- Example: Test classification for multiple document types with single test function

**Test Isolation:**
- Each test is independent
- Fixtures create isolated temporary directories
- Database tests use separate `test.sqlite` file per test
- No shared state between tests

---

*Testing analysis: 2026-02-23*

"""Tests for Python extractor."""

from pathlib import Path

from corpus_analyzer.extractors.python import PythonExtractor


def test_extract_module_docstring(sample_python: Path, temp_dir: Path):
    """Test module docstring extraction."""
    extractor = PythonExtractor()
    doc = extractor.extract(sample_python, temp_dir)
    assert doc.module_docstring == "Sample module for testing."


def test_extract_imports(sample_python: Path, temp_dir: Path):
    """Test import extraction."""
    extractor = PythonExtractor()
    doc = extractor.extract(sample_python, temp_dir)

    assert "os" in doc.imports
    assert "pathlib" in doc.imports
    assert "typer" in doc.imports


def test_detect_cli(sample_python: Path, temp_dir: Path):
    """Test CLI detection."""
    extractor = PythonExtractor()
    doc = extractor.extract(sample_python, temp_dir)

    # Should detect typer as CLI framework
    assert doc.is_cli is True


def test_extract_symbols(sample_python: Path, temp_dir: Path):
    """Test class and function extraction."""
    extractor = PythonExtractor()
    doc = extractor.extract(sample_python, temp_dir)

    symbol_names = [s.name for s in doc.symbols]
    assert "SampleClass" in symbol_names
    assert "sample_function" in symbol_names
    assert "SampleClass.method" in symbol_names


def test_extract_symbol_docstrings(sample_python: Path, temp_dir: Path):
    """Test docstring extraction for symbols."""
    extractor = PythonExtractor()
    doc = extractor.extract(sample_python, temp_dir)

    class_symbol = next(s for s in doc.symbols if s.name == "SampleClass")
    assert class_symbol.docstring == "A sample class."

    func_symbol = next(s for s in doc.symbols if s.name == "sample_function")
    assert func_symbol.docstring == "A sample function."

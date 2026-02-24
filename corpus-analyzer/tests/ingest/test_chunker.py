"""Tests for corpus_analyzer.ingest.chunker — Document chunking functions.

Follows RED-GREEN-REFACTOR TDD cycle.
Uses inline fixture strings written to tmp_path for Path-based API.
"""

from pathlib import Path

from corpus_analyzer.ingest.chunker import (
    chunk_file,
    chunk_lines,
    chunk_markdown,
    chunk_python,
)

# ---------------------------------------------------------------------------
# chunk_markdown tests
# ---------------------------------------------------------------------------


class TestChunkMarkdown:
    """Tests for chunk_markdown function."""

    def test_splits_on_atx_headings(self, tmp_path: Path) -> None:
        r"""chunk_markdown splits on ATX headings (^#{1,6}\s)."""
        md_file = tmp_path / "test.md"
        md_file.write_text("""# Heading 1
Content under heading 1.
More content.

## Heading 2
Content under heading 2.

### Heading 3
Final content.
""")
        chunks = chunk_markdown(md_file)

        assert len(chunks) >= 3
        assert chunks[0]["text"].startswith("# Heading 1")
        assert chunks[1]["text"].startswith("## Heading 2")
        assert chunks[2]["text"].startswith("### Heading 3")

    def test_includes_line_ranges(self, tmp_path: Path) -> None:
        """Each chunk has correct start_line and end_line (1-indexed)."""
        md_file = tmp_path / "test.md"
        md_file.write_text("""# First
Line 2
Line 3

## Second
Line 5
""")
        chunks = chunk_markdown(md_file)

        assert chunks[0]["start_line"] == 1
        assert chunks[0]["end_line"] == 4  # Includes blank line before next heading
        assert chunks[1]["start_line"] == 5
        assert chunks[1]["end_line"] == 7  # End of file

    def test_content_before_first_heading(self, tmp_path: Path) -> None:
        """First chunk includes content before first heading if present."""
        md_file = tmp_path / "test.md"
        md_file.write_text("""Preamble text here.

# First Heading
Content.
""")
        chunks = chunk_markdown(md_file)

        assert chunks[0]["text"].startswith("Preamble text here.")
        assert "# First Heading" in chunks[0]["text"]

    def test_no_headings_single_chunk(self, tmp_path: Path) -> None:
        """File with no headings returns single chunk with all content."""
        md_file = tmp_path / "test.md"
        md_file.write_text("""Just some text.
More text here.
Final line.
""")
        chunks = chunk_markdown(md_file)

        assert len(chunks) == 1
        assert chunks[0]["start_line"] == 1
        assert "Just some text." in chunks[0]["text"]
        assert "Final line." in chunks[0]["text"]

    def test_large_section_subsplit(self, tmp_path: Path) -> None:
        """Heading section exceeding max_words is sub-split with chunk_lines."""
        md_file = tmp_path / "test.md"
        # Create a large section with many short lines (each word is a line to exceed count)
        large_content = "# Large Section\n" + "word\n" * 600  # 600 words
        md_file.write_text(large_content)

        chunks = chunk_markdown(md_file, max_words=100)

        # Should have multiple chunks from sub-splitting
        assert len(chunks) > 1
        # First chunk should still start with the heading
        assert chunks[0]["text"].startswith("# Large Section")


# ---------------------------------------------------------------------------
# chunk_python tests
# ---------------------------------------------------------------------------


class TestChunkPython:
    """Tests for chunk_python function."""

    def test_top_level_functions(self, tmp_path: Path) -> None:
        """chunk_python returns one chunk per top-level function."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""def first_func():
    pass

class MyClass:
    pass

def second_func():
    return 42
""")
        chunks = chunk_python(py_file)

        assert len(chunks) == 3
        assert "def first_func():" in chunks[0]["text"]
        assert "class MyClass:" in chunks[1]["text"]
        assert "def second_func():" in chunks[2]["text"]

    def test_nested_not_separate(self, tmp_path: Path) -> None:
        """Nested functions inside classes are NOT separate chunks."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""class Outer:
    def method(self):
        def nested():
            pass
        return nested()
""")
        chunks = chunk_python(py_file)

        # Only one chunk for the class
        assert len(chunks) == 1
        assert "class Outer:" in chunks[0]["text"]

    def test_async_functions(self, tmp_path: Path) -> None:
        """chunk_python includes async functions as top-level chunks."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""async def async_func():
    await something()

def regular_func():
    pass
""")
        chunks = chunk_python(py_file)

        assert len(chunks) == 2
        assert "async def async_func():" in chunks[0]["text"]
        assert "def regular_func():" in chunks[1]["text"]

    def test_line_ranges_correct(self, tmp_path: Path) -> None:
        """Each chunk has correct start_line and end_line."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""# Comment line
def first():
    pass

# Another comment
class Second:
    pass
""")
        chunks = chunk_python(py_file)

        assert chunks[0]["start_line"] == 2  # def first()
        assert chunks[0]["end_line"] == 5   # includes blank/comments before next def
        assert chunks[1]["start_line"] == 6  # class Second
        assert chunks[1]["end_line"] == 7   # ends at pass

    def test_no_top_level_fallback(self, tmp_path: Path) -> None:
        """File with no top-level defs falls back to chunk_lines."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""# Just a comment
x = 1
y = 2
z = 3
""")
        chunks = chunk_python(py_file)

        # Should use chunk_lines fallback
        assert len(chunks) >= 1
        assert all("start_line" in c and "end_line" in c for c in chunks)


# ---------------------------------------------------------------------------
# chunk_lines tests
# ---------------------------------------------------------------------------


class TestChunkLines:
    """Tests for chunk_lines function."""

    def test_window_and_overlap(self, tmp_path: Path) -> None:
        """chunk_lines creates overlapping windows correctly."""
        txt_file = tmp_path / "test.txt"
        # 120 lines
        txt_file.write_text("\n".join(f"Line {i}" for i in range(1, 121)))

        chunks = chunk_lines(txt_file, window=50, overlap=10)

        # Window 50, overlap 10 -> step 40
        # Chunks: 1-50, 41-90, 81-120
        assert len(chunks) == 3
        assert chunks[0]["start_line"] == 1
        assert chunks[0]["end_line"] == 50
        assert chunks[1]["start_line"] == 41
        assert chunks[1]["end_line"] == 90
        assert chunks[2]["start_line"] == 81
        assert chunks[2]["end_line"] == 120

    def test_text_content_includes_lines(self, tmp_path: Path) -> None:
        """Each chunk's text includes the correct line range."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5")

        chunks = chunk_lines(txt_file, window=3, overlap=1)

        assert len(chunks) == 2
        assert "Line 1" in chunks[0]["text"]
        assert "Line 3" in chunks[0]["text"]
        assert "Line 3" in chunks[1]["text"]
        assert "Line 5" in chunks[1]["text"]

    def test_small_file_single_chunk(self, tmp_path: Path) -> None:
        """Small file produces single chunk."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Line 1\nLine 2")

        chunks = chunk_lines(txt_file, window=50, overlap=10)

        assert len(chunks) == 1
        assert chunks[0]["start_line"] == 1
        assert chunks[0]["end_line"] == 2


# ---------------------------------------------------------------------------
# chunk_file dispatcher tests
# ---------------------------------------------------------------------------


class TestChunkFile:
    """Tests for chunk_file dispatcher function."""

    def test_dispatches_md_to_chunk_markdown(self, tmp_path: Path) -> None:
        """chunk_file(".md") calls chunk_markdown."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Heading\nContent.")

        chunks = chunk_file(md_file)

        assert len(chunks) == 1
        assert "# Heading" in chunks[0]["text"]

    def test_dispatches_py_to_chunk_python(self, tmp_path: Path) -> None:
        """chunk_file(".py") calls chunk_python."""
        py_file = tmp_path / "test.py"
        py_file.write_text("def func():\n    pass\n")

        chunks = chunk_file(py_file)

        assert len(chunks) == 1
        assert "def func():" in chunks[0]["text"]

    def test_dispatches_other_to_chunk_lines(self, tmp_path: Path) -> None:
        """chunk_file(".ts", ".js", ".json", etc.) calls chunk_lines."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("const x = 1;\nconst y = 2;\n")

        chunks = chunk_file(ts_file)

        assert len(chunks) >= 1
        assert all("start_line" in c and "end_line" in c for c in chunks)

    def test_yaml_uses_chunk_lines(self, tmp_path: Path) -> None:
        """chunk_file(".yaml") uses chunk_lines fallback."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("key: value\nlist:\n  - item1\n  - item2\n")

        chunks = chunk_file(yaml_file)

        assert len(chunks) >= 1
        assert "key: value" in chunks[0]["text"]

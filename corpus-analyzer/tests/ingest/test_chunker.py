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
from corpus_analyzer.ingest.ts_chunker import chunk_typescript

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
# chunk_typescript tests
# ---------------------------------------------------------------------------


class TestChunkTypeScript:
    """Tests for chunk_typescript function (TDD RED phase — 15-01)."""

    def test_function_extraction(self, tmp_path: Path) -> None:
        """Plain function declaration yields one chunk with correct chunk_name and start_line."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("function foo(): void {\n  console.log('hi');\n}\n")

        chunks = chunk_typescript(ts_file)

        assert len(chunks) == 1
        assert chunks[0]["chunk_name"] == "foo"
        assert chunks[0]["start_line"] == 1

    def test_generator_extraction(self, tmp_path: Path) -> None:
        """Generator function yields chunk with correct chunk_name."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text(
            "function* gen(): Generator<number, void, void> {\n  yield 1;\n}\n"
        )

        chunks = chunk_typescript(ts_file)

        assert any(c["chunk_name"] == "gen" for c in chunks)

    def test_class_extraction(self, tmp_path: Path) -> None:
        """Class declaration yields chunk with correct chunk_name."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("class Bar {\n  x = 1;\n}\n")

        chunks = chunk_typescript(ts_file)

        assert any(c["chunk_name"] == "Bar" for c in chunks)

    def test_abstract_class_extraction(self, tmp_path: Path) -> None:
        """Abstract class yields chunk with correct chunk_name."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("abstract class Abs {\n  abstract method(): void;\n}\n")

        chunks = chunk_typescript(ts_file)

        assert any(c["chunk_name"] == "Abs" for c in chunks)

    def test_interface_extraction(self, tmp_path: Path) -> None:
        """Interface declaration yields chunk with correct chunk_name."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("interface IFoo {\n  x: number;\n}\n")

        chunks = chunk_typescript(ts_file)

        assert any(c["chunk_name"] == "IFoo" for c in chunks)

    def test_type_alias_extraction(self, tmp_path: Path) -> None:
        """Type alias yields chunk with correct chunk_name."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("type Alias = string | number;\n")

        chunks = chunk_typescript(ts_file)

        assert any(c["chunk_name"] == "Alias" for c in chunks)

    def test_lexical_declaration_extraction(self, tmp_path: Path) -> None:
        """Arrow function in const declaration yields chunk_name matching variable name."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("const fn = (): void => {};\n")

        chunks = chunk_typescript(ts_file)

        assert any(c["chunk_name"] == "fn" for c in chunks)

    def test_enum_extraction(self, tmp_path: Path) -> None:
        """Enum declaration yields chunk with correct chunk_name."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("enum Color {\n  Red,\n  Green,\n  Blue,\n}\n")

        chunks = chunk_typescript(ts_file)

        assert any(c["chunk_name"] == "Color" for c in chunks)

    def test_export_function_unwrapping(self, tmp_path: Path) -> None:
        """Exported function preserves 'export' in text and uses bare name as chunk_name."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("export function foo(): void {}\n")

        chunks = chunk_typescript(ts_file)

        assert len(chunks) == 1
        assert "export function foo" in chunks[0]["text"]
        assert chunks[0]["chunk_name"] == "foo"

    def test_export_class_unwrapping(self, tmp_path: Path) -> None:
        """Exported class preserves 'export' in text and uses bare name as chunk_name."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("export class Bar {}\n")

        chunks = chunk_typescript(ts_file)

        assert "export class Bar" in chunks[0]["text"]
        assert chunks[0]["chunk_name"] == "Bar"

    def test_export_default_function(self, tmp_path: Path) -> None:
        """export default function() yields chunk_name 'default'."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("export default function(): void {}\n")

        chunks = chunk_typescript(ts_file)

        assert any(c["chunk_name"] == "default" for c in chunks)

    def test_line_range_accuracy(self, tmp_path: Path) -> None:
        """Function on line 3 (after two comment lines) has start_line == 3."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("// line 1\n// line 2\nfunction foo(): void {}\n")

        chunks = chunk_typescript(ts_file)

        foo_chunks = [c for c in chunks if c.get("chunk_name") == "foo"]
        assert len(foo_chunks) == 1
        assert foo_chunks[0]["start_line"] == 3

    def test_jsdoc_included(self, tmp_path: Path) -> None:
        """JSDoc comment immediately preceding declaration is included; start_line is doc line."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("/** JSDoc comment */\nfunction foo(): void {}\n")

        chunks = chunk_typescript(ts_file)

        foo_chunks = [c for c in chunks if c.get("chunk_name") == "foo"]
        assert len(foo_chunks) == 1
        assert foo_chunks[0]["start_line"] == 1
        assert "/** JSDoc comment */" in foo_chunks[0]["text"]

    def test_single_line_comment_not_included(self, tmp_path: Path) -> None:
        """Single-line // comment before declaration is NOT included.

        start_line is the function declaration line, not the comment line.
        """
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("// not jsdoc\nfunction foo(): void {}\n")

        chunks = chunk_typescript(ts_file)

        foo_chunks = [c for c in chunks if c.get("chunk_name") == "foo"]
        assert len(foo_chunks) == 1
        assert foo_chunks[0]["start_line"] == 2
        assert "// not jsdoc" not in foo_chunks[0]["text"]

    def test_jsdoc_blank_line_not_included(self, tmp_path: Path) -> None:
        """JSDoc with blank line between it and declaration is NOT included."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("/** doc */\n\nfunction foo(): void {}\n")

        chunks = chunk_typescript(ts_file)

        foo_chunks = [c for c in chunks if c.get("chunk_name") == "foo"]
        assert len(foo_chunks) == 1
        assert foo_chunks[0]["start_line"] == 3

    def test_jsx_in_tsx_parses(self, tmp_path: Path) -> None:
        """JSX syntax in .tsx file parses without fallback; returns named chunk."""
        tsx_file = tmp_path / "test.tsx"
        tsx_file.write_text("const el = (): JSX.Element => <div />;\n")

        chunks = chunk_typescript(tsx_file)

        assert any(c["chunk_name"] == "el" for c in chunks)

    def test_jsx_in_jsx_parses(self, tmp_path: Path) -> None:
        """JSX syntax in .jsx file parses without fallback; returns named chunk."""
        jsx_file = tmp_path / "test.jsx"
        jsx_file.write_text("const el = (): JSX.Element => <div />;\n")

        chunks = chunk_typescript(jsx_file)

        assert any(c["chunk_name"] == "el" for c in chunks)

    def test_non_ascii_identifier(self, tmp_path: Path) -> None:
        """Non-ASCII identifier in function name is extracted correctly."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("function héllo(): void {}\n")

        chunks = chunk_typescript(ts_file)

        assert any(c["chunk_name"] == "héllo" for c in chunks)

    def test_has_error_does_not_fall_back(self, tmp_path: Path) -> None:
        """Partial parse (valid + invalid syntax) does NOT fall back; extracts good constructs."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("function good(): void {}\n@@@@invalid@@@@\n")

        chunks = chunk_typescript(ts_file)

        assert any(c["chunk_name"] == "good" for c in chunks)

    def test_catastrophic_failure_falls_back(self, tmp_path: Path) -> None:
        """Binary / undecodable file falls back gracefully; returns list without raising."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_bytes(b"\x00\x01\x02\x03" * 100)

        result = chunk_typescript(ts_file)

        assert isinstance(result, list)

    def test_chunk_name_field_present(self, tmp_path: Path) -> None:
        """Every chunk dict returned by chunk_typescript has a 'chunk_name' key."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("function foo(): void {}\nconst x = 1;\n")

        chunks = chunk_typescript(ts_file)

        assert all("chunk_name" in c for c in chunks)

    def test_parser_cache(self, tmp_path: Path) -> None:
        """Calling chunk_typescript twice on .ts files produces no cache-related crash."""
        ts_file1 = tmp_path / "a.ts"
        ts_file1.write_text("function alpha(): void {}\n")
        ts_file2 = tmp_path / "b.ts"
        ts_file2.write_text("function beta(): void {}\n")

        result1 = chunk_typescript(ts_file1)
        result2 = chunk_typescript(ts_file2)

        assert isinstance(result1, list)
        assert isinstance(result2, list)

    def test_large_file_falls_back_to_chunk_lines(self, tmp_path: Path) -> None:
        """Files exceeding 50,000 characters skip AST parse and fall back to chunk_lines."""
        ts_file = tmp_path / "test.ts"
        # 50,001 chars — just above the threshold
        ts_file.write_text("x" * 50_001)

        chunks = chunk_typescript(ts_file)

        # chunk_lines output has no chunk_name field; AST path would have chunk_name
        assert isinstance(chunks, list)
        assert all("chunk_name" not in c for c in chunks)

    def test_import_error_falls_back_to_chunk_lines(self, tmp_path: Path) -> None:
        """chunk_typescript falls back to chunk_lines when tree-sitter is not installed."""
        from unittest.mock import patch

        ts_file = tmp_path / "test.ts"
        ts_file.write_text("function foo(): void {}\n")

        with patch(
            "corpus_analyzer.ingest.ts_chunker._get_cached_parser",
            side_effect=ImportError("No module named 'tree_sitter'"),
        ):
            result = chunk_typescript(ts_file)

        assert isinstance(result, list)
        assert len(result) > 0
        assert all("chunk_name" not in c for c in result)


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

    def test_dispatches_ts_to_chunk_typescript(self, tmp_path: Path) -> None:
        """chunk_file(".ts") routes to chunk_typescript, not chunk_lines (AST-based)."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("function foo(): void {}\n")

        chunks = chunk_file(ts_file)

        assert any("foo" in c.get("chunk_name", "") for c in chunks)

    def test_dispatches_tsx_to_chunk_typescript(self, tmp_path: Path) -> None:
        """chunk_file(".tsx") routes to chunk_typescript."""
        tsx_file = tmp_path / "test.tsx"
        tsx_file.write_text("function bar(): void {}\n")

        chunks = chunk_file(tsx_file)

        assert any("bar" in c.get("chunk_name", "") for c in chunks)

    def test_dispatches_js_to_chunk_typescript(self, tmp_path: Path) -> None:
        """chunk_file(".js") routes to chunk_typescript."""
        js_file = tmp_path / "test.js"
        js_file.write_text("function baz(): void {}\n")

        chunks = chunk_file(js_file)

        assert any("baz" in c.get("chunk_name", "") for c in chunks)

    def test_dispatches_jsx_to_chunk_typescript(self, tmp_path: Path) -> None:
        """chunk_file(".jsx") routes to chunk_typescript."""
        jsx_file = tmp_path / "test.jsx"
        jsx_file.write_text("function qux(): void {}\n")

        chunks = chunk_file(jsx_file)

        assert any("qux" in c.get("chunk_name", "") for c in chunks)

    def test_yaml_uses_chunk_lines(self, tmp_path: Path) -> None:
        """chunk_file(".yaml") uses chunk_lines fallback."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("key: value\nlist:\n  - item1\n  - item2\n")

        chunks = chunk_file(yaml_file)

        assert len(chunks) >= 1
        assert "key: value" in chunks[0]["text"]

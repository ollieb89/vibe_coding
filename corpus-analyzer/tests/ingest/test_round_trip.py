"""Round-trip integration tests for ChunkRecord v4 fields.

Parametrised across Markdown, Python, and TypeScript fixtures.
All tests in this module are RED until Phase 17-02 implements the v4 fields.
"""

from pathlib import Path

import pytest

from corpus_analyzer.config.schema import SourceConfig
from corpus_analyzer.ingest.indexer import CorpusIndex


class MockEmbedder:
    """Minimal mock OllamaEmbedder for round-trip tests."""

    model = "test-model"

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return fixed 768-dim zero vectors."""
        return [[0.0] * 768 for _ in texts]


@pytest.mark.parametrize(
    "fixture_type,content,expected_chunk_name,expected_start_line,expected_chunk_text_prefix",
    [
        (
            ".md",
            "# Section One\n\nSome body text here.\n\n## Section Two\n\nMore content.\n",
            "# Section One",
            1,
            "# Section One",
        ),
        (
            ".py",
            "def greet(name: str) -> str:\n    \"\"\"Greet.\"\"\"\n    return f'Hello {name}'\n",
            "greet",
            1,
            "def greet",
        ),
        (
            ".ts",
            "export function hello(name: string): string {\n    return `Hello ${name}`;\n}\n",
            "hello",
            1,
            "export function hello",
        ),
        (
            ".py",
            (
                "class Greeter:\n"
                '    """A greeter class."""\n'
                "\n"
                "    def __init__(self, name: str) -> None:\n"
                "        self.name = name\n"
                "\n"
                "    def greet(self) -> str:\n"
                '        return f"Hello, {self.name}"\n'
            ),
            "Greeter.__init__",
            4,
            "    def __init__",
        ),
        (
            ".ts",
            (
                "export class Greeter {\n"
                "    constructor(private name: string) {}\n"
                "    greet(): string {\n"
                "        return `Hello, ${this.name}`;\n"
                "    }\n"
                "}\n"
            ),
            "Greeter.constructor",
            2,
            "    constructor",
        ),
    ],
)
def test_round_trip_chunk_fields(
    tmp_path: Path,
    fixture_type: str,
    content: str,
    expected_chunk_name: str,
    expected_start_line: int,
    expected_chunk_text_prefix: str,
) -> None:
    """Index a synthetic file and assert v4 fields are stored in LanceDB.

    This test WILL FAIL (RED) until Phase 17-02 implements chunk_name and
    chunk_text emission in the chunkers and storage in the indexer.
    """
    # Write synthetic file
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    test_file = source_dir / f"test{fixture_type}"
    test_file.write_text(content, encoding="utf-8")

    # Index via CorpusIndex
    index = CorpusIndex.open(tmp_path / "index", MockEmbedder())
    source = SourceConfig(name="test-source", path=str(source_dir))
    index.index_source(source)

    # Query LanceDB directly — no vector search needed, just dump all rows
    rows = index._table.search().limit(20).to_list()

    # Find rows for our test file
    matching = [r for r in rows if test_file.name in r["file_path"]]
    assert matching, f"No chunks found for {fixture_type} file; all rows: {rows}"

    # Find the specific chunk by expected chunk_name
    target = next(
        (r for r in matching if r.get("chunk_name") == expected_chunk_name), None
    )
    assert target is not None, (
        f"No chunk with chunk_name={expected_chunk_name!r}; "
        f"found chunk_names: {[r.get('chunk_name') for r in matching]}"
    )
    assert target["start_line"] == expected_start_line, (
        f"start_line mismatch: expected {expected_start_line}, "
        f"got {target['start_line']}"
    )
    assert target["chunk_text"].startswith(expected_chunk_text_prefix), (
        f"chunk_text does not start with {expected_chunk_text_prefix!r}; "
        f"got: {target['chunk_text'][:80]!r}"
    )

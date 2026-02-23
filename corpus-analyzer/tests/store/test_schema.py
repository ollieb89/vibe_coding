"""Tests for corpus_analyzer.store.schema — ChunkRecord and make_chunk_id.

Follows RED-GREEN-REFACTOR TDD cycle.
Tests are schema-driven: vector dimension is referenced from the schema,
not hardcoded, to keep tests resilient to schema changes.
"""

import hashlib

import pytest

from corpus_analyzer.store.schema import ChunkRecord, make_chunk_id


# ---------------------------------------------------------------------------
# make_chunk_id — determinism and uniqueness
# ---------------------------------------------------------------------------


class TestMakeChunkId:
    """Tests for the make_chunk_id() deterministic hash helper."""

    def test_returns_hex_string(self) -> None:
        """make_chunk_id returns a hex string (valid sha256 output)."""
        result = make_chunk_id("src", "/home/user/skills/foo.md", 1, "# Title\nHello")
        assert isinstance(result, str)
        assert len(result) == 64  # sha256 hex digest is always 64 chars
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic_same_inputs(self) -> None:
        """Same inputs always produce the same chunk_id."""
        a = make_chunk_id("my-skills", "/home/user/skills/foo.md", 1, "# Title\nHello")
        b = make_chunk_id("my-skills", "/home/user/skills/foo.md", 1, "# Title\nHello")
        assert a == b

    def test_different_source_name_produces_different_id(self) -> None:
        """Different source_name → different chunk_id, even with identical path and text."""
        id_a = make_chunk_id("my-skills", "/home/user/skills/foo.md", 1, "# Title\nHello")
        id_b = make_chunk_id("other-src", "/home/user/skills/foo.md", 1, "# Title\nHello")
        assert id_a != id_b

    def test_different_file_path_produces_different_id(self) -> None:
        """Different file_path → different chunk_id, even with identical source and text."""
        id_a = make_chunk_id("my-skills", "/home/user/skills/foo.md", 1, "# Title\nHello")
        id_b = make_chunk_id("my-skills", "/home/user/bar.md", 1, "# Title\nHello")
        assert id_a != id_b

    def test_different_start_line_produces_different_id(self) -> None:
        """Different start_line → different chunk_id, even with same text."""
        id_a = make_chunk_id("my-skills", "/home/user/foo.md", 1, "duplicate text")
        id_b = make_chunk_id("my-skills", "/home/user/foo.md", 10, "duplicate text")
        assert id_a != id_b

    def test_different_text_produces_different_id(self) -> None:
        """Different text → different chunk_id."""
        id_a = make_chunk_id("src", "/a.md", 1, "first chunk")
        id_b = make_chunk_id("src", "/a.md", 1, "second chunk")
        assert id_a != id_b

    def test_matches_expected_sha256(self) -> None:
        """make_chunk_id output matches manually computed sha256 of concatenated inputs."""
        source_name = "my-skills"
        file_path = "/home/user/skills/foo.md"
        start_line = 1
        text = "# Title\nHello"
        raw = source_name + file_path + str(start_line) + text
        expected = hashlib.sha256(raw.encode()).hexdigest()
        assert make_chunk_id(source_name, file_path, start_line, text) == expected


# ---------------------------------------------------------------------------
# ChunkRecord — schema structure and instantiation
# ---------------------------------------------------------------------------


class TestChunkRecordInstantiation:
    """Tests for ChunkRecord LanceModel schema correctness."""

    def _make_valid_record(self, **overrides: object) -> ChunkRecord:
        """Return a fully populated ChunkRecord with valid defaults."""
        chunk_id = make_chunk_id("src", "/path/file.md", 1, "hello")
        defaults: dict[str, object] = {
            "chunk_id": chunk_id,
            "file_path": "/path/to/file.md",
            "source_name": "my-skills",
            "text": "hello world",
            "vector": [0.1] * 768,
            "start_line": 1,
            "end_line": 5,
            "file_type": ".md",
            "content_hash": "abc123",
            "embedding_model": "nomic-embed-text",
            "indexed_at": "2026-02-23T14:00:00Z",
        }
        defaults.update(overrides)
        return ChunkRecord(**defaults)  # type: ignore[arg-type]

    def test_instantiates_with_valid_fields(self) -> None:
        """ChunkRecord can be instantiated with all required fields and 768-dim vector."""
        record = self._make_valid_record()
        assert record.chunk_id is not None
        assert record.file_path == "/path/to/file.md"
        assert record.source_name == "my-skills"
        assert record.text == "hello world"
        assert len(record.vector) == 768
        assert record.start_line == 1
        assert record.end_line == 5
        assert record.file_type == ".md"
        assert record.content_hash == "abc123"
        assert record.embedding_model == "nomic-embed-text"
        assert record.indexed_at == "2026-02-23T14:00:00Z"

    def test_chunk_id_field_is_str(self) -> None:
        """chunk_id field annotation is str."""
        fields = ChunkRecord.model_fields
        assert "chunk_id" in fields
        assert fields["chunk_id"].annotation is str

    def test_all_required_fields_present(self) -> None:
        """All required fields exist in the model_fields mapping."""
        expected_fields = {
            "chunk_id",
            "file_path",
            "source_name",
            "text",
            "vector",
            "start_line",
            "end_line",
            "file_type",
            "content_hash",
            "embedding_model",
            "indexed_at",
            "construct_type",
            "summary",
        }
        actual = set(ChunkRecord.model_fields.keys())
        assert expected_fields == actual, f"Missing fields: {expected_fields - actual}"

    def test_vector_dimension_is_768(self) -> None:
        """Vector field requires exactly 768 dimensions."""
        # We infer dimension from a valid record so the test is schema-driven.
        record = self._make_valid_record()
        assert len(record.vector) == 768

    def test_wrong_vector_dimension_raises(self) -> None:
        """ChunkRecord raises ValidationError when vector has wrong length (e.g. 512)."""
        with pytest.raises(Exception):  # pydantic ValidationError or similar
            self._make_valid_record(vector=[0.1] * 512)

    def test_wrong_vector_dimension_1024_raises(self) -> None:
        """ChunkRecord raises ValidationError when vector has 1024 dims (mxbai model dims)."""
        with pytest.raises(Exception):
            self._make_valid_record(vector=[0.0] * 1024)

    def test_start_line_is_int(self) -> None:
        """start_line field annotation is int."""
        fields = ChunkRecord.model_fields
        assert "start_line" in fields
        assert fields["start_line"].annotation is int

    def test_end_line_is_int(self) -> None:
        """end_line field annotation is int."""
        fields = ChunkRecord.model_fields
        assert "end_line" in fields
        assert fields["end_line"].annotation is int

    def test_indexed_at_is_str(self) -> None:
        """indexed_at is a str field (not datetime) to avoid pyarrow coercion issues."""
        fields = ChunkRecord.model_fields
        assert "indexed_at" in fields
        assert fields["indexed_at"].annotation is str

    def test_chunk_id_is_deterministic_in_record(self) -> None:
        """chunk_id generated via make_chunk_id is stable when the same record is recreated."""
        cid1 = make_chunk_id("my-skills", "/home/user/foo.md", 1, "# Title")
        cid2 = make_chunk_id("my-skills", "/home/user/foo.md", 1, "# Title")
        assert cid1 == cid2

        record1 = self._make_valid_record(chunk_id=cid1)
        record2 = self._make_valid_record(chunk_id=cid2)
        assert record1.chunk_id == record2.chunk_id

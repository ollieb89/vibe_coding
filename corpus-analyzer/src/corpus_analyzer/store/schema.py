"""LanceDB schema for the corpus-analyzer vector index.

This module defines the ``ChunkRecord`` LanceModel — the single source of truth
for the shape of every row stored in the LanceDB ``chunks`` table — and the
``make_chunk_id`` helper that generates a deterministic merge key for each chunk.

**Schema lock-in warning:** The vector dimension (768) and all field names /
types are baked into the LanceDB table at creation time.  Changing them
requires dropping and rebuilding the entire table.  Do not modify this file
without also running a full ``corpus reindex --force``.
"""

from __future__ import annotations

import hashlib

import lancedb  # type: ignore[import-untyped]
from lancedb.pydantic import LanceModel, Vector  # type: ignore[import-untyped]


def make_chunk_id(
    source_name: str,
    file_path: str,
    start_line: int,
    text: str,
) -> str:
    """Return a deterministic sha256 hex digest identifying a single chunk.

    The ID is derived from all four positional inputs so that:

    * The same chunk re-indexed later produces the **same** ID (idempotent
      upsert via ``merge_insert``).
    * Two chunks with identical text at different paths produce **different**
      IDs (collision safety across sources and files).
    * Two chunks at the same path but different line positions produce
      **different** IDs (handles repeated boilerplate within a single file).

    Args:
        source_name: The ``name`` field from the ``[[sources]]`` entry in
            ``corpus.toml`` (e.g. ``"my-skills"``).
        file_path: Absolute path to the source file on disk.
        start_line: 1-indexed line number where the chunk begins.
        text: Raw text content of the chunk.

    Returns:
        A 64-character lowercase hex string (sha256 digest).
    """
    raw = source_name + file_path + str(start_line) + text
    return hashlib.sha256(raw.encode()).hexdigest()


def ensure_schema_v2(table: lancedb.table.Table) -> None:
    """Add Phase 2 nullable columns to an existing chunks table if they don't exist.

    Uses LanceDB's add_columns API for in-place schema evolution — no data loss
    and no table rebuild required. Safe to call on every CorpusIndex.open() call.

    Args:
        table: The LanceDB chunks table to upgrade.
    """
    existing_cols = {field.name for field in table.schema}
    if "construct_type" not in existing_cols:
        table.add_columns({"construct_type": "cast(NULL as string)"})
    if "summary" not in existing_cols:
        table.add_columns({"summary": "cast(NULL as string)"})


class ChunkRecord(LanceModel):  # type: ignore[misc]
    """Schema for a single indexed chunk stored in the LanceDB ``chunks`` table.

    **Field notes:**

    * ``chunk_id`` — Serve as the ``merge_insert`` key; computed via
      :func:`make_chunk_id`.
    * ``vector`` — Must match the embedding model dimension exactly.
      ``nomic-embed-text`` produces 768-dim vectors.  Switching models
      requires a full table rebuild.
    * ``indexed_at`` — Stored as an ISO 8601 string rather than ``datetime``
      to avoid pyarrow timestamp coercion issues across LanceDB versions.
    * ``embedding_model`` — Stored per-chunk so that a model mismatch can be
      detected at query time and a clear error can be raised.
    """

    # --- Identity ------------------------------------------------------------
    chunk_id: str
    """sha256(source_name + file_path + str(start_line) + text) — merge key."""

    file_path: str
    """Absolute path to the source file on disk."""

    source_name: str
    """Name from the ``[[sources]]`` entry in ``corpus.toml``."""

    # --- Content -------------------------------------------------------------
    text: str
    """Raw text content of the chunk."""

    vector: Vector(768)  # type: ignore[valid-type]
    """Embedding vector; dimension must match the configured embedding model.

    ``nomic-embed-text`` → 768 dims.  Changing models requires a full rebuild.
    """

    # --- Location ------------------------------------------------------------
    start_line: int
    """1-indexed line number where the chunk begins (inclusive)."""

    end_line: int
    """1-indexed line number where the chunk ends (inclusive)."""

    file_type: str
    """File extension including the leading dot: ``.md``, ``.py``, ``.ts``, etc."""

    # --- Bookkeeping ---------------------------------------------------------
    content_hash: str
    """sha256 of the full file content at index time, used for change detection."""

    embedding_model: str
    """Name of the model used to generate ``vector`` (e.g. ``"nomic-embed-text"``)."""

    indexed_at: str
    """ISO 8601 timestamp string of when this chunk was last (re-)indexed.

    Stored as ``str`` rather than ``datetime`` to avoid pyarrow type-coercion
    surprises across LanceDB versions.
    """

    # --- Phase 2 fields (nullable, added via schema evolution) --------------
    construct_type: str | None = None
    """Agent construct type: skill, prompt, workflow, agent_config, code, documentation.

    Set to None for chunks indexed before Phase 2. Populated during corpus index
    after Phase 2 lands. Treat None as 'documentation' in search display.
    """

    summary: str | None = None
    """1-2 sentence AI summary of the file generated at index time via Ollama.

    Set to None for chunks indexed before Phase 2 or when summarize=False on source.
    """

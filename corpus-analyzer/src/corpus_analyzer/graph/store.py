"""SQLite-backed directed adjacency store for the corpus relationship graph.

Schema (``relationships`` table):

    id            INTEGER PRIMARY KEY
    source_path   TEXT NOT NULL    -- absolute path of the source file
    target_path   TEXT NOT NULL    -- absolute path (resolved) or raw slug (unresolved)
    resolved      INTEGER NOT NULL -- 1 = path resolved, 0 = slug only
    relation_type TEXT NOT NULL    -- e.g. 'related_skill', 'related_file'
    indexed_at    TEXT NOT NULL    -- ISO 8601 UTC timestamp

Unique constraint: ``(source_path, target_path)`` — ``INSERT OR REPLACE`` (via
``ON CONFLICT DO UPDATE``) handles re-indexing without duplicating edges.
"""
from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class GraphStore:
    """Thin wrapper around a SQLite file storing the relationship graph."""

    def __init__(self, db_path: Path) -> None:
        """Open (or create) the SQLite graph database at *db_path*.

        Args:
            db_path: Filesystem path to the SQLite file.  Created if absent.
        """
        self._path = db_path
        self._init_schema()

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        """Yield a ``sqlite3.Connection`` with ``Row`` factory and WAL mode."""
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """Create the relationships table and indexes if they do not exist."""
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS relationships (
                    id            INTEGER PRIMARY KEY,
                    source_path   TEXT NOT NULL,
                    target_path   TEXT NOT NULL,
                    resolved      INTEGER NOT NULL DEFAULT 0,
                    relation_type TEXT NOT NULL DEFAULT 'related_skill',
                    indexed_at    TEXT NOT NULL,
                    UNIQUE(source_path, target_path)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_source ON relationships(source_path)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_target ON relationships(target_path)"
            )
            conn.commit()

    def write_edges(
        self,
        source_path: str,
        edges: list[tuple[str, bool, str]],
    ) -> None:
        """Upsert directed edges for *source_path*.

        Args:
            source_path: Absolute path of the source file (edge origin).
            edges: List of ``(target_path_or_slug, resolved, relation_type)`` tuples.
                ``resolved`` is True when ``target_path_or_slug`` is a resolved
                absolute path, False when it is a raw slug that could not be mapped.
        """
        now = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO relationships
                    (source_path, target_path, resolved, relation_type, indexed_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(source_path, target_path) DO UPDATE SET
                    resolved      = excluded.resolved,
                    relation_type = excluded.relation_type,
                    indexed_at    = excluded.indexed_at
                """,
                [
                    (source_path, target, int(resolved), rel_type, now)
                    for target, resolved, rel_type in edges
                ],
            )
            conn.commit()

    def clear_edges_for(self, source_path: str) -> None:
        """Delete all edges originating from *source_path*.

        Called before re-indexing a file to avoid stale edges persisting.

        Args:
            source_path: Absolute path of the source file whose edges to delete.
        """
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM relationships WHERE source_path = ?", (source_path,)
            )
            conn.commit()

    def edges_from(self, source_path: str) -> list[dict[str, Any]]:
        """Return all downstream edges originating from *source_path*.

        Args:
            source_path: Absolute path of the source file.

        Returns:
            List of row dicts ordered by ``target_path``.
        """
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM relationships WHERE source_path = ? ORDER BY target_path",
                (source_path,),
            ).fetchall()
        return [{**dict(r), "resolved": bool(r["resolved"])} for r in rows]

    def edges_to(self, target_path: str) -> list[dict[str, Any]]:
        """Return all upstream edges pointing at *target_path*.

        Args:
            target_path: Absolute path (or slug) of the target.

        Returns:
            List of row dicts ordered by ``source_path``.
        """
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM relationships WHERE target_path = ? ORDER BY source_path",
                (target_path,),
            ).fetchall()
        return [{**dict(r), "resolved": bool(r["resolved"])} for r in rows]

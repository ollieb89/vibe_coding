"""Corpus indexer for managing LanceDB vector storage.

Provides table creation, model validation, and source indexing with
change detection and stale chunk cleanup.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import lancedb  # type: ignore[import-untyped]

from corpus_analyzer.config.schema import SourceConfig
from corpus_analyzer.graph.extractor import extract_related_slugs
from corpus_analyzer.graph.registry import SlugRegistry
from corpus_analyzer.graph.store import GraphStore
from corpus_analyzer.ingest.chunker import chunk_file
from corpus_analyzer.ingest.embedder import OllamaEmbedder
from corpus_analyzer.ingest.scanner import file_content_hash, walk_source
from corpus_analyzer.search.classifier import classify_file
from corpus_analyzer.search.summarizer import generate_summary, should_summarize
from corpus_analyzer.store.schema import (
    ChunkRecord,
    ensure_schema_v2,
    ensure_schema_v3,
    ensure_schema_v4,
    make_chunk_id,
)


@dataclass
class SourceStatus:
    """Pre-index check result for a single source.

    Attributes:
        source_name: Name of the source that was checked.
        needs_indexing: True if the source has changes and should be indexed.
        reason: Human-readable reason: "new source", "up to date", or "changes detected".
        last_indexed_at: ISO 8601 UTC timestamp of last index run, or None if never indexed.
        file_count: Number of files recorded at last index time (0 if never indexed).
    """

    source_name: str
    needs_indexing: bool
    reason: str
    last_indexed_at: str | None
    file_count: int = 0


@dataclass
class IndexResult:
    """Result of indexing a source.

    Attributes:
        source_name: Name of the source that was indexed.
        files_indexed: Number of files that had changes and were (re)indexed.
        chunks_written: Number of chunk records written to LanceDB.
        files_skipped: Number of files that were unchanged and skipped.
        files_removed: Number of files removed from index (stale or extension-excluded).
        elapsed: Time elapsed in seconds.
    """

    source_name: str
    files_indexed: int
    chunks_written: int
    files_skipped: int
    files_removed: int = 0
    elapsed: float = 0.0


def _migrate_agent_config_to_agent(table: lancedb.table.Table) -> None:
    """Rename legacy 'agent_config' construct_type values to 'agent'.

    Idempotent — safe to call on tables that have already been migrated.
    """
    try:
        table.update(
            values={"construct_type": "agent"},
            where="construct_type = 'agent_config'",
        )
    except Exception as exc:
        logging.warning("Failed to migrate agent_config → agent: %s", exc)


class CorpusIndex:
    """Manages the LanceDB vector index for document chunks.

    Handles table creation, model validation, source indexing with
    change detection, and stale chunk cleanup.
    """

    def __init__(
        self, table: lancedb.table.Table, embedder: OllamaEmbedder, data_dir: Path
    ) -> None:
        """Initialize with LanceDB table, embedder, and data directory.

        Args:
            table: LanceDB table instance.
            embedder: OllamaEmbedder for generating embeddings.
            data_dir: Root data directory (used for source manifest storage).
        """
        self._table = table
        self._embedder = embedder
        self._data_dir = data_dir

    @property
    def table(self) -> lancedb.table.Table:
        """Access the underlying LanceDB table."""
        return self._table

    @classmethod
    def open(cls, data_dir: Path, embedder: OllamaEmbedder) -> CorpusIndex:
        """Open or create the corpus index.

        Creates the "chunks" table if it doesn't exist. Verifies model
        compatibility if the table already exists.

        Args:
            data_dir: Directory for LanceDB data.
            embedder: OllamaEmbedder for generating embeddings.

        Returns:
            CorpusIndex instance.

        Raises:
            RuntimeError: If stored model doesn't match embedder model.
        """
        db_path = data_dir / "index"
        db = lancedb.connect(str(db_path))

        table_name = "chunks"

        try:
            table = db.open_table(table_name)
            # Table exists - verify model compatibility
            cls._verify_model_match(table, embedder.model)
        except RuntimeError:
            # Model mismatch - re-raise
            raise
        except Exception:
            # Table doesn't exist - create it
            table = db.create_table(table_name, schema=ChunkRecord)

        # Ensure Phase 2/6/17 nullable/empty-string columns exist regardless of table creation path.
        ensure_schema_v2(table)
        ensure_schema_v3(table)
        ensure_schema_v4(table)
        _migrate_agent_config_to_agent(table)

        return cls(table, embedder, data_dir)

    @staticmethod
    def _verify_model_match(table: lancedb.table.Table, expected_model: str) -> None:
        """Verify that stored model matches expected model.

        Args:
            table: LanceDB table to check.
            expected_model: Expected embedding model name.

        Raises:
            RuntimeError: If models don't match.
        """
        try:
            # Try to get a sample record to check model
            df = table.to_pandas()
            if len(df) > 0:
                stored_model = df["embedding_model"].iloc[0]
                if stored_model != expected_model:
                    raise RuntimeError(
                        f"Model mismatch: stored='{stored_model}', "
                        f"configured='{expected_model}'. "
                        f"Run 'corpus reindex --force' to rebuild."
                    )
        except (KeyError, IndexError):
            # No records or no embedding_model column - no check needed
            pass

    @property
    def _manifest_path(self) -> Path:
        """Path to the source manifest JSON file."""
        return self._data_dir / "index" / "source_manifest.json"

    def _load_manifest(self) -> dict[str, dict[str, str | int]]:
        """Load the source manifest, returning empty dict on any error.

        Returns:
            Mapping of source_name → {last_indexed_at: str, file_count: int}.
        """
        try:
            return json.loads(self._manifest_path.read_text())  # type: ignore[no-any-return]
        except Exception:
            return {}

    def _save_source_stats(self, source_name: str, last_indexed_at: str, file_count: int) -> None:
        """Persist source index stats to the manifest JSON.

        Args:
            source_name: Name of the source.
            last_indexed_at: ISO 8601 UTC timestamp string.
            file_count: Number of files found in the source walk.
        """
        manifest = self._load_manifest()
        manifest[source_name] = {"last_indexed_at": last_indexed_at, "file_count": file_count}
        try:
            self._manifest_path.write_text(json.dumps(manifest, indent=2))
        except Exception as exc:
            logging.warning("Failed to write source manifest: %s", exc)

    def _source_has_any_changes(
        self,
        source: SourceConfig,
        last_indexed_at: str,
        stored_file_count: int,
    ) -> bool:
        """Return True if the source has any new, modified, or deleted files.

        Uses only mtime checks (no file reads) for speed.

        Args:
            source: SourceConfig to check.
            last_indexed_at: ISO 8601 UTC string of last index time.
            stored_file_count: File count recorded at last index time.

        Returns:
            True if any change detected; False if source is clean.
        """
        try:
            last_ts = datetime.fromisoformat(last_indexed_at).timestamp()
        except ValueError:
            return True  # Can't parse — treat as changed

        source_path = Path(source.path).expanduser()
        current_files = list(
            walk_source(source_path, source.include, source.exclude, extensions=source.extensions)
        )

        if len(current_files) != stored_file_count:
            return True

        for file_path in current_files:
            try:
                if file_path.stat().st_mtime > last_ts:
                    return True
            except OSError:
                return True  # File disappeared mid-scan

        return False

    def check_source_status(self, source: SourceConfig) -> SourceStatus:
        """Return the pre-index status of a source without modifying any state.

        Performs a fast manifest-based check (mtime + file count only).
        No LanceDB queries or file reads are performed.

        Args:
            source: SourceConfig to check.

        Returns:
            SourceStatus with needs_indexing flag, human-readable reason, and metadata.
        """
        manifest = self._load_manifest()

        if source.name not in manifest:
            return SourceStatus(
                source_name=source.name,
                needs_indexing=True,
                reason="new source",
                last_indexed_at=None,
                file_count=0,
            )

        entry = manifest[source.name]
        last_indexed_at = str(entry["last_indexed_at"])
        file_count = int(entry["file_count"])

        if self._source_has_any_changes(source, last_indexed_at, file_count):
            return SourceStatus(
                source_name=source.name,
                needs_indexing=True,
                reason="changes detected",
                last_indexed_at=last_indexed_at,
                file_count=file_count,
            )

        return SourceStatus(
            source_name=source.name,
            needs_indexing=False,
            reason="up to date",
            last_indexed_at=last_indexed_at,
            file_count=file_count,
        )

    def index_source(
        self,
        source: SourceConfig,
        progress_callback: Callable[[int], None] | None = None,
        *,
        graph_store: GraphStore | None = None,
        registry: SlugRegistry | None = None,
    ) -> IndexResult:
        """Index a source, handling changes and stale chunks.

        Walks source files, chunks changed files, embeds them, and upserts
        to LanceDB. Deletes stale chunks (files no longer present).

        When *graph_store* and *registry* are both provided, relationship edges
        are extracted from each changed/new file's ``## Related Skills`` section
        and written to the graph store.

        Args:
            source: SourceConfig to index.
            progress_callback: Optional callback(files_processed) for progress.
            graph_store: Optional GraphStore for writing relationship edges.
            registry: Optional SlugRegistry for resolving slug references to paths.

        Returns:
            IndexResult with indexing statistics.
        """
        start_time = time.time()

        # Source-level fast pre-check: skip if manifest says nothing changed
        manifest = self._load_manifest()
        if source.name in manifest:
            entry = manifest[source.name]
            if not self._source_has_any_changes(
                source,
                str(entry["last_indexed_at"]),
                int(entry["file_count"]),
            ):
                return IndexResult(
                    source_name=source.name,
                    files_indexed=0,
                    chunks_written=0,
                    files_skipped=int(entry["file_count"]),
                    elapsed=time.time() - start_time,
                )

        # Build file index from existing records for this source
        existing_files = self._get_existing_files(source.name)
        stored_summaries = self._get_stored_summaries(source.name)

        # Walk source files
        source_path = Path(source.path).expanduser()
        files_found = 0
        files_indexed = 0
        files_skipped = 0
        chunks_written = 0
        new_chunk_dicts: list[dict[str, object]] = []
        current_file_hashes: dict[str, str] = {}

        for file_path in walk_source(
            source_path,
            source.include,
            source.exclude,
            extensions=source.extensions,
        ):
            files_found += 1
            resolved_path = str(file_path.resolve())
            current_hash = file_content_hash(file_path)
            current_file_hashes[resolved_path] = current_hash

            # Check if file needs reindexing (hash-based change detection)
            stored_hash = existing_files.get(resolved_path, "")
            if current_hash == stored_hash:
                # File unchanged - skip
                files_skipped += 1
                if progress_callback:
                    progress_callback(1)
                continue

            # File changed or new - index it
            files_indexed += 1

            # Chunk the file
            chunks = chunk_file(file_path)

            if not chunks:
                if progress_callback:
                    progress_callback(1)
                continue

            # Classify and summarize once per changed/new file.
            full_text = file_path.read_text(errors="replace")
            classify_result = classify_file(
                file_path,
                full_text,
                model=self._embedder.model,
                use_llm=False,
            )

            stored_summary = stored_summaries.get(resolved_path)
            summary_text = stored_summary or ""
            if should_summarize(
                source_summarize=source.summarize,
                stored_summary=stored_summary,
                content_hash_changed=True,
            ):
                summary_text = generate_summary(
                    filename=file_path.name,
                    content=full_text,
                    model=self._embedder.model,
                    host=self._embedder.host,
                )

            # SUMM-02: prepend summary to first chunk text before embedding.
            if summary_text:
                chunks[0]["text"] = f"{summary_text}\n\n{chunks[0]['text']}"

            # GRAPH: extract relationship edges from ## Related Skills section.
            if graph_store is not None and registry is not None and full_text:
                try:
                    slugs = extract_related_slugs(full_text)
                    if slugs:
                        graph_store.clear_edges_for(resolved_path)
                        edges: list[tuple[str, bool, str]] = []
                        for slug in slugs:
                            resolved_target = registry.resolve(slug, context_path=resolved_path)
                            if resolved_target is not None:
                                edges.append((str(resolved_target), True, "related_skill"))
                            else:
                                edges.append((slug, False, "related_skill"))
                        graph_store.write_edges(resolved_path, edges)
                except Exception as exc:  # noqa: BLE001
                    logging.warning("Failed to write graph edges for '%s': %s", resolved_path, exc)

            # Embed chunks
            texts = [chunk["text"] for chunk in chunks]
            embeddings = self._embedder.embed_batch(texts)

            # Build ChunkRecord dicts
            for chunk, vector in zip(chunks, embeddings, strict=True):
                chunk_dict = {
                    "chunk_id": make_chunk_id(
                        source.name, resolved_path, chunk["start_line"], chunk["text"]
                    ),
                    "file_path": resolved_path,
                    "source_name": source.name,
                    "text": chunk["text"],
                    "vector": vector,
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                    "file_type": file_path.suffix,
                    "content_hash": current_hash,
                    "embedding_model": self._embedder.model,
                    "indexed_at": datetime.now(UTC).isoformat(),
                    "construct_type": classify_result.construct_type,
                    "classification_source": classify_result.source,
                    "classification_confidence": classify_result.confidence,
                    "summary": summary_text or None,
                    "chunk_name": chunk.get("chunk_name", ""),
                    "chunk_text": chunk.get("chunk_text", ""),
                }
                new_chunk_dicts.append(chunk_dict)
                chunks_written += 1

            if progress_callback:
                progress_callback(1)

        # Upsert new/updated chunks
        if new_chunk_dicts:
            self._table.merge_insert("chunk_id").when_matched_update_all().when_not_matched_insert_all().execute(
                new_chunk_dicts
            )

        # Delete stale chunks (files no longer in source)
        if files_found > 0 or existing_files:
            self._delete_stale_chunks(source.name, set(current_file_hashes.keys()))
        # Optimize table
        self._table.optimize()

        # Rebuild FTS index so hybrid search stays in sync with new content.
        self._table.create_fts_index("text", replace=True)

        # Count files that will be removed (stale or extension-excluded)
        files_to_remove = set(existing_files.keys()) - set(current_file_hashes.keys())
        files_removed = len(files_to_remove)

        elapsed = time.time() - start_time

        # Update manifest so next run can fast-path this source
        self._save_source_stats(
            source.name,
            datetime.now(UTC).isoformat(),
            files_found,
        )

        return IndexResult(
            source_name=source.name,
            files_indexed=files_indexed,
            chunks_written=chunks_written,
            files_skipped=files_skipped,
            files_removed=files_removed,
            elapsed=elapsed,
        )

    def _get_existing_files(self, source_name: str) -> dict[str, str]:
        """Get mapping of file paths to content hashes for a source.

        Args:
            source_name: Name of the source.

        Returns:
            Dict mapping file_path to content_hash.
        """
        try:
            # Query for existing chunks for this source
            results = (
                self._table.search()
                .where(f"source_name = '{source_name}'")
                .limit(10000)
                .to_list()
            )

            # Build file -> hash mapping
            files: dict[str, str] = {}
            for row in results:
                file_path = row.get("file_path", "")
                content_hash = row.get("content_hash", "")
                if file_path:
                    # Keep the hash (all chunks from same file have same hash)
                    files[file_path] = content_hash

            return files
        except Exception as exc:
            logging.warning("Failed to query existing files for source '%s': %s", source_name, exc)
            return {}

    def _get_stored_summaries(self, source_name: str) -> dict[str, str | None]:
        """Get mapping of file paths to stored summary strings for a source."""
        try:
            results = (
                self._table.search()
                .where(f"source_name = '{source_name}'")
                .limit(10000)
                .to_list()
            )

            summaries: dict[str, str | None] = {}
            for row in results:
                file_path = row.get("file_path", "")
                if file_path:
                    summaries[file_path] = row.get("summary")
            return summaries
        except Exception:
            return {}

    def _delete_stale_chunks(self, source_name: str, current_files: set[str]) -> None:
        """Delete chunks for files no longer in the source.

        Args:
            source_name: Name of the source.
            current_files: Set of file paths currently in the source.
        """
        try:
            # Get all chunks for this source
            all_chunks = (
                self._table.search()
                .where(f"source_name = '{source_name}'")
                .limit(10000)
                .to_list()
            )

            # Find chunk IDs to delete (files no longer present)
            ids_to_delete = [
                row["chunk_id"]
                for row in all_chunks
                if row.get("file_path", "") not in current_files
            ]

            if ids_to_delete:
                # Delete in batches to avoid query length issues
                batch_size = 100
                for i in range(0, len(ids_to_delete), batch_size):
                    batch = ids_to_delete[i : i + batch_size]
                    # Build IN clause
                    id_list = ", ".join(f"'{cid}'" for cid in batch)
                    self._table.delete(f"chunk_id IN ({id_list})")
        except Exception as exc:
            logging.warning("Failed to delete stale chunks for source '%s': %s", source_name, exc)

    def close(self) -> None:
        """Close the index and release resources."""
        # LanceDB handles cleanup automatically
        pass

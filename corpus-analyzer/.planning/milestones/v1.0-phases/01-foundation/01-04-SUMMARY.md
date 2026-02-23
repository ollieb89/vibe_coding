---
phase: 01-foundation
plan: 01-04
subsystem: ingest
tags: [ollama, embedding, lancedb, indexer, vector-db]

# Dependency graph
requires:
  - plan: 01-01
    provides: "ChunkRecord schema, make_chunk_id()"
  - plan: 01-03
    provides: "chunk_file(), walk_source(), file_content_hash()"
provides:
  - "OllamaEmbedder with connection validation and batch embedding"
  - "CorpusIndex with table creation and model verification"
  - "index_source() with hash-based change detection"
  - "Stale chunk cleanup (deleted files)"
  - "Cross-source isolation (no interference between sources)"
affects:
  - "01-foundation"
  - "02-cli"  # CLI will use CorpusIndex
  - "03-query"  # Query will search the index

tech-stack:
  added:
    - "pandas - Required by LanceDB for to_pandas()"
  patterns:
    - "Ollama client wrapper with connection validation"
    - "LanceDB table lifecycle (open/create/verify)"
    - "Content-hash based change detection"
    - "merge_insert for idempotent upserts"
    - "Per-source stale chunk deletion"

key-files:
  created:
    - "src/corpus_analyzer/ingest/embedder.py"
    - "src/corpus_analyzer/ingest/indexer.py"
    - "tests/ingest/test_embedder.py"
    - "tests/ingest/test_indexer.py"
  modified:
    - "pyproject.toml" (added pandas dependency)

key-decisions:
  - "Batch embedding via single ollama.embed() call (not one per text)"
  - "Model mismatch detection via embedding_model column check"
  - "Hash-only change detection (mtime not persisted, simpler)"
  - "Strict zip() for chunk/embedding pairing (lengths must match)"
  - "Exception handling: RuntimeError re-raised (not caught as 'table not exists')"

patterns-established:
  - "Mocked external services in unit tests (OllamaEmbedder.embed_batch)"
  - "Real database with tmp_path (LanceDB in tests)"
  - "Dataclass for operation results (IndexResult)"
  - "Type: ignore for untyped libraries (lancedb, ollama)"

requirements-completed:
  - "INGEST-01"
  - "INGEST-04"
  - "INGEST-05"
  - "INGEST-06"
  - "INGEST-07"

# Metrics
duration: ~35min
completed: 2026-02-23
---

# Phase 01-foundation: Plan 01-04 Summary

**Ollama embedding client and CorpusIndex engine with LanceDB integration, change detection, and stale chunk cleanup**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-02-23T15:57:00Z
- **Completed:** 2026-02-23T16:32:00Z
- **Tasks:** 6
- **Files modified:** 4 created, 1 modified

## Accomplishments

- OllamaEmbedder with validate_connection(), get_model_dims(), embed_batch()
- Connection error handling with helpful messages ("Start Ollama with: ollama serve")
- Model not found handling with pull instructions
- CorpusIndex.open() with table creation and model verification
- RuntimeError on model mismatch with rebuild instructions
- index_source() with hash-based change detection
- IndexResult dataclass with files_indexed, chunks_written, files_skipped, elapsed
- Stale chunk cleanup when files are deleted
- Cross-source isolation verified (deleting source1 doesn't affect source2)
- 12 embedder tests (all mocked)
- 11 indexer tests (real LanceDB + mocked embedder)
- pandas added as dependency for LanceDB compatibility

## Task Commits

1. **Task 1: OllamaEmbedder** - Created embedder.py with 3 methods
2. **Task 2: Embedder tests** - 12 tests with mocked ollama client
3. **Task 3: CorpusIndex** - indexer.py with open(), index_source(), _delete_stale_chunks()
4. **Task 4: Indexer tests** - 11 tests with real LanceDB
5. **FIX: Dependencies** - Added pandas to pyproject.toml
6. **FIX: Type issues** - Fixed mypy and ruff warnings

## Files Created/Modified

- `src/corpus_analyzer/ingest/embedder.py` - OllamaEmbedder class
- `src/corpus_analyzer/ingest/indexer.py` - CorpusIndex class, IndexResult dataclass
- `tests/ingest/test_embedder.py` - 12 embedder tests
- `tests/ingest/test_indexer.py` - 11 indexer tests
- `pyproject.toml` - Added pandas>=2.0.0 dependency

## Decisions Made

- Used type: ignore for lancedb and ollama imports (untyped libraries)
- Exception hierarchy: RuntimeError for model mismatch re-raised, other exceptions indicate table doesn't exist
- Hash-only change detection (simpler than mtime+hash, no mtime persistence needed)
- Cast Sequence[Sequence[float]] to list[list[float]] for embed_batch return type
- Used strict=True in zip(chunks, embeddings) - lengths must match

## Deviations from Plan

None - plan executed as written.

## Issues Encountered

- **pandas not installed**: LanceDB to_pandas() requires pandas - added to dependencies
- **Model mismatch test failure**: Exception handling was too broad, caught RuntimeError as "table not exists"
  - Fixed by explicitly re-raising RuntimeError before generic Exception handler
- **Type issues**: mypy and ruff flagged several style issues
  - Fixed with type: ignore comments and ruff --fix

## User Setup Required

Ollama must be installed and running:
```bash
ollama serve
ollama pull nomic-embed-text
```

## Next Phase Readiness

- Foundation phase complete - all core components ready:
  - Config (corpus.toml parsing)
  - Schema (ChunkRecord LanceModel)
  - Chunker (markdown, python, lines)
  - Scanner (file walking, hash, change detection)
  - Embedder (Ollama client)
  - Indexer (LanceDB integration)

Ready for CLI integration and query implementation.

---

*Phase: 01-foundation*
*Completed: 2026-02-23*

"""Public Python API for querying the corpus index programmatically."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from corpus_analyzer.config import load_config, CorpusConfig
from corpus_analyzer.config.schema import DATA_DIR
from corpus_analyzer.ingest.embedder import OllamaEmbedder
from corpus_analyzer.ingest.indexer import CorpusIndex
from corpus_analyzer.search.engine import CorpusSearch
from corpus_analyzer.search.formatter import extract_snippet


@dataclass
class SearchResult:
    """A single search result from the corpus index."""

    path: str
    file_type: str
    construct_type: str
    summary: str
    score: float
    snippet: str


def _find_config() -> Path:
    """Walk up from CWD to find corpus.toml, stopping at git root or filesystem root.

    Falls back to the XDG user config dir if no corpus.toml is found.
    """
    current = Path.cwd()
    while True:
        candidate = current / "corpus.toml"
        if candidate.exists():
            return candidate
        git_root = current / ".git"
        if git_root.exists() or current == current.parent:
            from platformdirs import user_config_dir

            return Path(user_config_dir("corpus")) / "corpus.toml"
        current = current.parent


_ENGINE_CACHE: dict[str, tuple[CorpusSearch, Any, float]] = {}


def _open_engine() -> tuple[CorpusSearch, Any]:
    """Open and cache (CorpusSearch, config, mtime) keyed by config path.

    Cache is invalidated if the corpus.toml file changes on disk.
    """
    from platformdirs import user_data_dir

    config_path = _find_config()
    cache_key = str(config_path)
    mtime = config_path.stat().st_mtime if config_path.exists() else 0.0

    cached = _ENGINE_CACHE.get(cache_key)
    if cached is not None:
        # Validate cache by checking stored mtime
        stored_mtime = cached[2]
        if stored_mtime == mtime:
            return cached[0], cached[1]

    config = load_config(config_path)
    data_dir = Path(user_data_dir("corpus"))
    embedder = OllamaEmbedder(model=config.embedding.model, host=config.embedding.host)
    try:
        index = CorpusIndex.open(DATA_DIR, embedder)
        engine = CorpusSearch(index.table, embedder)
    except Exception as exc:
        raise RuntimeError(f"Failed to open index. Have you run 'corpus index'? Error: {exc}") from exc
    _ENGINE_CACHE[cache_key] = (engine, config, mtime)
    return engine, config


def search(
    query: str,
    *,
    source: str | None = None,
    file_type: str | None = None,
    construct_type: str | None = None,
    limit: int = 10,
) -> list[SearchResult]:
    """Search the corpus index and return structured results.

    Config is discovered by walking up from CWD to find corpus.toml.
    Uses the same CorpusSearch.hybrid_search() engine as the CLI and MCP server (API-03).

    Args:
        query: Natural language search query.
        source: Optional source name filter.
        file_type: Optional file type filter (e.g. ".md").
        construct_type: Optional construct type filter.
        limit: Maximum number of results.

    Returns:
        List of SearchResult dataclass instances.
    """
    engine, _ = _open_engine()
    raw = engine.hybrid_search(
        query,
        source=source,
        file_type=file_type,
        construct_type=construct_type,
        limit=limit,
    )
    return [
        SearchResult(
            path=str(r.get("file_path", "")),
            file_type=str(r.get("file_type", "")),
            construct_type=str(r.get("construct_type") or "documentation"),
            summary=str(r.get("summary") or ""),
            score=float(r.get("_relevance_score", 0.0)),
            snippet=extract_snippet(str(r.get("text", "")), query),
        )
        for r in raw
    ]


def index(*, verbose: bool = False) -> list[dict[str, Any]]:
    """Trigger incremental re-index of all configured sources programmatically.

    Uses the same CorpusIndex.index_source() pipeline as the CLI (API-03).

    Args:
        verbose: If True, print per-source results to stdout.

    Returns:
        List of dicts with keys: source_name, files_indexed, chunks_written,
        files_skipped, elapsed.
    """
    from platformdirs import user_data_dir

    config_path = _find_config()
    config = load_config(config_path)
    data_dir = Path(user_data_dir("corpus"))
    embedder = OllamaEmbedder(model=config.embedding.model, host=config.embedding.host)
    corpus_index = CorpusIndex.open(data_dir, embedder)

    results = []
    for source in config.sources:
        result = corpus_index.index_source(source)
        entry = {
            "source_name": source.name,
            "files_indexed": result.files_indexed,
            "chunks_written": result.chunks_written,
            "files_skipped": result.files_skipped,
            "elapsed": result.elapsed,
        }
        results.append(entry)
        if verbose:
            print(f"{source.name}: {result.files_indexed} files, {result.chunks_written} chunks")  # noqa: T201
    return results

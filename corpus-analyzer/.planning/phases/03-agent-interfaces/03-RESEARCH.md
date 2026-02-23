# Phase 3: Agent Interfaces - Research

**Researched:** 2026-02-23
**Domain:** FastMCP stdio server, Python public API (dataclasses), `corpus status` enhanced CLI, entry-point naming
**Confidence:** HIGH

## Summary

Phase 3 wires the completed Phase 2 search engine to two external consumers: an MCP server (for Claude Code and other agents) and a thin Python API (for scripts). The `corpus status` command also gets a significant upgrade per the locked decisions. All three deliverables are integration work over the Phase 2 foundation — no new search logic, no new LanceDB calls beyond what `CorpusSearch` and `CorpusIndex` already provide.

The primary technical domain is FastMCP: a mature Python framework for building stdio MCP servers. Its `@mcp.tool` decorator generates the input schema automatically from Python type annotations, which means schema correctness (MCP-05 — top-level `type: "object"`, no Union types) is achieved by writing clean Python signatures. The lifespan pattern (`@lifespan` + `yield`) is the correct hook to pre-warm the embedding model at startup (MCP-06). All FastMCP logging goes through the MCP protocol's log message channel (not stdout), satisfying MCP-04. One important naming issue must be resolved before planning: the `pyproject.toml` entry point is currently `corpus-analyzer`, but CONTEXT.md specifies the invocation as `corpus mcp serve`. The planner must decide whether to add a `corpus` entry point alias or rename the existing one.

The Python API is trivially thin: a `corpus/__init__.py` (or `corpus_analyzer/__init__.py` re-export) that exposes `search()` and `index()` as module-level functions backed by the same `CorpusSearch` and `CorpusIndex` stack. Config discovery walks up from CWD to the git root to find `corpus.toml`, which requires a small `find_config()` utility. Results are `@dataclass` instances matching the API-01 field list. The sync-only constraint eliminates async complexity entirely.

**Primary recommendation:** Implement in three sequential waves — (1) entry-point alias + `corpus mcp serve` subcommand with FastMCP server + lifespan pre-warm, (2) Python public API with CWD-walk config discovery, (3) enhanced `corpus status` command with per-source staleness, JSON output, and model reachability check.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**MCP response shape**
- Each search result contains both the matching chunk/snippet AND full file content
- Results returned as structured objects with fields: `path`, `score`, `snippet`, `full_content`, `construct_type`, `summary`, `file_type`
- No results → return `{ results: [], message: "No results found for query: X" }` (empty array + message field, not an error)
- Index missing or embedding model unreachable → raise an MCP error with descriptive, actionable message (e.g. "Index not found. Run corpus index first.")

**MCP tool surface**
- Single tool: `corpus_search` — agents search, humans use CLI for indexing and status
- No MCP resources exposed (Claude's discretion — tool already returns content)
- Server invocation: `corpus mcp serve` (CLI subcommand over stdio)
- Claude Code config: `{ "command": "corpus", "args": ["mcp", "serve"] }`
- Config discovery: reads `corpus.toml` from CWD (same discovery as the CLI)
- Embedding model pre-warmed at startup (MCP-06 — eliminates cold-start latency)

**Python API ergonomics**
- Function-based: `from corpus import search` — `results = search("my query")`
- Also expose `from corpus import index` for programmatic re-indexing (API-02)
- Config discovery: walk up from CWD to git root to find `corpus.toml` (pyproject.toml-style)
- Returns **dataclasses** — `result.path`, `result.score`, `result.snippet`, `result.summary`, `result.construct_type`, `result.file_type`
- Sync only — no async variant needed for v1 scripting use cases
- Same underlying query engine as CLI and MCP (API-03 — no divergence)

**Index status UX**
- `corpus status` CLI command (standalone, not embedded in other commands)
- Shows all of:
  - **Sources**: name, path, file count, per-source staleness indicator (✅ current / ⚠️ stale)
  - **Last indexed**: timestamp + human-readable age ("2 hours ago")
  - **Health/staleness**: overall health indicator + count of changed files since last index
  - **Embedding model**: name and reachability status (connected / unreachable)
  - **Index stats**: total file count, total chunk count
  - **Database**: path and size
- Default: Rich-formatted table with color health indicators (✅ ⚠️ ❌)
- `--json` flag: structured JSON output for scripting and CI/CD pipelines

### Claude's Discretion

- Whether to expose any MCP resources (leaning toward none — tool is sufficient)
- Rich table layout and exact column formatting for `corpus status`
- Exact dataclass field names for Python API result objects (must include: path, file_type, construct_type, summary, score, snippet per API-01)
- Staleness threshold definition (how many hours/minutes before "stale" warning triggers)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MCP-01 | Corpus exposes a FastMCP server registerable with Claude Code via stdio transport | `FastMCP(name="corpus")` + `mcp.run()` defaults to stdio; registerable via `{ "command": "corpus", "args": ["mcp", "serve"] }` in Claude Code config |
| MCP-02 | MCP `search` tool returns full file content for top matches (not just snippets) | Read full file from `result["file_path"]` after `CorpusSearch.hybrid_search()` returns results; bundle as `full_content` in response dict |
| MCP-03 | MCP `search` tool accepts: `query` (required), `source` (optional), `type` (optional), `construct` (optional), `top_k` (optional, default 5) | `@mcp.tool` with typed Python signature; FastMCP auto-generates schema from type annotations |
| MCP-04 | MCP server writes nothing to stdout; all logging goes to stderr | FastMCP's `ctx.info()` / `ctx.warning()` / `ctx.error()` send log messages via MCP protocol (not stdout); Python `logging` module configured to `sys.stderr` for stdlib logs |
| MCP-05 | MCP tool input schema uses top-level `type: "object"` with no Union types (Claude Code compatibility) | Use `Optional[str]` (not `str \| None`) for optional params in Python 3.10+; FastMCP generates `{"type": "object", "properties": {...}}` with `required: ["query"]`; avoid `anyOf`/`oneOf` in schema |
| MCP-06 | Embedding model pre-warmed at MCP server startup to eliminate cold-start latency | FastMCP `@lifespan` context manager: call `embedder.embed_batch(["warmup"])` before `yield`; store embedder in lifespan context for tool access via `ctx.lifespan_context` |
| API-01 | `from corpus import search` returns structured results: `path`, `file_type`, `construct_type`, `summary`, `score`, `snippet` | `@dataclass SearchResult` with those 6 fields; `search()` function wraps `CorpusSearch.hybrid_search()` and maps dicts to dataclass instances |
| API-02 | `from corpus import index` triggers incremental re-index programmatically | `index()` function wraps `CorpusIndex.open()` + `index.index_source()` per configured source; returns summary dict or `IndexResult` list |
| API-03 | Python API results use the same underlying query engine as CLI and MCP (no divergence) | All three use `CorpusSearch.hybrid_search()` — the same method; no separate implementation permitted |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `fastmcp` | ≥2.14.4 | MCP server framework: tool registration, stdio transport, lifespan hooks | Official Python MCP framework; Claude Code supports its schema output natively; `@mcp.tool` generates correct `type: "object"` schemas |
| `typer[all]` | ≥0.12.0 (already installed) | Add `mcp` sub-app + `serve` subcommand to existing CLI | Already present; same pattern as existing `db_app`, `samples_app` sub-groups |
| `dataclasses` | stdlib | `SearchResult` dataclass for Python API return type | Zero extra dependency; `@dataclass` is the locked decision for API-01 |
| `platformdirs` | ≥4.9.2 (already installed) | Locate `user_data_dir` for index in Python API (same as CLI) | Already present; consistent path resolution |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pathlib` | stdlib | CWD-walk config discovery (Python API): `Path.cwd()` → walk up to git root | Only in `corpus/_config_discovery.py` (new utility) |
| `subprocess` / `pathlib` | stdlib | Detect git root for config discovery: `git rev-parse --show-toplevel` or walk for `.git` | Config discovery for Python API — walk up until `.git` found or filesystem root |
| `datetime` | stdlib | Human-readable age string for `corpus status` ("2 hours ago") | In enhanced `status_command` |
| `json` | stdlib | `corpus status --json` output | In enhanced `status_command` |
| `logging` | stdlib | Redirect stdlib logger output to `sys.stderr` in MCP server | MCP-04 compliance — `logging.basicConfig(stream=sys.stderr)` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `fastmcp` | Raw `mcp` Python SDK | `fastmcp` is higher-level; generates schemas automatically; handles stdio plumbing; no reason to use raw SDK |
| `@dataclass` for API results | `TypedDict`, `pydantic.BaseModel`, plain `dict` | `@dataclass` gives attribute access (`result.path`), is serializable, and has zero dependencies — locked decision |
| Walk-up config discovery | Always use XDG config path | Walk-up matches pyproject.toml convention (scripts expect config near the project); XDG path is for user-global config, not per-project |

**Installation:**
```bash
uv add fastmcp
```

Note: `fastmcp` is the only new dependency for Phase 3. Everything else is already in `pyproject.toml`.

## Architecture Patterns

### Recommended Project Structure (additions to Phase 2)

```
src/corpus_analyzer/
├── mcp/
│   ├── __init__.py
│   └── server.py          # FastMCP server: corpus_search tool + lifespan
├── api/
│   ├── __init__.py
│   └── public.py          # search(), index() functions + SearchResult dataclass
└── cli.py                 # Add: mcp_app sub-group + status --json enhancement

corpus/
├── __init__.py            # from corpus import search, index  (thin re-export)
```

The `corpus/` package at the project root (sibling of `src/`) provides the `from corpus import search` import path. Alternatively, expose via `src/corpus_analyzer/__init__.py` and add a `corpus` package that imports from it. The cleanest approach: add `corpus/` as a separate installable package that re-exports from `corpus_analyzer.api.public`.

**Entry point naming issue:** `pyproject.toml` currently registers `corpus-analyzer = "corpus_analyzer.cli:app"`. The locked decision requires `corpus mcp serve`. Two options:
1. Add a second entry point: `corpus = "corpus_analyzer.cli:app"` (preferred — keeps backward compat)
2. Rename the existing entry point from `corpus-analyzer` to `corpus`

Option 1 is safer (does not break existing users). The planner must add `corpus = "corpus_analyzer.cli:app"` to `[project.scripts]`.

### Pattern 1: FastMCP Server with Lifespan Pre-Warm

**What:** Use `@lifespan` to pre-warm the Ollama embedding model at server startup. Store the `CorpusSearch` instance in the lifespan context. Access it in the tool via `ctx.lifespan_context`.

**When to use:** In `src/corpus_analyzer/mcp/server.py`.

**Example:**
```python
# Source: https://gofastmcp.com/servers/lifespan
from fastmcp import FastMCP, Context
from fastmcp.server.lifespan import lifespan

from corpus_analyzer.config import load_config
from corpus_analyzer.ingest.embedder import OllamaEmbedder
from corpus_analyzer.ingest.indexer import CorpusIndex
from corpus_analyzer.search.engine import CorpusSearch
from corpus_analyzer.cli import CONFIG_PATH, DATA_DIR

@lifespan
async def corpus_lifespan(server: FastMCP):  # type: ignore[type-arg]
    """Pre-warm embedding model and open index at startup."""
    config = load_config(CONFIG_PATH)
    embedder = OllamaEmbedder(model=config.embedding.model, host=config.embedding.host)
    # Pre-warm: send one dummy embed to load the model into memory (MCP-06)
    try:
        embedder.embed_batch(["warmup"])
    except Exception:
        pass  # Server still starts; first search will show cold-start error
    index = CorpusIndex.open(DATA_DIR, embedder)
    engine = CorpusSearch(index.table, embedder)
    yield {"engine": engine, "config": config}

mcp = FastMCP("corpus", lifespan=corpus_lifespan)
```

### Pattern 2: Tool Registration with Claude-Compatible Schema

**What:** Register `corpus_search` tool. Use `Optional[str]` (not `str | None`) for optional parameters. Use `Optional[int]` for `top_k`. This ensures FastMCP generates a schema with no `anyOf`/`oneOf` Union types (MCP-05).

**When to use:** In `src/corpus_analyzer/mcp/server.py`.

**Example:**
```python
# Source: Context7 /jlowin/fastmcp — tool registration pattern
import logging
import sys
from typing import Any, Optional
from fastmcp import FastMCP, Context

# Redirect stdlib logging to stderr (MCP-04)
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

@mcp.tool
async def corpus_search(
    query: str,
    source: Optional[str] = None,
    type: Optional[str] = None,
    construct: Optional[str] = None,
    top_k: Optional[int] = 5,
    ctx: Context = None,
) -> dict[str, Any]:
    """Search the corpus index with a natural language query.

    Returns full file content for top matching files plus metadata.
    """
    engine: CorpusSearch = ctx.lifespan_context["engine"]
    config = ctx.lifespan_context["config"]

    limit = top_k if top_k is not None else 5

    try:
        raw_results = engine.hybrid_search(
            query,
            source=source,
            file_type=type,
            construct_type=construct,
            limit=limit,
        )
    except Exception as e:
        # MCP-01: raise MCP error with actionable message
        raise ValueError(f"Search failed: {e}. Ensure 'corpus index' has been run.") from e

    if not raw_results:
        return {"results": [], "message": f"No results found for query: {query}"}

    results = []
    for row in raw_results:
        file_path = row.get("file_path", "")
        try:
            full_content = Path(file_path).read_text(errors="replace")
        except OSError:
            full_content = ""
        results.append({
            "path": file_path,
            "score": row.get("_relevance_score", 0.0),
            "snippet": extract_snippet(str(row.get("text", "")), query),
            "full_content": full_content,
            "construct_type": row.get("construct_type") or "documentation",
            "summary": row.get("summary") or "",
            "file_type": row.get("file_type", ""),
        })

    return {"results": results}
```

### Pattern 3: CLI `corpus mcp serve` Subcommand

**What:** Wire FastMCP server as a Typer sub-app command, analogous to `db_app`. The `serve` command calls `mcp.run()` which defaults to stdio transport.

**When to use:** In `cli.py`.

**Example:**
```python
mcp_app = typer.Typer(help="MCP server commands.")
app.add_typer(mcp_app, name="mcp")

@mcp_app.command("serve")
def mcp_serve() -> None:
    """Start the corpus MCP server (stdio transport for Claude Code)."""
    from corpus_analyzer.mcp.server import mcp
    mcp.run()  # defaults to stdio; writes nothing to stdout (MCP-04)
```

### Pattern 4: Python Public API with CWD-Walk Config Discovery

**What:** Module-level `search()` and `index()` functions. Config discovery walks up from `Path.cwd()` until finding `corpus.toml` or hitting the filesystem root. Returns `SearchResult` dataclasses.

**When to use:** In `src/corpus_analyzer/api/public.py` and `corpus/__init__.py`.

**Example:**
```python
# src/corpus_analyzer/api/public.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from corpus_analyzer.config import load_config
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
    """Walk up from CWD to find corpus.toml, stopping at git root or filesystem root."""
    current = Path.cwd()
    while True:
        candidate = current / "corpus.toml"
        if candidate.exists():
            return candidate
        git_root = current / ".git"
        if git_root.exists() or current == current.parent:
            # Reached git root or filesystem root — use XDG fallback
            from platformdirs import user_config_dir
            return Path(user_config_dir("corpus")) / "corpus.toml"
        current = current.parent


def _open_engine() -> tuple[CorpusSearch, Any]:
    """Open config, embedder, index, and search engine from discovered config."""
    from platformdirs import user_data_dir
    config_path = _find_config()
    config = load_config(config_path)
    data_dir = Path(user_data_dir("corpus"))
    embedder = OllamaEmbedder(model=config.embedding.model, host=config.embedding.host)
    index = CorpusIndex.open(data_dir, embedder)
    engine = CorpusSearch(index.table, embedder)
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
```

### Pattern 5: Enhanced `corpus status` with Staleness + JSON

**What:** Extend the existing `status_command` to show per-source staleness (compare file mtimes vs `indexed_at` timestamp in LanceDB), human-readable age, model reachability, database path/size, and `--json` output.

**When to use:** In `cli.py`, replacing the current `status_command`.

**Key implementation details:**

```python
import json
from datetime import UTC, datetime

def _human_age(ts: str) -> str:
    """Convert ISO timestamp to human-readable age string."""
    try:
        dt = datetime.fromisoformat(ts).replace(tzinfo=UTC)
        delta = datetime.now(UTC) - dt
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return f"{seconds} seconds ago"
        elif seconds < 3600:
            return f"{seconds // 60} minutes ago"
        elif seconds < 86400:
            return f"{seconds // 3600} hours ago"
        else:
            return f"{seconds // 86400} days ago"
    except Exception:
        return ts

def _count_stale_files(source: SourceConfig, indexed_at: str) -> int:
    """Count files in a source directory modified after the last index time."""
    try:
        indexed_dt = datetime.fromisoformat(indexed_at)
        source_path = Path(source.path).expanduser()
        from corpus_analyzer.ingest.scanner import walk_source
        stale = sum(
            1 for fp in walk_source(source_path, source.include, source.exclude)
            if fp.stat().st_mtime > indexed_dt.timestamp()
        )
        return stale
    except Exception:
        return 0
```

### Anti-Patterns to Avoid

- **Printing to stdout from the MCP server process:** Any `print()` or `logging` to stdout will corrupt the MCP protocol stream. All output must go to `stderr` or via `ctx.info()`. Apply `logging.basicConfig(stream=sys.stderr)` at module level in `server.py`.
- **Using `str | None` Union types in MCP tool signatures:** FastMCP with some Claude Code versions generates `anyOf: [{"type": "string"}, {"type": "null"}]` which breaks Claude Code. Use `Optional[str]` from `typing` (which generates the same schema, but more reliably produces `{"type": "string"}` in some FastMCP versions). Verify the generated schema with `fastmcp list server.py --input-schema`.
- **Opening `CorpusIndex` on every MCP tool call:** Index open is expensive (LanceDB connection + FTS index check). Always open once in lifespan and reuse via `ctx.lifespan_context`. Never open in the tool handler itself.
- **Raising `Exception` directly from MCP tools:** FastMCP converts unhandled exceptions to MCP errors. For user-facing error cases (index missing, model unreachable), raise `ValueError` or `RuntimeError` with an actionable message. The MCP error will include the message.
- **Config discovery in Python API opening the wrong index:** The API uses `user_data_dir("corpus")` for the LanceDB index path (same as CLI). Do not use a relative path or CWD-derived path for the index — only the config discovery walks up; the index itself always lives in the XDG data dir.
- **Implementing `from corpus import search` as a separate implementation:** API-03 requires using the same `CorpusSearch.hybrid_search()` as the CLI. Never copy the search logic into the public API.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MCP protocol, stdio framing, schema generation | Custom JSON-RPC server | `fastmcp` | FastMCP handles the entire MCP wire protocol, schema generation, error serialization, and stdio transport |
| Human-readable time delta | Custom datetime formatting | `datetime` stdlib arithmetic → simple string formatting | No library needed; a 10-line helper covers all cases |
| Config file discovery | Recursive `glob` or `os.walk` | `pathlib.Path` parent iteration + `.git` sentinel check | Simple, correct, follows pyproject.toml convention |

**Key insight:** Phase 3 is pure plumbing. The search logic (Phase 2), config parsing (Phase 1), and indexing (Phase 1) are all done. Phase 3 assembles them into two new consumers (FastMCP server, Python API) and one enhanced existing consumer (status command). The only non-trivial new code is the FastMCP lifespan + tool handler (~60 lines) and the SearchResult dataclass + public functions (~40 lines).

## Common Pitfalls

### Pitfall 1: stdout Corruption in MCP Server
**What goes wrong:** Claude Code receives garbled JSON-RPC responses because the MCP process writes to stdout (e.g., from `print()`, `logging.info()`, or Rich Console with default stream).
**Why it happens:** MCP stdio transport uses stdout as the protocol channel. Any non-protocol bytes corrupt the stream.
**How to avoid:** In `server.py`, apply `logging.basicConfig(stream=sys.stderr, level=logging.WARNING)` at import time. Never use `print()` or `Console()` without explicitly passing `file=sys.stderr`. Rich's `Console` defaults to stdout — do not use it in the MCP server module.
**Warning signs:** Claude Code reports "connection error" or "invalid JSON" immediately after tool call.

### Pitfall 2: Ollama Cold-Start After 5-Minute Keep-Alive Expiry
**What goes wrong:** The first MCP search after 5 minutes of inactivity times out because Ollama unloads the model from GPU/RAM.
**Why it happens:** Ollama's default `KEEP_ALIVE` is 5 minutes. After expiry, the first `embed_batch` call triggers a slow model reload (3-30 seconds depending on hardware). Claude Code may time out waiting.
**How to avoid:** Pre-warm at startup (done via lifespan — MCP-06). Additionally, consider setting `OLLAMA_KEEP_ALIVE=-1` in the environment (keeps model loaded indefinitely). Document this in the server's startup output to stderr.
**Warning signs:** First search after idle period is very slow or times out.

### Pitfall 3: `Optional[str]` vs `str | None` in Tool Signatures
**What goes wrong:** Claude Code rejects the tool call with a schema validation error because the input schema contains `anyOf: [{"type": "string"}, {"type": "null"}]` instead of just `{"type": "string"}` with the parameter in the `not required` list.
**Why it happens:** FastMCP's schema generation behavior for Union types differs between versions. `Optional[str]` (from `typing`) is more reliably handled than `str | None` (Python 3.10+ syntax) in some FastMCP versions.
**How to avoid:** Use `from typing import Optional` and `Optional[str]` for all optional tool parameters. Verify generated schema after implementation with `fastmcp list corpus_mcp_server.py --input-schema` and confirm no `anyOf` in the output.
**Warning signs:** Claude Code tool call fails with "schema validation error" on the server side.

### Pitfall 4: Python API Opens Index Twice (Performance)
**What goes wrong:** Each call to `search("query")` opens a new LanceDB connection, runs model validation, and creates an FTS index — taking several seconds.
**Why it happens:** Naive implementation calls `_open_engine()` on every invocation without caching.
**How to avoid:** Cache the `(CorpusSearch, config)` tuple in a module-level `_ENGINE_CACHE` dict keyed by config path. Invalidate only if the config file mtime changes. For v1 scripting use cases (batch queries), this is sufficient.
**Warning signs:** Repeated `search()` calls in a loop are unexpectedly slow.

### Pitfall 5: `corpus mcp serve` Entry Point Not Found
**What goes wrong:** Claude Code config `{ "command": "corpus", "args": ["mcp", "serve"] }` fails because the `corpus` command is not found in PATH — only `corpus-analyzer` exists.
**Why it happens:** `pyproject.toml` currently registers only `corpus-analyzer = "corpus_analyzer.cli:app"`. The `corpus` short name is not registered.
**How to avoid:** Add `corpus = "corpus_analyzer.cli:app"` to `[project.scripts]` and re-run `uv sync` to install the new entry point. Verify with `which corpus` after install.
**Warning signs:** `claude mcp add corpus corpus mcp serve` fails with "command not found".

### Pitfall 6: `from corpus import search` — Module Not Found
**What goes wrong:** Users get `ModuleNotFoundError: No module named 'corpus'` when trying `from corpus import search`.
**Why it happens:** The installed package is `corpus_analyzer`, not `corpus`. The `corpus/` top-level package must be explicitly added to `[tool.hatch.build.targets.wheel] packages` in `pyproject.toml`.
**How to avoid:** Create `src/corpus/__init__.py` (or `corpus/__init__.py` at project root, added to packages) that re-exports `search` and `index` from `corpus_analyzer.api.public`. Add the package to hatch's build config.
**Warning signs:** `from corpus import search` raises `ModuleNotFoundError` even after `uv sync`.

## Code Examples

Verified patterns from official sources:

### FastMCP Server with Lifespan (Startup Pre-Warm)
```python
# Source: https://gofastmcp.com/servers/lifespan
from fastmcp import FastMCP, Context
from fastmcp.server.lifespan import lifespan

@lifespan
async def corpus_lifespan(server: FastMCP):  # type: ignore[type-arg]
    config = load_config(CONFIG_PATH)
    embedder = OllamaEmbedder(model=config.embedding.model, host=config.embedding.host)
    embedder.embed_batch(["warmup"])  # pre-warm (MCP-06)
    index = CorpusIndex.open(DATA_DIR, embedder)
    engine = CorpusSearch(index.table, embedder)
    yield {"engine": engine, "config": config}

mcp = FastMCP("corpus", lifespan=corpus_lifespan)
```

### FastMCP Tool Accessing Lifespan Context
```python
# Source: https://gofastmcp.com/servers/lifespan
@mcp.tool
async def corpus_search(query: str, ctx: Context) -> dict:
    engine: CorpusSearch = ctx.lifespan_context["engine"]
    results = engine.hybrid_search(query, limit=5)
    return {"results": [...]}
```

### FastMCP Logging to Stderr (Not stdout)
```python
# Source: https://gofastmcp.com/servers/context
# Use ctx.info() / ctx.warning() for MCP protocol log messages
# Use logging module (redirected to stderr) for internal diagnostics

import logging, sys
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

@mcp.tool
async def corpus_search(query: str, ctx: Context) -> dict:
    await ctx.info(f"Searching for: {query}")  # goes to MCP client log, not stdout
    ...
```

### `corpus` Entry Point Registration
```toml
# pyproject.toml [project.scripts] addition
[project.scripts]
corpus-analyzer = "corpus_analyzer.cli:app"
corpus = "corpus_analyzer.cli:app"  # NEW: enables `corpus mcp serve`
```

### FastMCP `mcp.run()` for Stdio
```python
# Source: Context7 /jlowin/fastmcp
# mcp.run() defaults to stdio transport — correct for Claude Code
if __name__ == "__main__":
    mcp.run()

# Or from CLI subcommand:
# @mcp_app.command("serve")
# def mcp_serve() -> None:
#     mcp.run()
```

### SearchResult Dataclass
```python
from dataclasses import dataclass

@dataclass
class SearchResult:
    """Structured search result for the corpus Python API."""
    path: str
    file_type: str
    construct_type: str
    summary: str
    score: float
    snippet: str
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Raw `mcp` Python SDK (verbose) | `fastmcp` decorator-based server | 2024 | Schema auto-generation, stdio plumbing handled, lifespan hooks built-in |
| Custom stdio MCP server | `FastMCP.run()` default stdio | FastMCP 2.x | Zero boilerplate for Claude Code compatible server |
| `str \| None` Union types in tool params | `Optional[str]` from `typing` | Best practice for Claude Code compat | Generates clean non-Union JSON schema |

**Deprecated/outdated:**
- `mcp.run(transport="sse")`: SSE transport is not supported by Claude Code's `stdio`-based MCP registration. Always use `mcp.run()` (default) or `mcp.run(transport="stdio")`.

## Open Questions

1. **FastMCP version and `Optional[str]` schema output**
   - What we know: FastMCP ≥2.14.4 exists; `@mcp.tool` generates `type: "object"` top-level schemas
   - What's unclear: Whether current fastmcp generates `anyOf` for `Optional[str]` parameters, or correctly emits them as optional properties without `anyOf`
   - Recommendation: After installing fastmcp, run `fastmcp list` on the server module with `--input-schema` flag and verify the output before considering MCP-05 done. If `anyOf` appears, use `str = ""` defaults instead of `Optional[str]` for optional string params.

2. **`from corpus import search` — package naming**
   - What we know: Installed package is `corpus_analyzer`; `from corpus import search` requires a `corpus` module in the Python path
   - What's unclear: Best location — `src/corpus/__init__.py` (sibling package) vs root `corpus/__init__.py`; whether hatch build config needs `packages = ["src/corpus_analyzer", "src/corpus"]`
   - Recommendation: Use `src/corpus/__init__.py` consistent with the `src/` layout convention; add `"src/corpus"` to `[tool.hatch.build.targets.wheel] packages`.

3. **MCP lifespan error handling — what if Ollama is down at startup**
   - What we know: `CorpusIndex.open()` may fail if the data dir doesn't exist; `embed_batch(["warmup"])` will fail if Ollama is unreachable
   - What's unclear: Whether a failed lifespan causes FastMCP to refuse to start (crash) or start anyway and let tools return errors
   - Recommendation: Wrap lifespan setup in try/except; on failure, `yield {"engine": None, "error": str(e)}`; in the tool handler, check `ctx.lifespan_context.get("engine")` and return an MCP error if None. This allows the server to start even with a broken index.

## Sources

### Primary (HIGH confidence)
- `/jlowin/fastmcp` (Context7) — `FastMCP` class, `@mcp.tool` decorator, `mcp.run()` stdio, lifespan pattern, `Context` type, logging via `ctx.info()`
- `/llmstxt/gofastmcp_llms_txt` (Context7) — lifespan context access in tools (`ctx.lifespan_context`), `@lifespan` decorator pattern, logging methods
- https://gofastmcp.com/servers/lifespan — lifespan startup/shutdown, context sharing with tools

### Secondary (MEDIUM confidence)
- Phase 2 RESEARCH.md (this project) — confirmed `CorpusSearch.hybrid_search()` API, `CorpusIndex.open()` interface, `extract_snippet()` availability
- Existing `src/corpus_analyzer/cli.py` — confirmed Typer sub-app pattern (`db_app`, `samples_app`), CONFIG_PATH/DATA_DIR constants, existing `status_command` structure

### Tertiary (LOW confidence)
- Open Question 1 (FastMCP `Optional[str]` schema behavior): Needs live verification after install
- Open Question 3 (FastMCP lifespan failure mode): Needs live verification against actual FastMCP behavior

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — FastMCP confirmed via Context7; all other dependencies already installed
- Architecture: HIGH — patterns taken directly from FastMCP docs; codebase integration points verified by reading source
- Pitfalls: HIGH — stdout corruption is a known MCP footgun; entry point naming confirmed by reading pyproject.toml; cold-start Ollama issue documented in STATE.md
- Open questions: LOW/MEDIUM — FastMCP schema details need live verification

**Research date:** 2026-02-23
**Valid until:** 2026-03-23 (FastMCP is actively developed; core API is stable but schema generation behavior may change in minor versions)

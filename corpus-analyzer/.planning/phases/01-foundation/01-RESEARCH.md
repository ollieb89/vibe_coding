# Phase 1: Foundation - Research

**Researched:** 2026-02-23
**Domain:** LanceDB embedded vector store, Ollama embeddings, TOML config, file chunking pipeline
**Confidence:** HIGH

## Summary

Phase 1 builds the complete ingestion pipeline: read `corpus.toml` from `~/.config/corpus/`, walk configured source directories, chunk files (heading-based for `.md`, AST-based for `.py`, line-based fallback), embed with Ollama, and persist to LanceDB at `~/.local/share/corpus/`. Incremental indexing (skip unchanged files via mtime + sha256) and ghost document removal (delete chunks for deleted/moved source files) are first-class concerns because the schema and LanceDB table structure cannot be retrofitted after initial creation.

LanceDB 0.29.x (Feb 2026) is mature, embedded, ships full-text search via tantivy, and the `merge_insert` API with `when_not_matched_by_source_delete()` is the right tool for incremental sync without ghost documents. The Ollama Python SDK `embed()` API is stable. The existing project uses `typer[all]` and `rich`, both of which cover progress bars natively — no new UI libraries required.

The main implementation risk is schema lock-in: the LanceDB table schema (vector dimensions, metadata fields, embedding model name) cannot be changed after table creation without a full rebuild. Getting the schema right in the first plan wave is the most critical decision in the entire phase.

**Primary recommendation:** Define the LanceDB `LanceModel` schema as the first implementation task, store `embedding_model` as a scalar column, and use `merge_insert("chunk_id").when_matched_update_all().when_not_matched_insert_all().when_not_matched_by_source_delete()` for all index writes.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **corpus.toml format:** `[[sources]]` array of tables; location: `~/.config/corpus/corpus.toml` (global XDG config)
- **Per-source fields:** `name`, `path`, `include` (glob list), `exclude` (glob list)
- **Global `[embedding]` section:** `model`, `provider`, `host`; one model for the whole index
- **Embedding provider:** Phase 1 local Ollama only (no OpenAI/Cohere)
- **LanceDB index location:** `~/.local/share/corpus/` (XDG data dir)
- **Indexing UX:** progress bar with file counts while running; per-source summary on completion; `--verbose` flag for per-file output; total skipped count shown
- **`corpus add` behavior:** default name = directory basename; duplicate path/name = error + suggest `--force`; success output confirms add + suggests `corpus index`; supports `--include`/`--exclude` flags

### Claude's Discretion

- Default embedding model choice (nomic-embed-text vs mxbai-embed-large)
- First-run error message wording and whether to auto-detect if Ollama is not running
- Chunk size limits and overlap for heading-based (md) and AST-based (py) chunking
- Exact progress bar library/implementation

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CONF-01 | User can configure source directories to index via `corpus.toml` | `tomllib` (stdlib read) + `tomli-w` (write); `platformdirs` for XDG paths |
| CONF-02 | User can set embedding model in config (local Ollama only in Phase 1) | `[embedding]` section; model name stored as scalar in LanceDB schema |
| CONF-03 | User can configure file type inclusion/exclusion patterns per source | `fnmatch`/`pathlib.Path.match()` against `include`/`exclude` glob lists |
| CONF-04 | Config supports named sources (`[[sources]]` with `name` field) | TOML array-of-tables pattern; validated on load |
| CONF-05 | User can run `corpus add <dir>` to append a source to `corpus.toml` from CLI | `tomllib` read + `tomli-w` write; Typer command with `--name`/`--include`/`--exclude` |
| INGEST-01 | User can run `corpus index` to index all configured sources | Typer top-level `index` command; reads config, walks sources, embeds, writes LanceDB |
| INGEST-02 | Indexer supports `.md`, `.py`, `.ts`, `.js`, `.json`, `.yaml` file types | File extension dispatch in chunker; line-based fallback for `.ts`/`.js`/`.json`/`.yaml` |
| INGEST-03 | Structure-aware chunking: heading-based for `.md`, AST-based for `.py`, line-based fallback | Built-in `ast` module for Python; regex heading parser for Markdown |
| INGEST-04 | Deterministic content-hash-based chunk ID (re-indexing idempotent) | `sha256(file_path + chunk_text)` as `chunk_id`; used as merge key in `merge_insert` |
| INGEST-05 | Incremental indexing: only re-embeds files whose content has changed | mtime fast-check; sha256 full-check on mtime change; skip if hash unchanged |
| INGEST-06 | Per-chunk metadata: file path, line range, file type, source name, content hash, embedding model version, last-indexed timestamp | LanceModel scalar fields; all stored in LanceDB table |
| INGEST-07 | Re-index detects and removes stale chunks for deleted/moved files (no ghost documents) | `when_not_matched_by_source_delete()` in `merge_insert`; or explicit `table.delete()` by source path predicate |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `lancedb` | 0.29.2 | Embedded vector store with hybrid search | Ships BM25+vector+RRF natively; no separate DB process; Lance columnar format |
| `ollama` (python) | ≥0.3.0 (already in pyproject.toml) | Generate embeddings via local Ollama | Batch `embed()` API; async available; type-safe `EmbedResponse` |
| `tomllib` | stdlib (Python 3.11+) | Parse `corpus.toml` | Zero dependencies; TOML 1.0 compliant; already in Python 3.12 |
| `tomli-w` | latest | Write `corpus.toml` (for `corpus add`) | `tomllib` is read-only; `tomli-w` is the canonical write complement |
| `platformdirs` | latest | XDG-compliant config/data dirs | Returns `~/.config/corpus/` and `~/.local/share/corpus/` cross-platform |
| `typer[all]` | ≥0.12.0 (already in pyproject.toml) | CLI commands: `index`, `add`, future `search`/`status` | Already present; rich integration built-in |
| `rich` | ≥13.7.0 (already in pyproject.toml) | Progress bars, summary output | Already present; `Progress` context manager is the right pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pathlib` | stdlib | File walking, extension dispatch, glob matching | All file path operations |
| `hashlib` | stdlib | sha256 content hashing for chunk IDs and mtime+hash incremental check | Chunk ID generation and change detection |
| `ast` | stdlib | Python AST walking for function/class boundary chunking | `.py` file chunking only |
| `lancedb.pydantic.LanceModel` | (part of lancedb) | Schema definition with type safety | Defining the `Chunk` table schema |
| `lancedb.pydantic.Vector` | (part of lancedb) | Vector column type in LanceModel | Declaring embedding vector column |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `lancedb` | `sqlite-vec` | sqlite-vec lacks native BM25/hybrid — Phase 2 would require adding a separate FTS layer |
| `lancedb` | `chromadb` | ChromaDB is a server process; LanceDB is embedded, no daemon required |
| `platformdirs` | `xdg-base-dirs` | Both correct; `platformdirs` is more widely used and already available in many envs |
| `tomli-w` | manual TOML string building | String building is brittle; `tomli-w` handles quoting, escaping, array-of-tables correctly |
| built-in `ast` | `tree-sitter` | `tree-sitter` is richer but is a v2 requirement (IDX-01); stdlib `ast` is sufficient for Phase 1 |
| `rich.Progress` | `tqdm` | `rich` is already a dependency; no reason to add `tqdm` |

**Installation:**
```bash
uv add lancedb tomli-w platformdirs
# ollama, typer[all], rich, pathlib, hashlib, ast are already present or stdlib
```

## Architecture Patterns

### Recommended Project Structure
```
src/corpus_analyzer/
├── config/
│   ├── __init__.py
│   ├── schema.py          # Pydantic models: CorpusConfig, SourceConfig, EmbeddingConfig
│   └── io.py              # load_config(), save_config(), add_source()
├── ingest/
│   ├── __init__.py
│   ├── chunker.py         # chunk_markdown(), chunk_python(), chunk_lines()
│   ├── embedder.py        # OllamaEmbedder, embed_batch()
│   ├── indexer.py         # CorpusIndex: open(), index_source(), remove_stale()
│   └── scanner.py         # walk_source(), hash_file()
├── store/
│   ├── __init__.py
│   └── schema.py          # LanceModel: ChunkRecord (vector + all metadata fields)
└── cli.py                 # 'corpus add', 'corpus index' commands
```

This separates concerns: `config/` is TOML read/write only; `store/` is the LanceDB schema; `ingest/` is the pipeline logic. The existing `corpus_analyzer/` structure (extractors, classifiers, etc.) remains untouched — this is a new tool, not a refactor.

### Pattern 1: LanceDB Schema Definition (Schema Lock-In Prevention)

**What:** Define all fields needed by both Phase 1 and Phase 2 in the initial `LanceModel`. Changing vector dimensions or adding non-nullable columns requires a full table rebuild.

**When to use:** At table creation time — only once.

**Example:**
```python
# Source: https://docs.lancedb.com/embedding/quickstart
import lancedb
from lancedb.pydantic import LanceModel, Vector
from datetime import datetime

class ChunkRecord(LanceModel):
    """Schema for a single indexed chunk stored in LanceDB."""
    # Identity
    chunk_id: str           # sha256(source_name + file_path + chunk_text) — merge key
    file_path: str          # absolute path to source file
    source_name: str        # name from corpus.toml [[sources]]
    # Content
    text: str               # raw chunk text
    vector: Vector(768)     # embedding — dimension depends on model (nomic=768, mxbai=1024)
    # Location
    start_line: int
    end_line: int
    file_type: str          # ".md", ".py", ".ts", etc.
    # Bookkeeping
    content_hash: str       # sha256 of full file content at index time
    embedding_model: str    # e.g. "nomic-embed-text" — validated on every query
    indexed_at: str         # ISO8601 timestamp as string (LanceDB datetime support varies)
```

**CRITICAL:** `Vector(768)` must match the actual model dimension. `nomic-embed-text` produces 768-dim vectors; `mxbai-embed-large` produces 1024-dim. This dimension is baked into the schema at table creation. Changing models requires dropping and rebuilding the table.

### Pattern 2: Incremental Sync with merge_insert

**What:** Use `merge_insert` with the chunk's content-hash-based ID as the key. This handles inserts (new chunks), updates (changed chunks), and ghost document removal (stale chunks) in a single operation per source.

**When to use:** Every `corpus index` run.

**Example:**
```python
# Source: https://docs.lancedb.com/tables/update
def sync_source(table, new_chunks: list[dict], source_name: str) -> None:
    """Upsert new chunks and delete stale ones for a given source."""
    (
        table.merge_insert("chunk_id")
        .when_matched_update_all()           # update changed chunks
        .when_not_matched_insert_all()       # insert new chunks
        .when_not_matched_by_source_delete() # delete ghost chunks for this source
        .execute(new_chunks)
    )
```

**Warning:** `when_not_matched_by_source_delete()` removes ALL target rows not present in the incoming data — it is source-scoped in the merge's comparison. If you pass only chunks for `source_name = "my-skills"`, you must filter the source dataset passed to `merge_insert` OR use a predicate. The safer pattern for per-source incremental sync is: collect all current chunks for the source, merge_insert, then use `table.delete(f"source_name = '{source_name}' AND chunk_id NOT IN ({ids})")` explicitly.

### Pattern 3: mtime + sha256 Change Detection

**What:** Check `os.stat().st_mtime` first (cheap); only compute sha256 if mtime changed (or if no previous record). Skip embedding if sha256 matches the stored `content_hash`.

**When to use:** Before embedding any file during `corpus index`.

**Example:**
```python
import hashlib, os
from pathlib import Path

def file_content_hash(path: Path) -> str:
    """Compute sha256 of file content for change detection."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def needs_reindex(path: Path, stored_mtime: float, stored_hash: str) -> bool:
    """Return True if file must be re-embedded."""
    current_mtime = os.stat(path).st_mtime
    if current_mtime == stored_mtime:
        return False  # fast path: mtime unchanged
    return file_content_hash(path) != stored_hash
```

The `stored_mtime` and `stored_hash` come from a lightweight index (e.g., a dict keyed by `file_path` built from a `table.search(...).to_list()` or a separate SQLite tracking table).

### Pattern 4: Rich Progress Bar

**What:** Use `rich.progress.Progress` context manager. `typer[all]` ships rich, so it's already available.

**When to use:** In the `corpus index` command.

**Example:**
```python
# Source: https://rich.readthedocs.io/en/stable/progress.html
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

with Progress(
    SpinnerColumn(),
    TextColumn("[bold blue]{task.description}"),
    BarColumn(),
    TextColumn("{task.completed}/{task.total} files"),
    TimeElapsedColumn(),
) as progress:
    task = progress.add_task(f"Indexing {source.name}...", total=total_files)
    for file in files:
        # process file
        progress.advance(task)
```

### Pattern 5: XDG Config and Data Paths

**What:** Use `platformdirs.user_config_dir()` and `platformdirs.user_data_dir()` to get the correct paths on all platforms.

**Example:**
```python
from platformdirs import user_config_dir, user_data_dir
from pathlib import Path

CONFIG_DIR = Path(user_config_dir("corpus"))    # ~/.config/corpus/
CONFIG_PATH = CONFIG_DIR / "corpus.toml"
DATA_DIR = Path(user_data_dir("corpus"))        # ~/.local/share/corpus/
LANCEDB_PATH = DATA_DIR / "index"
```

### Pattern 6: TOML Read/Write

**What:** `tomllib` (stdlib) for reading; `tomli-w` for writing. Both use Python dicts as the interchange format.

**Example:**
```python
import tomllib, tomli_w
from pathlib import Path

def load_config(path: Path) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)

def save_config(path: Path, config: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        tomli_w.dump(config, f)
```

### Anti-Patterns to Avoid

- **Storing vectors in SQLite alongside metadata:** Don't use the existing `corpus.sqlite` for the vector index. LanceDB is the vector store; SQLite is the old pipeline. Keep them separate.
- **Calling `embed()` one chunk at a time:** Ollama's `embed()` supports batch input. Pass all chunks for a file (or even a whole source) as a list in one API call.
- **Rebuilding the full index on every run:** Only embed chunks whose content has changed. The mtime+sha256 pattern is required by INGEST-05 and prevents multi-minute re-runs.
- **Using `mode="overwrite"` on index runs:** This drops the entire table. Use `merge_insert` for incremental runs; reserve `overwrite` for a future `corpus reindex --force` command.
- **Hardcoding vector dimensions:** Always read `ndims()` from the embedding model response on first run; do not hardcode `768`. Store the expected dimension alongside the model name so the schema can assert consistency.
- **Building a new CLI app from scratch:** The existing `cli.py` uses Typer. Add the new `corpus add` and `corpus index` commands to the existing `app` or a new Typer sub-app added with `app.add_typer()`.
- **Skipping `table.optimize()` on large loads:** After bulk inserts, soft-deleted rows accumulate. Call `table.optimize()` at the end of a full index run to compact storage.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Vector storage + ANN search | Custom numpy index | `lancedb` | BM25, hybrid, disk-resident, ACID transactions |
| Ghost document removal | Custom "seen files" tracking table | `merge_insert(...).when_not_matched_by_source_delete()` | Built-in to LanceDB's merge API |
| Embedding generation | HTTP calls to Ollama REST API | `ollama.embed()` | Typed responses, error handling, batch support |
| XDG directory paths | `os.path.expanduser("~/.config/...")` | `platformdirs` | Respects `XDG_CONFIG_HOME` env override, cross-platform |
| TOML writing | Manual string building | `tomli-w` | Handles quoting, escaping, array-of-tables, type coercion correctly |
| Python code chunking | Regex on source text | `ast.walk()` on parsed AST | Handles decorators, nested classes, comments, multiline strings correctly |

**Key insight:** Every problem in this phase has a well-maintained library solution. The phase's implementation complexity is in the integration plumbing, not in any individual component.

## Common Pitfalls

### Pitfall 1: Vector Dimension Mismatch
**What goes wrong:** Table created with `Vector(768)` but operator switches to `mxbai-embed-large` (1024-dim) — all subsequent inserts fail.
**Why it happens:** LanceDB bakes vector dimensions into the schema at table creation. Changing the embedding model is a breaking change to the schema.
**How to avoid:** Store `embedding_model` as a metadata field. On every `corpus index` run, read the model from config and compare to the stored `embedding_model` in the table. If they differ, abort with: `"Model mismatch: index was built with {stored}, config says {new}. Run 'corpus reindex --force' to rebuild."` Do not auto-migrate silently.
**Warning signs:** `pyarrow.lib.ArrowInvalid: Vector dimension mismatch` on `table.add()`.

### Pitfall 2: Ghost Documents on Partial Source Sync
**What goes wrong:** `merge_insert` with `when_not_matched_by_source_delete()` is called with the full incoming dataset — which only covers one source — but the "not matched by source" comparison covers the entire table. Result: chunks from all OTHER sources are deleted.
**Why it happens:** `when_not_matched_by_source_delete()` operates on the full target table unless you scope the merge with a filter predicate.
**How to avoid:** One of two approaches:
  1. Per-source: do NOT use `when_not_matched_by_source_delete()`. Instead, after upserting, explicitly delete: `table.delete(f"source_name = 'X' AND chunk_id NOT IN ({current_chunk_ids_sql_list})")`
  2. Full-index merge: pass ALL chunks from ALL sources in one `merge_insert` call with global `when_not_matched_by_source_delete()`.
**Warning signs:** Source counts in `corpus status` show unexpectedly zero chunks for non-indexed sources after a partial run.

### Pitfall 3: TOML Write Corrupts Config on `corpus add`
**What goes wrong:** Round-tripping `corpus.toml` through `tomllib.load` → modify → `tomli_w.dump` drops comments or reorders keys.
**Why it happens:** TOML parsers discard comments; `tomli_w` does not preserve original formatting.
**How to avoid:** This is by design and acceptable. Document clearly in help text that comments in `corpus.toml` will not be preserved after `corpus add`. Users who want comments should edit manually.
**Warning signs:** User-added comments disappear after `corpus add` invocation.

### Pitfall 4: Ollama Not Running at Index Time
**What goes wrong:** `corpus index` hangs or throws an obscure connection error if Ollama is not running.
**Why it happens:** `ollama.embed()` makes an HTTP connection to `localhost:11434`.
**How to avoid:** At startup of `corpus index`, make a lightweight probe call (e.g., `ollama.list()` or a single test embed) and fail fast with a clear message: `"Cannot connect to Ollama at {host}. Start Ollama with: ollama serve"`. Do not auto-start Ollama.
**Warning signs:** `httpx.ConnectError` or `ConnectionRefusedError` bubbling up without user-friendly message.

### Pitfall 5: Large File Chunking Produces Oversized Embeddings
**What goes wrong:** A single heading section in a large `.md` file is 50,000 tokens, far exceeding the model's context window (nomic-embed-text: 8192 tokens).
**Why it happens:** Heading-based chunking produces variable-sized chunks.
**How to avoid:** Apply a secondary line-based split as a fallback within each heading section if `len(text.split())` exceeds a threshold (e.g., 1500 words / ~2000 tokens). The exact threshold is Claude's Discretion — a sensible default is 512 tokens (≈380 words) for overlap-based chunking.
**Warning signs:** Ollama returning truncation warnings or embedding quality degradation on large markdown files.

### Pitfall 6: sha256 as Only Chunk ID Component
**What goes wrong:** Two different files with identical content in different sources produce the same `chunk_id`, causing one to silently overwrite the other during `merge_insert`.
**Why it happens:** If `chunk_id = sha256(text)` only, identical text at different paths collides.
**How to avoid:** `chunk_id = sha256(source_name + file_path + str(start_line) + text)` — include path and line range in the hash input to guarantee uniqueness across all sources.
**Warning signs:** Lower-than-expected chunk counts in `corpus status` after indexing multiple sources with shared boilerplate content.

## Code Examples

Verified patterns from official sources:

### Ollama Batch Embeddings
```python
# Source: https://github.com/ollama/ollama-python/blob/main/README.md
import ollama

response = ollama.embed(
    model="nomic-embed-text",
    input=["chunk text one", "chunk text two", "chunk text three"]
)
vectors = response.embeddings  # list of list[float]
```

### LanceDB Connect + Create or Open Table
```python
# Source: https://docs.lancedb.com/tables
import lancedb
from pathlib import Path

db = lancedb.connect(str(DATA_DIR / "index"))

if "chunks" in db.table_names():
    table = db.open_table("chunks")
else:
    table = db.create_table("chunks", schema=ChunkRecord)
```

### merge_insert Upsert
```python
# Source: https://docs.lancedb.com/tables/update
table.merge_insert("chunk_id") \
    .when_matched_update_all() \
    .when_not_matched_insert_all() \
    .execute(new_chunk_dicts)
```

### Delete Stale Chunks for a Source (safe per-source approach)
```python
# Source: https://docs.lancedb.com/tables/update
current_ids = {c["chunk_id"] for c in new_chunks}
id_list = ", ".join(f"'{cid}'" for cid in current_ids)
table.delete(
    f"source_name = '{source_name}' AND chunk_id NOT IN ({id_list})"
)
```

### Python AST Chunking (function and class boundaries)
```python
# Source: https://docs.python.org/3/library/ast.html
import ast
from pathlib import Path

def chunk_python(path: Path) -> list[dict]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    chunks = []
    lines = source.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = node.lineno - 1
            end = node.end_lineno  # type: ignore[attr-defined]
            text = "\n".join(lines[start:end])
            chunks.append({"text": text, "start_line": start + 1, "end_line": end})
    return chunks
```

### Markdown Heading-Based Chunking
```python
import re
from pathlib import Path

def chunk_markdown(path: Path) -> list[dict]:
    """Split on ATX headings (#, ##, ###, etc.)."""
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)
    heading_re = re.compile(r"^#{1,6}\s")
    chunks, current, start = [], [], 1
    for i, line in enumerate(lines, start=1):
        if heading_re.match(line) and current:
            chunks.append({"text": "".join(current), "start_line": start, "end_line": i - 1})
            current, start = [line], i
        else:
            current.append(line)
    if current:
        chunks.append({"text": "".join(current), "start_line": start, "end_line": len(lines)})
    return chunks
```

### corpus add — TOML Append Source
```python
import tomllib, tomli_w
from pathlib import Path

def add_source(config_path: Path, name: str, path: str,
               include: list[str], exclude: list[str]) -> None:
    config = tomllib.loads(config_path.read_text()) if config_path.exists() else {}
    sources = config.setdefault("sources", [])
    if any(s.get("name") == name or s.get("path") == path for s in sources):
        raise ValueError(f"Source '{name}' or path '{path}' already exists. Use --force to re-add.")
    sources.append({"name": name, "path": path, "include": include, "exclude": exclude})
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_bytes(tomli_w.dumps(config).encode())
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Separate vector DB process (Chroma, Qdrant) | Embedded LanceDB (no daemon) | 2023-2024 | No infrastructure to manage; index is just files |
| `tomli` third-party parser | `tomllib` stdlib | Python 3.11 (2022) | Zero-dep TOML reading; already available in Python 3.12 |
| `ollama.embeddings()` (old API) | `ollama.embed()` (current API) | ~2024 | Batch support; `EmbedResponse` typed return |
| Custom ghost-doc cleanup scripts | `merge_insert(...).when_not_matched_by_source_delete()` | LanceDB 2024+ | Single-call incremental sync |
| Monolithic index rebuilds | Per-source incremental with mtime+sha256 | Established pattern | Sub-second re-index for unchanged files |

**Deprecated/outdated:**
- `ollama.embeddings()`: the older single-embedding API. Use `ollama.embed()` which accepts `input` as a string or list.
- `lancedb` ≤0.5.x: pre-stable API; `merge_insert` and `when_not_matched_by_source_delete` require 0.10+. Current is 0.29.2 — install latest.

## Embedding Model Recommendation (Claude's Discretion)

**Recommendation: `nomic-embed-text`**

Rationale based on research findings:
- Context length: 8,192 tokens vs mxbai-embed-large's 512 tokens — critical for agent skill files which can be long
- Inference speed: "Very Fast" (548 MB model) vs mxbai "Fast" (1,340 MB) — matters for indexing hundreds of files
- MTEB retrieval score: nomic 49.01 vs mxbai 54.39 — mxbai wins on general retrieval benchmarks
- nomic outperforms mxbai on short/direct questions (retrieval accuracy 57.5% vs 63.75% in one benchmark)
- Agent skill files are typically short, structured Markdown — nomic's advantage in short semantic queries applies

**For this use case** (agent files, skill files, short structured markdown): `nomic-embed-text` is the better fit. mxbai-embed-large's higher MTEB score is primarily on longer, context-rich documents.

Vector dimension for `nomic-embed-text`: **768** — use `Vector(768)` in the schema.

**Chunk size recommendation (Claude's Discretion):**
- Markdown heading sections: max 512 tokens (~380 words) with secondary line-split fallback if exceeded
- Python AST nodes: no size limit (function/class boundaries are semantic); but cap at 1500 lines as a safety guard
- Line-based fallback: 50 lines, 10-line overlap

## Open Questions

1. **Does LanceDB support datetime columns natively in Python LanceModel?**
   - What we know: LanceDB stores Lance format which supports timestamps; Pydantic LanceModel docs show string fields
   - What's unclear: Whether `datetime` type in `LanceModel` serializes correctly without pyarrow coercion errors
   - Recommendation: Use `str` (ISO8601) for `indexed_at` to avoid type system surprises; can always cast at query time

2. **Behavior of `merge_insert` with empty source list**
   - What we know: `when_not_matched_by_source_delete()` with an empty input would delete all rows
   - What's unclear: Whether LanceDB raises an error or silently deletes everything if `new_chunks = []`
   - Recommendation: Guard against empty chunk list explicitly: `if not new_chunks: return` before calling `merge_insert`

3. **Ollama `embed()` error behavior when model not pulled**
   - What we know: Ollama returns an error if the model is not present locally
   - What's unclear: Whether it's a typed exception or raw HTTP error in the Python SDK
   - Recommendation: Wrap `ollama.embed()` in a try/except; catch `ollama.ResponseError` and surface: `"Model '{model}' not found. Pull it with: ollama pull {model}"`

## Sources

### Primary (HIGH confidence)
- `/websites/lancedb` (Context7) — table creation, merge_insert, delete, upsert, schema patterns
- `/ollama/ollama-python` (Context7) — `embed()` API, batch embeddings, async client
- https://docs.lancedb.com/tables/update — merge_insert, delete, when_not_matched_by_source_delete
- https://docs.python.org/3/library/ast.html — ast.walk(), FunctionDef, ClassDef, end_lineno
- https://docs.python.org/3.12/library/tomllib.html — tomllib stdlib TOML parser
- https://pypi.org/project/lancedb/ — version 0.29.2 confirmed Feb 2026

### Secondary (MEDIUM confidence)
- https://docs.lancedb.com/embedding/quickstart — LanceModel + embedding registry patterns (verified with Context7)
- https://rich.readthedocs.io/en/stable/progress.html — Progress context manager (verified: rich is already a dependency)
- https://github.com/tox-dev/platformdirs — XDG path helper (widely used, well maintained)
- https://typer.tiangolo.com/tutorial/progressbar/ — Typer+Rich progress bar pattern
- https://www.tigerdata.com/blog/finding-the-best-open-source-embedding-model-for-rag — nomic vs mxbai benchmark data (verified against multiple sources)

### Tertiary (LOW confidence)
- https://fahadsid1770.medium.com/... — LanceDB admin handbook (Medium article, single source; core patterns verified via official docs)
- Embedding model MTEB benchmark scores — from multiple web sources (Jan-Feb 2025); scores are directionally correct but exact values vary by benchmark version

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified via Context7 or official docs; versions from PyPI
- Architecture: HIGH — patterns taken directly from LanceDB official docs and verified via Context7
- Pitfalls: MEDIUM-HIGH — ghost document pitfall verified against official merge_insert docs; schema lock-in verified via LanceDB architecture docs; others from first-principles analysis of the known behaviors
- Embedding model recommendation: MEDIUM — benchmark data from multiple secondary sources; choice is reasonable but not definitive

**Research date:** 2026-02-23
**Valid until:** 2026-03-23 (LanceDB releases ~every 2 weeks; core patterns are stable)

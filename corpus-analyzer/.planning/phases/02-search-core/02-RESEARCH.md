# Phase 2: Search Core - Research

**Researched:** 2026-02-23
**Domain:** LanceDB hybrid search (BM25+vector+RRF), construct classification, Ollama summary generation, Rich CLI output
**Confidence:** HIGH

## Summary

Phase 2 builds on top of a fully implemented Phase 1 foundation. The LanceDB `chunks` table exists, the ingestion pipeline is complete, and the CLI framework is in place. Phase 2's job is to add three capabilities on top of that foundation: (1) hybrid search via LanceDB's native `query_type="hybrid"` + `RRFReranker`, (2) construct type classification stored in the `chunks` schema, and (3) AI summary generation at index time.

The most critical architectural decision is that the existing `ChunkRecord` schema must be extended with two new columns — `construct_type` and `summary` — before any other Phase 2 work begins. LanceDB supports schema evolution via `table.add_columns()` for nullable columns, which means the existing index can be upgraded in-place without a full rebuild. However, newly classified/summarised fields only populate for files re-indexed after the upgrade, so the indexer must backfill these fields during the first `corpus index` run after Phase 2 lands.

The hybrid search pipeline is straightforward to wire up: `create_fts_index("text")` must be called once (idempotent with `replace=True`), then every search call uses `query_type="hybrid"` with `RRFReranker()`. Filtering by `source_name`, `file_type`, and `construct_type` is done via `.where()` SQL clauses chained onto the search builder. The `_relevance_score` column (returned by RRFReranker) is the display score for CLI output.

**Primary recommendation:** Treat schema extension as Plan Wave 1 (add nullable `construct_type` and `summary` columns via `add_columns`), FTS index creation as Wave 1, search engine as Wave 2, classification logic as Wave 3, summary generation as Wave 4, and CLI commands as Wave 5. This ordering prevents blocking dependencies.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Search result display:** Default limit 10; each result shows file path, snippet, construct type, and score; snippet is 2-4 lines of surrounding context truncated at word boundaries; Rich formatting with path highlighted, score dimmed; graceful degradation when piped.
- **BM25 + vector fusion:** Reciprocal Rank Fusion (RRF) — no raw score normalization needed; exact title/filename matches boosted in BM25 step; zero results show clear message echoing query.
- **Construct classification:** Hybrid approach — rule-based heuristics first, LLM fallback only when rules can't classify; rule signals: file path segments, file extension, frontmatter fields; unclassified fallback label is `documentation`; classification stored at file level (all chunks from a file inherit same construct type).
- **AI summaries:** Generated at index time, stored alongside document, regenerated only when file content changes; 1-2 sentences covering what the file does and when to use it; shown by default in every search result; uses `CORPUS_OLLAMA_MODEL` (same model as embeddings).

### Claude's Discretion

- Exact score display format (raw `_relevance_score` float vs. normalized 0-1)
- Prompt template for summary generation
- How `corpus status` output is laid out
- How multiple `--source`/`--type`/`--construct` filters compose (AND semantics assumed)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SEARCH-01 | User can search with a natural language query and get ranked results | `table.search(query, query_type="hybrid").rerank(RRFReranker())` — direct LanceDB API |
| SEARCH-02 | Hybrid ranking: vector similarity + BM25, fused via RRF | `RRFReranker` in `lancedb.rerankers`; FTS index via `create_fts_index("text")`; `query_type="hybrid"` |
| SEARCH-03 | User can filter results by source name | `.where("source_name = 'X'")` SQL clause on search builder |
| SEARCH-04 | User can filter results by file type | `.where("file_type = '.md'")` SQL clause on search builder |
| SEARCH-05 | Result format: snippets for CLI (full content/structured objects for MCP/API in Phase 3) | Snippet extracted from `text` field post-search; 2-4 surrounding lines around best match window |
| CLASS-01 | Classify each file by construct type: `skill`, `prompt`, `workflow`, `agent_config`, `code`, `documentation` | Rule-based classifier + LLM fallback; stored in `construct_type` nullable column (schema evolution) |
| CLASS-02 | Construct type stored as metadata per chunk, filterable at query time | `construct_type: str` column added to `ChunkRecord` via `add_columns`; propagated to all chunks of a file |
| CLASS-03 | User can filter search results by construct type | `.where("construct_type = 'skill'")` SQL clause |
| SUMM-01 | Indexer generates AI summary for each file at index time via Ollama | `ollama.chat()` or `ollama.generate()` with a focused 1-2 sentence prompt; stored in `summary` column |
| SUMM-02 | Summaries embedded and indexed alongside raw chunk text | Summary text concatenated or stored as a separate chunk with `is_summary=True` flag; OR stored as scalar and prepended to first chunk's text before embedding |
| SUMM-03 | Summary generation skippable per source (config flag) | `summarize: bool = True` field on `SourceConfig`; checked before generating summaries |
| CLI-01 | `corpus index` indexes all configured sources (incremental) | Already implemented in Phase 1; Phase 2 extends it to classify + summarize during indexing |
| CLI-02 | `corpus search "<query>"` returns ranked results with file path, snippet, and score | New Typer `search` command; calls hybrid search engine; Rich table output |
| CLI-03 | `corpus search` supports `--source`, `--type`, `--construct`, `--limit` flags | Typer `Option` flags; translated to `.where()` SQL predicates |
| CLI-04 | `corpus status` shows file count, chunk count, last indexed, embedding model | New Typer `status` command; queries LanceDB table for counts and metadata |
| CLI-05 | `corpus add <dir> [--name <name>]` appends directory to corpus.toml | Already implemented in Phase 1; no changes needed |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `lancedb` | 0.29.2 (already installed) | Hybrid search via `query_type="hybrid"` + RRFReranker + FTS index | Ships everything needed — no additional search library required |
| `lancedb.rerankers.RRFReranker` | (part of lancedb) | Reciprocal Rank Fusion fusion of vector + BM25 scores | Locked decision; built-in, zero config, no external API calls |
| `ollama` (python) | ≥0.3.0 (already installed) | Generate AI summaries at index time | Already present; use `ollama.generate()` or `ollama.chat()` with `CORPUS_OLLAMA_MODEL` |
| `typer[all]` | ≥0.12.0 (already installed) | `search` and `status` CLI commands | Already present; same pattern as `add` and `index` |
| `rich` | ≥13.7.0 (already installed) | Rich formatted search results (path highlighted, score dimmed) | Already present; `rich.table.Table` or `rich.panel.Panel` for result display |
| `python-frontmatter` | ≥1.1.0 (already installed) | Read YAML frontmatter for construct classification signals | Already present; `frontmatter.load()` exposes `name:`, `description:` etc. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `re` | stdlib | Regex for rule-based construct classification (path segments, filename patterns) | Classifier rules engine |
| `pathlib` | stdlib | Path analysis for construct type signals (e.g. `"skills/"` in path parts) | Classifier heuristics |
| `tomllib` | stdlib | Read `SourceConfig.summarize` flag (if added to config schema) | Only if per-source summary toggle is implemented |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `RRFReranker` (built-in) | `LinearCombinationReranker` | RRF is locked by user; linear requires weight tuning; RRF needs no normalization |
| `lancedb.rerankers.RRFReranker` | Manual Python RRF implementation | Don't hand-roll — LanceDB's implementation is verified and handles edge cases |
| `ollama.generate()` for summaries | `ollama.chat()` | Both work; `generate()` is simpler for single-shot prompts without conversation history |
| Rule-based + LLM fallback classifier | Pure LLM classifier | Locked decision; rules are fast/free for the majority of files; LLM only for ambiguous cases |

**Installation:**
```bash
# All dependencies already in pyproject.toml — no new packages required
uv sync
```

## Architecture Patterns

### Recommended Project Structure (additions to Phase 1)
```
src/corpus_analyzer/
├── search/
│   ├── __init__.py
│   ├── engine.py          # CorpusSearch: hybrid_search(), status()
│   ├── classifier.py      # construct_type rules + LLM fallback
│   ├── summarizer.py      # generate_summary() via Ollama
│   └── formatter.py       # snippet extraction, Rich result formatting
├── store/
│   ├── __init__.py
│   └── schema.py          # ChunkRecord — add construct_type, summary columns
├── config/
│   └── schema.py          # SourceConfig — add summarize: bool field
└── cli.py                 # Add: search_command(), status_command()
```

The `search/` module is new. All existing Phase 1 modules (`ingest/`, `config/`, `store/`) are extended, not replaced.

### Pattern 1: FTS Index Creation (One-Time, Idempotent)

**What:** `create_fts_index` must be called on the `chunks` table before any hybrid search. Use `replace=True` to make it idempotent — safe to call on every `corpus index` run.

**When to use:** At the end of every `corpus index` run (after all chunks are written).

**Example:**
```python
# Source: https://docs.lancedb.com/integrations/reranking/rrf
table.create_fts_index("text", replace=True)
```

**Important:** The FTS index only covers the `text` column. If summaries are to be searchable, concatenate or prepend the summary to the `text` before embedding and before indexing, OR store them in a separate summary chunk.

### Pattern 2: Hybrid Search with RRF

**What:** Pass `query_type="hybrid"` to `table.search()` and chain `.rerank(RRFReranker())`. The reranker fuses vector similarity (`_distance`) and BM25 (`score`) into a single `_relevance_score`. Filter with `.where()` SQL predicates.

**When to use:** Every `corpus search` invocation.

**Example:**
```python
# Source: https://docs.lancedb.com/integrations/reranking/rrf
from lancedb.rerankers import RRFReranker

reranker = RRFReranker()

results = (
    table.search("systematic debugging", query_type="hybrid")
    .rerank(reranker=reranker)
    .where("source_name = 'my-skills'")   # optional filter
    .where("file_type = '.md'")            # optional filter
    .where("construct_type = 'skill'")     # optional filter
    .limit(10)
    .to_list()
)
```

Each result dict contains: all `ChunkRecord` fields + `_relevance_score` (float, higher = more relevant).

**Score display:** Use `_relevance_score` directly as the display score. It's a float produced by RRF; it does not need to be normalized. Display it with 3 decimal places (e.g. `0.032`) — this is honest and readable.

### Pattern 3: Schema Evolution — Adding Nullable Columns

**What:** Add `construct_type` and `summary` as nullable columns to the existing `chunks` table. This upgrades the live index without dropping it. Existing rows will have `None` for these fields until re-indexed.

**When to use:** Once, at `CorpusIndex.open()` time — check whether columns exist before adding.

**Example:**
```python
# Source: https://docs.lancedb.com/tables/schema
def ensure_schema_v2(table: lancedb.table.Table) -> None:
    """Add Phase 2 columns if they don't exist."""
    existing_cols = {field.name for field in table.schema}
    if "construct_type" not in existing_cols:
        table.add_columns({"construct_type": "cast(NULL as string)"})
    if "summary" not in existing_cols:
        table.add_columns({"summary": "cast(NULL as string)"})
```

**Critical:** After adding nullable columns, all chunks for previously-indexed files will have `construct_type = NULL`. The first `corpus index` run after Phase 2 will re-classify and re-summarize changed files, but unchanged files (same hash) will NOT be re-processed unless you force reindex. This is acceptable because the fallback is `documentation` for any unclassified file — null values must be handled as `"documentation"` in search display.

### Pattern 4: Construct Type Classification (Rule-Based + LLM Fallback)

**What:** A two-tier classifier. Tier 1 checks path segments, filename, and frontmatter fields against rules. Tier 2 calls Ollama only when Tier 1 produces no confident match. Result is one of six labels: `skill`, `prompt`, `workflow`, `agent_config`, `code`, `documentation`.

**When to use:** During `corpus index`, once per file (not per chunk). Result is stored in all chunks for that file.

**Rule signals (Tier 1):**

| Signal | Construct Type |
|--------|---------------|
| `skills/` or `skill` in path parts | `skill` |
| `prompts/` or `prompt` in path parts | `prompt` |
| `workflows/` in path parts | `workflow` |
| File extension `.py`, `.ts`, `.js` | `code` |
| Frontmatter has `name:` + `description:` + `tools:` | `agent_config` |
| Frontmatter has `name:` + `description:` (no `tools:`) | `skill` |
| Filename contains `workflow` | `workflow` |
| Filename contains `prompt` | `prompt` |
| Otherwise | → LLM fallback |
| LLM fallback fails or is disabled | `documentation` |

**Example:**
```python
import re
from pathlib import Path
import frontmatter  # python-frontmatter

CONSTRUCT_TYPES = {"skill", "prompt", "workflow", "agent_config", "code", "documentation"}

def classify_by_rules(file_path: Path, text: str) -> str | None:
    """Return construct type from rules, or None if unclear."""
    path_lower = file_path.as_posix().lower()
    parts = set(file_path.parts)

    # Extension-based
    if file_path.suffix in {".py", ".ts", ".js"}:
        return "code"

    # Path segment signals
    if any("skill" in p.lower() for p in parts):
        return "skill"
    if any("prompt" in p.lower() for p in parts):
        return "prompt"
    if any("workflow" in p.lower() for p in parts):
        return "workflow"

    # Frontmatter signals (for .md and .yaml files)
    if file_path.suffix in {".md", ".yaml", ".yml"}:
        try:
            post = frontmatter.loads(text)
            has_name = "name" in post.metadata
            has_desc = "description" in post.metadata
            has_tools = "tools" in post.metadata
            if has_name and has_desc and has_tools:
                return "agent_config"
            if has_name and has_desc:
                return "skill"
        except Exception:
            pass

    return None  # unclear — trigger LLM fallback
```

### Pattern 5: Summary Generation via Ollama

**What:** Call `ollama.generate()` with a focused prompt. Generate once per file, store in `summary` column. Skip if file content hash unchanged from previous index run.

**When to use:** During `corpus index`, after classification, per file (not per chunk).

**Example:**
```python
import ollama

SUMMARY_PROMPT_TEMPLATE = """You are indexing files in an AI agent library.
Write 1-2 sentences describing what this file does and when an agent should use it.
Be specific and agent-actionable. Do not start with "This file".

File: {filename}
Content:
{content}

Summary:"""

def generate_summary(filename: str, content: str, model: str) -> str:
    """Generate a 1-2 sentence summary using Ollama."""
    prompt = SUMMARY_PROMPT_TEMPLATE.format(
        filename=filename,
        content=content[:4000],  # truncate to avoid context overflow
    )
    response = ollama.generate(model=model, prompt=prompt)
    return response.response.strip()
```

**Note:** Summaries are stored as scalar strings in the `summary` column. For SUMM-02 (summaries embedded to improve retrieval on short files), the simplest approach is to prepend the summary to the `text` of the first chunk before embedding — this keeps the schema unchanged and requires no separate summary chunk handling. An alternative is to store a synthetic chunk with the summary text; this adds a separate row but is more explicit.

### Pattern 6: CLI `corpus search` with Rich Output

**What:** Typer command that calls the search engine, formats results with Rich. Output degrades gracefully when piped (Rich auto-detects TTY).

**Example:**
```python
from rich.console import Console
from rich.table import Table

console = Console()

@app.command("search")
def search_command(
    query: Annotated[str, typer.Argument(help="Natural language search query")],
    source: Annotated[str | None, typer.Option("--source", help="Filter by source name")] = None,
    type_: Annotated[str | None, typer.Option("--type", help="Filter by file type (.md, .py, etc.)")] = None,
    construct: Annotated[str | None, typer.Option("--construct", help="Filter by construct type")] = None,
    limit: Annotated[int, typer.Option("--limit", "-n", help="Max results")] = 10,
) -> None:
    """Search the indexed corpus with a natural language query."""
    results = search_engine.hybrid_search(
        query, source=source, file_type=type_, construct_type=construct, limit=limit
    )
    if not results:
        console.print(f'[yellow]No results for "[bold]{query}[/bold]"[/yellow]')
        return
    for result in results:
        console.print(f"[bold blue]{result['file_path']}[/]  "
                      f"[dim]{result.get('construct_type', 'documentation')}[/]  "
                      f"[dim]score: {result['_relevance_score']:.3f}[/]")
        if result.get("summary"):
            console.print(f"  [italic]{result['summary']}[/italic]")
        console.print(f"  {extract_snippet(result['text'], query)}")
        console.print()
```

### Pattern 7: Snippet Extraction

**What:** Extract 2-4 lines of context around the most relevant portion of the chunk text. Truncate at word boundaries.

**When to use:** In the result formatter, after search.

**Example:**
```python
def extract_snippet(text: str, query: str, max_lines: int = 3) -> str:
    """Extract a snippet of up to max_lines lines from text."""
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    # Find the line most likely to contain query terms
    query_terms = set(query.lower().split())
    best_line = 0
    best_score = -1
    for i, line in enumerate(lines):
        score = sum(1 for term in query_terms if term in line.lower())
        if score > best_score:
            best_score = score
            best_line = i
    # Return window around best line
    start = max(0, best_line - 1)
    end = min(len(lines), start + max_lines)
    snippet = "\n".join(lines[start:end])
    # Truncate at word boundary if too long
    if len(snippet) > 200:
        snippet = snippet[:200].rsplit(" ", 1)[0] + "…"
    return snippet
```

### Anti-Patterns to Avoid

- **Building hybrid search from scratch:** Don't implement custom RRF in Python or combine vector and BM25 scores manually. LanceDB's `RRFReranker` and `query_type="hybrid"` do exactly this correctly.
- **Calling `create_fts_index` without `replace=True`:** Without `replace=True`, calling it on an existing index raises an error. Always use `replace=True`.
- **Classifying at chunk level:** Construct type is a file-level attribute. Classify once per file, then store the result in all chunks from that file. Classifying each chunk independently wastes LLM calls and produces inconsistent results.
- **Regenerating summaries on every index run:** Check the file's `content_hash` before generating a summary. If the hash matches the stored hash, skip generation. Summary generation is the slowest step in Phase 2.
- **Hardcoding `.where()` filter composition as OR:** The user decision specifies AND semantics. Multiple `.where()` calls on the LanceDB query builder chain as AND. This is correct and should not be changed to OR.
- **Forgetting the FTS index in `corpus index`:** `create_fts_index("text", replace=True)` must be called after every batch of writes to keep the FTS index in sync. Add it to the end of `CorpusIndex.index_source()`.
- **Treating `_relevance_score` as a probability:** RRF scores are not probabilities. Do not present them as percentages. Display raw float with 3 decimal places.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| BM25 + vector fusion | Custom scoring combination | `RRFReranker` + `query_type="hybrid"` | LanceDB handles tantivy BM25, vector ANN, and fusion internally |
| Full-text search index | Separate Whoosh/SQLite FTS | `table.create_fts_index("text")` | LanceDB uses tantivy internally — embedded, fast, zero config |
| Schema migration | Drop and rebuild table | `table.add_columns({"col": "cast(NULL as string)"})` | LanceDB supports nullable column addition in-place |
| Result ranking | Sort by custom score | `.rerank(RRFReranker())` | Correct, verified, handles edge cases (empty BM25 result sets, etc.) |
| Frontmatter parsing | Manual YAML parsing | `python-frontmatter` (already installed) | Handles edge cases: no frontmatter, invalid YAML, mixed encodings |

**Key insight:** Every technical problem in Phase 2 has a first-class solution in the existing dependency set. The implementation is primarily integration work, not algorithm work.

## Common Pitfalls

### Pitfall 1: FTS Index Not Created Before First Search
**What goes wrong:** `table.search(query, query_type="hybrid")` raises an error or silently falls back to vector-only if no FTS index exists.
**Why it happens:** `query_type="hybrid"` requires a pre-built FTS index on the `text` column.
**How to avoid:** Call `table.create_fts_index("text", replace=True)` in `CorpusIndex.open()` (after table creation/opening) AND at the end of every `index_source()` run.
**Warning signs:** `RuntimeError` or empty BM25 scores on first search after fresh install.

### Pitfall 2: Schema Evolution Not Guarded — `add_columns` Called Twice
**What goes wrong:** `table.add_columns({"construct_type": "cast(NULL as string)"})` raises if the column already exists.
**Why it happens:** LanceDB does not silently skip `add_columns` if the column is present.
**How to avoid:** Always guard with: `if "construct_type" not in {f.name for f in table.schema}:` before calling `add_columns`.
**Warning signs:** `pyarrow.lib.ArrowInvalid: column already exists` on second run.

### Pitfall 3: Classify and Summarize on Every Index Run (Performance)
**What goes wrong:** Every `corpus index` call re-classifies and re-summarizes all files — including unchanged ones. Summary generation with Ollama takes 2-10 seconds per file.
**Why it happens:** Missing guard: existing content_hash not checked before generating summary.
**How to avoid:** In the indexer, check if the file's content_hash matches the stored hash AND the stored `summary` is non-null. Only generate if the file changed or summary is missing. This requires reading stored summaries per file at the start of `index_source()`.
**Warning signs:** `corpus index` takes minutes even on unchanged sources.

### Pitfall 4: NULL `construct_type` Not Handled in Search Display
**What goes wrong:** Results for files indexed before Phase 2 (or files skipped during re-index) show `None` as the construct type in CLI output.
**Why it happens:** Schema evolution adds nullable columns; existing rows have NULL values.
**How to avoid:** In the result formatter, always use `result.get("construct_type") or "documentation"` — treat NULL as the safe fallback `"documentation"` label.
**Warning signs:** CLI output displays `None` or crashes on `result['construct_type']` KeyError.

### Pitfall 5: WHERE Clause SQL Injection via User-Supplied Filter Values
**What goes wrong:** A user passes `--source "'; DROP TABLE chunks; --"` which gets interpolated into a raw SQL `.where()` string.
**Why it happens:** Naive string formatting in `.where()` predicates.
**How to avoid:** Validate that `--source`, `--type`, and `--construct` values are alphanumeric + hyphens + underscores + dots only before passing to `.where()`. Reject invalid values with a clear error message.
**Warning signs:** Unexpected LanceDB errors on unusual filter values.

### Pitfall 6: LLM Fallback in Classifier Blocks Index Progress
**What goes wrong:** LLM fallback classification adds 2-10 seconds per unclassified file. With 1000 files and 30% LLM fallback rate, `corpus index` takes 10+ minutes.
**Why it happens:** LLM calls are serial and slow.
**How to avoid:** Cache classification results per file (store in `construct_type` column; only re-classify if file changed). Improve rule coverage to reduce LLM fallback rate. Log the count of LLM-classified files in the index summary so users can see the rate.
**Warning signs:** Index time grows linearly with file count even on unchanged sources.

### Pitfall 7: Summary Embedded in Separate Chunk Causes Duplicate File in Results
**What goes wrong:** If summaries are stored as separate "virtual" chunks, a search may return two results for the same file — one for the summary chunk and one for a content chunk.
**Why it happens:** Both chunks have the same `file_path` but different `chunk_id`.
**How to avoid:** Either (a) deduplicate by `file_path` in the search engine before returning results (keeping highest `_relevance_score`), or (b) prepend the summary to the first chunk's text before embedding (simpler, no deduplication needed). Option (b) is recommended.
**Warning signs:** Multiple results for the same file in `corpus search` output.

## Code Examples

Verified patterns from official sources:

### Hybrid Search with RRF and Filters
```python
# Source: https://docs.lancedb.com/integrations/reranking/rrf
# Source: https://docs.lancedb.com/search/hybrid-search
from lancedb.rerankers import RRFReranker

def hybrid_search(
    table: lancedb.table.Table,
    query: str,
    query_vector: list[float],
    source: str | None = None,
    file_type: str | None = None,
    construct_type: str | None = None,
    limit: int = 10,
) -> list[dict]:
    reranker = RRFReranker()
    builder = (
        table.search(query, query_type="hybrid")
        .rerank(reranker=reranker)
        .limit(limit)
    )
    # AND-chain all active filters
    if source:
        builder = builder.where(f"source_name = '{source}'")
    if file_type:
        builder = builder.where(f"file_type = '{file_type}'")
    if construct_type:
        builder = builder.where(f"construct_type = '{construct_type}'")

    return builder.to_list()
```

### Create FTS Index (Idempotent)
```python
# Source: https://docs.lancedb.com/indexing/fts-index
table.create_fts_index("text", replace=True)
```

### Schema Evolution (Safe)
```python
# Source: https://docs.lancedb.com/tables/schema
def ensure_schema_v2(table: lancedb.table.Table) -> None:
    existing = {field.name for field in table.schema}
    if "construct_type" not in existing:
        table.add_columns({"construct_type": "cast(NULL as string)"})
    if "summary" not in existing:
        table.add_columns({"summary": "cast(NULL as string)"})
```

### corpus status Query
```python
import pandas as pd

def get_status(table: lancedb.table.Table, embedding_model: str) -> dict:
    df = table.to_pandas()
    if df.empty:
        return {"files": 0, "chunks": 0, "last_indexed": "never", "model": embedding_model}
    files = df["file_path"].nunique()
    chunks = len(df)
    last_indexed = df["indexed_at"].max()
    stored_model = df["embedding_model"].iloc[0]
    return {"files": files, "chunks": chunks, "last_indexed": last_indexed, "model": stored_model}
```

### SourceConfig Extension for SUMM-03
```python
# Add to corpus_analyzer/config/schema.py
class SourceConfig(BaseModel):
    name: str
    path: str
    include: list[str] = Field(default_factory=lambda: ["**/*"])
    exclude: list[str] = Field(default_factory=list)
    summarize: bool = True  # NEW: False to skip AI summary generation for this source
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Separate BM25 + vector pipeline with custom fusion | `query_type="hybrid"` + `RRFReranker` in LanceDB | LanceDB 0.10+ (2024) | No separate FTS library; single API call |
| Separate FTS engine (Whoosh, Elasticsearch) | `create_fts_index()` via tantivy embedded in LanceDB | LanceDB 2024 | Zero external infrastructure for keyword search |
| Schema rebuilt on every migration | `table.add_columns()` for nullable column additions | LanceDB 0.15+ (2024) | In-place schema evolution without data loss |
| Manual per-chunk classification | File-level classify-once, propagate to chunks | Best practice | Consistent labels, fewer LLM calls |

**Deprecated/outdated:**
- `query_type="fts"` alone: Keyword-only search misses semantic matches. Always use `"hybrid"` with RRFReranker per the locked decision.
- Manual RRF Python implementations: LanceDB's built-in `RRFReranker` supersedes any hand-rolled fusion.

## Open Questions

1. **Does `.where()` on hybrid search apply pre-filter or post-filter?**
   - What we know: LanceDB applies `.where()` as pre-filter by default for vector search
   - What's unclear: Whether pre-filter on hybrid search reduces FTS recall unexpectedly on small datasets
   - Recommendation: Test with a small corpus that has filtering; if recall is poor, use post-filter via Python list comprehension after `.to_list()`

2. **Does `RRFReranker` require the query embedding to be passed separately, or does it re-embed internally?**
   - What we know: In the embedding registry pattern (`embedder.SourceField()`), LanceDB auto-embeds. In our manual pattern (Phase 1 uses `ollama.embed()` externally), the query embedding must be provided.
   - What's unclear: Whether `table.search(query_string, query_type="hybrid")` auto-generates the query vector using the table's registered embedder, or whether we must pass the pre-computed vector.
   - Recommendation: In Phase 1, embeddings are NOT registered via LanceDB's embedding registry (we called `ollama.embed()` manually and stored vectors). For Phase 2, we must embed the query externally with `OllamaEmbedder.embed_batch([query])[0]` and pass it as the search vector. The `text` side of hybrid search uses the FTS index and does not require a vector.

3. **How does `add_columns` interact with `merge_insert`?**
   - What we know: After `add_columns`, existing rows have NULL for the new columns; `merge_insert` on `chunk_id` will update matching rows with new data
   - What's unclear: Whether `merge_insert` silently drops new column data if the incoming dict has extra keys beyond the original schema
   - Recommendation: After `add_columns`, verify that a test `merge_insert` with `construct_type` and `summary` populated writes correctly; add an integration test in Wave 0.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.0.0 |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `uv run pytest tests/search/ -x -q` |
| Full suite command | `uv run pytest -v` |
| Estimated runtime | ~10–20 seconds (mocked Ollama, real LanceDB in tmp_path) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SEARCH-01 | Hybrid search returns ranked results | integration | `uv run pytest tests/search/test_engine.py::test_hybrid_search_returns_results -x` | ❌ Wave 0 gap |
| SEARCH-02 | RRF fusion combines vector + BM25 | integration | `uv run pytest tests/search/test_engine.py::test_hybrid_uses_rrf -x` | ❌ Wave 0 gap |
| SEARCH-03 | Filter by source name | integration | `uv run pytest tests/search/test_engine.py::test_filter_by_source -x` | ❌ Wave 0 gap |
| SEARCH-04 | Filter by file type | integration | `uv run pytest tests/search/test_engine.py::test_filter_by_file_type -x` | ❌ Wave 0 gap |
| SEARCH-05 | Snippet extracted from chunk text | unit | `uv run pytest tests/search/test_formatter.py::test_extract_snippet -x` | ❌ Wave 0 gap |
| CLASS-01 | Construct type classified for each file | unit | `uv run pytest tests/search/test_classifier.py::test_classify_skill_by_path -x` | ❌ Wave 0 gap |
| CLASS-02 | construct_type stored per chunk | integration | `uv run pytest tests/search/test_engine.py::test_construct_type_stored -x` | ❌ Wave 0 gap |
| CLASS-03 | Filter by construct type | integration | `uv run pytest tests/search/test_engine.py::test_filter_by_construct -x` | ❌ Wave 0 gap |
| SUMM-01 | Summary generated at index time | unit | `uv run pytest tests/search/test_summarizer.py::test_generate_summary -x` | ❌ Wave 0 gap |
| SUMM-02 | Summary improves retrieval | integration | `uv run pytest tests/search/test_engine.py::test_summary_in_results -x` | ❌ Wave 0 gap |
| SUMM-03 | Summary skippable per source | unit | `uv run pytest tests/search/test_summarizer.py::test_skip_when_summarize_false -x` | ❌ Wave 0 gap |
| CLI-01 | `corpus index` now classifies + summarizes | integration | `uv run pytest tests/ingest/test_indexer.py::test_index_adds_construct_type -x` | ❌ Wave 0 gap |
| CLI-02 | `corpus search` returns results | integration | `uv run pytest tests/search/test_engine.py::test_search_end_to_end -x` | ❌ Wave 0 gap |
| CLI-03 | `--source`/`--type`/`--construct`/`--limit` flags work | integration | `uv run pytest tests/search/test_engine.py::test_all_filters -x` | ❌ Wave 0 gap |
| CLI-04 | `corpus status` shows correct stats | unit | `uv run pytest tests/search/test_engine.py::test_status_returns_stats -x` | ❌ Wave 0 gap |
| CLI-05 | `corpus add` unchanged from Phase 1 | unit | `uv run pytest tests/ingest/ -x` (existing) | ✅ yes |

### Nyquist Sampling Rate
- **Minimum sample interval:** After every committed task → run: `uv run pytest tests/search/ -x -q`
- **Full suite trigger:** Before merging final task of any plan wave
- **Phase-complete gate:** Full suite green (`uv run pytest -v`) before `/gsd:verify-work` runs
- **Estimated feedback latency per task:** ~5–15 seconds

### Wave 0 Gaps (must be created before implementation)
- [ ] `tests/search/__init__.py` — package init for search tests
- [ ] `tests/search/test_engine.py` — covers SEARCH-01 through SEARCH-05, CLASS-02, CLASS-03, SUMM-02, CLI-02, CLI-03, CLI-04; shared `tmp_path` LanceDB fixture with mock embedder
- [ ] `tests/search/test_classifier.py` — covers CLASS-01; unit tests for rule-based classifier and LLM fallback mock
- [ ] `tests/search/test_summarizer.py` — covers SUMM-01, SUMM-03; mock `ollama.generate()`
- [ ] `tests/search/test_formatter.py` — covers SEARCH-05; unit tests for `extract_snippet()`
- [ ] `tests/ingest/test_indexer.py` additions — covers CLI-01; extend existing test file with `test_index_adds_construct_type` and `test_index_skips_summary_on_unchanged_file`

## Sources

### Primary (HIGH confidence)
- `/websites/lancedb` (Context7) — hybrid search, RRF reranker, FTS index, schema evolution, filter/where, score columns
- https://docs.lancedb.com/integrations/reranking/rrf — `RRFReranker` usage, `return_score`, `_relevance_score`
- https://docs.lancedb.com/search/hybrid-search — `query_type="hybrid"`, `.rerank()`, filter chaining
- https://docs.lancedb.com/indexing/fts-index — `create_fts_index`, `replace=True`, async building
- https://docs.lancedb.com/tables/schema — `add_columns`, nullable column evolution

### Secondary (MEDIUM confidence)
- Phase 1 RESEARCH.md (this project) — LanceDB schema, indexer patterns, OllamaEmbedder, existing code verified
- Existing codebase at `src/corpus_analyzer/` — confirmed Phase 1 implementation; `ChunkRecord` schema, `CorpusIndex`, CLI patterns

### Tertiary (LOW confidence)
- Open Question #2 (query embedding): Whether `table.search(text, query_type="hybrid")` auto-embeds or needs a pre-computed vector when using a manual (non-registry) embedder — to be verified with a small integration test in Wave 0.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in pyproject.toml; LanceDB hybrid search API verified via Context7
- Architecture: HIGH — patterns taken directly from LanceDB official docs; schema evolution verified
- Pitfalls: HIGH — most derived from Phase 1 pitfalls + verified LanceDB behavior; classification pitfalls from first-principles analysis
- Validation map: MEDIUM — test commands are correctly structured but Wave 0 files don't exist yet; test names are design-forward

**Research date:** 2026-02-23
**Valid until:** 2026-03-23 (LanceDB releases frequently; core hybrid search API is stable)

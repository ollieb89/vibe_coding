# Architecture Research

**Domain:** Intelligent search pipeline — v3 additions to corpus-analyzer
**Researched:** 2026-02-24
**Confidence:** HIGH (direct source code inspection + verified library docs)

---

## System Overview

Current v2 pipeline (baseline for v3 additions):

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          Query Surfaces                                   │
│  ┌────────────┐  ┌──────────────────┐  ┌────────────────────────────┐    │
│  │   CLI       │  │  FastMCP server   │  │  Python API (public.py)    │    │
│  │ cli.py      │  │  mcp/server.py    │  │  api/public.py             │    │
│  └─────┬──────┘  └────────┬──────────┘  └────────────┬───────────────┘    │
│        └─────────────────┬┘─────────────────────────┘                    │
├──────────────────────────┼───────────────────────────────────────────────┤
│                    Search Engine                                           │
│  ┌───────────────────────▼──────────────────────────────────────────┐    │
│  │  CorpusSearch.hybrid_search()  — search/engine.py                 │    │
│  │  LanceDB hybrid (vector + BM25) → RRFReranker → post-filter       │    │
│  └───────────────────────┬──────────────────────────────────────────┘    │
├──────────────────────────┼───────────────────────────────────────────────┤
│                    Storage Layer                                           │
│  ┌────────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │  LanceDB           │  │  graph.sqlite     │  │  source_manifest  │     │
│  │  chunks table      │  │  GraphStore       │  │  .json            │     │
│  │  (schema v4)       │  │  relationships    │  │                  │     │
│  └────────────────────┘  └──────────────────┘  └──────────────────┘      │
└──────────────────────────────────────────────────────────────────────────┘
```

v3 inserts a **post-search pipeline** layer between `hybrid_search()` and the display surfaces:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     Query Surfaces (thin wrappers, mostly unchanged)      │
│  CLI / FastMCP / Python API                                               │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │ calls SearchCoordinator.search()
┌────────────────────────────▼─────────────────────────────────────────────┐
│                    SearchCoordinator (NEW — search/coordinator.py)        │
│                                                                            │
│  1. Multi-query fan-out: run N hybrid_search() calls, intersect results   │
│  2. --exclude-path glob filter                                             │
│  3. Centrality boost: multiply _relevance_score by centrality factor      │
│  4. MMR diversity re-rank: penalise near-duplicate / same-file chunks     │
│  5. Cross-encoder re-rank (optional, --rerank flag)                       │
│  6. Graph expansion: fetch graph neighbours, append with labels           │
│  7. Contiguous chunk merge: collapse adjacent same-file method chunks     │
│  8. Source label: ensure source_name present in every result              │
└──────────────────────────┬──────────────────┬──────────────────────────┘
                           │                  │
          ┌────────────────▼──┐  ┌────────────▼────────────────────┐
          │  CorpusSearch     │  │  GraphStore (graph.sqlite)       │
          │  hybrid_search()  │  │  edges_from / edges_to           │
          │  (modified:       │  │  walk_n_hops (NEW)               │
          │   return_vectors) │  │  get_centrality (NEW)            │
          └───────────────────┘  └──────────────────────────────────┘
```

---

## Component Responsibilities

| Component | Responsibility | New vs Modified |
|-----------|----------------|-----------------|
| `search/engine.py` `CorpusSearch.hybrid_search()` | Single-query BM25+vector+RRF retrieval | **Modified** — add `return_vectors: bool = False` param only |
| `search/diversity.py` | MMR re-ranking of result list | **New** |
| `search/reranker.py` | Cross-encoder two-stage re-rank wrapper | **New** |
| `search/coordinator.py` | Multi-query fan-out, pipeline orchestration | **New** |
| `graph/store.py` `GraphStore` | Edge storage and lookup | **Modified** — add `walk_n_hops()`, `indegree_counts()`, `get_centrality()` |
| `graph/centrality.py` | Indegree centrality computation at index time | **New** |
| `ingest/indexer.py` | Index pipeline | **Modified** — call `compute_indegree()` at end of `index_source()` |
| `cli.py` `search_command` | Search flags | **Modified** — add `--query` (multiple), `--exclude-path`, `--expand-graph`, `--rerank` |
| `cli.py` `graph_command` | Graph traversal | **Modified** — implement `--depth N` recursive walk |
| `mcp/server.py` `corpus_search` | MCP tool response | **Modified** — add `source` field, multi-query, `expand_graph` param |
| `api/public.py` `search()` | Python API | **Modified** — `SearchResult` gets `source` field; `search()` accepts `queries` list |

---

## Recommended Project Structure

```
src/corpus_analyzer/
├── search/
│   ├── engine.py          # existing — hybrid_search(); add return_vectors param
│   ├── diversity.py       # NEW — mmr_rerank(results, query_vec, lambda_=0.5)
│   ├── reranker.py        # NEW — CrossEncoderReranker (lazy-loads model on first use)
│   ├── coordinator.py     # NEW — SearchCoordinator: fan-out, merge, pipeline steps
│   ├── formatter.py       # existing
│   ├── summarizer.py      # existing
│   └── classifier.py      # existing
├── graph/
│   ├── store.py           # existing — add walk_n_hops(), indegree_counts(), get_centrality()
│   ├── centrality.py      # NEW — compute_indegree(); writes to centrality table in graph.sqlite
│   ├── extractor.py       # existing
│   └── registry.py        # existing
├── store/
│   └── schema.py          # existing — no LanceDB schema changes needed for v3
├── ingest/
│   └── indexer.py         # existing — call centrality.compute_indegree() at end of index_source()
├── mcp/
│   └── server.py          # existing — source field; multi-query; expand_graph param
├── api/
│   └── public.py          # existing — SearchResult source field; search() multi-query
└── cli.py                 # existing — new flags for search and graph commands
```

### Structure Rationale

- **search/coordinator.py:** All three query surfaces (CLI, MCP, API) currently call `hybrid_search()` directly and format results themselves. Adding v3 pipeline steps to all three surfaces individually would triplicate logic. A `SearchCoordinator` provides a single composition point.
- **search/diversity.py:** Isolated to keep MMR algorithm testable independently of the coordinator.
- **search/reranker.py:** Isolated because it has an optional `sentence-transformers` dependency that the rest of the codebase must not require.
- **graph/centrality.py:** Isolated because centrality computation runs at index time (not query time) and has its own SQLite write path.

---

## v3 Feature Integration: Precise Answers

### Question 1: Where Does MMR Fit in the Search Pipeline?

**Answer:** Post-retrieval, inside `SearchCoordinator`, after `hybrid_search()` returns results. MMR is NOT inside `hybrid_search()` itself.

**Why not inside `hybrid_search()`:** MMR requires access to the embedding vector of each candidate to compute cosine similarity between results. The current `hybrid_search()` does not return vectors — it strips them from the LanceDB result dicts before returning `list[dict]`. Adding MMR inside the engine would either permanently bloat every result dict with vectors, or create a second code path that only sometimes returns vectors.

**Clean solution:** Add a single parameter `return_vectors: bool = False` to `hybrid_search()`. Default `False` preserves the existing API contract. When `True`, vectors are included in result dicts for downstream MMR use. The coordinator calls with `return_vectors=True` and a higher `limit` (3x the desired final count) to give MMR enough candidates to select from.

```python
# search/diversity.py
import numpy as np
from numpy.typing import NDArray


def _cosine_sim(a: NDArray, b: NDArray) -> float:
    """Cosine similarity between two vectors."""
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


def mmr_rerank(
    results: list[dict],
    query_vec: list[float],
    lambda_: float = 0.5,
    top_k: int | None = None,
) -> list[dict]:
    """Maximal Marginal Relevance re-ranking.

    MMR score = (1 - lambda) * relevance_score - lambda * max_sim_to_selected

    Args:
        results: list[dict] from hybrid_search(), each containing 'vector'
                 and '_relevance_score'. Results without 'vector' are passed through.
        query_vec: Embedding of the original query.
        lambda_: 0.0 = pure relevance, 1.0 = pure diversity. Default 0.5.
        top_k: Number of results to return. Defaults to len(results).
    """
    if not results:
        return results
    k = top_k if top_k is not None else len(results)
    qv = np.array(query_vec, dtype=np.float32)
    selected: list[dict] = []
    remaining = list(results)
    while remaining and len(selected) < k:
        best_idx = 0
        best_score = float("-inf")
        for i, r in enumerate(remaining):
            rel = float(r.get("_relevance_score", 0.0))
            vec = r.get("vector")
            if vec is None:
                mmr = rel
            else:
                rv = np.array(vec, dtype=np.float32)
                sim_to_selected = max(
                    (_cosine_sim(rv, np.array(s["vector"], dtype=np.float32))
                     for s in selected if s.get("vector") is not None),
                    default=0.0,
                )
                mmr = (1 - lambda_) * rel - lambda_ * sim_to_selected
            if mmr > best_score:
                best_score = mmr
                best_idx = i
        selected.append(remaining.pop(best_idx))
    # Strip vectors from output so they don't pollute display layers
    for r in selected:
        r.pop("vector", None)
    return selected
```

**Confidence:** HIGH — algorithm is standard, pure Python + numpy, no new runtime dependencies (numpy is transitively required by LanceDB and pandas already).

---

### Question 2: How Does Cross-Encoder Re-ranking Slot In Without Breaking `hybrid_search()` API Contract?

**Answer:** The cross-encoder is applied _after_ `hybrid_search()` returns, inside `SearchCoordinator`. The `CorpusSearch.hybrid_search()` method is not modified.

`CrossEncoderReranker` in `search/reranker.py` is a standalone post-processing step. The coordinator checks whether `--rerank` was requested and, if so, calls `reranker.rerank(query, results[:20])`.

```python
# search/reranker.py

class CrossEncoderReranker:
    """Optional two-stage cross-encoder reranker.

    Lazy-loads sentence-transformers on first use. Raises ImportError with
    install instructions if the package is not available.
    """

    _model: object | None = None  # CrossEncoder instance

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L6-v2") -> None:
        self._model_name = model_name

    def _load(self) -> object:
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder  # type: ignore[import-untyped]
            except ImportError as exc:
                raise ImportError(
                    "sentence-transformers is required for --rerank. "
                    "Install with: uv add sentence-transformers"
                ) from exc
            self._model = CrossEncoder(self._model_name)
        return self._model

    def rerank(self, query: str, results: list[dict], top_k: int = 20) -> list[dict]:
        """Re-score top_k results with cross-encoder, sort descending, return full list."""
        model = self._load()
        candidates = results[:top_k]
        pairs = [(query, str(r.get("text", ""))) for r in candidates]
        scores = model.predict(pairs)  # type: ignore[union-attr]
        for r, s in zip(candidates, scores, strict=True):
            r["_rerank_score"] = float(s)
        candidates.sort(key=lambda r: r.get("_rerank_score", 0.0), reverse=True)
        return candidates + results[top_k:]
```

**Offline-first constraint:** `sentence-transformers` models download to `~/.cache/huggingface/` on first use and run fully offline afterward. This matches the project constraint.

**Optional dependency approach:** Do NOT add `sentence-transformers` to `pyproject.toml` `[dependencies]`. Add it to an optional extras group: `[project.optional-dependencies] rerank = ["sentence-transformers>=3.0"]`. Users who want `--rerank` run `uv sync --extra rerank`. The lazy import guard ensures `--rerank` prints a clean install hint if the package is absent.

**Confidence:** HIGH — CrossEncoder API is stable since SBERT v2.x; pattern is well-established.

---

### Question 3: Where Is Centrality Stored — LanceDB or graph.sqlite?

**Answer: graph.sqlite, in a new `centrality` table. Do NOT add a centrality column to LanceDB.**

**Rationale:**

1. Centrality is a property of the graph topology, not of a chunk's content. It belongs with the graph data.
2. LanceDB schema changes require `ensure_schema_vN()` migration functions and user warnings about re-indexing. A SQLite `CREATE TABLE IF NOT EXISTS` is instant and idempotent.
3. Centrality changes every time a file adds or removes a `## Related Skills` reference. Updating LanceDB for a topology change would require re-writing every chunk of the affected file via `merge_insert` — wasteful when the content hasn't changed.
4. The established architectural decision: "SQLite for graph store (not LanceDB)" — see PROJECT.md key decisions table.

**Schema addition to graph.sqlite (idempotent, in `GraphStore._init_schema()`):**

```sql
CREATE TABLE IF NOT EXISTS centrality (
    file_path    TEXT PRIMARY KEY,
    indegree     INTEGER NOT NULL DEFAULT 0,
    computed_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_centrality_path ON centrality(file_path);
```

**GraphStore additions:**

```python
def upsert_centrality(self, scores: dict[str, int]) -> None:
    """Upsert indegree counts for all files. Called once per index run."""
    now = datetime.now(UTC).isoformat()
    with self._connect() as conn:
        conn.executemany(
            "INSERT INTO centrality (file_path, indegree, computed_at) VALUES (?, ?, ?)"
            " ON CONFLICT(file_path) DO UPDATE SET indegree=excluded.indegree, computed_at=excluded.computed_at",
            [(path, count, now) for path, count in scores.items()],
        )
        conn.commit()

def get_centrality(self, file_path: str) -> int:
    """Return indegree for file_path, 0 if not present."""
    with self._connect() as conn:
        row = conn.execute(
            "SELECT indegree FROM centrality WHERE file_path = ?", (file_path,)
        ).fetchone()
    return int(row["indegree"]) if row else 0

def indegree_counts(self) -> dict[str, int]:
    """Return {file_path: indegree} for all resolved targets."""
    with self._connect() as conn:
        rows = conn.execute(
            "SELECT target_path, COUNT(*) as cnt FROM relationships"
            " WHERE resolved=1 GROUP BY target_path"
        ).fetchall()
    return {r["target_path"]: r["cnt"] for r in rows}
```

**Centrality computation module (`graph/centrality.py`):**

```python
def compute_indegree(graph_store: GraphStore) -> dict[str, int]:
    """Compute indegree centrality from graph.sqlite relationships table."""
    counts = graph_store.indegree_counts()
    graph_store.upsert_centrality(counts)
    return counts
```

**Index-time wiring** in `indexer.py`: after `self._table.create_fts_index(...)`, call `compute_indegree(graph_store)` when `graph_store is not None`.

**Query-time boost** in `SearchCoordinator`:

```python
def _apply_centrality_boost(self, results: list[dict]) -> list[dict]:
    for r in results:
        indegree = self._graph_store.get_centrality(r.get("file_path", ""))
        # Boost: +0–20%, capped; indegree 0 → 1.0x, indegree 50+ → 1.2x
        boost = 1.0 + min(indegree / 50.0, 0.2)
        r["_relevance_score"] = float(r.get("_relevance_score", 0.0)) * boost
    return results
```

**Confidence:** HIGH — pure SQLite, no new dependencies.

---

### Question 4: Multi-Query — Does LanceDB Support Multiple Vector Queries in One Call?

**Answer: No. LanceDB does NOT support multiple independent vector queries in one API call.**

**Verified against LanceDB docs:** The "multivector search" feature in LanceDB is for ColBERT-style late interaction — it handles multiple embeddings _per document_, not multiple independent queries. Running N separate queries requires N separate `.search()` calls.

**Implementation:** Run N separate `hybrid_search()` calls, then compute AND-intersection by `file_path`:

```python
# search/coordinator.py
def _multi_query_search(
    self,
    queries: list[str],
    limit: int,
    **kwargs: object,
) -> list[dict]:
    if len(queries) == 1:
        return self._engine.hybrid_search(queries[0], limit=limit, **kwargs)

    # Fetch more candidates per query to ensure intersection has results
    per_query_limit = limit * len(queries) * 2
    result_sets = [
        self._engine.hybrid_search(q, limit=per_query_limit, **kwargs)
        for q in queries
    ]

    # AND-intersection by file_path (file-level semantic AND)
    path_sets = [frozenset(r["file_path"] for r in rs) for rs in result_sets]
    common_paths = frozenset.intersection(*path_sets)

    # Retain result order from first query, keeping only intersected paths
    merged = [r for r in result_sets[0] if r["file_path"] in common_paths]
    return merged[:limit]
```

**Note on intersection semantics:** Intersecting by `file_path` (not `chunk_id`) provides file-level AND semantics. A file about "auth + saml" will likely have different chunks discussing each term. Chunk-level intersection would often return zero results. File-level is the practical correct choice.

**Performance note:** N queries means N embed calls to Ollama. `OllamaEmbedder.embed_batch()` accepts a list — batch all query texts into a single embed call:

```python
query_vecs = self._engine._embedder.embed_batch(queries)
# Then use each vec in a manual search call
```

Requires exposing `embed_batch` result to coordinator, or passing pre-computed vectors into a lower-level search path. Design decision: keep it simple — accept N sequential Ollama calls for v3. At 2–3 queries, this is ~100–150ms extra latency, acceptable for CLI.

**Confidence:** HIGH for limitation (LanceDB docs verified). MEDIUM for intersection logic (needs UAT to tune candidate multiplier).

---

### Question 5: Graph Expansion — Query-Time Lookup or Pre-Computed?

**Answer: Query-time lookup from graph.sqlite.**

**Rationale:** The `GraphStore.edges_from()` and `edges_to()` methods are O(1) keyed lookups on indexed columns (`idx_source` and `idx_target` exist already). At local scale with hundreds to thousands of files, even 10 lookups per result set (e.g., 10 results × 2 directions) takes <5ms total.

Pre-computing graph expansions would require re-running lookups every time the query changes (no benefit) and storing per-file neighbour lists (redundant with the relationships table). The existing `GraphStore` API is already sufficient.

```python
# search/coordinator.py
def _expand_with_graph(
    self,
    results: list[dict],
    limit_per_result: int = 3,
) -> list[dict]:
    """Append graph neighbours to results with [Depends On] / [Imported By] labels."""
    expanded = list(results)
    seen_paths = {r.get("file_path", "") for r in results}

    for result in results:
        path = result.get("file_path", "")
        if not path:
            continue
        for edge in self._graph_store.edges_from(path)[:limit_per_result]:
            target = edge["target_path"]
            if target not in seen_paths and edge["resolved"]:
                expanded.append(self._stub_result(target, label="Depends On", source=path))
                seen_paths.add(target)
        for edge in self._graph_store.edges_to(path)[:limit_per_result]:
            src = edge["source_path"]
            if src not in seen_paths:
                expanded.append(self._stub_result(src, label="Imported By", source=path))
                seen_paths.add(src)
    return expanded
```

Graph-expanded results have `_graph_label` set; the CLI formatter and MCP response builder use this to render them distinctly from ranked search results.

**Confidence:** HIGH — existing infrastructure sufficient, no new storage needed.

---

### Question 6: What New Components Are Needed vs. Modified?

#### New Files (thin to create)

| File | Approximate Size | Notes |
|------|------------------|-------|
| `search/diversity.py` | ~70 lines | Pure Python + numpy; MMR only |
| `search/reranker.py` | ~60 lines | Lazy-loads optional `sentence-transformers` |
| `search/coordinator.py` | ~200 lines | Orchestrates all pipeline steps; the core v3 module |
| `graph/centrality.py` | ~30 lines | Calls `graph_store.indegree_counts()`, `upsert_centrality()` |

#### Modified Files (surgical changes)

| File | Change | Lines Added |
|------|--------|-------------|
| `search/engine.py` | Add `return_vectors: bool = False` param | ~10 |
| `graph/store.py` | Add `walk_n_hops()`, `indegree_counts()`, `get_centrality()`, `upsert_centrality()`, `centrality` table in `_init_schema()` | ~80 |
| `ingest/indexer.py` | Call `compute_indegree(graph_store)` at end of `index_source()` when graph_store is not None | ~5 |
| `cli.py` | New flags on `search_command`; implement depth on `graph_command`; wire through `SearchCoordinator` | ~100 |
| `mcp/server.py` | Add `source` field to results; add `expand_graph`, multi-query params; use `SearchCoordinator` | ~50 |
| `api/public.py` | `SearchResult` source field; `search()` accepts `queries: list[str]` | ~20 |

#### No Changes Needed

| File | Reason |
|------|--------|
| `store/schema.py` (LanceDB) | No new LanceDB columns for v3 |
| `graph/extractor.py` | Edge extraction unchanged |
| `graph/registry.py` | Slug resolution unchanged |
| `ingest/chunker.py` | Chunking unchanged |
| `ingest/embedder.py` | Embedding unchanged |
| `search/classifier.py` | Classification unchanged |
| `search/formatter.py` | Minor additions only for graph label display |

---

## Data Flow — v3 Search Pipeline

```
User: corpus search --query auth --query saml --expand-graph --rerank

cli.py:search_command
    │ creates SearchCoordinator(engine, graph_store, reranker)
    │ calls coordinator.search(queries=["auth","saml"], expand_graph=True, rerank=True, limit=10)
    ▼
SearchCoordinator.search()
    │
    ├── 1. Fan-out:
    │      hybrid_search("auth",  limit=40, return_vectors=True)
    │      hybrid_search("saml",  limit=40, return_vectors=True)
    │      Intersect by file_path → ~N candidates
    │
    ├── 2. --exclude-path: fnmatch.fnmatch(file_path, pattern) filter (if set)
    │
    ├── 3. Centrality boost: graph_store.get_centrality(file_path) per result
    │      score *= (1.0 + min(indegree/50, 0.2))
    │
    ├── 4. MMR re-rank: diversity.mmr_rerank(results, query_vec, lambda_=0.5, top_k=10)
    │      (strips vectors from dicts after use)
    │
    ├── 5. Cross-encoder (--rerank): reranker.rerank("auth saml", results[:20])
    │      (re-scores top 20, re-sorts, appends rest)
    │
    ├── 6. Graph expansion (--expand-graph):
    │      coordinator._expand_with_graph(results, limit_per_result=3)
    │
    ├── 7. Contiguous chunk merge: collapse adjacent same-file method chunks
    │      (requires chunk_name/start_line from v2 schema v4)
    │
    └── 8. Source label: source_name already in each dict (no-op, just assert presence)

cli formatter: renders each result as source:path:start-end [construct] score:X.XXX
               graph-expanded results appended as [Depends On] / [Imported By]
```

---

## Architectural Patterns

### Pattern 1: Post-Retrieval Pipeline (not in-retrieval)

**What:** All v3 ranking features operate on `list[dict]` returned by `hybrid_search()`. The engine method is not modified except for the `return_vectors` flag.

**When to use:** Always for optional/composable steps. `hybrid_search()` is the shared contract between CLI, MCP, and Python API. Keeping it stable prevents ripple effects across all three surfaces.

**Trade-off:** Requires retrieving more candidates than the final display limit (3x for MMR). At local scale with <100K chunks this adds ~30ms, acceptable for CLI use. If this becomes a bottleneck for very large corpora, add a `candidate_limit_multiplier` tuning parameter.

### Pattern 2: SearchCoordinator as Pipeline Orchestrator

**What:** A `SearchCoordinator` class wires all post-retrieval steps. CLI, MCP, and API surfaces call `coordinator.search(...)` instead of calling `engine.hybrid_search()` directly.

**When to use:** When multiple surfaces need the same pipeline logic. Avoids triplicating v3 logic across CLI, MCP, and API.

**Trade-off:** Introduces an additional abstraction layer. For v3's eight pipeline steps, it is the right trade-off. For v4+ simpler additions, individual steps can still be composed without a coordinator.

### Pattern 3: Centrality in graph.sqlite (not LanceDB)

**What:** Indegree centrality is stored as a `centrality` table in `graph.sqlite`, looked up at query time with a keyed SELECT.

**When to use:** For any derived graph metric. LanceDB is for content+vectors; SQLite is for topology.

**Trade-off:** One extra SQLite file read per result. At local scale (<10K files), this is negligible. If the corpus grows to 100K+ files, batch the centrality lookups into a single `IN (...)` query.

### Pattern 4: Lazy-Load Optional Dependencies

**What:** `CrossEncoderReranker` wraps its `sentence-transformers` import in a `try/except ImportError`. The reranker is None when `--rerank` is not requested.

**When to use:** For any dependency that is large (400MB+ model download) or requires significant setup. The `--rerank` flag is an explicit opt-in; users who request it know they need the package.

**Trade-off:** Optional dependencies fragment the install story. Mitigated by clear error messages with `uv add sentence-transformers` instructions.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Modifying `hybrid_search()` API Contract

**What people do:** Add MMR or centrality parameters directly to `hybrid_search(query, ..., lambda_mmr=0.5, centrality_boost=True)`.

**Why it's wrong:** `hybrid_search()` is called by three surfaces. Each signature change ripples to CLI, MCP, API, and all test fixtures that call the engine directly. The engine should remain a pure "retrieve N candidates" function.

**Do this instead:** Put all post-retrieval steps in `SearchCoordinator.search()`. Call `hybrid_search()` with a larger `limit` to get candidates, then apply steps as a pipeline.

### Anti-Pattern 2: Centrality Column in LanceDB

**What people do:** Add `centrality_score: float = 0.0` to `ChunkRecord` in `store/schema.py`.

**Why it's wrong:** Centrality changes whenever any file adds or removes a `## Related Skills` reference. This would require re-running `merge_insert` on all chunks of the affected file just to update a score that has nothing to do with content. LanceDB `merge_insert` rewrites the entire row including re-embedding — prohibitively expensive for a graph topology update.

**Do this instead:** Store in `graph.sqlite`'s `centrality` table. Look it up at query time with a fast keyed SQLite read.

### Anti-Pattern 3: Graph Expansion Inside MMR or Cross-Encoder Pass

**What people do:** Include graph-expanded stub results in the MMR or cross-encoder re-ranking step.

**Why it's wrong:** Graph neighbours are included because of structural relationships, not because they are semantically similar to the query. MMR would incorrectly penalise them for being dissimilar to selected results. Cross-encoder would score them low because their text may not contain query terms. Both effects would incorrectly suppress useful graph context.

**Do this instead:** Apply graph expansion _after_ all re-ranking steps. Graph-expanded results are appended with `_graph_label` metadata, displayed distinctly.

### Anti-Pattern 4: Eager Cross-Encoder Model Load

**What people do:** `self._model = CrossEncoder(...)` at `__init__` time of `SearchCoordinator` or in `corpus_lifespan`.

**Why it's wrong:** Loading the model takes ~1–3 seconds and ~400MB. Every MCP server startup and every CLI invocation pays this cost even when `--rerank` is not requested.

**Do this instead:** Lazy-load in `CrossEncoderReranker.rerank()` on first call. Cache the loaded model as an instance attribute.

### Anti-Pattern 5: Chunk-Level Multi-Query Intersection

**What people do:** Intersect multi-query results by `chunk_id` rather than `file_path`.

**Why it's wrong:** A file about "authentication" and "SAML" will likely discuss each topic in different chunks. Chunk-level intersection would return zero results for most real-world multi-topic queries.

**Do this instead:** Intersect by `file_path`. A file is included if any chunk from that file matched each query. File-level AND is the correct semantic for this use case.

---

## Build Order (Phase Dependencies)

Feature dependency graph for v3:

```
Source labeling          → Independent (data already in LanceDB schema)
--exclude-path           → Independent (post-filter, no new deps)
SearchCoordinator        → Foundation for all other features
Multi-query              → Requires SearchCoordinator scaffold
MMR diversity            → Requires SearchCoordinator + return_vectors in hybrid_search
Centrality scoring       → Requires centrality table in graph.sqlite
Graph expansion (search) → Requires SearchCoordinator + existing GraphStore.edges_from/to
Recursive graph walk     → Requires GraphStore.walk_n_hops
Cross-encoder rerank     → Requires SearchCoordinator (plugs in as optional step)
Contiguous chunk merge   → Requires v2 chunk_name/start_line/end_line (done in v2 schema v4)
```

**Recommended build sequence:**

1. **Source labeling + --exclude-path** — zero-risk. Data is already in LanceDB; cosmetic + thin filter. Validates coordinator scaffold with passthrough logic.
2. **SearchCoordinator scaffold** — wire CLI/MCP/API through coordinator with pure passthrough (no logic change yet). Validates the plumbing.
3. **Multi-query fan-out** — first real coordinator logic. Run N queries, intersect by file_path.
4. **MMR diversity** — add `return_vectors` to `hybrid_search()`; implement `diversity.py`; wire into coordinator.
5. **Centrality scoring** — add `centrality` table to graph.sqlite; implement `centrality.py`; wire into `index_source()` and coordinator.
6. **Graph expansion (search)** — `--expand-graph` flag; uses existing `GraphStore.edges_from/to`.
7. **Recursive graph walk** — add `walk_n_hops()` to `GraphStore`; implement `--depth N` in `graph_command`.
8. **Cross-encoder rerank** — add `reranker.py`; gate on optional `sentence-transformers` dep.
9. **Contiguous chunk merge** — display polish; depends on v2 chunk_name fields being populated.

Steps 1–2 are foundational and safe. Steps 3–5 form a coherent "smarter ranking" block. Steps 6–7 form a "richer graph" block. Step 8 is optional and fully isolated. Step 9 is display polish.

---

## Integration Points

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `SearchCoordinator` ↔ `CorpusSearch` | Direct call: `engine.hybrid_search()` | Coordinator holds reference to engine |
| `SearchCoordinator` ↔ `GraphStore` | Direct call: `store.edges_from()`, `store.get_centrality()` | Coordinator receives graph_store as constructor arg |
| `SearchCoordinator` ↔ `CrossEncoderReranker` | Direct call: `reranker.rerank()` | Reranker is None when --rerank not requested |
| `CLI` ↔ `SearchCoordinator` | Direct call; coordinator returns `list[dict]` | CLI formats output; passes flags as coordinator params |
| `MCP lifespan` ↔ `SearchCoordinator` | Coordinator stored in `lifespan_context` | Same pattern as existing `engine` storage |
| `ingest/indexer.py` ↔ `graph/centrality.py` | Called at end of `index_source()` | `compute_indegree(graph_store)` when graph_store is not None |

### External Services

| Service | Integration | Notes |
|---------|-------------|-------|
| Ollama (embeddings) | Unchanged — `OllamaEmbedder` used by `CorpusSearch` | Multi-query runs N embed calls; N×~50ms latency |
| HuggingFace (cross-encoder model) | One-time download via `sentence-transformers` | Runs locally after download; offline-first preserved |

---

## Scaling Considerations

This is a single-user local tool. Scaling is corpus size, not user count.

| Corpus Size | Key Concern | Approach |
|-------------|-------------|----------|
| <10K chunks (current) | None — all approaches work | MMR 3x candidate over-fetch is ~30ms |
| 10K–100K chunks | Multi-query embed latency | N queries × Ollama latency (~50ms each); acceptable for CLI |
| 100K+ chunks | Centrality lookup per result | Batch `get_centrality` calls into single `IN (...)` query |

**First bottleneck for multi-query:** Ollama embedding latency. Three queries = 3 × ~50ms = ~150ms extra. `OllamaEmbedder.embed_batch()` already accepts a list — if the engine exposes pre-embedding, all query texts can be batched in one Ollama call. Low priority for v3; worth noting as a v4 optimisation.

---

## Sources

- Source code: `/home/ollie/Development/Tools/vibe_coding/corpus-analyzer/src/corpus_analyzer/` (direct inspection, all key files read)
- LanceDB multi-vector docs: [Multivector Search - LanceDB](https://docs.lancedb.com/search/multivector-search) — confirmed multi-vector is ColBERT-style per-document, not multi-query; no batch-query API exists
- LanceDB custom reranker API: [Building Custom Rerankers - LanceDB](https://docs.lancedb.com/reranking/custom-reranker) — Reranker base class verified; `rerank_hybrid(query, vector_results, fts_results) -> pa.Table` is the required interface
- MMR algorithm: [Balancing Relevance and Diversity with MMR Search - Qdrant](https://qdrant.tech/blog/mmr-diversity-aware-reranking/)
- Cross-encoder reranking: [Retrieve & Re-Rank — Sentence Transformers](https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html)
- Cross-encoder offline use: [sentence-transformers · PyPI](https://pypi.org/project/sentence-transformers/) — local model, no API key, offline after first download

---

*Architecture research for: corpus-analyzer v3 Intelligent Search*
*Researched: 2026-02-24*

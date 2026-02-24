# Stack Research

**Domain:** Search precision controls — relevance score display, sort flag, min-score filtering for LanceDB hybrid search CLI/API/MCP
**Researched:** 2026-02-24
**Confidence:** HIGH (all findings verified against installed LanceDB 0.29.2 source code; no external sources required)

---

## Context: v1.4 Search Precision

This research covers ONLY what is new or changed for v1.4. The full application stack (LanceDB,
FastMCP, Typer, Rich, Pydantic) is validated and unchanged. No new packages are required.

**Active milestone requirements:**
- Relevance score displayed in `corpus search` output
- `--sort relevance|path` flag on `corpus search`
- `--min-score <float>` flag to hard-filter low-relevance results
- Python `search()` API accepts `sort_by` and `min_score` parameters
- MCP `corpus_search` tool accepts `min_score` parameter

---

## Key Finding: _relevance_score is already populated

The `_relevance_score` field IS present in hybrid search result dicts right now. No LanceDB API
changes are needed to access it.

**Trace through LanceDB 0.29.2 source (verified):**

1. `CorpusSearch.hybrid_search()` calls `.rerank(reranker=RRFReranker())` — the reranker runs
   during `LanceHybridQueryBuilder.to_arrow()`.

2. `RRFReranker.rerank_hybrid()` appends `_relevance_score` as a `pa.float32()` column to the
   Arrow table after computing RRF scores.

3. `RRFReranker(return_score="relevance")` is the default. In this mode, `_keep_relevance_score()`
   drops `_score` and `_distance` columns but **keeps `_relevance_score`**. The score column
   survives to the output.

4. `to_list()` calls `to_arrow().to_pylist()`. The `_relevance_score` key is present in every
   result dict.

5. `public.py` already reads it: `float(r.get("_relevance_score", 0.0))` — the Python API
   already captures the real RRF score in `SearchResult.score`.

6. `server.py` already reads it: `float(row.get("_relevance_score", 0.0))` — MCP already
   captures and returns the score per result.

7. `cli.py` line 366 already prints it: `f"[dim]score: {result.get('_relevance_score', 0.0):.3f}[/]"`

**Conclusion:** Score display is already wired end-to-end. The CLI already shows scores. The API
already populates `SearchResult.score`. The MCP already includes `score` in each result dict.

---

## RRF Score Characteristics (verified via calculation)

```python
# RRF score formula: sum(1 / (rank + K)) for each retrieval system
# K = 60 (RRFReranker default)
# Two retrieval systems: vector + BM25/FTS

max_score = 1/(1+60) + 1/(1+60)  # = 0.0328  (rank 1 in both systems)
typical_high = 1/(1+60) + 1/(5+60)  # ≈ 0.0316  (rank 1 vector, rank 5 FTS)
only_vector = 1/(1+60)              # ≈ 0.0164  (appears in vector only)
low_score = 1/(50+60)               # ≈ 0.0091  (rank 50 in one system)
```

**Practical range:** `[~0.009, ~0.033]`

This has implications for `--min-score` UX: users will not intuitively understand scores of 0.015.
The recommended approach is to display scores as-is (3 decimal places) and document the range, OR
normalise to [0, 1] by dividing by the theoretical maximum (2/61 ≈ 0.0328). See "Score Display
Options" below.

---

## Recommended Stack

### Core Technologies (no changes)

| Technology | Version | Purpose | Status |
|------------|---------|---------|--------|
| LanceDB | 0.29.2 | Vector storage + hybrid search + RRF scoring | Unchanged. `_relevance_score` already populated. |
| Typer | 0.12+ | CLI option parsing | Add `--sort` simplification + `--min-score` option |
| Rich | 13.7+ | Terminal formatting | Already printing score; format as needed |
| FastMCP | 2.14.4+ | MCP server | Add `min_score` parameter to `corpus_search` tool |

### No New Libraries Required

Zero new dependencies. All v1.4 changes are pure Python logic over existing infrastructure:

- **Score filtering** — a list comprehension `[r for r in results if score(r) >= min_score]`
- **Sort by path** — `sorted(results, key=lambda r: r["file_path"])` — already done for other keys
- **Sort by relevance** — already the default (RRFReranker sorts descending by `_relevance_score`)
- **API parameters** — adding kwargs to existing function signatures

---

## What Changes in Each Layer

### Layer 1: `search/engine.py` — CorpusSearch.hybrid_search()

**Current state:**
- `sort_by` accepts `"relevance" | "construct" | "confidence" | "date" | "path"` — already implemented
- No `min_score` parameter

**v1.4 changes needed:**
- Add `min_score: float = 0.0` parameter
- Apply score filter AFTER the text-term filter, BEFORE sort:
  ```python
  filtered = [r for r in filtered if float(r.get("_relevance_score", 0.0)) >= min_score]
  ```
- The `sort_by` values for v1.4 are `"relevance" | "path"` per the milestone spec. The existing
  `"construct" | "confidence" | "date"` variants already work and should be KEPT — they are not
  removed. The milestone spec uses `--sort relevance|path` as the user-facing options, but the
  engine already supports more.

**Score access pattern (verified):**
```python
score = float(r.get("_relevance_score", 0.0))
```
This is the correct key. It is a `pa.float32()` value that Python casts cleanly to `float`.

### Layer 2: `api/public.py` — search()

**Current state:**
- `SearchResult.score` is already populated from `_relevance_score`
- No `sort_by` or `min_score` parameter

**v1.4 changes needed:**
- Add `sort_by: str = "relevance"` and `min_score: float = 0.0` parameters
- Pass both through to `engine.hybrid_search()`

### Layer 3: `cli.py` — search_command()

**Current state:**
- `--sort` option already exists with `"relevance|construct|confidence|date|path"` help text
- Score already displayed: `score: {result.get('_relevance_score', 0.0):.3f}`
- No `--min-score` option

**v1.4 changes needed:**
- Add `--min-score` Typer option (type `float`, default `0.0`)
- Pass `min_score` to `search.hybrid_search()`
- The score display format is already correct

### Layer 4: `mcp/server.py` — corpus_search()

**Current state:**
- `score: float(row.get("_relevance_score", 0.0))` is already in each result dict
- No `min_score` parameter

**v1.4 changes needed:**
- Add `min_score: Optional[float] = None` parameter to the `@mcp.tool` function
- Apply: `if min_score is not None: raw_results = [r for r in raw_results if float(r.get("_relevance_score", 0.0)) >= min_score]`

---

## Score Display Options

Two valid approaches for displaying RRF scores to users:

### Option A: Raw RRF score (recommended)

Display as-is with 3 decimal places: `score: 0.019`

**Why:** Honest representation. Advanced users can reason about the range. Consistent with what
the API returns in `SearchResult.score`. No normalisation code to maintain.

**Downside:** Range [0.009, 0.033] is not intuitive. Users see `--min-score 0.015` and have no
mental model for what 0.015 means.

### Option B: Normalised score (0.0 to 1.0)

Divide raw score by theoretical maximum (2 / (1 + K) = 2/61 ≈ 0.0328):
```python
MAX_RRF_SCORE = 2.0 / (1 + 60)  # 0.032787
normalised = score / MAX_RRF_SCORE
```

**Why:** Users understand `--min-score 0.5` as "half the maximum relevance". More natural for
filtering.

**Downside:** Requires a normalisation constant that changes if RRFReranker K is ever changed.
Introduces a mismatch between raw `_relevance_score` and what users see.

**Recommendation:** Use raw scores for v1.4 (Option A). It is simpler, honest, and avoids
introducing a normalisation constant that could desync. Document the score range in help text:
`--min-score: Filter results below this RRF relevance score (range ~0.009–0.033, default 0.0 keeps all)`

---

## LanceDB Native Sorting: Does Not Exist for Hybrid Search

**Finding (verified against LanceDB 0.29.2):**

`LanceHybridQueryBuilder` has NO `sort_by`, `order_by`, or equivalent method. The public methods
are: `analyze_plan`, `bypass_vector_index`, `create`, `distance_range`, `distance_type`, `ef`,
`explain_plan`, `limit`, `maximum_nprobes`, `metric`, `minimum_nprobes`, `nprobes`, `offset`,
`phrase_query`, `refine_factor`, `rerank`, `select`, `text`, `to_arrow`, `to_batches`, `to_df`,
`to_list`, `to_pandas`, `to_polars`, `to_pydantic`, `to_query_object`, `vector`, `where`,
`with_row_id`.

The existing implementation of post-retrieval Python sorting in `engine.py` is therefore the
CORRECT approach. There is no LanceDB-native alternative.

**RRFReranker already sorts descending by `_relevance_score` before returning results.** The
`"relevance"` sort mode in `hybrid_search()` already works correctly — it is the default
ordering from the reranker and requires no additional sorting step.

---

## LanceDB Native Score Filtering: Does Not Exist

`LanceHybridQueryBuilder` has no `where` predicate that can reference `_relevance_score`. The
`where()` method filters on stored table columns (schema fields). `_relevance_score` is a
computed column added by the reranker after retrieval — it is not a stored column and cannot be
used in a pre-retrieval SQL predicate.

**Conclusion:** `--min-score` filtering MUST be implemented as post-processing in Python. This is
correct and sufficient — the result set is already limited by `limit` before the score filter
applies, so the filter operates on at most `limit` rows (typically 10).

---

## Implementation Pattern: min_score Filter

Apply at the innermost layer (engine) for consistency across CLI, API, and MCP:

```python
# In CorpusSearch.hybrid_search(), after text-term filter, before sort:
if min_score > 0.0:
    filtered = [
        r for r in filtered
        if float(r.get("_relevance_score", 0.0)) >= min_score
    ]
```

Applying it at the engine layer means:
- CLI, API, and MCP all get filtering for free
- MCP does not need a duplicate filter (though it can still apply one as a belt-and-suspenders)
- Tests can verify filtering behaviour at the engine level

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| New LanceDB API calls for sorting | `LanceHybridQueryBuilder` has no sort_by — verified | Post-processing Python sort (already implemented) |
| Score normalisation to [0, 1] | Adds a fragile constant tied to K=60; confusing if K changes | Display raw RRF scores with range documentation |
| `_relevance_score` as a stored LanceDB column | It is computed per-query by the reranker; storing it makes no sense | Read from query result dict |
| Pandas for score filtering | overkill for ≤10 rows of post-processing | Plain list comprehension |
| Third-party rerankers (ColBERT, cross-encoders) | Out of scope; adds Ollama/GPU dependency | RRFReranker is correct for this use case |
| `--sort` values beyond relevance/path for v1.4 | Milestone spec only requires `relevance|path`; others already work | Keep existing sort_by values; don't break them |

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Post-processing Python sort | LanceDB native sort_by | Native would be better for large result sets, but doesn't exist for hybrid search |
| Raw RRF score display | Normalised 0–1 score | Use normalisation if UX testing shows users are confused by 0.019 scores |
| Single min_score filter in engine | Duplicate filter in engine + MCP | Redundant. Engine layer is sufficient. MCP can add its own if it needs to override engine behaviour. |
| `min_score: float = 0.0` default | `min_score: float | None = None` | `None` is fine too, but `0.0` avoids a None check and is semantically identical (0.0 keeps all results) |

---

## Version Compatibility

| Package | Version | Verified Against | Notes |
|---------|---------|-----------------|-------|
| lancedb | 0.29.2 | Source code inspected | `_relevance_score` in results: YES. Native sort_by: NO. Score filter predicate: NO. |
| RRFReranker | ships with lancedb | Source code inspected | Default K=60, return_score="relevance"; score range [0.009, 0.033] |

---

## Sources

- `LanceHybridQueryBuilder` source (lancedb 0.29.2 installed) — confirmed no sort_by, confirmed to_list() returns dicts with `_relevance_score` key (HIGH)
- `RRFReranker.rerank_hybrid` source (lancedb 0.29.2 installed) — confirmed `_relevance_score` column appended as `pa.float32()`, kept in `return_score="relevance"` mode (HIGH)
- `src/corpus_analyzer/search/engine.py` — confirmed `sort_by` already implemented for 5 sort modes; `_VALID_SORT_VALUES` frozenset (HIGH)
- `src/corpus_analyzer/api/public.py` line 116 — confirmed `SearchResult.score = float(r.get("_relevance_score", 0.0))` (HIGH)
- `src/corpus_analyzer/mcp/server.py` line 95 — confirmed `score: float(row.get("_relevance_score", 0.0))` in MCP result dicts (HIGH)
- `src/corpus_analyzer/cli.py` line 366 — confirmed score display already present (HIGH)
- Mathematical derivation: RRF score range [0.009, 0.033] with K=60 (HIGH)

---

*Stack research for: Corpus v1.4 — Search Precision (score display, sort, min-score filtering)*
*Researched: 2026-02-24*

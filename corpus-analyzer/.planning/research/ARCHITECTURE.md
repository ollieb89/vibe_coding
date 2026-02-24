# Architecture Research

**Domain:** Search precision controls — sort_by, min_score, score display across CLI/API/MCP
**Researched:** 2026-02-24
**Confidence:** HIGH (all findings from direct source inspection; no external research required)

---

## Context

This is a SUBSEQUENT MILESTONE (v1.4) research file. The question is: where in the existing
search pipeline should `sort_by` and `min_score` be applied, and how should score be surfaced
through `SearchResult` to CLI/API/MCP without breaking existing callers?

All findings are from direct inspection of the v1.3 codebase at
`/home/ollie/Development/Tools/vibe_coding/corpus-analyzer`.

---

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        Caller Layer                              │
├──────────────┬───────────────────┬───────────────────────────────┤
│  CLI         │  Python API       │  MCP Server                   │
│  cli.py      │  api/public.py    │  mcp/server.py                │
│  search_cmd  │  search()         │  corpus_search()              │
├──────────────┴───────────────────┴───────────────────────────────┤
│                     Search Engine Layer                          │
│         search/engine.py — CorpusSearch.hybrid_search()         │
├──────────────────────────────────────────────────────────────────┤
│                       Data Layer                                 │
│    LanceDB (chunks table)  ←  store/schema.py (ChunkRecord)     │
└──────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | File | Responsibility |
|-----------|------|----------------|
| CorpusSearch | `search/engine.py` | Executes hybrid BM25+vector query; applies post-retrieval sort; owns `_VALID_SORT_VALUES` |
| SearchResult | `api/public.py` | Public dataclass for Python API callers; maps raw dict fields to typed attributes |
| search() | `api/public.py` | Bridges callers to CorpusSearch; marshals kwargs; maps raw dicts to SearchResult |
| search_command | `cli.py` | Typer command; owns `--sort`, `--limit`, `--min-score` flags; renders Rich output |
| corpus_search | `mcp/server.py` | FastMCP async tool; maps MCP params to hybrid_search kwargs; formats results as dicts |
| ChunkRecord | `store/schema.py` | LanceDB schema; `_relevance_score` is computed by RRFReranker at query time, not a stored column |

---

## Existing Pipeline: v1.3 Baseline

Precise understanding of the current pipeline is required before placing new controls.

### hybrid_search() Signature (v1.3)

```python
# search/engine.py:47
def hybrid_search(
    self,
    query: str,
    *,
    source: str | None = None,
    file_type: str | None = None,
    construct_type: str | None = None,
    limit: int = 10,
    sort_by: str = "relevance",    # already exists
) -> list[dict[str, Any]]:
```

`_VALID_SORT_VALUES = frozenset({"relevance", "construct", "confidence", "date", "path"})` —
already defined at module level.

### Data Flow: v1.3

```
User query
    │
    ▼
search_command() [cli.py:300]
    │  passes: query, source, file_type, construct_type, limit, sort_by
    ▼
CorpusSearch.hybrid_search() [engine.py:47]
    │  1. Validate sort_by against _VALID_SORT_VALUES
    │  2. Embed query → query_vec
    │  3. LanceDB .search("hybrid").vector().text().rerank(RRFReranker()).limit(limit)
    │     → raw rows with _relevance_score injected by RRFReranker
    │  4. Text-match gate: drop rows with no query term in text
    │  5. Post-sort: construct / confidence / date / path (relevance = RRF order, no-op)
    │  returns: list[dict[str, Any]]
    │
    ▼
CLI renders: file_path, construct_type, _relevance_score, summary, snippet
API maps to: SearchResult(path, file_type, construct_type, summary, score, snippet)
MCP returns: dict with "path", "score", "snippet", "full_content", "construct_type", "summary"
```

### Critical Observation: Score is Already Threaded Through All Layers

`_relevance_score` is already:

1. **Present in raw dicts** — RRFReranker injects it on every LanceDB result row
2. **Rendered in CLI** — `score: {result.get('_relevance_score', 0.0):.3f}` (cli.py:366)
3. **Mapped in Python API** — `score=float(r.get("_relevance_score", 0.0))` in `SearchResult`
4. **Exposed in MCP** — `"score": float(row.get("_relevance_score", 0.0))` in result dict

**Score display is already fully implemented in v1.3.** The v1.4 work is:
- `min_score` filtering (new capability)
- `sort_by` wired to API + MCP (already in CLI and engine, not yet in API/MCP callers)
- CLI `--sort` help text scoped to `relevance|path` per spec

---

## v1.4 Change Analysis

### 1. sort_by — Engine Already Has It; API and MCP Need Wiring

**Current gap:**
- `CorpusSearch.hybrid_search()` already accepts `sort_by` with full implementation
- CLI `search_command` already passes `--sort` through to `hybrid_search(sort_by=sort)`
- `api/public.py` `search()` does NOT pass `sort_by` — calls engine without it (uses default "relevance")
- `mcp/server.py` `corpus_search()` does NOT accept `sort_by` — calls engine without it

**v1.4 work:** Wire sort_by through API and MCP. No engine changes.

### 2. min_score — New; Must Be Applied Post-Retrieval in Engine

**Decision: Apply min_score as post-processing inside `hybrid_search()`, not as a LanceDB `.where()` predicate.**

Rationale — why NOT at LanceDB query time:
- `_relevance_score` is injected by `RRFReranker` after retrieval; it is not a stored column in `ChunkRecord` and cannot be used in a `.where()` predicate
- Even if stored, filtering before `limit` would interact poorly: a `limit=10` query filtered by score could return fewer than 10 results with no mechanism to fill slots
- LanceDB's hybrid search API does not expose a native score threshold

Rationale — why post-retrieval in Python:
- Consistent with how all existing `sort_by` variants are applied (post-retrieval, engine.py:106–121)
- The text-match gate is already a post-retrieval filter on the same list; `min_score` is the same pattern
- Simple, testable, zero LanceDB API constraints

**Placement:** Inside `hybrid_search()`, after the text-match gate (step 4), before post-sort (step 5).

### 3. Score Display — No Action Required

Already implemented across all three layers. The `SearchResult.score` field already exists and is tested by `test_search_result_has_required_fields`. Do not add a second score field.

---

## Integration Points

### New vs Modified — Explicit Breakdown

| Component | Change Type | What Changes |
|-----------|-------------|--------------|
| `search/engine.py` | **Modified** | `hybrid_search()` gains `min_score: float = 0.0` param; filter step inserted after text-match gate |
| `api/public.py` | **Modified** | `search()` gains `sort_by: str = "relevance"` and `min_score: float = 0.0`; both passed to `hybrid_search()` |
| `mcp/server.py` | **Modified** | `corpus_search()` gains `min_score: Optional[float] = None`; passed as `min_score or 0.0` to `hybrid_search()` |
| `cli.py` | **Modified** | `--min-score` Typer option added; passed to `hybrid_search()`; `--sort` help text updated to `relevance\|path` |
| `corpus/__init__.py` | **No change** | Re-exports `SearchResult`, `search`, `index` — public surface unchanged |
| `store/schema.py` | **No change** | `_relevance_score` is not a stored field; no schema migration required |
| `SearchResult` dataclass | **No change** | `score` field already exists; do not add fields (test asserts exact 6-field set) |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| CLI → engine | `search.hybrid_search(sort_by=sort, min_score=min_score)` | Already passes `sort_by`; add `min_score` |
| API → engine | `hybrid_search(sort_by=sort_by, min_score=min_score)` | Currently omits both; add both |
| MCP → engine | `hybrid_search(min_score=min_score or 0.0)` | Currently omits both; add `min_score`; keep `sort_by` optional (agents can live without it) |
| API → Python caller | `SearchResult` dataclass | No field changes; `score` already present |
| MCP → agent caller | `dict[str, Any]` with `"score"` key | Already present; no change to output shape |

---

## Data Flow: v1.4 Target State

```
corpus search "agent memory" --sort path --min-score 0.4
    │
    ▼
search_command() [cli.py]
    │  passes: query, source, file_type, construct_type, limit,
    │           sort_by="path", min_score=0.4
    ▼
CorpusSearch.hybrid_search() [engine.py]
    │  1. Validate sort_by ("path" in _VALID_SORT_VALUES — passes)
    │  2. Embed query → query_vec
    │  3. LanceDB hybrid search → raw_results (with _relevance_score)
    │  4. Text-match gate (existing — unchanged)
    │  5. [NEW] min_score filter: drop rows where _relevance_score < 0.4
    │  6. Post-sort by "path" (ascending file_path)
    │  returns: filtered, sorted list[dict[str, Any]]
    │
    ▼
CLI renders: file_path, construct_type, score (already shown :.3f), summary, snippet
```

```
from corpus import search
results = search("agent memory", sort_by="relevance", min_score=0.4)
# SearchResult.score already populated from _relevance_score — no dataclass change
```

```
# MCP
await corpus_search(query="agent", min_score=0.6, ctx=ctx)
# Returns existing dict shape with "score" — no output schema change
```

---

## Architectural Patterns

### Pattern 1: Additive Defaults for Backward Compatibility

**What:** New parameters use defaults that reproduce current behaviour exactly.
**When to use:** Adding parameters to a function consumed by multiple callers (CLI, API, MCP, tests).
**Trade-offs:** All existing callers continue to work without modification.

```python
# engine.py — existing callers omit min_score, get identical behaviour to v1.3
def hybrid_search(self, query: str, *, ..., min_score: float = 0.0) -> list[dict[str, Any]]:
    ...
    if min_score > 0.0:   # guard: skip filter entirely when not requested
        filtered = [r for r in filtered if float(r.get("_relevance_score", 0.0)) >= min_score]
```

### Pattern 2: Post-Retrieval Filter (not Query-Time)

**What:** Score thresholding happens in Python after LanceDB returns results.
**When to use:** When the filter criterion (`_relevance_score`) is computed by the reranker, not stored as a column.
**Trade-offs:** Slightly more rows potentially fetched from LanceDB; negligible at local scale. Avoids LanceDB API constraints and limit-interaction edge cases.

### Pattern 3: Thin Caller Passthrough

**What:** CLI, API, and MCP pass parameters straight through to the engine without validating them.
**When to use:** Engine owns validation (`_VALID_SORT_VALUES`, `FILTER_SAFE_PATTERN`). Callers should not duplicate validation logic.
**Trade-offs:** Engine is the single source of truth. Callers catch `ValueError` and format for their output channel.

```python
# api/public.py — thin passthrough, engine handles validation
def search(query: str, *, sort_by: str = "relevance", min_score: float = 0.0, ...) -> list[SearchResult]:
    engine, _ = _open_engine()
    raw = engine.hybrid_search(query, ..., sort_by=sort_by, min_score=min_score)
    return [SearchResult(...) for r in raw]
```

---

## Anti-Patterns

### Anti-Pattern 1: Query-Time Score Filter via `.where()`

**What people might do:** Add `.where(f"_relevance_score >= {min_score}")` to the LanceDB query builder.
**Why it's wrong:** `_relevance_score` is not a stored column — it is injected by `RRFReranker` into result rows after the query executes. It does not exist in `ChunkRecord` and cannot be used in a `.where()` predicate. This would raise a LanceDB runtime error.
**Do this instead:** Filter the `filtered` list in Python after `builder.limit(limit).to_list()`.

### Anti-Pattern 2: Adding or Renaming the `score` Field in SearchResult

**What people might do:** Add a new `relevance_score` field or rename `score` to `relevance_score` assuming the field is missing or unclear.
**Why it's wrong:** `SearchResult.score` already exists and is already populated from `_relevance_score`. The test `test_search_result_has_required_fields` asserts exactly 6 fields: `{"path", "file_type", "construct_type", "summary", "score", "snippet"}`. Adding or renaming a field breaks this test and breaks existing callers.
**Do this instead:** Use the existing `score` field as-is.

### Anti-Pattern 3: Duplicating Validation in Each Caller

**What people might do:** Validate `sort_by` values or `min_score >= 0` in CLI, API, and MCP separately.
**Why it's wrong:** Engine already owns `sort_by` validation via `_VALID_SORT_VALUES`. Duplicating creates divergence risk when new sort values are added.
**Do this instead:** Let the engine raise `ValueError`; callers catch it and format for their output channel. The CLI pattern at cli.py:348–350 is the model.

### Anti-Pattern 4: Narrowing Engine's sort_by Options to {relevance, path}

**What people might do:** Interpret the v1.4 spec "sort relevance|path" as meaning `construct`, `confidence`, `date` should be removed from `_VALID_SORT_VALUES`.
**Why it's wrong:** These sort values are already shipped, tested (7 tests in `TestHybridSearchSort`), and used by existing `--sort construct` callers. The v1.4 spec scopes the CLI `--sort` help text to the two new options, not the engine's capability.
**Do this instead:** Update `--sort` help text to show `relevance|path` as the featured options; leave `_VALID_SORT_VALUES` unchanged.

### Anti-Pattern 5: Applying min_score Before the Text-Match Gate

**What people might do:** Apply `min_score` immediately after `to_list()`, before the text-match gate.
**Why it's wrong:** The text-match gate can promote or demote scores indirectly (by removing rows). The correct order is: (1) LanceDB retrieval, (2) text-match gate, (3) min_score filter, (4) sort. This matches the existing two-stage filtering idiom.
**Do this instead:** Insert `min_score` filter as step 5 in `hybrid_search()`, after the text-match gate at line 104, before the sort block at line 106.

---

## Recommended Build Order

Dependencies flow upward: engine → API/MCP/CLI. Tests at each layer must pass before wiring the next.

### Phase 1: Engine (no caller impact)

1. Add `min_score: float = 0.0` to `hybrid_search()` signature
2. Insert filter step (after text-match gate line ~104, before sort block line ~106):
   ```python
   if min_score > 0.0:
       filtered = [r for r in filtered if float(r.get("_relevance_score", 0.0)) >= min_score]
   ```
3. Add engine unit tests:
   - `min_score=0.0` returns all results (existing behaviour preserved)
   - `min_score=1.1` returns empty list (no result can score > 1.0 in RRF)
   - `min_score=0.5` with seeded data filters correctly

### Phase 2: Python API (depends on Phase 1)

4. Add `sort_by: str = "relevance"` and `min_score: float = 0.0` to `search()`
5. Pass both through to `hybrid_search()`
6. Update `test_public.py:test_search_calls_hybrid_search_and_maps_to_dataclasses`:
   - The `assert_called_once_with` check must include `sort_by` and `min_score` in expected kwargs
7. Update `test_public.py:test_search_passes_filters_to_hybrid_search` similarly

### Phase 3: MCP Server (depends on Phase 1)

8. Add `min_score: Optional[float] = None` to `corpus_search()` tool signature
9. Pass `min_score=min_score or 0.0` to `hybrid_search()`
10. Update `test_server.py:test_corpus_search_passes_filters_to_hybrid_search`:
    - `assert_called_once_with` must include `min_score` in expected kwargs

### Phase 4: CLI (depends on Phase 1)

11. Add `min_score: float` Typer option with `--min-score` flag, default `0.0`
12. Pass `min_score=min_score` to `hybrid_search()`
13. Update `--sort` help text to `relevance|path` (plus optionally list others as secondary)
14. Add CLI tests:
    - `--min-score` flag appears in `--help` output
    - Mock returning result with `_relevance_score=0.3` with `--min-score 0.5` → no output rendered

---

## Test Contracts That Must Be Preserved

| Test | File | Contract |
|------|------|----------|
| `test_search_result_has_required_fields` | `tests/api/test_public.py:13` | Field set = exactly `{"path", "file_type", "construct_type", "summary", "score", "snippet"}` — do not add fields |
| `test_search_calls_hybrid_search_and_maps_to_dataclasses` | `tests/api/test_public.py:37` | `assert_called_once_with` — must be updated to include new kwargs after adding `sort_by`/`min_score` |
| `test_search_passes_filters_to_hybrid_search` | `tests/api/test_public.py:69` | `assert_called_once_with` — must be updated similarly |
| `test_corpus_search_passes_filters_to_hybrid_search` | `tests/mcp/test_server.py:137` | `assert_called_once_with` — must be updated to include `min_score` |
| `test_hybrid_uses_rrf` | `tests/search/test_engine.py:114` | `_relevance_score` present in all results — preserved by default `min_score=0.0` |
| All `TestHybridSearchSort` tests | `tests/search/test_engine.py:282` | Sort behaviour unchanged — `min_score=0.0` default means no filtering, all rows retained |
| `test_zero_results_no_crash` | `tests/search/test_engine.py:204` | Empty result returns `[]` — preserved (min_score filter on empty list is a no-op) |

---

## Recommended Project Structure (Unchanged)

No new files or directories required. All changes are in-place modifications to existing files.

```
src/corpus_analyzer/
├── search/
│   └── engine.py          # MODIFIED: min_score param + filter step
├── api/
│   └── public.py          # MODIFIED: sort_by + min_score params
├── mcp/
│   └── server.py          # MODIFIED: min_score param
└── cli.py                 # MODIFIED: --min-score option
```

---

## Scaling Considerations

Not applicable. This is a single-user local tool. The post-retrieval `min_score` filter operates
on a list already bounded by `limit` (default 10, max reasonable ~100). Zero performance concern.

---

## Sources

- Direct inspection: `search/engine.py` — hybrid_search signature, `_VALID_SORT_VALUES`, post-sort block
- Direct inspection: `api/public.py` — SearchResult dataclass (6 fields), search() signature, _open_engine()
- Direct inspection: `mcp/server.py` — corpus_search() params, hybrid_search() call site
- Direct inspection: `cli.py` lines 300–373 — search_command() params, rendering loop
- Direct inspection: `store/schema.py` — ChunkRecord fields (confirms `_relevance_score` not stored)
- Direct inspection: `tests/search/test_engine.py` — TestHybridSearchSort class, seeded fixtures
- Direct inspection: `tests/api/test_public.py` — field assertion test, call-site assertions
- Direct inspection: `tests/mcp/test_server.py` — filter passthrough assertion
- Direct inspection: `tests/cli/test_search_status.py` — CLI contract tests
- `.planning/PROJECT.md` — v1.4 milestone requirements (score display, `--sort relevance|path`, `--min-score`)

---

*Architecture research for: corpus-analyzer v1.4 Search Precision*
*Researched: 2026-02-24*

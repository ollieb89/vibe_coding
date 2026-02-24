# Phase 13: Engine Min-Score Filter - Research

**Researched:** 2026-02-24
**Domain:** Python post-retrieval filtering on LanceDB hybrid search results
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Phase Boundary:** Add `min_score: float = 0.0` parameter to `CorpusSearch.hybrid_search()`. Apply post-retrieval Python list comprehension filter. Unit tests only. No CLI, API, or MCP changes — those are Phase 14.

**Threshold semantics:**
- Operator is `>=` (inclusive) — a result at exactly `min_score` passes the filter
- Matches standard search tool convention (Elasticsearch, OpenSearch, etc.)
- Avoids user surprise when threshold is calibrated from an observed score

**Zero default contract:**
- `min_score=0.0` is a guaranteed no-op — returns identical results to not filtering
- Any real RRF score is > 0.0, so this is a hard zero-regression guarantee for existing callers
- Default must be 0.0 (not None) — callers should not need to handle optional

**Filter placement in pipeline:**
- Filter is applied **after** the existing text-match gate, **before** the sort block
- Consistent with the existing pipeline order (text gate → score filter → sort)
- Do not apply before text-match gate

**Post-filter sort:**
- Sort the remaining survivors normally — min_score just shrinks the pool
- Sort ordering logic is unchanged

### Claude's Discretion

- Exact Python expression for the filter (`score >= min_score` in a list comprehension)
- Whether to add a comment explaining RRF score range at the filter site
- Test fixture approach (seeded mock scores vs real RRF values)

### Deferred Ideas (OUT OF SCOPE)

- Input validation for negative `min_score` values — not discussed; Claude's discretion (recommend: accept silently, since 0.0 default covers the common case and negative values are a no-op)
- CLI empty-result hint — Phase 14
- API/MCP parity — Phase 14
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FILT-01 | User can filter `corpus search` results below a threshold with `--min-score <float>` (default `0.0` — no filtering) | Engine-only change: add `min_score: float = 0.0` parameter to `hybrid_search()`, apply post-retrieval list comprehension on `_relevance_score` key. CLI wiring is Phase 14; Phase 13 covers only the engine. |
</phase_requirements>

---

## Summary

Phase 13 is a narrow, engine-only change: add a single `min_score: float = 0.0` keyword argument to `CorpusSearch.hybrid_search()` in `src/corpus_analyzer/search/engine.py`, and apply a one-line post-retrieval Python list comprehension to filter the `filtered` list (which already exists at that point in the pipeline) to keep only rows where `float(r.get("_relevance_score", 0.0)) >= min_score`.

All the necessary research has been pre-done and documented in `.planning/research/STACK.md`. The `_relevance_score` field is already injected by `RRFReranker` into every result dict after retrieval — it is not a stored LanceDB column and cannot be used in a `.where()` predicate. Post-processing Python is both the correct and only viable approach. The score range is ~0.009–0.033 (RRF with K=60, two retrieval systems). The `0.0` default guarantees zero regression for all existing callers.

The entire implementation is two or three lines in `engine.py` plus a small set of new unit tests in `tests/search/test_engine.py`. The existing test fixture pattern (`seeded_table` / `sortable_table`) is the right model: seed rows with known vectors, create FTS index, query with a real query string, and assert on `_relevance_score`. Because RRF scores are computed by LanceDB at query time (not controlled by the test author), a `min_score=99.0` test must use a threshold known to exceed any real RRF score.

**Primary recommendation:** Add `min_score: float = 0.0` to `hybrid_search()`, apply `[r for r in filtered if float(r.get("_relevance_score", 0.0)) >= min_score]` immediately after the text-gate comprehension and before the sort block, and test with three cases: default (no-op), exact-zero threshold, and impossibly-high threshold (returns empty).

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| LanceDB | 0.29.2 (installed) | Vector storage + hybrid search + RRFReranker | Already in use; `_relevance_score` confirmed present in result dicts |
| Python stdlib | 3.12+ | List comprehension for post-retrieval filtering | No library needed; ≤10 rows post-retrieval |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.0+ | Unit testing | Testing the new `min_score` parameter behaviour |
| lancedb (test) | 0.29.2 | Real LanceDB table in `tmp_path` for integration-style engine tests | Existing pattern in `test_engine.py` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Python list comprehension | Pandas/NumPy filtering | Overkill for ≤10 rows; no new dependency needed |
| Post-retrieval Python filter | LanceDB `.where()` predicate on `_relevance_score` | `.where()` only operates on stored columns; `_relevance_score` is computed by RRFReranker after retrieval — this approach is impossible |
| `min_score: float = 0.0` | `min_score: float \| None = None` | `None` adds a None-check; `0.0` is semantically identical (passes all real scores) and avoids the check |

**Installation:** No new packages. Zero new dependencies for this phase.

---

## Architecture Patterns

### File Location

```
src/corpus_analyzer/search/
└── engine.py        # Only file that changes in Phase 13

tests/search/
└── test_engine.py   # New tests appended here
```

### Pattern 1: Filter Placement in Existing Pipeline

**What:** The `hybrid_search()` method already has a two-stage pipeline after retrieval. Stage 1 is a text-term gate (text-match list comprehension into `filtered`). Stage 2 is sorting. The `min_score` filter inserts between these two stages.

**When to use:** Always — this placement matches the locked decision and is consistent with the existing pipeline order.

**Current pipeline (lines 100–121 of `engine.py`):**

```python
# Stage 1: text-match gate (existing)
filtered = [
    r
    for r in results
    if any(term in str(r.get("text", "")).lower() for term in query_terms)
]

# Stage 2: min_score filter (NEW — insert here)
# RRF scores range from ~0.009 to ~0.033 for K=60.
# min_score=0.0 (default) is a no-op since all real scores are positive.
if min_score > 0.0:
    filtered = [
        r for r in filtered
        if float(r.get("_relevance_score", 0.0)) >= min_score
    ]

# Stage 3: sort block (existing, unchanged)
if sort_by == "construct":
    ...
```

**Note on the `if min_score > 0.0` guard:** It is an optional performance shortcut — the comprehension `[r for r in filtered if float(r.get("_relevance_score", 0.0)) >= 0.0]` is logically correct without the guard (0.0 passes all scores), but the guard avoids a redundant iteration for the common default case. Claude's discretion per CONTEXT.md.

### Pattern 2: Signature Change

**What:** Add `min_score` as a keyword-only float argument with default `0.0`.

**Example:**

```python
def hybrid_search(
    self,
    query: str,
    *,
    source: str | None = None,
    file_type: str | None = None,
    construct_type: str | None = None,
    limit: int = 10,
    sort_by: str = "relevance",
    min_score: float = 0.0,          # NEW
) -> list[dict[str, Any]]:
    """Run a hybrid BM25+vector query with optional AND-filter chaining.

    Args:
        ...
        min_score: Minimum _relevance_score threshold (inclusive). Results
            below this score are excluded. Default 0.0 keeps all results.
            RRF scores range approximately 0.009–0.033 for K=60.
    """
```

### Pattern 3: Test Fixture Approach

**What:** Reuse the existing `seeded_table` / `search` fixture pattern. The `_relevance_score` values are produced by LanceDB's RRFReranker during the query — they are not directly controlled by the test author. Use boundary values:

- `min_score=0.0` → same results as no argument (regression test)
- `min_score=0.001` → passes any real RRF score (returns the same results as 0.0, confirming threshold logic)
- `min_score=99.0` → exceeds maximum possible RRF score (returns empty list)

**Example tests:**

```python
def test_min_score_zero_is_noop(search: CorpusSearch) -> None:
    """FILT-01: min_score=0.0 returns identical results to no filter."""
    without_filter = search.hybrid_search("search")
    with_zero = search.hybrid_search("search", min_score=0.0)
    assert with_zero == without_filter


def test_min_score_above_max_returns_empty(search: CorpusSearch) -> None:
    """FILT-01: min_score=99.0 exceeds any real RRF score → empty list."""
    results = search.hybrid_search("search", min_score=99.0)
    assert results == []


def test_min_score_filters_below_threshold(search: CorpusSearch) -> None:
    """FILT-01: min_score just above zero removes results whose _relevance_score is below it."""
    # Get real scores from a baseline query
    baseline = search.hybrid_search("search")
    if not baseline:
        pytest.skip("no results in seeded table for this query")
    # Find the maximum observed score and use it as a threshold
    max_score = max(float(r.get("_relevance_score", 0.0)) for r in baseline)
    # Filter at threshold = max_score keeps at least one result (inclusive)
    results = search.hybrid_search("search", min_score=max_score)
    assert len(results) >= 1
    assert all(float(r.get("_relevance_score", 0.0)) >= max_score for r in results)
```

### Anti-Patterns to Avoid

- **Filtering before the text-gate:** The locked decision requires filtering after the text-gate. Do not move the filter before `filtered` is populated.
- **Using `.where()` on LanceDB builder:** `_relevance_score` is not a stored column — `.where(f"_relevance_score >= {min_score}")` will fail at runtime. Verified against LanceDB 0.29.2.
- **`min_score: float | None = None` signature:** The locked decision requires `float = 0.0`. Do not use Optional.
- **Mutating `results` directly:** Apply the filter to `filtered` (post-text-gate list), not `results` (raw retrieval output). Matches pipeline order in locked decisions.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Score threshold filtering | Custom reranker subclass, score normalisation layer | Plain list comprehension on `_relevance_score` | `_relevance_score` is already in every result dict; a comprehension is 1 line |
| Score range discovery | Dynamic calibration, histogram analysis | Hard-coded range ~0.009–0.033 documented in comment/docstring | Range is deterministic from RRF formula with K=60 |

**Key insight:** The entire implementation is a parameter addition + one list comprehension. Any abstraction beyond that is over-engineering for a ≤10-row post-processing step.

---

## Common Pitfalls

### Pitfall 1: Applying Filter to Wrong Variable

**What goes wrong:** Adding the comprehension to `results` (raw LanceDB output) instead of `filtered` (post-text-gate list).
**Why it happens:** Both variables exist in the function; easy to target the wrong one.
**How to avoid:** Insert the filter block immediately after the text-gate `filtered = [...]` block, operating on `filtered`.
**Warning signs:** Tests that expect empty results for `min_score=99.0` pass but tests for zero-regression with `min_score=0.0` fail when the query has no text matches (empty `filtered` but non-empty `results`).

### Pitfall 2: Using `_relevance_score` as a Stored Column in `.where()`

**What goes wrong:** `builder.where(f"_relevance_score >= {min_score}")` raises a LanceDB error or returns zero results.
**Why it happens:** `_relevance_score` looks like a column name but is computed by the reranker post-retrieval.
**How to avoid:** Never add a `.where()` call for `_relevance_score`. Post-retrieval Python list comprehension is the only correct approach.
**Warning signs:** LanceDB raises `ArrowInvalid` or `ColumnNotFound` error.

### Pitfall 3: `_relevance_score` Type

**What goes wrong:** Comparing `r.get("_relevance_score", 0.0)` directly against `min_score` without casting may fail if LanceDB returns a `numpy.float32` or `pyarrow` scalar rather than a Python `float`.
**Why it happens:** `pa.float32()` values from `to_list()` can be numpy scalars depending on Arrow version.
**How to avoid:** Always cast: `float(r.get("_relevance_score", 0.0)) >= min_score`. This is the pattern already used in `public.py` and `server.py`.
**Warning signs:** `TypeError: '>=' not supported between instances of 'numpy.float32' and 'float'`.

### Pitfall 4: Test Scores Not Deterministic

**What goes wrong:** Tests assert specific score values (e.g., `assert results[0]["_relevance_score"] == 0.0192`) and break when LanceDB or the FTS index changes behaviour.
**Why it happens:** RRF scores depend on rank ordering, which depends on vector similarity and BM25 term frequency — both implementation details.
**How to avoid:** Use boundary-value tests (0.0 = no-op, 99.0 = empty list) and relative assertions (`>= min_score`), not exact score values.

---

## Code Examples

Verified patterns from existing codebase:

### Score Access Pattern (already used in api/public.py and mcp/server.py)

```python
# Source: src/corpus_analyzer/api/public.py line 116
score=float(r.get("_relevance_score", 0.0)),

# Source: src/corpus_analyzer/mcp/server.py line 95
"score": float(row.get("_relevance_score", 0.0)),
```

### Min-Score Filter (new, to be added to engine.py)

```python
# After text-gate, before sort block
# RRF scores range ~0.009–0.033 for K=60; min_score=0.0 is a no-op.
if min_score > 0.0:
    filtered = [
        r for r in filtered
        if float(r.get("_relevance_score", 0.0)) >= min_score
    ]
```

### Existing Text-Gate Pattern (for reference, lines 100–104 of engine.py)

```python
filtered = [
    r
    for r in results
    if any(term in str(r.get("text", "")).lower() for term in query_terms)
]
```

### Existing Sort Block Pattern (for reference, lines 106–121 of engine.py)

```python
if sort_by == "construct":
    filtered.sort(
        key=lambda r: (
            CONSTRUCT_PRIORITY.get(str(r.get("construct_type") or ""), 99),
            -float(r.get("classification_confidence") or 0.0),
        )
    )
elif sort_by == "confidence":
    filtered.sort(
        key=lambda r: float(r.get("classification_confidence") or 0.0), reverse=True
    )
elif sort_by == "date":
    filtered.sort(key=lambda r: str(r.get("indexed_at") or ""), reverse=True)
elif sort_by == "path":
    filtered.sort(key=lambda r: str(r.get("file_path") or ""))

return filtered
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No score filtering | `min_score: float = 0.0` parameter with post-retrieval list comprehension | Phase 13 | Callers can drop low-relevance results without touching LanceDB query logic |

**Deprecated/outdated:**
- Nothing deprecated. This is a pure addition.

---

## Open Questions

1. **Negative `min_score` handling**
   - What we know: CONTEXT.md defers this to Claude's discretion; the locked decision says "accept silently" since negative values are a no-op (all scores are > 0.0)
   - What's unclear: Whether a docstring warning is worth adding ("negative values behave the same as 0.0")
   - Recommendation: Accept silently, add a one-line docstring note. No validation code.

2. **Guard clause `if min_score > 0.0`**
   - What we know: CONTEXT.md marks the exact filter expression as Claude's discretion
   - What's unclear: Whether to include the guard or apply the comprehension unconditionally
   - Recommendation: Include the guard for clarity and micro-efficiency. Document it with an inline comment.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.0+ |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`, `testpaths = ["tests"]`) |
| Quick run command | `uv run pytest tests/search/test_engine.py -v` |
| Full suite command | `uv run pytest -v` |
| Estimated runtime | ~30 seconds (full suite); ~5 seconds (engine tests only) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FILT-01 | `min_score=0.0` returns same results as no filter | unit | `uv run pytest tests/search/test_engine.py::test_min_score_zero_is_noop -x` | No — Wave 0 gap |
| FILT-01 | `min_score=99.0` returns empty list | unit | `uv run pytest tests/search/test_engine.py::test_min_score_above_max_returns_empty -x` | No — Wave 0 gap |
| FILT-01 | `hybrid_search()` accepts `min_score` parameter | unit | `uv run pytest tests/search/test_engine.py::test_min_score_parameter_accepted -x` | No — Wave 0 gap |
| FILT-01 | Results passing filter all have score >= threshold | unit | `uv run pytest tests/search/test_engine.py::test_min_score_filters_below_threshold -x` | No — Wave 0 gap |
| FILT-01 | 281 existing tests remain green | regression | `uv run pytest -v` | Yes — existing suite |

### Nyquist Sampling Rate

- **Minimum sample interval:** After every committed task → run: `uv run pytest tests/search/test_engine.py -v`
- **Full suite trigger:** Before merging final task of any plan wave
- **Phase-complete gate:** Full suite green (`uv run pytest -v`) before `/gsd:verify-work` runs
- **Estimated feedback latency per task:** ~5 seconds (engine test file only)

### Wave 0 Gaps (must be created before implementation)

- [ ] `tests/search/test_engine.py` — append new `min_score` test functions (file exists; new tests added, not a new file)

None — existing test infrastructure and `seeded_table` / `search` fixtures in `tests/search/test_engine.py` cover all phase requirements. No new fixtures or framework setup needed.

---

## Sources

### Primary (HIGH confidence)

- `src/corpus_analyzer/search/engine.py` — full source read; confirmed current `hybrid_search()` signature, pipeline order (text-gate → sort), `_relevance_score` access patterns
- `tests/search/test_engine.py` — full source read; confirmed existing fixture patterns (`seeded_table`, `sortable_table`), test structure, `MockEmbedder`
- `.planning/research/STACK.md` — pre-existing v1.4 stack research (2026-02-24); confirmed `_relevance_score` is injected by RRFReranker (not stored column), LanceDB 0.29.2 native sort/filter not available, RRF score range ~0.009–0.033
- `src/corpus_analyzer/api/public.py` line 116 — `float(r.get("_relevance_score", 0.0))` pattern confirmed
- `src/corpus_analyzer/mcp/server.py` line 95 — same pattern confirmed

### Secondary (MEDIUM confidence)

None required — all critical findings were verified against installed source code.

### Tertiary (LOW confidence)

None.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries; all findings from installed source code
- Architecture: HIGH — filter placement locked by CONTEXT.md; insertion point unambiguous from reading engine.py
- Pitfalls: HIGH — verified against LanceDB 0.29.2 source; `_relevance_score` stored column pitfall confirmed impossible

**Research date:** 2026-02-24
**Valid until:** 2026-03-24 (stable library; 30-day estimate)

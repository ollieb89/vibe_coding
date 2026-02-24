# Pitfalls Research

**Domain:** Adding sort/filter/score controls to an existing hybrid search system (LanceDB + RRF + Typer CLI + FastMCP)
**Researched:** 2026-02-24
**Confidence:** HIGH (code inspected directly; RRF score behaviour confirmed via Azure AI Search official docs and LanceDB docs)

---

## Critical Pitfalls

### Pitfall 1: Treating RRF Score as an Absolute, Cross-Query Threshold

**What goes wrong:**
A developer sets `--min-score 0.02` expecting it to reliably filter noise across all queries. It filters nothing on query A (all results score 0.03–0.05) and filters everything on query B (all results score 0.008–0.015). The threshold carries no stable meaning across different queries or index states.

**Why it happens:**
RRF score is computed as `Σ 1 / (k + rank_i)` — a rank-fusion formula, not a similarity measure. With LanceDB's default `k=60` and two search methods (vector + BM25), the theoretical maximum for any single document is approximately `1/61 + 1/61 ≈ 0.033`. The actual observed range depends on how many sub-query results come back, which varies by query term specificity, index size, and filter predicates.

Concretely: at `--limit 10`, score distribution compresses into the top of the range. At `--limit 50`, it spreads. A threshold calibrated on one query at one limit will misfire at a different limit or on a different query. This is confirmed by Azure AI Search documentation: "The upper limit is bounded by the number of queries being fused, with each query contributing a maximum of approximately 1/k to the RRF score."

**How to avoid:**
- Document the score range in help text: `"Score is an RRF rank-fusion value (typically 0.005–0.033 with 2 sub-queries). Not a percentage. Not comparable across different queries or different --limit values."`
- Default `--min-score` to `0.0` (no filtering). It is an expert knob.
- Never recommend a threshold value in docs. Tell users to run the query without `--min-score`, observe the score column, then calibrate.
- Apply `min_score` filtering as a Python list comprehension _after_ `.to_list()` returns — do not try to use it as a LanceDB `.where()` predicate (see Pitfall 4).

**Warning signs:**
- `--min-score 0.01` returns 0 results on some queries and all results on others
- Tests for `min_score` written against hardcoded score values that were calibrated at one specific `--limit`

**Phase to address:** Whichever phase ships `--min-score`. The score range caveat must appear in help text from the first commit.

---

### Pitfall 2: Exact-Set Test on `SearchResult` Fields Blocks Every New Field Addition

**What goes wrong:**
Adding `sort_by: str` or `min_score: float` to `SearchResult` immediately fails the existing test at `tests/api/test_public.py:18`:

```python
assert field_names == {"path", "file_type", "construct_type", "summary", "score", "snippet"}
```

This uses `==` (exact set match), not a superset check. Any new field on `SearchResult` causes a test failure even if all existing callers still work correctly. The test suite goes red before any feature is usable.

**Why it happens:**
The test is a correct API contract test — it enforces the declared public surface. It is behaving as designed. The problem is that developers add a field without updating the test in the same commit, then are surprised when CI fails.

**How to avoid:**
- When adding fields to `SearchResult`, update this test in the same commit. It is a required coupling, not an optional cleanup.
- Make new fields optional with defaults: `sort_key: str = "relevance"` so existing positional-arg callers do not break at instantiation.
- Never add a required (no-default) positional field to `SearchResult` — it would break all existing call sites that construct the dataclass directly.
- The test at line 24 uses keyword arguments, so field order does not matter for construction. But the exact-set check at line 18 still requires updating.

**Warning signs:**
- A PR adds a field to `SearchResult` without touching `tests/api/test_public.py` — CI fails immediately.

**Phase to address:** API parity phase (when `sort_by` / `min_score` are added to `search()`).

---

### Pitfall 3: API Surface Left Behind When CLI and MCP Are Implemented First

**What goes wrong:**
The CLI grows `--sort` and `--min-score` flags. The MCP server grows `min_score`. Users calling `from corpus_analyzer.api.public import search` get none of these controls. The three surfaces diverge. This is explicitly a v1.4 failure mode — requirements state API and MCP parity are required.

**Why it happens:**
The gap already exists for `sort_by` in the current codebase. `api/public.py:search()` does not accept or pass `sort_by`, even though `engine.hybrid_search()` already supports it (added as part of v1.2/v1.3 engine work). It is easy to implement CLI + MCP and declare "done" without threading the same parameters through the Python API.

Current gap (confirmed by code inspection):

```python
# api/public.py lines 103-109 — sort_by is absent
raw = engine.hybrid_search(
    query,
    source=source,
    file_type=file_type,
    construct_type=construct_type,
    limit=limit,
    # sort_by silently defaults to "relevance"
    # min_score not implemented at all
)
```

**How to avoid:**
- Implement all three surfaces (CLI, API, MCP) in the same phase, not sequentially.
- Add an integration test that calls `api.public.search(sort_by="path")` and verifies results are path-sorted. This test will catch the gap at CI time before it reaches users.
- Treat the v1.4 requirements checklist literally: "Python `search()` API accepts `sort_by` and `min_score` parameters" is a pass/fail requirement, not a stretch goal.

**Warning signs:**
- Phase plan says "CLI and MCP done, API to follow" — do not accept this as an acceptable split.
- No test asserts that `api.public.search(sort_by=...)` changes result ordering.

**Phase to address:** Implement all three call sites atomically. Do not phase them separately.

---

### Pitfall 4: `min_score` Implemented as LanceDB `.where()` Predicate (Runtime Error)

**What goes wrong:**
A developer writes:
```python
builder = builder.where(f"_relevance_score >= {min_score}")
```
This either fails silently (returns all results, ignoring the filter) or raises a LanceDB error at runtime. LanceDB `.where()` operates on stored schema columns only. `_relevance_score` is a computed column injected by `RRFReranker` after retrieval — it does not exist in the `ChunkRecord` schema and cannot be referenced in a filter predicate.

**Why it happens:**
Developers familiar with SQL assume any field that appears in results can be used in a filter. LanceDB's query builder separates pre-retrieval filters (`.where()` on schema columns) from post-retrieval computations (reranker-injected fields like `_relevance_score`). The field name starts with `_` as a signal that it is synthetic, but this convention is not documented prominently.

**How to avoid:**
Apply `min_score` as a Python list comprehension after `.to_list()`, after the existing text-term filter:

```python
results = [dict(row) for row in builder.limit(limit).to_list()]

# Existing text-term filter (do not change order)
filtered = [r for r in results if any(term in str(r.get("text", "")).lower() for term in query_terms)]

# New min_score filter (after text-term filter)
if min_score > 0.0:
    filtered = [r for r in filtered if float(r.get("_relevance_score", 0.0)) >= min_score]
```

Order matters: apply `min_score` after the text-term filter so that the text-matching semantics of the existing behaviour are preserved.

**Warning signs:**
- Implementation uses `.where(f"_relevance_score >= {min_score}")` — will fail at runtime or be silently ignored.
- `min_score` filter applied before the text-term filter — changes observable filtering semantics.

**Phase to address:** Engine modification phase (when `min_score` is added to `hybrid_search()`).

---

### Pitfall 5: MCP Tool Signature Change Breaks Cached Schema in Claude Code

**What goes wrong:**
Adding `min_score: Optional[float] = None` to `corpus_search()` changes the FastMCP-generated JSON schema for the tool. Claude Code sessions that cached the old schema will show the old tool signature (no `min_score` parameter) until the MCP server is restarted and the session is refreshed. Users may not notice the new parameter is available.

Additionally: a known FastMCP issue (GitHub issue #1015) shows that optional parameters with default values are sometimes parsed incorrectly at the MCP boundary — the default value gets replaced with `None` rather than the declared default. For `min_score: Optional[float] = None`, this is not a problem (None is already the intended default). But it is worth verifying with a live test after implementation.

**Why it happens:**
MCP tool schemas are derived at server startup from the decorated function signature. Adding a parameter requires a server restart to take effect. Claude Code and other MCP clients cache the tool schema for the lifetime of a session.

The noqa concern: the existing codebase uses `Optional[str]` with `# noqa: UP045` on every parameter in `corpus_search()`. If a new parameter is added without the noqa comment, `uv run ruff check .` will fail CI because ruff UP045 flags `Optional[X]` as non-idiomatic (use `X | None` instead). But changing existing parameters to `X | None` is also a diff risk if it changes FastMCP's schema generation behaviour.

**How to avoid:**
- Follow the existing pattern exactly: `min_score: Optional[float] = None,  # noqa: UP045`
- After implementing, restart Claude Code to pick up the updated schema.
- Test the MCP tool with `min_score=None` (default path) and `min_score=0.01` (filtering path) to confirm no type errors at the tool boundary.
- Do not change existing parameter annotations from `Optional[X]` to `X | None` in the same PR — it is an unnecessary diff risk.

**Warning signs:**
- `uv run ruff check .` fails on the new parameter (missing `# noqa: UP045`).
- MCP tool works in pytest but the live Claude Code tool still shows the old signature (restart required).

**Phase to address:** MCP parity phase.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Add `--min-score` only to CLI, skip API/MCP | Faster to ship | Three surfaces diverge; v1.4 requirements explicitly require parity | Never — all three surfaces must ship together |
| Skip documenting RRF score range in `--min-score` help text | Saves one line | Users set `--min-score 0.5`, get 0 results, conclude the feature is broken | Never — caveat must be in help text from day one |
| Apply `min_score` as LanceDB `.where()` predicate | Looks cleaner | Runtime error or silent no-op — `_relevance_score` is not a schema column | Never |
| Apply `min_score` filter before text-term filter | Marginally simpler code | Changes observable filtering order, breaks existing text-matching semantics | Never |
| Update `SearchResult` without updating the exact-set test | Faster initial implementation | CI immediately fails — net zero time saved | Never |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| LanceDB `_relevance_score` | Using in `.where()` predicate | Filter in Python after `.to_list()` — it is a computed reranker column, not a stored schema field |
| LanceDB `_relevance_score` | Assuming 0–1 range like cosine similarity | Range is `0` to approximately `num_sub_queries / (k + 1)` ≈ `0.033` with default k=60 and 2 sub-queries |
| LanceDB `_relevance_score` | Comparing scores across queries | Scores are relative to the current result set and vary with `--limit`; not absolute |
| FastMCP `corpus_search` | Forgetting `# noqa: UP045` on `Optional[float]` | Copy the existing parameter pattern: `min_score: Optional[float] = None,  # noqa: UP045` |
| `SearchResult` dataclass | Adding field without updating the exact-set test | Update `test_search_result_has_required_fields` in the same commit |
| `api/public.search()` | Not threading `sort_by` and `min_score` to engine | Add both parameters to `search()` signature and pass them to `hybrid_search()` |
| Text-term filter ordering | Applying `min_score` before text-term filter | Apply `min_score` after text-term filter to preserve existing text-matching semantics |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| `min_score` filters all results after `limit` fetch | User gets 0 results with no explanation | Print hint when `min_score` discards all results: "No results above {min_score}. Try lowering." | Any time `min_score` is above the score range for the current query |
| High `limit` + aggressive `min_score` wastes retrieval | Fetch 50 results, discard 48, return 2 | This is acceptable at current scale; document if over-fetching becomes needed at larger indexes | Not a concern until index has >10k chunks |
| `search.status()` uses `to_pandas()` on full table | Slow for large indexes | Already present pre-v1.4; not introduced by this milestone | >10k chunks |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No score shown before `--min-score` lands | User cannot calibrate threshold without seeing scores | Score display must ship in the same phase as or before `--min-score`; CLI already partially shows score at line 366 |
| `--min-score` returns 0 results silently | User thinks search is broken | Print: "No results above min-score {x}. Run without --min-score to see available scores." |
| Score formatted with full float precision | `score: 0.016393442622950817` is unreadable | Format to 3–4 decimal places; CLI already uses `:.3f` at line 366 — verify this is applied consistently |
| Score column header labelled "score" | Users expect 0–100 or 0–1; `0.033` max looks like "3% match" | Label as "relevance" or add range hint: `score (RRF, max ~0.033)` |
| `--sort` flag not exposed in CLI help alongside score | Users discover sort by reading source, not `--help` | Ensure help text for `--sort` lists all valid values: `relevance\|construct\|confidence\|date\|path` |

---

## "Looks Done But Isn't" Checklist

- [ ] **Score display:** `_relevance_score` non-zero in real results — verify field name matches LanceDB output exactly (typo returns silent `0.0` via `r.get("_relevance_score", 0.0)`)
- [ ] **`--sort relevance` default:** Results return in RRF order (not sorted) when `sort_by="relevance"` — verify no accidental sort is applied on the "relevance" branch
- [ ] **`--sort path`:** Results sorted ascending by `file_path` — add a test asserting ordering
- [ ] **`--min-score` CLI:** Typer option added as `float`, default `0.0`, documented with RRF range caveat
- [ ] **`--min-score` engine:** Applied as Python filter after `.to_list()` and after text-term filter — not as `.where()` predicate
- [ ] **API parity:** `api/public.search()` signature includes `sort_by: str = "relevance"` and `min_score: float = 0.0`; both passed to `hybrid_search()`
- [ ] **`SearchResult` test updated:** `test_search_result_has_required_fields` exact-set assertion updated if any new fields added to `SearchResult`
- [ ] **MCP parity:** `corpus_search` tool accepts `min_score: Optional[float] = None`; `# noqa: UP045` present; MCP tests cover the parameter
- [ ] **Empty result hint:** CLI prints informative message when `min_score` filters all results to zero
- [ ] **Type annotations:** All new parameters annotated; `uv run mypy src/` exits 0
- [ ] **Ruff clean:** `uv run ruff check .` exits 0
- [ ] **Tests green:** 281 existing tests pass; new tests added for score display, `--min-score` filtering, API/MCP parity, and sort ordering

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| `min_score` via `.where()` fails at runtime | LOW | Move filter to Python post-processing; no schema change needed |
| `SearchResult` field addition breaks exact-set test | LOW | Update `test_search_result_has_required_fields` to include the new field |
| API surface missing `sort_by` after CLI ships | LOW | Add parameter with backward-compatible default; no schema migration |
| MCP schema cached by Claude Code after parameter addition | LOW | Restart Claude Code / MCP host |
| Users file bugs because `--min-score 0.5` returns nothing | LOW | Add score range to help text; no code change for calibration itself |
| `--min-score` filter applied before text-term filter | LOW | Swap filter order in engine; add regression test |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| RRF score range / threshold semantics | Score display phase | Help text includes range caveat; `--min-score 0.0` returns all results; `--min-score 99.0` returns none with hint |
| Exact-set test on `SearchResult` breaks | API parity phase | CI passes after updating `test_search_result_has_required_fields` |
| API surface missing `sort_by` / `min_score` | API parity phase | Test calls `api.public.search(sort_by="path")` and verifies path ordering |
| `min_score` via `.where()` predicate | Engine modification phase | Integration test with real LanceDB table verifies `min_score` parameter reduces result count without error |
| MCP schema break / noqa pattern | MCP parity phase | `uv run ruff check .` exits 0; MCP test passes with `min_score` argument |
| Empty result hint missing | CLI output phase | Manual test: `corpus search "query" --min-score 99` prints informative message |
| `min_score` applied before text-term filter | Engine modification phase | Ordering verified by unit test; text-term filter semantics unchanged |

---

## Sources

- LanceDB RRF Reranker documentation: https://docs.lancedb.com/integrations/reranking/rrf
- Azure AI Search Hybrid Scoring (RRF) — authoritative score range documentation: https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking
- FastMCP optional parameter handling issue: https://github.com/jlowin/fastmcp/issues/1015
- Direct code inspection: `src/corpus_analyzer/search/engine.py` (lines 30, 47–122), `src/corpus_analyzer/api/public.py` (lines 18, 79–120), `src/corpus_analyzer/mcp/server.py` (lines 43–108), `src/corpus_analyzer/cli.py` (lines 300–372)
- Existing contract test: `tests/api/test_public.py:18` — exact-set assertion on `SearchResult` fields

---
*Pitfalls research for: v1.4 Search Precision — adding sort, min-score, and score display to existing LanceDB hybrid search*
*Researched: 2026-02-24*

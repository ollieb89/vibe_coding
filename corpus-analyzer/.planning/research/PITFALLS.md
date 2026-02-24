# Pitfalls Research

**Domain:** Adding Intelligent Search features (MMR, cross-encoder re-ranking, graph centrality, multi-query AND, graph expansion, score normalisation) to an existing Python 3.12 hybrid search system (LanceDB BM25+vector+RRF, FastMCP, SQLite graph store, Typer CLI)
**Researched:** 2026-02-24
**Confidence:** HIGH (official Python docs, LanceDB docs, sentence-transformers docs, direct code inspection; cross-verified against multiple sources)

---

## Critical Pitfalls

### Pitfall 1: MMR on Unnormalized Embeddings Produces Wrong Diversity Scores

**What goes wrong:**
MMR computes `cosine_similarity(candidate, selected_item)` to penalize near-duplicates. If the embedding vectors are not L2-normalized, cosine similarity is computed as `dot(a, b) / (||a|| * ||b||)`. When vectors are stored as raw `list[float]` in LanceDB (as they are in this codebase — `embed_batch()` returns `list[list[float]]` from Ollama without normalization), the denominators vary per vector. Two chunks from the same file that have different-length vectors (because one chunk is longer than the other) will receive lower cosine similarity scores than they should, making them appear more "different" than they are. MMR will surface near-duplicates from the same file instead of suppressing them — the opposite of its purpose.

The bug is invisible in unit tests unless you deliberately test with known-near-duplicate embeddings from the same file.

**Why it happens:**
The existing `OllamaEmbedder.embed_batch()` returns whatever Ollama returns — nomic-embed-text outputs normalized vectors by default, but this is model-specific behavior that is not enforced by the code. If the model is changed (e.g., to a model that does not normalize), or if a test uses random vectors, MMR silently produces wrong results. The developer adds MMR assuming cosine similarity "just works" without reading whether the vectors are normalized.

**How to avoid:**
Before passing embeddings to the MMR function, explicitly L2-normalize them:
```python
import math

def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm < 1e-12:
        return vec  # zero vector — return as-is, not a valid embedding
    return [x / norm for x in vec]
```
Apply this inside the MMR function itself (not in the embedder), so the contract is "MMR always normalizes its inputs." Write a unit test where two chunks share 90% of their text — assert they are penalized (not selected together) when `lambda_param < 1.0`.

**Warning signs:**
- MMR with `lambda=0.5` returns results where the top 5 are all chunks from the same file
- Changing `lambda` from 0.0 to 1.0 produces no visible change in result diversity
- Unit tests pass with random vectors but fail on real embeddings

**Phase to address:** MMR implementation phase (RANK-01). Normalize inside the MMR function before any similarity computation.

---

### Pitfall 2: MMR Lambda Is a Global Constant — Wrong Defaults Degrade Quality

**What goes wrong:**
The developer hardcodes `lambda_param = 0.5` as a module constant or CLI default and never exposes it. The default feels reasonable in testing (small corpora, hand-crafted queries) but performs poorly on the actual user corpus where 80% of files are similar skills. At `lambda=0.5`, diversity is under-weighted and the top results still cluster around one sub-topic. Users do not know the knob exists and report that "diversity doesn't work."

Conversely, exposing lambda as a required CLI argument forces users to learn MMR theory before getting any results.

**Why it happens:**
Lambda tuning requires domain knowledge. The published guidance (`lambda=0.7` for precision, `lambda=0.3-0.5` for exploration) is for general document retrieval, not dense agent-skill corpora where documents are intentionally similar.

**How to avoid:**
Default `lambda_param = 0.7` (relevance-heavy) at the CLI level. Expose `--diversity <float>` as an optional flag (0.0 = pure diversity, 1.0 = pure relevance). Document the range in help text alongside the existing RRF score range documentation. Validate in the range `[0.0, 1.0]` with `ValueError` on invalid input — use the same pattern as the existing `min_score` validation. Do not apply MMR when `--limit 1` (single result — diversity is meaningless).

**Warning signs:**
- All top-5 results come from the same file even with `--diversity 0.3`
- `lambda=0.0` returns 5 results from 5 different sources but score=0.001 (pure diversity ignores relevance entirely)
- No test asserts that changing lambda changes the result set

**Phase to address:** MMR implementation phase (RANK-01). Bake the default and validation in before exposing the flag.

---

### Pitfall 3: MMR Quadratic Complexity Blocks Large Result Sets

**What goes wrong:**
MMR is O(n * k) where n is the candidate pool size and k is the number of results to select. For each of the k results to return, MMR scores all remaining n candidates. At the default `limit=10` with a candidate pool of `n=40` (4x overfetch), this is 400 comparisons — negligible. But if someone uses `--limit 50` with overfetch factor 4, the candidate pool is 200, and the inner loop runs 200 * 50 = 10,000 cosine similarity computations. Each cosine similarity on a 768-dim vector is ~1,500 floating-point operations. That is 15M FLOPs — approximately 50–100ms of Python-level computation, which makes the search feel slow.

More critically: the candidate pool grows quadratically with limit. At `limit=100` with 4x overfetch, the inner loop is 40,000 cosine comparisons — noticeable latency.

**Why it happens:**
The MMR candidate pool must be larger than the requested result count (otherwise diversity has no room to operate). The temptation is to set overfetch factor = 4x or 5x universally. Nobody notices latency at `limit=10` during development.

**How to avoid:**
Cap the MMR candidate pool at `min(overfetch * limit, 40)`. Beyond 40 candidates, the diversity benefit is marginal but the compute cost compounds. Document the cap. If numpy is already a dependency (via LanceDB), use vectorized cosine similarity: `np.dot(candidates_matrix, selected_matrix)` instead of a Python loop.

**Warning signs:**
- `corpus search --limit 50` is noticeably slower than `corpus search --limit 10`
- Profiling shows the MMR inner loop inside Python (not LanceDB or Ollama) is the bottleneck
- MCP latency grows proportionally with `limit` parameter

**Phase to address:** MMR implementation phase (RANK-01). Set the pool cap before performance testing. Test with `limit=50` in the integration test suite.

---

### Pitfall 4: Cross-Encoder Scores Are Incompatible With RRF Scores — Mixing Them Breaks Ranking

**What goes wrong:**
The existing search pipeline produces RRF scores in the range approximately `0.009–0.033`. Cross-encoder models produce logit scores typically in the range `[-10, +10]` (raw) or `[0, 1]` after sigmoid. If the v3 `--rerank` flag fetches cross-encoder scores and returns them directly to the existing display/filtering layer, the `--min-score 0.02` filter will exclude every result (all cross-encoder scores are > 1.0 in logit form), or pass every result if sigmoid-transformed (all > 0.02). The existing FILT-03 hint will fire spuriously. The MCP 0–1 normalisation added in v2 will double-normalise, compressing scores to the range 0.009–0.033 again.

**Why it happens:**
The search result dict uses `_relevance_score` as the unified score field. Cross-encoder output replaces RRF scores in this field without rescaling. The `--min-score` validation and FILT-03 logic were designed around the RRF range and have no awareness of score source.

**How to avoid:**
When `--rerank` is active, apply sigmoid to raw cross-encoder logits: `1 / (1 + exp(-logit))` to map to `[0, 1]`. Then annotate the result with `score_type: "cross_encoder"` (or `"rrf"`). Update the `--min-score` documentation to note that when `--rerank` is active, the score range shifts to `[0, 1]`. The FILT-03 hint text should reference the score type when firing. Do not mix scores from the two systems in a single sorted result list.

**Warning signs:**
- `--rerank --min-score 0.02` returns zero results
- `corpus search --rerank` without `--min-score` returns results in wrong order compared to RRF
- MCP `corpus_search` with `sort_by=score` and `rerank=true` returns items in descending score order but the scores look like integers (0, 1, or near-0)

**Phase to address:** Cross-encoder re-ranking phase (RANK-03). Score type annotation and the sigmoid transformation must be implemented before the `--min-score` compatibility test.

---

### Pitfall 5: Cross-Encoder Model Loads on Every Search Call — 5–30s Cold Start

**What goes wrong:**
`CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")` triggers a model download (first run) and a model load from disk (every subsequent cold start). Model load takes 2–5 seconds for a small model, 20–30 seconds for larger ones. If the model is loaded inside the `hybrid_search()` call (or in the CLI command function), every `corpus search --rerank` query has a 2–5s overhead before returning results. For the MCP server, if the model is re-loaded per request, MCP tool calls will time out.

**Why it happens:**
The pattern `model = CrossEncoder(name)` is placed inside the search function because "that's where it's used." Process-level caching (module-level singleton) is not considered during initial implementation.

**How to avoid:**
Instantiate the cross-encoder once at module level using a lazy singleton pattern:
```python
_reranker: CrossEncoder | None = None

def _get_reranker(model_name: str) -> CrossEncoder:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(model_name)
    return _reranker
```
For the MCP server (long-lived process), initialise the reranker during `startup()` if `--rerank` is configured. Log the load time prominently so users understand the one-time cost. Add a `--rerank-model` config option to `corpus.toml` so users choose a model size appropriate to their hardware.

**Warning signs:**
- `time corpus search --rerank "auth"` shows a 3–5s delay before first result
- MCP `corpus_search` with `rerank=true` times out the first call (FastMCP default timeout is 30s)
- Unit test that mocks `CrossEncoder` passes but integration test hits real model loading

**Phase to address:** Cross-encoder re-ranking phase (RANK-03). The singleton pattern must be implemented before any integration or MCP test. Test that the second call to `--rerank` is faster than the first.

---

### Pitfall 6: Cross-Encoder Is a Heavy Optional Dependency — ImportError Must Not Crash Search

**What goes wrong:**
`sentence-transformers` (which provides `CrossEncoder`) depends on `torch` (PyTorch), which is approximately 2–3 GB installed. Adding it as a required dependency triples the install size of the tool and breaks install on systems without compatible PyTorch wheels. If `sentence-transformers` is imported at module top-level in `engine.py` or `cli.py`, every `corpus search` call (even without `--rerank`) fails with `ImportError` on systems where it is not installed.

**Why it happens:**
The developer adds `from sentence_transformers import CrossEncoder` at the top of `engine.py` because "that's where the search logic lives." The import is not guarded. `uv sync` on a fresh clone installs `sentence-transformers` because it was added to `pyproject.toml` without marking it as optional.

**How to avoid:**
Declare `sentence-transformers` as an optional dependency in `pyproject.toml` under an `[extras]` group:
```toml
[project.optional-dependencies]
rerank = ["sentence-transformers>=2.6.0"]
```
Guard the import at the call site (not module top-level), matching the existing pattern for `tree-sitter` in `chunker.py`:
```python
def _get_reranker(model_name: str) -> Any:
    try:
        from sentence_transformers import CrossEncoder  # noqa: PLC0415
    except ImportError as exc:
        raise RuntimeError(
            "Cross-encoder re-ranking requires 'sentence-transformers'. "
            "Install with: uv add corpus-analyzer[rerank]"
        ) from exc
    return CrossEncoder(model_name)
```
The `--rerank` flag must raise this error at CLI dispatch time (before running the search), not buried inside the search result loop.

**Warning signs:**
- `uv sync` on a new machine increases install time by 5 minutes (torch download)
- `corpus search "auth"` (no `--rerank`) fails with `ImportError` after adding `sentence-transformers` to module-level imports
- `mypy src/` fails because `sentence_transformers` stub is absent — need `# type: ignore[import-untyped]`

**Phase to address:** Cross-encoder re-ranking phase (RANK-03). The optional dependency architecture must be decided and tested before writing any cross-encoder logic.

---

### Pitfall 7: Centrality Explosion on Star-Topology Graphs Inflates Scores Unboundedly

**What goes wrong:**
One file references 50 other skills (a hub README or index page). Its indegree becomes 50 while all other files have indegree 1–3. Applying a raw indegree multiplier (e.g., `score *= (1 + indegree * 0.1)`) multiplies the hub's score by 6x while all others are multiplied by 1.1–1.3x. Every search that touches any topic covered by the hub returns the hub first — regardless of actual relevance. The hub dominates all results.

This is the "Wikipedia main page" problem: high centrality does not imply high relevance to a specific query.

**Why it happens:**
Indegree centrality is a raw count. Without normalisation, a well-connected hub artificially dominates searches. The developer tests centrality on a 10-file corpus where the max indegree is 3 — the multiplier is at most 1.3x, which seems harmless. On a real 500-file corpus with a hub README, the multiplier is 6x.

**How to avoid:**
Use logarithmic dampening: `score_multiplier = 1 + log(1 + indegree) * 0.1`. This gives diminishing returns at high indegree (indegree=50 → 1.39x vs raw 6x). Cap the multiplier at 2.0 regardless. Validate on the actual user corpus by printing the top-10 files by centrality and confirming they are genuinely "central" documents (architecture overviews, not index pages). Consider storing `normalized_centrality = indegree / max_indegree_in_graph` and using that instead of raw counts.

**Warning signs:**
- The same file appears in the top-3 results for every search query regardless of topic
- `corpus status` shows one file with significantly higher indegree than all others
- `--sort-by score` with centrality boost produces a ranking that differs from `--sort-by relevance` by more than 2 positions on average

**Phase to address:** Centrality scoring phase (GCENT-01). Test on the real user corpus before shipping. The cap and logarithmic formula must be in the first implementation.

---

### Pitfall 8: Centrality Is Computed at Index Time But the Graph Changes Per-File Reindex

**What goes wrong:**
Centrality is computed once during `corpus index` and stored in LanceDB (or in `graph.sqlite`). When one file's edges change (it links to 3 new skills), the centrality of those 3 target files increases — but only the re-indexed file's edges are updated. The other 3 files still have their old centrality scores until a full reindex. Searches immediately after a partial reindex return stale centrality boosts: a file that just became highly referenced does not receive its boost, and a file whose references were removed still receives a boost it no longer deserves.

**Why it happens:**
The existing `index_source()` only re-computes edges for files that changed (hash-based change detection). Centrality is a graph-global property — it cannot be computed correctly from local edge changes alone.

**How to avoid:**
Compute centrality from the full `graph.sqlite` at the end of every `index_source()` run, after all edge writes are complete — not per-file. This is a single `SELECT target_path, COUNT(*) as indegree FROM relationships WHERE resolved=1 GROUP BY target_path` query, which is cheap (single full-table scan). Store the result in a `centrality` table in `graph.sqlite` rather than in LanceDB (avoid the LanceDB `update()` per-row cost). At search time, join centrality scores by `file_path` lookup after LanceDB returns results.

**Warning signs:**
- `corpus search "auth"` returns different centrality-boosted results on the first run vs the second run after indexing the same files
- Deleting all edges from a hub file and re-indexing it does not reduce its centrality score until `--force` reindex
- Integration test with a two-file corpus produces correct centrality but the test with a five-file update produces stale centrality

**Phase to address:** Centrality scoring phase (GCENT-01). The "compute after all edges are written" pattern must be in the spec, not discovered during debugging.

---

### Pitfall 9: Multi-Query AND Returns Empty Results on Every Real Query

**What goes wrong:**
`--query auth --query saml` is implemented as: run each query independently, collect result sets, return the intersection. Each query returns chunks where at least one query term appears in the text (the existing text-term filter in `hybrid_search()`). Chunk A matches "auth" and chunk B matches "saml" but chunk C matches both. If the two result sets (each limited to `limit=10`) do not share chunk C — because it ranked 12th in the "auth" query and 15th in the "saml" query — the intersection is empty even though chunk C exists and is relevant.

The failure is worse with the text-term filter currently in `engine.py` (lines 101–109): a chunk must contain one of the query terms in its text. Two separate queries against the same vector+BM25 index with different terms will almost never produce identical top-10 result sets.

**Why it happens:**
Hard intersection of limited result sets is the obvious implementation. It works on high-overlap corpora or when limit is large, but fails on sparse corpora or small limits. The developer tests with two queries that happen to share a top result during development, then ships.

**How to avoid:**
Use soft intersection via score combination: for multi-query AND, run each query with `limit * 3` overfetch, merge results by `chunk_id` (summing scores), keep only chunks that appear in ALL query result sets, then re-rank by combined score. This is different from OR (which would keep any chunk from any query). Expose `--query-mode and|or` with `and` as default for `--query --query`. Document that AND returns fewer results than OR. Add an explicit "no AND results — try OR mode" hint analogous to FILT-03.

**Warning signs:**
- `corpus search --query auth --query saml` returns zero results even when both topics exist in the corpus
- Increasing `--limit` from 10 to 20 suddenly produces results (confirms the intersection-emptiness is a pool-size problem)
- Single-query results for each term separately return relevant chunks, but AND returns nothing

**Phase to address:** Multi-query phase (MULTI-01). Overfetch + score-sum intersection must be the first design decision, not a fallback fix.

---

### Pitfall 10: Score Normalisation Breaks Existing `--min-score` Filter and MCP Callers

**What goes wrong:**
v2 adds per-query min-max normalisation inside `hybrid_search()` (NORM-01), mapping RRF scores to `[0, 1]`. This changes the `_relevance_score` field from `0.009–0.033` to `0–1`. All existing callers using `--min-score 0.02` (a meaningful RRF threshold) now pass every result (0.02 < all normalised scores). All MCP callers that check `result["_relevance_score"] > 0.01` now have that logic silently become a no-op. The FILT-03 hint text says "typical RRF range 0.009–0.033" — now misleading.

This is not hypothetical: v1.4 explicitly documented the RRF range in CLI help text and in MCP tool documentation.

**Why it happens:**
Normalisation changes the semantic meaning of `_relevance_score` without a corresponding update to all downstream consumers. The change is "internal to the search engine" but it has an externally observable contract.

**How to avoid:**
When adding normalisation, simultaneously update:
1. `--min-score` help text from `"0.009–0.033 range"` to `"0.0–1.0 range when normalisation is active"`
2. FILT-03 hint message
3. MCP `corpus_search` docstring and response schema documentation
4. All existing tests that assert specific `_relevance_score` values (these will break and must be updated to assert `0 <= score <= 1`)
5. The `--min-score` default remains `0.0` (safe no-op) regardless of score regime

Treat the normalisation change as a breaking API change within the test suite: expect 10+ test failures on first run, fix them all before merging.

**Warning signs:**
- `uv run pytest` fails with assertion errors on `_relevance_score` values after adding normalisation
- `--min-score 0.02` returns all results instead of filtering low-confidence matches
- Existing integration test using `assert result["_relevance_score"] < 0.05` passes vacuously (0.0 < 0.05 is always true post-normalisation)

**Phase to address:** v2 normalisation phase (NORM-01). Must come with a test update pass as part of the same phase, not as a separate cleanup.

---

### Pitfall 11: Normalisation Applied After MMR Invalidates MMR's Similarity Comparisons

**What goes wrong:**
If score normalisation (min-max scaling of `_relevance_score`) is applied before MMR, the MMR relevance term `lambda * score` operates on the correctly-ranged `[0, 1]` values. But if normalisation is applied after MMR (i.e., MMR uses raw RRF scores in `0.009–0.033` and normalisation happens in the display layer), then MMR's `lambda` parameter has a different effective weight: at `lambda=0.7`, the relevance contribution is `0.7 * 0.02` (tiny) while the diversity penalty is `(1 - 0.7) * cosine_sim` which ranges `0–0.3`. Diversity always dominates relevance because the RRF scores are too small to compete with cosine similarity values.

**Why it happens:**
MMR and normalisation are implemented in separate phases (RANK-01 and NORM-01). The developer implementing MMR uses RRF scores "as-is" because normalisation hasn't landed yet. When normalisation lands in a later phase, nobody audits the MMR lambda balance.

**How to avoid:**
The correct order is: (1) run hybrid search, (2) normalise RRF scores to `[0, 1]`, (3) apply MMR using normalised scores. Codify this order in a comment at the top of the search pipeline function. Add a test that asserts the top MMR result has `_relevance_score > 0.5` (i.e., normalised — a score of 0.02 would indicate un-normalised scores reaching MMR).

**Warning signs:**
- Changing `--diversity` from 0.3 to 0.9 produces no change in result ordering (diversity always wins because RRF scores are too small)
- MMR with `--diversity 1.0` (pure relevance, no diversity penalty) still returns different results than the non-MMR baseline (unexpected — pure relevance MMR should match baseline order exactly)

**Phase to address:** MMR implementation phase (RANK-01). Even if NORM-01 comes later in v2, the MMR implementation must normalize scores internally before computing MMR weights.

---

### Pitfall 12: `--expand-graph` N+1 Queries Against `graph.sqlite` Per Result

**What goes wrong:**
`--expand-graph` fetches graph neighbors for each search result. The naive implementation calls `graph_store.edges_from(result["file_path"])` and `graph_store.edges_to(result["file_path"])` inside a loop over the top-N results. At `limit=10`, this is 20 SQLite queries per search call (10 results × 2 directions). Each query opens a connection, executes, and closes. On an NVMe drive with a warm OS cache, each query takes ~0.5–1ms. Total overhead: 10–20ms — probably acceptable. But if the user runs `corpus search --expand-graph --limit 50`, the overhead is 100 SQLite queries = 50–100ms, making search feel sluggish.

For the MCP server (long-lived process), repeated `corpus_graph` calls accumulate connection overhead because `GraphStore._connect()` creates a new connection per query (contextmanager pattern in the current implementation).

**Why it happens:**
The `GraphStore.edges_from()` / `edges_to()` methods are designed for single-path lookup. Batch lookup across multiple paths was not needed for the existing `corpus graph` CLI command.

**How to avoid:**
Add a `batch_edges_from(paths: list[str]) -> dict[str, list[dict]]` method to `GraphStore` that uses a single `WHERE source_path IN (?, ?, ...)` query. Use this in the `--expand-graph` path instead of the per-result loop. The `IN` clause query with 10 paths is one round-trip to SQLite vs 10. For the MCP server, consider holding a persistent SQLite connection rather than using the contextmanager pattern per query.

**Warning signs:**
- `corpus search --expand-graph` is noticeably slower than the same search without `--expand-graph`
- Profiling shows repeated `sqlite3.connect()` calls in the search hot path
- MCP tool `corpus_search` with `expand_graph=True` takes 200ms when the same query without expansion takes 30ms

**Phase to address:** Graph expansion phase (GEXP-01). The batch query method must be designed before implementing the `--expand-graph` flag — do not add it as a "performance fix" after the fact.

---

### Pitfall 13: Recursive Graph Walk Hangs on Cyclic Graphs

**What goes wrong:**
`corpus graph --depth 2` performs a recursive BFS/DFS over `graph.sqlite`. Skill A references skill B, which references skill A (mutual dependency). The recursive walk visits A → B → A → B → ... and either hangs forever or blows the recursion stack. The current `edges_from()` / `edges_to()` methods do not detect cycles.

Cycles are realistic: two skills that build on each other will likely reference each other in their `## Related Skills` sections. The graph was designed as a directed graph but does not prevent cycles at write time.

**Why it happens:**
Graph walks without cycle detection are a textbook error. The existing `corpus graph <slug>` command only fetches one-hop neighbors (no recursion), so cycles are not a problem today. Adding `--depth N` makes the problem manifest.

**How to avoid:**
Maintain a `visited: set[str]` of paths already added to the result. Before enqueueing a neighbor, check `if neighbor not in visited`. This is BFS cycle detection — O(V + E) time, O(V) memory:
```python
def walk_graph(start: str, depth: int, store: GraphStore) -> dict[str, list[str]]:
    visited: set[str] = {start}
    queue: list[tuple[str, int]] = [(start, 0)]
    result: dict[str, list[str]] = {}
    while queue:
        node, current_depth = queue.pop(0)
        if current_depth >= depth:
            continue
        neighbors = [e["target_path"] for e in store.edges_from(node)]
        result[node] = neighbors
        for n in neighbors:
            if n not in visited:
                visited.add(n)
                queue.append((n, current_depth + 1))
    return result
```
Add a test with a two-node cycle (A → B → A) and assert the walk terminates and returns both nodes exactly once.

**Warning signs:**
- `corpus graph --depth 2 <slug>` hangs (never returns) on a corpus with any mutual references
- `corpus graph` with a well-connected hub node returns the same node multiple times in results
- Integration test for `--depth 2` times out but `--depth 1` completes immediately

**Phase to address:** Graph walk phase (GWALK-01). The visited-set must be in the first recursive walk implementation — not added "later when cycles are detected."

---

### Pitfall 14: `--exclude-path` Using `pathlib.Path.match()` Silently Fails for Directory Globs

**What goes wrong:**
The user passes `--exclude-path "tests/**"` expecting to exclude all paths under any `tests/` directory. `pathlib.PurePath.match()` does not support `**` — it treats `**` as a literal non-recursive wildcard (equivalent to `*`). The pattern `"tests/**"` does not match `"/home/user/.local/share/corpus/skills/tests/unit/test_auth.py"` because `**` in `match()` only matches one path component, not multiple. Files under nested `tests/` directories silently pass the exclude filter.

Additionally, `PurePath.match()` with a relative pattern matches from the right: `"tests/unit"` will match any path ending in `tests/unit`, which may be correct, but `"**/tests/**"` will not work as expected because `**` is non-recursive in `match()`.

**Why it happens:**
Python documentation for `PurePath.match()` is easy to confuse with `Path.glob()`. The `**` "recursive wildcard" works in `glob()` and in `fnmatch`-style matching but explicitly does not work in `match()`. The change in Python 3.12 (accepting path-like objects) does not change this limitation. Most examples online use `glob()` patterns which do support `**`.

**How to avoid:**
Use `PurePath.full_match()` (added in Python 3.13) if the runtime supports it, or use `fnmatch.fnmatch(str(path), pattern)` which supports `*` but not `**`, or re-implement `--exclude-path` as a `fnmatch`-based check that explicitly splits on `/` and matches each component. The simplest correct approach for Python 3.12:
```python
import fnmatch

def matches_exclude_pattern(file_path: str, pattern: str) -> bool:
    # Match against full path or just the filename
    return fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(
        Path(file_path).name, pattern
    )
```
Document that `--exclude-path` supports `*` (single component) but not `**` (recursive), or support only simple patterns like `"*.test.ts"` or `"tests/"` (directory name prefix).

**Warning signs:**
- `--exclude-path "tests/**"` does not exclude files under `tests/unit/` or `tests/integration/`
- `--exclude-path "**/*.test.ts"` matches no files even when `*.test.ts` files are present
- Unit test for `--exclude-path` passes with a simple `"*.md"` pattern but the integration test with `"docs/**"` produces unexpected results

**Phase to address:** `--exclude-path` implementation phase (MULTI-02). Decide on the supported pattern syntax and document it in CLI help text before writing any matching logic.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcode `lambda=0.5` in MMR implementation | No need to expose config | Wrong diversity for most real corpora; impossible to tune without code change | Never — expose as `--diversity` flag from the start |
| Compute centrality per-file during indexing | Simpler to implement alongside edge writes | Stale centrality after partial reindex; wrong boost signals | Never — compute after all edges are written |
| Load `CrossEncoder` model per search call | Simplest code structure | 2–5s latency per `--rerank` query; MCP timeout on first call | Never — lazy singleton at process level |
| Add `sentence-transformers` to required dependencies | No ImportError to handle | 2–3 GB install size; breaks install on systems without compatible torch wheels | Never — optional dependency with `[extras]` |
| Hard intersection for multi-query AND | Easiest to reason about | Returns zero results on sparse corpora; users abandon the feature | Never — use overfetch + score-sum intersection |
| Apply normalisation to `_relevance_score` without updating `--min-score` docs | Quick normalisation implementation | Silent breakage of existing min-score filters; FILT-03 hint fires on wrong threshold | Never — normalisation is a breaking change to the score API |
| Use `PurePath.match()` for `**` glob patterns | Single built-in function | `**` is not recursive in `match()`; exclude patterns silently fail | Never — use `fnmatch` with documented limitations |
| Raw indegree as centrality multiplier (no cap) | Simplest centrality boost | Hub nodes dominate all results; star topology corrupts ranking | Never — logarithmic dampening + cap from day one |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| LanceDB `RRFReranker` + custom MMR | Fetching embedding vectors from LanceDB result rows for MMR similarity computation — vectors are not returned by default in search results | Fetch embeddings via `embed_batch([query])` for the query; for candidate–candidate similarity in MMR, embed the candidate texts (from `text` field) at search time, or store pre-computed similarities |
| LanceDB hybrid search + `--expand-graph` | Fetching `file_path` from LanceDB results and using it directly in `GraphStore` queries — LanceDB stores absolute paths but `graph.sqlite` may have different path representations if indexed on a different machine | Normalise paths with `Path(p).resolve()` before any GraphStore lookup; verify path format matches between the two stores |
| SQLite `graph.sqlite` + centrality computation | Running `SELECT COUNT(*) GROUP BY target_path` at query time for every search | Pre-compute centrality at index time, store in `centrality` table; join at query time with a single lookup |
| `sentence-transformers CrossEncoder` + `mypy --strict` | `CrossEncoder` is untyped — `# type: ignore[import-untyped]` required; `predict()` return type is `float \| list[float]` depending on input shape | Guard with `isinstance(scores, list)` after `predict()`; add `py.typed` marker check in `pyproject.toml` for sentence-transformers |
| FastMCP `corpus_search` + MMR | MCP tool runs in an async context; `embed_batch()` is synchronous and blocks the event loop during MMR candidate embedding | Run `embed_batch()` in a thread executor if MMR is applied inside the MCP handler: `await asyncio.get_event_loop().run_in_executor(None, embed_batch, texts)` |
| `--rerank` + `--min-score` | `--min-score 0.02` silently passes all results when cross-encoder scores are in `[0, 1]` range (0.02 is a very low threshold for normalised scores) | Document separate thresholds for RRF mode (0.009–0.033) and rerank mode (0.5 = neutral, >0.7 = confident); consider a separate `--rerank-min-score` flag |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| MMR Python inner loop without numpy | `corpus search --limit 20` takes 200ms vs 30ms for basic search | Use numpy vectorized dot product for cosine similarity matrix when `limit > 10` | Noticeable at `limit=20`; severe at `limit=50` |
| N+1 `graph.sqlite` queries in `--expand-graph` | `--expand-graph` adds 50–100ms to search latency | Batch `edges_from` / `edges_to` across all result paths in one SQL `IN` clause | Noticeable at `limit=10`; severe at `limit=50` |
| Centrality join per result in search hot path | Each search result triggers a `SELECT` against `centrality` table | Pre-load centrality dict into memory at `CorpusSearch.__init__` time (it's a small table) | Any search with centrality boost enabled — load at startup, not per-query |
| Re-computing SlugRegistry at search time for graph expansion | SlugRegistry scans entire source tree; each `--expand-graph` query rebuilds it | Build registry once at `CorpusIndex.open()` time and cache it on the `CorpusIndex` instance | On corpora with 1000+ files, SlugRegistry build takes 500ms+ |
| Cross-encoder batching: one `predict()` call per pair | `CrossEncoder.predict([(q, text)])` × 20 results = 20 forward passes | Pass all (query, text) pairs as a batch: `CrossEncoder.predict([(q, t1), (q, t2), ..., (q, t20)])` — one forward pass | Any `--rerank` query on a corpus with > 5 candidates |

---

## "Looks Done But Isn't" Checklist

- [ ] **MMR normalisation:** Vectors are L2-normalized inside the MMR function before cosine similarity — assert that two identical chunks receive similarity = 1.0
- [ ] **MMR lambda balance:** `--diversity 1.0` returns results in the same order as the non-MMR baseline (pure relevance); `--diversity 0.0` returns results where consecutive results have cosine similarity < 0.5
- [ ] **MMR pool cap:** `corpus search --limit 50 --diversity 0.5` completes in under 500ms on a corpus with 1000 chunks
- [ ] **Cross-encoder singleton:** Two consecutive `corpus search --rerank` calls; the second is at least 4x faster than the first (model already loaded)
- [ ] **Cross-encoder optional:** `corpus search "auth"` (no `--rerank`) works normally when `sentence-transformers` is not installed; `corpus search --rerank "auth"` raises a clear error with install instructions
- [ ] **Score type annotation:** MCP `corpus_search` response includes `score_type: "rrf" | "cross_encoder"` so callers can apply appropriate thresholds
- [ ] **Centrality staleness:** After running `corpus index` on one changed file, centrality scores reflect the updated edge counts (not just the changed file's edges, but the full graph recompute)
- [ ] **Centrality cap:** No single file receives a centrality multiplier greater than 2.0 regardless of indegree
- [ ] **Multi-query AND non-empty:** `corpus search --query auth --query saml` returns results (via overfetch + score-sum) when both topics exist in the corpus — does not return empty set
- [ ] **`--expand-graph` cycles:** `corpus search --expand-graph` on a corpus with mutual references (A → B → A) terminates and does not return duplicate results
- [ ] **`--exclude-path` semantics documented:** CLI help text explicitly states whether `**` is supported; integration test confirms `--exclude-path "tests/"` excludes `tests/unit/test_auth.py`
- [ ] **Normalisation + existing tests:** After adding NORM-01, `uv run pytest` fails on score-range assertions — all failures are fixed before merging
- [ ] **`--min-score` help text updated:** Help text reflects `0–1` range when normalisation is active, not the old RRF range

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| MMR on unnormalized vectors (wrong diversity) | LOW | Add L2 normalization inside MMR function; re-run search (no re-index needed) |
| Cross-encoder scores break `--min-score` filter | LOW | Add sigmoid transformation + score type annotation; update CLI help and FILT-03 hint |
| Cross-encoder loads per query (latency) | LOW | Refactor to process-level singleton; no schema change |
| `sentence-transformers` in required deps (3GB install) | MEDIUM | Move to optional extras; remove from required deps; update install docs |
| Hard AND intersection returns empty results | MEDIUM | Refactor multi-query to overfetch + score-sum; add no-AND-results hint; existing single-query behavior unchanged |
| Centrality explosion on hub nodes (corrupted ranking) | MEDIUM | Add log dampening + 2.0 cap; recompute centrality table; no re-index needed |
| Stale centrality after partial reindex | MEDIUM | Move centrality recompute to post-all-edges-written step; recompute centrality table once |
| Cyclic graph walk hangs | HIGH | Add visited set to recursive walk; must fix before shipping `--depth N`; no data migration needed |
| `--exclude-path **` silently no-ops | LOW | Switch to `fnmatch` + document limitations; no schema change |
| Normalisation breaks existing `--min-score` filters | MEDIUM | Update help text + FILT-03 + all score-range tests in one pass; cannot defer |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| MMR on unnormalized embeddings | RANK-01 (MMR diversity) | Unit test: two identical chunk texts receive cosine similarity = 1.0 inside MMR |
| MMR lambda imbalance with un-normalised scores | RANK-01 (MMR diversity) — normalise before MMR | Test: `--diversity 1.0` produces same order as non-MMR baseline |
| MMR quadratic complexity | RANK-01 (MMR diversity) | Benchmark: `--limit 50` completes under 500ms |
| Centrality explosion on star topology | GCENT-01 (centrality scoring) | Test: indegree=50 file receives multiplier <= 2.0 |
| Centrality staleness after partial reindex | GCENT-01 (centrality scoring) | Test: index one changed file; verify all centrality scores are recomputed |
| Cross-encoder score incompatibility | RANK-03 (cross-encoder re-ranking) | Test: `--rerank --min-score 0.02` still filters results; FILT-03 hint references correct range |
| Cross-encoder cold-start latency | RANK-03 (cross-encoder re-ranking) | Benchmark: second `--rerank` call is >= 4x faster than first |
| Cross-encoder as heavy required dependency | RANK-03 (cross-encoder re-ranking) | Test: `corpus search` without `sentence-transformers` installed raises clear ImportError only with `--rerank` |
| Multi-query AND empty intersection | MULTI-01 (multi-query AND) | Test: `--query auth --query saml` returns non-empty when both topics exist; overfetch confirmed |
| Score normalisation breaks `--min-score` | NORM-01 (score normalisation, v2) | Test: all pre-NORM-01 score-range assertions updated; `--min-score 0.02` retains filtering effect |
| `--expand-graph` N+1 SQLite queries | GEXP-01 (graph expansion) | Benchmark: `--expand-graph --limit 10` adds less than 10ms vs non-expand baseline |
| Cyclic graph walk hang | GWALK-01 (recursive graph walk) | Test: two-node cycle terminates; each node appears exactly once in output |
| `--exclude-path **` non-recursive | MULTI-02 (exclude-path flag) | Test: `--exclude-path "tests/**"` excludes `tests/unit/test_auth.py`; document supported syntax |

---

## Sources

- LanceDB hybrid search docs and RRF score documentation: https://docs.lancedb.com/search/hybrid-search
- MMR algorithm and lambda guidance (Aayush Agrawal, 2025): https://aayushmnit.com/posts/2025-12-25-DiversityMMRPart1/DiversityMMRPart1.html
- MMR Elasticsearch implementation note on performance and normalization: https://www.elastic.co/search-labs/blog/maximum-marginal-relevance-diversify-results
- Cross-encoder practical guide (Michael Ryaboy): https://medium.com/@aimichael/cross-encoders-colbert-and-llm-based-re-rankers-a-practical-guide-a23570d88548
- Cross-encoder latency data (Ailog, 2025): https://app.ailog.fr/en/blog/guides/reranking
- sentence-transformers CrossEncoder reference: https://sbert.net/docs/package_reference/cross_encoder/cross_encoder.html
- Python optional dependency lazy loading (PEP 810 discussion): https://discuss.python.org/t/optional-imports-for-optional-dependencies/104760
- Python `pathlib.PurePath.match()` official docs — `**` not recursive: https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.match
- CPython issue on `pathlib.PurePath.match` vs `glob.glob` inconsistency: https://github.com/python/cpython/issues/118701
- L2 normalization requirement for cosine similarity in embedding models: https://zilliz.com/ai-faq/what-is-the-proper-way-to-normalize-embeddings
- OpenSearch score normalization pitfalls (min-max sensitivity to outliers): https://opensearch.org/blog/introducing-reciprocal-rank-fusion-hybrid-search/
- SQLite recursive CTE for graph traversal with cycle detection: https://www.fusionbox.com/blog/detail/graph-algorithms-in-a-database-recursive-ctes-and-topological-sort-with-postgres/620/
- Direct code inspection: `src/corpus_analyzer/search/engine.py`, `src/corpus_analyzer/graph/store.py`, `src/corpus_analyzer/ingest/indexer.py`, `src/corpus_analyzer/ingest/embedder.py`, `src/corpus_analyzer/store/schema.py`

---
*Pitfalls research for: v3.0 Intelligent Search — Adding MMR diversity, cross-encoder re-ranking, graph centrality, multi-query AND, graph expansion, score normalisation, and exclude-path to an existing LanceDB hybrid search system*
*Researched: 2026-02-24*

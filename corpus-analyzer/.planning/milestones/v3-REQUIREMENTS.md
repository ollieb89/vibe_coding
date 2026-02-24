# Requirements: v3.0 Intelligent Search

**Defined:** 2026-02-24
**Status:** ROADMAP CREATED
**Milestone:** v3.0 Intelligent Search
**Depends on:** v2 complete (Phases 17–25; specifically Phase 17 for RANK-02, Phase 23 for RERANK score normalisation)

---

## Milestone Goal

Stop flooding results with variations of the same file. Surface the architectural spread — diverse, graph-enriched search results via a SearchCoordinator pipeline, multi-query AND composition, cross-encoder re-ranking, recursive graph traversal, centrality-boosted scoring, and intelligent score gap detection.

---

## Cluster A — Foundation: Coordinator Scaffold and Display (HIGHEST PRIORITY)

These land first — zero new infrastructure; validates the coordinator before ranking logic is added.

- [ ] **COORD-01**: A `SearchCoordinator` class is introduced as the single pipeline composition point for all three query surfaces (CLI `corpus search`, MCP `corpus_search`, Python `search()` API); all three surfaces call `coordinator.search()` instead of `engine.hybrid_search()` directly; coordinator runs post-retrieval steps in sequence: exclude → cap → boost → re-rank → graph-expand → merge → label; existing `hybrid_search()` API contract is not broken (coordinator calls it internally)

- [ ] **XSRC-01**: `corpus search` CLI output includes a `[source_name]` prefix on each result line (e.g., `[superpowers] path/to/file.md:42-67 [skill] score:0.021`); source name comes from the `source_name` field already stored in LanceDB — zero new infrastructure

- [ ] **XSRC-02**: MCP `corpus_search` response includes a `source` field per result object alongside existing `path`, `score`, `construct`, etc. fields

- [ ] **FILTER-01**: `corpus search --exclude-path <glob>` excludes results whose file path matches the glob pattern; `fnmatch.fnmatch()` semantics (NOT `pathlib.PurePath.match()` — `**` is non-recursive there); multiple `--exclude-path` flags are OR'd together

- [ ] **FILTER-02**: A `.corpus-ignore` file at the corpus root (same level as `corpus.toml`) provides persistent exclude-path patterns — one glob per line; patterns are merged with any `--exclude-path` CLI flags so users don't repeat common exclusions on every search

---

## Cluster B — Result Quality: Cap, Merge, and Gap Detection (SECOND PRIORITY)

Direct response to the top UX complaint: "too many results to scan."

- [ ] **RANK-01**: `corpus search --max-per-file N` (default `3`) caps the number of chunks returned from any single file in the result set; the top-N scoring chunks from that file are kept, the rest are silently filtered; this is a post-retrieval post-filter applied before display

- [ ] **RANK-02**: Adjacent sub-chunks from the same class that appear consecutively in a result set are collapsed into a single display entry showing the merged line range and combined chunk text; requires v2 `chunk_name`, `start_line`, and `end_line` fields (Phase 17); collapser skips gracefully if these fields are absent (empty string / 0 defaults)

- [ ] **RANK-03**: Score gap detection: if the score drop between consecutive results exceeds a significant threshold (≥40% of the top result's score), a visual separator is inserted in CLI output and a `gap_above: true` field is set in the MCP result; this signals "results below this line are materially less relevant" without truncating them

---

## Cluster C — Multi-Query Composition (THIRD PRIORITY)

Bridges "searching for a string" and "investigating an interaction."

- [ ] **MULTI-01**: `corpus search` accepts multiple `--query` flags (e.g., `--query auth --query saml`); results are computed via file-level AND intersection using overfetch+score-sum: N separate `hybrid_search()` calls with `limit * num_queries * 2` overfetch each; files present in all N result sets are returned with summed scores; files missing from any result set are excluded; if intersection is empty a "No results matching all queries" hint is shown (analogous to FILT-03)

- [ ] **BOOST-01**: `corpus search --boost <term>` applies a score nudge to results that mention `<term>` in chunk text or chunk name; does not exclude non-matching results; multiple `--boost` flags are additive; boosts are applied after RANK-01 cap and before RANK-03 gap detection; boost strength is fixed at +15% per matching term (not tunable in v3)

---

## Cluster D — Graph Features (THIRD PRIORITY, parallel to C)

- [ ] **GEXP-01**: `corpus search --expand-graph` annotates each result with its immediate graph neighbors from `graph.sqlite`; neighbors are categorized as `[Depends On]` (downstream edges) or `[Imported By]` (upstream edges) in CLI output; each neighbor shows its slug and construct type; MCP `corpus_search` with `expand_graph: true` includes an `neighbors` array per result with `{path, relation, construct}` objects; lookup uses batched SQL (`IN` clause) to avoid N+1 queries

- [ ] **GWALK-01**: `corpus graph <slug> --depth N` performs BFS N-hop graph traversal (default `N=2`); requires a `visited: set[str]` to prevent infinite loops on mutual-reference cycles (A→B→A); output shows all reachable nodes within N hops grouped by distance

- [ ] **GWALK-02**: `corpus graph` output labels hub nodes with their indegree count (e.g., `config.py [indegree: 42]`) so users can identify high-centrality dependencies at a glance

- [ ] **GCENT-01**: A `graph/centrality.py` module computes indegree centrality for all indexed files from the full `relationships` table in `graph.sqlite`; centrality is stored in a new `centrality` table `{file_path TEXT PRIMARY KEY, indegree INTEGER, computed_at REAL}`; `compute_indegree()` is called at the end of every `index_source()` run (full recompute from scratch — not per-file — because centrality is a global graph property); `networkx>=3.6.1` added as a core dependency

- [ ] **GCENT-02**: `SearchCoordinator` applies a log-dampened centrality score boost: `score *= (1.0 + math.log(1 + indegree) * 0.1)` with a hard `2.0×` cap; centrality values are pre-loaded into a dict at coordinator startup (not per-result SQLite SELECT); files with no centrality record receive a boost of 1.0 (neutral)

---

## Optional Cluster E — Cross-Encoder Reranker (DEFERRED, OPTIONAL)

Fully isolated from other v3 features; ships last.

- [ ] **RERANK-01**: `corpus search --rerank` enables two-stage retrieval: top-20 candidates from the coordinator pipeline are re-ranked by a `CrossEncoder` using `cross-encoder/ms-marco-MiniLM-L6-v2` (~91 MB, downloaded on first use); re-ranker scores are sigmoid-normalized before returning; a `score_type` annotation (`"rrf"` or `"cross_encoder"`) is added to all results so downstream consumers know which scoring regime was used

- [ ] **RERANK-02**: `sentence-transformers>=5.2.3` is added as an optional extra (`[rerank]`) in `pyproject.toml` and installed via `uv sync --extra rerank`; the `CrossEncoder` class is lazy-imported only inside the `--rerank` branch (same pattern as the existing `tree-sitter` optional dep in `chunker.py`); a missing `sentence-transformers` produces a clear error message pointing to `uv sync --extra rerank`

---

## Dependency Requirements

- [ ] **DEP-01**: `networkx>=3.6.1` added as a core dependency in `pyproject.toml` (required for GCENT-01/02); 2.1 MB pure Python wheel, zero required transitive deps; add `ignore_missing_imports = true` mypy override for `networkx`

---

## Quality Requirements

- [ ] **V3QUAL-01**: `uv run ruff check .` exits 0 and `uv run mypy src/` exits 0 after all v3 changes
- [ ] **V3QUAL-02**: All existing tests pass alongside new v3 tests; test count increases by at least 40 new test methods covering coordinator pipeline, per-file cap, multi-query intersection, gap detector, graph expansion, centrality scoring, and reranker (optional)

---

## Future Requirements (v3.x)

- **GSCOPE-01**: `--within-graph <slug>` soft scope (+20% boost for results in same graph component) — deferred; users can use `--source` + `--path` filters as an approximation
- **AUTO-THRESHOLD with configurable sensitivity**: Gap detection threshold tunable via `corpus.toml` (v3 hardcodes the algorithm)
- **`corpus graph --diff <branch>`**: Show which dependency edges are new or broken vs. main branch — graph-diff for PR review
- **Centrality decay**: Time-weighted centrality (recently-modified hub files boosted more than stale ones)

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| MMR (Maximal Marginal Relevance) diversity flag | `--max-per-file` + cross-encoder reranker solve the same UX problem more intuitively for code search; MMR adds L2-normalization complexity without proportional benefit in this domain |
| `--within-graph` soft scope | Elegant but rare for human users; `--source` filter achieves similar scoping; deferred to v3.x |
| LLM-based re-ranking via Ollama | 1–5s latency per candidate batch; cross-encoder is faster and more accurate for code |
| Persistent normalised score baseline across queries | Cross-query normalisation is misleading for hybrid scores; per-query scope is correct |
| Streaming MCP responses | Deferred from v2; out of scope for v3 |
| Cross-source graph traversal (import graph) | Requires crawling actual import statements across repos, not just Markdown links; complex, defer to v4 |
| Schema-to-implementation joins | Sophisticated "propagated search" across repos; v4+ |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| COORD-01 | Phase 26 | Pending |
| XSRC-01 | Phase 26 | Pending |
| XSRC-02 | Phase 26 | Pending |
| FILTER-01 | Phase 26 | Pending |
| FILTER-02 | Phase 26 | Pending |
| RANK-01 | Phase 27 | Pending |
| RANK-02 | Phase 27 | Pending |
| RANK-03 | Phase 27 | Pending |
| MULTI-01 | Phase 28 | Pending |
| BOOST-01 | Phase 28 | Pending |
| RERANK-01 | Phase 29 | Pending |
| RERANK-02 | Phase 29 | Pending |
| DEP-01 | Phase 30 | Pending |
| GCENT-01 | Phase 30 | Pending |
| GCENT-02 | Phase 30 | Pending |
| GEXP-01 | Phase 31 | Pending |
| GWALK-01 | Phase 31 | Pending |
| GWALK-02 | Phase 31 | Pending |
| V3QUAL-01 | Phase 32 | Pending |
| V3QUAL-02 | Phase 32 | Pending |

**Coverage:**
- v3 requirements: 20 total (18 primary + 2 quality)
- Mapped to phases: 20
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-24*
*Last updated: 2026-02-24 — roadmap created (v3-ROADMAP.md, Phases 26–32)*

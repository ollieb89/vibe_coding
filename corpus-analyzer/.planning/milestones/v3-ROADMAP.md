# Roadmap: v3.0 Intelligent Search

## Overview

v3 stops flooding results with variations of the same file. A `SearchCoordinator` becomes the single composition point for all three query surfaces (CLI, MCP, Python API), running a fixed 8-step post-retrieval pipeline. The 7 phases build in dependency order: scaffold the coordinator first with zero-risk passthrough features, then layer on result quality controls, multi-query composition, optional cross-encoder re-ranking, centrality-boosted scoring, and graph expansion with recursive traversal. The final phase hardens quality gates across all the new behaviour.

## Phases

- [ ] **Phase 26: Foundation** - SearchCoordinator scaffold wired to all surfaces; source labeling; exclude-path filter
- [ ] **Phase 27: Result Quality** - Per-file chunk cap; contiguous sub-chunk merging; score gap detection
- [ ] **Phase 28: Multi-Query AND + Boost** - Multiple --query AND intersection with overfetch+score-sum; --boost term nudge
- [ ] **Phase 29: Cross-Encoder Reranker** - Optional --rerank flag with sentence-transformers; sigmoid scores; score_type annotation
- [ ] **Phase 30: Centrality Scoring** - networkx dep; indegree centrality table; log-dampened boost in coordinator
- [ ] **Phase 31: Graph Expansion + Recursive Walk** - --expand-graph annotates results; corpus graph --depth N BFS with cycle detection; hub node labels
- [ ] **Phase 32: Quality Hardening** - ruff/mypy clean; 40+ new tests; score range docs updated for normalised scores

## Phase Details

### Phase 26: Foundation
**Goal**: Users can search with coordinator-mediated results that show source labels and respect path exclusions — with zero ranking regressions
**Depends on**: v2 Phase 17 (chunk_name/start_line/end_line in LanceDB schema v4; coordinator passthrough requires no v4 fields but RANK-02 in Phase 27 does)
**Requirements**: COORD-01, XSRC-01, XSRC-02, FILTER-01, FILTER-02
**Success Criteria** (what must be TRUE):
  1. Running `corpus search <query>` produces identical result ordering and scores as before — the coordinator is a transparent passthrough; all pre-v3 tests stay green
  2. Every CLI result line shows a `[source_name]` prefix (e.g., `[superpowers] path/to/file.md:42-67 [skill] score:0.021`) using the `source_name` field already stored in LanceDB
  3. MCP `corpus_search` response objects each contain a `source` field alongside existing `path`, `score`, and `construct` fields
  4. `corpus search --exclude-path "tests/**"` omits all results whose path matches the glob; multiple `--exclude-path` flags are OR'd; `fnmatch.fnmatch()` semantics used (not `pathlib.PurePath.match()`)
  5. A `.corpus-ignore` file at the corpus root is read automatically and its patterns merged with any `--exclude-path` flags, so the user does not need to repeat common exclusions on each search invocation
**Plans**: TBD

### Phase 27: Result Quality
**Goal**: Users receive focused, non-repetitive results — same-file flooding eliminated, adjacent method chunks merged, and relevance drop-offs surfaced visually
**Depends on**: Phase 26; v2 Phase 17 must be complete for RANK-02 (chunk_name/start_line/end_line fields)
**Requirements**: RANK-01, RANK-02, RANK-03
**Success Criteria** (what must be TRUE):
  1. `corpus search --max-per-file 2 <query>` returns at most 2 chunks per file across the result set; default cap of 3 applies when the flag is omitted; cap is applied post-retrieval before display
  2. Adjacent method chunks from the same class appearing consecutively in a result set are collapsed into a single display entry showing the merged line range (e.g., `MyClass:10-45`) and combined chunk text; requires v2 chunk_name/start_line/end_line; collapser skips gracefully on rows with empty chunk_name or 0 line values
  3. When the score drop between consecutive results is >= 40% of the top result's score, a visual separator (`---`) is inserted between those results in CLI output
  4. MCP results include a `gap_above: true` field on any result where the score gap threshold is exceeded, allowing MCP consumers to surface the same signal programmatically
**Plans**: TBD

### Phase 28: Multi-Query AND + Boost
**Goal**: Users can express compound intent with multiple --query flags and give a soft nudge to results mentioning specific terms — neither operation filters out valid results on sparse corpora
**Depends on**: Phase 27
**Requirements**: MULTI-01, BOOST-01
**Success Criteria** (what must be TRUE):
  1. `corpus search --query auth --query saml` returns results present in both query result sets using overfetch+score-sum (NOT hard set intersection on chunk IDs); files are included only if they appear in all N per-query result sets; scores are summed across queries before ranking
  2. On a sparse real corpus where hard chunk-ID intersection would return zero results, the overfetch+score-sum approach returns non-empty results — verified by a test with limit=5 and two queries against a corpus of 10 documents
  3. When no results satisfy the AND intersection, a contextual hint is displayed ("No results matching all queries — try a single --query to see individual results") analogous to the existing FILT-03 hint
  4. `corpus search --boost "async" <query>` applies a +15% score nudge to results whose chunk text or chunk name contains "async"; non-matching results are still returned; multiple `--boost` flags are additive; boosts are applied after the RANK-01 cap and before RANK-03 gap detection
**Plans**: TBD

### Phase 29: Cross-Encoder Reranker
**Goal**: Users who need maximum ranking accuracy for complex natural-language queries can opt in to a two-stage cross-encoder re-rank with a single flag
**Depends on**: Phase 28
**Requirements**: RERANK-01, RERANK-02
**Success Criteria** (what must be TRUE):
  1. `corpus search --rerank <query>` fetches top-20 candidates from the coordinator pipeline, re-ranks them using `cross-encoder/ms-marco-MiniLM-L6-v2`, and returns results with sigmoid-normalised scores — the `--rerank` flag is visible in `corpus search --help`
  2. Every result returned with `--rerank` carries a `score_type: "cross_encoder"` annotation; results returned without `--rerank` carry `score_type: "rrf"`; the two types are never mixed in a single result list
  3. Running `corpus search --rerank <query>` without `sentence-transformers` installed prints a clear error: "cross-encoder reranking requires sentence-transformers — install with: uv sync --extra rerank"; no traceback is shown
  4. `sentence-transformers>=5.2.3` appears as an optional extra under `[rerank]` in `pyproject.toml` and is NOT in the core required deps; `uv sync --extra rerank` succeeds; `uv sync` (without extra) succeeds and leaves cross-encoder unavailable
**Plans**: TBD

### Phase 30: Centrality Scoring
**Goal**: Files that are highly referenced in the relationship graph receive a proportional but dampened score boost in search results — computed correctly from the full graph after each index run, not per-file
**Depends on**: Phase 29; DEP-01 (networkx added as core dep)
**Requirements**: DEP-01, GCENT-01, GCENT-02
**Success Criteria** (what must be TRUE):
  1. `networkx>=3.6.1` is added as a core dependency in `pyproject.toml`; `uv sync` succeeds; `mypy src/` reports 0 errors with `ignore_missing_imports = true` override for networkx
  2. After `corpus index` completes, a `centrality` table exists in `graph.sqlite` with rows `{file_path, indegree, computed_at}`; the table reflects the indegree of every file in the full `relationships` table — not incremental per-file counts
  3. `compute_indegree()` is called exactly once at the END of `index_source()` — after all edges for the entire source have been written — not per-file during the walk; a test with a two-step source (index file A, then file B which links to A) verifies centrality reflects the full graph state after both files are indexed
  4. In `SearchCoordinator`, a high-indegree file (e.g., indegree=20) receives a score multiplier of `1.0 + math.log(1 + 20) * 0.1 ≈ 1.30`, confirmed by a unit test; the multiplier is capped at 2.0 regardless of indegree; files with no centrality record receive a multiplier of 1.0 (neutral)
  5. Centrality values are pre-loaded into a dict at coordinator startup (not fetched per-result via individual SQLite SELECTs)
**Plans**: TBD

### Phase 31: Graph Expansion + Recursive Walk
**Goal**: Users can augment search results with immediate graph neighbors and traverse the dependency graph N hops deep — without hanging on cyclic corpora
**Depends on**: Phase 30
**Requirements**: GEXP-01, GWALK-01, GWALK-02
**Success Criteria** (what must be TRUE):
  1. `corpus search --expand-graph <query>` annotates each result with its immediate graph neighbors from `graph.sqlite`; CLI output labels neighbors as `[Depends On]` (downstream) or `[Imported By]` (upstream) with slug and construct type; neighbor lookup uses a single batched SQL `IN` clause (not N individual queries) to avoid N+1 performance degradation
  2. MCP `corpus_search` with `expand_graph: true` includes a `neighbors` array per result containing `{path, relation, construct}` objects
  3. `corpus graph <slug> --depth 3` performs BFS traversal up to 3 hops and returns all reachable nodes grouped by distance; when `--depth` is omitted the default is 2
  4. A corpus with a mutual-reference cycle (file A references B, file B references A) does not cause infinite recursion or hang when `corpus graph <slug> --depth 5` is run; a `visited: set[str]` prevents re-enqueuing already-seen nodes; a test explicitly asserts this with an A→B→A graph
  5. Hub nodes in `corpus graph` output are labeled with their indegree count (e.g., `config.py [indegree: 42]`) so users can identify high-centrality dependencies at a glance
**Plans**: TBD

### Phase 32: Quality Hardening
**Goal**: The full v3 pipeline is lint-clean, type-clean, and covered by at least 40 new test methods; score range documentation reflects post-NORM-01 normalised scores throughout
**Depends on**: Phase 31
**Requirements**: V3QUAL-01, V3QUAL-02
**Success Criteria** (what must be TRUE):
  1. `uv run ruff check .` exits 0 and `uv run mypy src/` exits 0 across all v3 changes
  2. The test suite includes at least 40 new test methods covering: coordinator pipeline steps, per-file cap, multi-query overfetch+score-sum intersection, gap detector threshold, graph expansion neighbor batching, centrality boost multiplier, cycle detection in graph walk, and reranker score_type annotation
  3. All existing pre-v3 tests pass alongside v3 tests — total test count is at least (pre-v3 count + 40)
  4. `--min-score` CLI help text, FILT-03 hint message, and all score-range test assertions are updated to reflect 0–1 normalised scores (from v2 NORM-01); no documentation or test still references raw RRF score ranges (0.009–0.033) as expected output ranges
**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 26. Foundation | 0/TBD | Not started | - |
| 27. Result Quality | 0/TBD | Not started | - |
| 28. Multi-Query AND + Boost | 0/TBD | Not started | - |
| 29. Cross-Encoder Reranker | 0/TBD | Not started | - |
| 30. Centrality Scoring | 0/TBD | Not started | - |
| 31. Graph Expansion + Recursive Walk | 0/TBD | Not started | - |
| 32. Quality Hardening | 0/TBD | Not started | - |

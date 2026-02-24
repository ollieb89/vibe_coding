# Project Research Summary

**Project:** corpus-analyzer v3 Intelligent Search
**Domain:** Local semantic search CLI — post-retrieval ranking pipeline and graph-enriched results
**Researched:** 2026-02-24
**Confidence:** HIGH

## Executive Summary

corpus-analyzer v3 adds an intelligent search pipeline on top of an already-working LanceDB hybrid BM25+vector+RRF system. The recommended approach is to introduce a `SearchCoordinator` as a single composition point that all three query surfaces (CLI, MCP, Python API) route through, rather than modifying the existing `hybrid_search()` engine or triplicating v3 logic across surfaces. The coordinator applies a fixed sequence of post-retrieval steps: multi-query fan-out, path exclusion, centrality boost, MMR diversity re-rank, optional cross-encoder re-rank, graph expansion, and contiguous chunk merging. This keeps the engine stable and makes each step independently testable.

The key architectural insight across all research files is that v3 features divide cleanly into two dependency tiers: zero-schema-change features (cross-source labeling, `--exclude-path`, `--max-per-file`, `--expand-graph`) that can ship immediately using existing data, and infrastructure-requiring features (centrality scoring, MMR with vector access, `--depth N` graph walk, cross-encoder reranking) that each need a specific prerequisite. Delivering the first tier early validates the coordinator scaffold before adding complexity.

The dominant risk is not architectural but correctness-under-edge-cases: MMR on unnormalized vectors silently inverts its purpose, multi-query hard intersection reliably returns zero results on real corpora, recursive graph walks hang on mutual-reference cycles, and centrality hub nodes corrupt search ranking without logarithmic dampening. Every one of these bugs is invisible in development (small corpora, no cycles, no star topologies) and surfaces only in production. The mitigation is to encode the correct behavior — L2 normalization inside MMR, overfetch+score-sum for AND intersection, visited-set for graph walks, log dampening + 2.0x cap for centrality — as mandatory constraints in the implementation spec, not as post-ship fixes.

## Key Findings

### Recommended Stack

The v3 stack requires only two new packages. `networkx>=3.6.1` (2.1 MB, pure Python, zero required deps) is added as a core dependency to compute indegree centrality and PageRank from the existing `graph.sqlite` adjacency table. `sentence-transformers>=5.2.3` is added as an optional extra (`uv sync --extra rerank`) to provide the `CrossEncoder` class for two-stage re-ranking; it carries an ~800 MB PyTorch transitive dependency and must never be in required deps. Everything else — MMR, multi-query intersection, path exclusion, contiguous merging — uses numpy (already present via LanceDB/pandas) and stdlib `fnmatch`. No scikit-learn, no faiss, no scipy, no cloud API clients.

See `.planning/research/STACK.md` for full version justifications and mypy override notes.

**Core technologies:**
- `networkx>=3.6.1`: PageRank/indegree centrality for graph-aware ranking — pure Python, one-liner API, handles dangling nodes; add as core dep
- `numpy 2.4.2` (already present): MMR cosine similarity — `np.dot / np.linalg.norm`; no sklearn needed
- `fnmatch` (stdlib): `--exclude-path` glob matching — handles `*`, `**`, `?`, `[ranges]`; do NOT use `pathlib.PurePath.match()` (`**` is not recursive there)
- `sentence-transformers>=5.2.3` (optional extra): Cross-encoder re-ranking via `cross-encoder/ms-marco-MiniLM-L6-v2` (~91 MB weights, ~1800 passages/sec on CPU); lazy-import only inside `--rerank` branch

### Expected Features

The v3 feature set groups into four clusters: Cluster A (result diversity), Cluster B (graph-enriched results), Cluster C (multi-query composition), and Cluster D (quality-of-life display). Prioritization splits into P1 (zero new infrastructure, ship first), P2 (needs coordinator and some new logic), and P3 (high complexity, defer).

See `.planning/research/FEATURES.md` for full feature landscape tables and anti-feature analysis.

**Must have (table stakes):**
- Cross-source labeling — `[source_name]` prefix in CLI output + `source` field in MCP response; `source_name` already in LanceDB, display-layer change only
- `--exclude-path <glob>` — post-filter using `fnmatch`; excludes test files, generated code; OR logic for multiple patterns
- Same-file chunk cap (`--max-per-file N`, default 3) — addresses the top UX complaint without full MMR complexity; pure post-filter
- Contiguous sub-chunk merging — collapse adjacent method chunks from same class into single display entry; requires v2 `start_line`/`end_line` (Phase 17)
- `--expand-graph` on `corpus search` — annotates results with graph neighbors using existing `GraphStore`
- `corpus graph --depth N` — extends existing `corpus graph <slug>` to BFS N-hop traversal with hub node labels

**Should have (differentiators):**
- Full MMR with `--diversity` flag — guarantees architectural spread across files; numpy-only implementation; default `lambda=0.7`
- Multiple `--query` AND intersection — compound intent queries; overfetch+score-sum, file-level intersection
- `--within-graph <slug>` soft scope — +20% score boost for results in same graph component; BFS + score boosting
- `--rerank` cross-encoder — 20–35% accuracy gain for complex NL queries; optional dependency; lazy-loaded singleton

**Defer to v3.x or v4:**
- Centrality scoring in search ranking — requires `centrality` table in `graph.sqlite`, full recompute after every `corpus index` run, query-time lookup in coordinator; high value but high complexity; own milestone
- LLM-based re-ranking via Ollama — 1–5s latency per candidate batch; not primary path

### Architecture Approach

The v3 architecture inserts a `SearchCoordinator` layer between the storage tier and all query surfaces. The coordinator owns the 8-step post-retrieval pipeline and receives `CorpusSearch` (engine) and `GraphStore` as constructor arguments. All three surfaces (CLI, MCP, API) call `coordinator.search()` instead of `engine.hybrid_search()` directly — this is the single most important structural change in v3. The engine gains one parameter (`return_vectors: bool = False`) to support MMR; otherwise its API contract is frozen. Centrality is stored exclusively in `graph.sqlite` (new `centrality` table), never in LanceDB, because it is a graph topology property and changes independently of chunk content.

See `.planning/research/ARCHITECTURE.md` for precise component specs, code skeletons, and the anti-patterns table.

**Major components:**
1. `search/coordinator.py` (NEW, ~200 lines) — pipeline orchestrator: fan-out, exclude, centrality boost, MMR, cross-encoder, graph expansion, merge, source label
2. `search/diversity.py` (NEW, ~70 lines) — pure MMR implementation; L2-normalizes vectors internally before cosine sim
3. `search/reranker.py` (NEW, ~60 lines) — `CrossEncoderReranker` with lazy-load sentinel; loads `sentence-transformers` on first `--rerank` use only
4. `graph/centrality.py` (NEW, ~30 lines) — `compute_indegree()` called at end of every `index_source()` run
5. `graph/store.py` (MODIFIED) — add `walk_n_hops()`, `indegree_counts()`, `get_centrality()`, `upsert_centrality()`, `centrality` table DDL
6. `search/engine.py` (MODIFIED, ~10 lines) — add `return_vectors: bool = False` param only

### Critical Pitfalls

See `.planning/research/PITFALLS.md` for full details, phase-to-pitfall mapping, and recovery strategies.

1. **MMR on unnormalized vectors silently inverts diversity** — L2-normalize vectors inside the MMR function before any cosine similarity computation; also normalize RRF scores to `[0, 1]` before applying MMR weights (raw RRF scores in 0.009–0.033 are too small to compete with cosine similarity values, causing diversity to always dominate regardless of lambda); write unit tests asserting two identical-text chunks receive cosine similarity = 1.0 and that `--diversity 1.0` returns the same order as the non-MMR baseline

2. **Multi-query hard intersection returns zero results** — never intersect by `chunk_id`; use file-level intersection with `fetch_k = limit * num_queries * 2` overfetch, then score-sum and re-rank; add a "no AND results" hint analogous to FILT-03; this bug is invisible in development with hand-crafted queries but reliable on real sparse corpora

3. **Recursive graph walk hangs on mutual-reference cycles** — maintain a `visited: set[str]` and check before enqueuing any neighbor; test with a two-node A→B→A cycle before shipping `--depth N`; cycles are realistic in any corpus with bidirectional skill references

4. **Centrality hub explosion corrupts all search results** — use `score *= (1 + log(1 + indegree) * 0.1)` with a hard 2.0x cap; recompute centrality from the full `relationships` table after every `index_source()` run (not per-file), because centrality is a graph-global property — computing it per-file produces stale boost signals after partial reindexing

5. **Cross-encoder scores incompatible with existing `--min-score` filter** — apply sigmoid to raw logits before returning; add `score_type: "rrf" | "cross_encoder"` annotation; update FILT-03 hint text; never mix score types in one sorted result list; `--min-score 0.02` passes every result in logit range but filters too aggressively in sigmoid range without documentation

## Implications for Roadmap

Based on combined research, the recommended structure is 8 phases in three logical blocks: foundation (coordinator scaffold + zero-risk features), smarter ranking (MMR + centrality), and richer graph (expansion + recursive walk + reranker).

### Phase 1: Foundation — Coordinator Scaffold and Quick Wins
**Rationale:** Cross-source labeling and `--exclude-path` require zero new infrastructure — data is already in LanceDB. Shipping them first validates the coordinator scaffold with pure passthrough logic. If the scaffold wiring is wrong, the failure is cheap to fix before any ranking logic is layered on top.
**Delivers:** `SearchCoordinator` wired to CLI/MCP/API in passthrough mode; `[source_name]` prefix in CLI output; `source` field in MCP response; `--exclude-path` glob filter using `fnmatch`
**Addresses:** Cross-source labeling (P1), `--exclude-path` (P1)
**Avoids:** Triplicating v3 logic across CLI/MCP/API; disrupting existing `hybrid_search()` API

### Phase 2: Result Quality — Max-Per-File Cap and Contiguous Merge
**Rationale:** `--max-per-file` is a simple post-filter that immediately addresses the top UX complaint (result flooding) with zero dependencies. Contiguous sub-chunk merging depends on v2 Phase 17 (`chunk_name`/`start_line`/`end_line`) completing first — this phase should be sequenced after Phase 17 closes.
**Delivers:** `--max-per-file N` cap (default 3); adjacent method chunk collapsing in display layer
**Addresses:** Same-file chunk deduplication (P1), contiguous merging (P1)
**Avoids:** Delivering MMR complexity before the simpler diversity solution is validated

### Phase 3: Multi-Query AND Intersection
**Rationale:** No schema changes needed; pure Python post-processing on existing search. The simplest "real" coordinator logic. Validates the coordinator's ability to handle multiple engine calls before MMR makes it more complex.
**Delivers:** Multiple `--query` flags with AND semantics; overfetch+score-sum intersection at file level; "no AND results" hint
**Addresses:** Multi-query composition (P2)
**Avoids:** Pitfall 9 (empty hard intersection) — overfetch and file-level intersection must be the first implementation, not a fallback fix

### Phase 4: MMR Diversity
**Rationale:** MMR requires the `return_vectors: bool = False` parameter added to `hybrid_search()` and the `search/diversity.py` module. All pitfall mitigations (L2 normalization, score normalization before MMR weights are applied, quadratic complexity cap at 40 candidates) must be baked in from the start.
**Delivers:** `search/diversity.py` MMR implementation; `--diversity <float>` flag (default 0.7); `return_vectors` param on engine; candidate pool capped at `min(3 * limit, 40)`
**Uses:** numpy (already present)
**Avoids:** Pitfalls 1–3 (unnormalized vectors, lambda imbalance, quadratic complexity)

### Phase 5: Centrality Scoring
**Rationale:** Centrality is the highest-dependency v3 feature and must be isolated. It requires a new `centrality` table in `graph.sqlite`, a `graph/centrality.py` module, wiring into `ingest/indexer.py`, and query-time lookup in the coordinator. The correctness requirement — full graph recompute after every index run, not per-file — is a cross-cutting concern that needs its own phase.
**Delivers:** `graph/centrality.py`; `centrality` table in `graph.sqlite`; `compute_indegree()` called at end of `index_source()`; log-dampened, 2.0x-capped centrality boost in `SearchCoordinator`
**Uses:** `networkx>=3.6.1` (new core dep)
**Avoids:** Pitfalls 7–8 (hub explosion, stale centrality after partial reindex)

### Phase 6: Graph Expansion and Recursive Walk
**Rationale:** Both features build on the existing `GraphStore`. `--expand-graph` uses the existing `edges_from()`/`edges_to()` methods (with batch query optimization to avoid N+1 SQLite calls). `--depth N` adds `walk_n_hops()` with visited-set cycle detection. They share the BFS logic and are natural to implement together. `--within-graph` soft scope can also ship here as it reuses the BFS traversal.
**Delivers:** `--expand-graph` flag on `corpus search` with batched neighbor lookup; `corpus graph --depth N` with BFS and visited-set; hub node labeling; `--within-graph <slug>` soft scope (+20% boost for in-component results)
**Addresses:** `--expand-graph` (P1), `corpus graph --depth N` (P1), `--within-graph` (P2)
**Avoids:** Pitfall 12 (N+1 SQLite queries — batch with `IN` clause), Pitfall 13 (cyclic walk hang — visited-set required before any recursive walk ships)

### Phase 7: Cross-Encoder Reranker (Optional)
**Rationale:** Fully independent of all other v3 features. Deferred because it requires a new optional dependency, a one-time 91 MB model download, score-type annotation work, and singleton lifecycle management. Ships as a standalone optional capability that users opt into.
**Delivers:** `search/reranker.py` with lazy singleton; `--rerank` flag; sigmoid score normalization; `score_type` annotation in results; `[rerank]` extras group in `pyproject.toml`
**Uses:** `sentence-transformers>=5.2.3` (optional extra, `uv sync --extra rerank`)
**Avoids:** Pitfalls 4–6 (score incompatibility with `--min-score`, cold-start latency on every call, PyTorch as a required 3 GB dependency)

### Phase 8: Display Polish and Integration Hardening
**Rationale:** Once all ranking features are in place, final display polish (combined `--diversity` + `--max-per-file` interaction, MCP `score_type` field, help text updates for score range after normalization) and integration tests across the full 8-step pipeline.
**Delivers:** Consistent score range documentation; FILT-03 hint updates; full pipeline integration tests; `--within-graph` if deferred from Phase 6
**Avoids:** Pitfall 10 (normalisation breaking existing `--min-score` filter — help text, FILT-03, and all score-range test assertions updated in one pass)

### Phase Ordering Rationale

- **Phases 1–2 first** because they have zero new dependencies and validate the coordinator scaffold before ranking logic is added.
- **Phase 3 before Phase 4** because multi-query validates N-call fan-out in the coordinator without the vector-access complexity that MMR requires.
- **Phase 5 after Phase 4** because centrality boosts interact with MMR scores — MMR must be working correctly (with normalized scores) before centrality multipliers are applied on top.
- **Phase 6 after Phase 5** because `--within-graph` reuses the BFS logic from `walk_n_hops()` and the centrality table from Phase 5.
- **Phase 7 last (before polish)** because cross-encoder re-ranking is fully isolated and deferrable without blocking any other feature.
- **Contiguous chunk merge (Phase 2)** is gated on v2 Phase 17 closing — if Phase 17 slips, Phase 2 can ship without contiguous merging and add it later.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 5 (Centrality):** Query-time centrality lookup strategy — pre-load full centrality dict into memory at coordinator startup vs per-result SQLite SELECT; decision depends on measured corpus size and acceptable startup latency budget
- **Phase 7 (Cross-encoder):** Model selection for user hardware — MiniLM-L6-v2 vs TinyBERT-L2-v2 trade-off; whether to expose `--rerank-model` as a `corpus.toml` option

Phases with well-documented patterns (skip research-phase):
- **Phase 1 (Scaffold):** SearchCoordinator is standard pipeline-orchestrator pattern; architecture doc provides precise code skeletons; all integration points verified by source inspection
- **Phase 3 (Multi-query):** Overfetch+score-sum intersection is fully specified in ARCHITECTURE.md with working code; LanceDB multi-query limitation confirmed
- **Phase 4 (MMR):** MMR algorithm is standard; full numpy implementation provided in ARCHITECTURE.md; no ambiguity in algorithm
- **Phase 6 (Graph):** Existing `GraphStore` infrastructure is in place; BFS with visited-set is textbook; batch `IN` clause query is standard SQLite

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All libraries verified on PyPI with release dates; API confirmed from official sbert.net and NetworkX docs; environment-tested (numpy version, fnmatch patterns against all expected forms) |
| Features | MEDIUM-HIGH | P1 features confirmed against existing codebase via source inspection; P2/P3 features confirmed via LanceDB/sbert official docs and LangChain integration reference; graph centrality via NetworkX official docs |
| Architecture | HIGH | Based on direct source code inspection of existing codebase + verified library integration docs; code skeletons provided and cross-checked against actual `engine.py`, `store.py`, `indexer.py` |
| Pitfalls | HIGH | Most pitfalls verified against official Python docs, LanceDB docs, CPython issue tracker; L2 normalization requirement confirmed via Zilliz docs; MMR normalization order verified via Elasticsearch search labs article |

**Overall confidence:** HIGH

### Gaps to Address

- **Multi-query candidate multiplier tuning:** ARCHITECTURE.md recommends `per_query_limit = limit * len(queries) * 2` but notes this needs UAT to tune on a real corpus before Phase 3 ships.
- **Centrality pre-load vs per-query lookup:** PITFALLS.md recommends pre-loading the full centrality dict at coordinator startup for performance, but ARCHITECTURE.md shows per-result lookup. Resolve during Phase 5 planning based on measured corpus size (pre-load is almost certainly correct — the table is small).
- **Score normalization timing (NORM-01 vs v3):** Pitfall 11 notes that MMR requires scores normalized to `[0, 1]` before MMR weights are applied. If v2 NORM-01 is not yet shipped when Phase 4 begins, the MMR function must internally normalize RRF scores. This dependency must be tracked explicitly between v2 and v3 phase sequencing.
- **`--expand-graph` path format consistency:** LanceDB stores absolute paths; `graph.sqlite` may have different representations if indexed on a different machine. Normalize with `Path(p).resolve()` before any GraphStore lookup — confirm path format consistency during Phase 6 planning.

## Sources

### Primary (HIGH confidence)
- PyPI: `sentence-transformers` v5.2.3 (2026-02-17), `networkx` v3.6.1 (2025-12-08) — version, wheel size, dep requirements
- sbert.net official docs — `CrossEncoder` API, pretrained models table, MiniLM-L6-v2 NDCG@10 74.30, 1800 docs/sec CPU throughput
- NetworkX official docs — `in_degree_centrality()`, `pagerank(G, alpha=0.85)` API signatures
- Python stdlib docs — `fnmatch.fnmatch()` semantics; `pathlib.PurePath.match()` `**` limitation (CPython issue #118701)
- LanceDB docs — multivector search (ColBERT-style per-document, not multi-query); custom reranker API (`rerank_hybrid` signature)
- Direct source code inspection — `search/engine.py`, `graph/store.py`, `ingest/indexer.py`, `store/schema.py`, `mcp/server.py`
- Environment verification — numpy 2.4.2 confirmed; fnmatch patterns tested against all expected glob forms

### Secondary (MEDIUM confidence)
- LangChain-LanceDB integration reference — `max_marginal_relevance_search()` with `lambda_mult` parameter confirms LanceDB supports MMR internally
- Pinecone learning series — two-stage retrieval candidate sizing and CPU latency tradeoffs
- OpenSearch 3.3 announcement — native MMR with lambda parameter semantics confirmed
- Axon (GitHub) — blast-radius BFS traversal pattern with configurable depth
- Microsoft GraphRAG — local search fan-out to graph neighbors pattern
- Milvus multi-vector hybrid search docs — multi-query AND composition pattern (Python-level intersection is equivalent for LanceDB)
- Zilliz FAQ — L2 normalization requirement for cosine similarity in embedding models
- Elastic search labs — MMR normalization requirement and performance notes
- Qdrant blog — MMR diversity-aware reranking with lambda guidance
- ZeroEntropy reranking guide (2026) — TinyBERT/20 docs latency (~50ms on CPU) confirmed

### Tertiary (MEDIUM confidence)
- HuggingFace Hub — `cross-encoder/ms-marco-MiniLM-L6-v2` model card, ~91 MB safetensors weight size

---
*Research completed: 2026-02-24*
*Ready for roadmap: yes*

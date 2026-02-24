# Feature Research

**Domain:** Intelligent Search — v3 features for local semantic search CLI (corpus-analyzer)
**Researched:** 2026-02-24
**Confidence:** MEDIUM-HIGH (MMR and cross-encoder patterns verified via multiple official sources; graph-centrality ranking verified via academic and production sources; LanceDB-specific MMR confirmed via LangChain integration docs; offline cross-encoder via sentence-transformers sbert.net docs)

---

## Scope of This Document

This document covers **only v3 NEW features**. The following are already built and are NOT re-researched here:

- Hybrid BM25+vector+RRF search (LanceDB)
- `--source`, `--construct`, `--name`, `--min-score`, `--sort-by`, `--output json` filters
- `corpus graph <slug>` upstream/downstream neighbors
- MCP `corpus_search` and `corpus_graph` tools
- Chunk-level results with `start_line`/`end_line`/`chunk_name`/`chunk_text` (v2, in progress)

---

## Feature Clusters

The v3 features group into four clusters. Each cluster is addressed separately below.

### Cluster A — Result Diversity (MMR + Sub-chunk Merging)
### Cluster B — Graph-Enriched Results (Graph Expansion + Centrality Scoring + Blast Radius)
### Cluster C — Multi-Query Composition (AND Intersection + Negative Filter)
### Cluster D — Quality-of-Life Display (Cross-Source Labeling + Contiguous Merging + --within-graph)

---

## Cluster A: Result Diversity

### How MMR Works in Practice

MMR (Maximal Marginal Relevance) is a post-retrieval reranking algorithm. The standard flow is:

1. Retrieve a larger candidate set from the vector store (e.g., `fetch_k=50`)
2. Score every candidate against the query (relevance score already available from vector search)
3. Greedily select the next result by maximizing: `λ * relevance(doc) - (1-λ) * max_similarity(doc, already_selected)`
4. Repeat until `k` results are selected

The `λ` parameter is the diversity lever: `λ=1.0` is pure relevance (identical to standard search), `λ=0.0` is maximum diversity (ignores relevance). Practical values: `λ=0.5` for exploratory queries (agent library discovery), `λ=0.7–0.8` for precision queries where users know the construct name.

**User-visible behavior:** Without MMR, a query like `"authentication token validation"` may return 5 chunks from the same `auth_validator.py` file (consecutive method chunks, very high cosine similarity to each other). With MMR (`λ=0.5`), those 5 slots are replaced by 1 chunk from `auth_validator.py` plus chunks from `token_store.py`, `session_middleware.py`, `oauth_handler.ts`, and `role_guard.ts`. The user sees the full architectural spread in one query.

**LanceDB implementation path:** LanceDB's LangChain integration exposes `max_marginal_relevance_search(query, k, fetch_k, lambda_mult)`. The underlying mechanism — embedding all candidates and computing inter-candidate cosine similarity — can be implemented in pure Python using numpy without LangChain. The existing `CorpusSearch` class can implement MMR as a post-processing step on the raw candidate list returned by `table.search(...).limit(fetch_k).to_list()`.

**Confidence:** HIGH (LangChain-LanceDB integration docs confirm `max_marginal_relevance_search` exists; MMR algorithm is well-established academic literature; implementation in numpy is trivial)

### Contiguous Sub-Chunk Merging

When v2 sub-chunking ships (`ClassName.method_name` chunks), a `corpus search` query often returns several consecutive method chunks from the same class. These are displayed as separate results with identical file paths but adjacent line ranges (`42-67`, `68-91`, `92-114`). The display is noisy and the user must mentally reassemble the class.

**Merge rule:** After scoring and ordering, if two results satisfy all three conditions — (1) same `file_path`, (2) same class prefix (for method chunks), and (3) `end_line[i] + 1 >= start_line[i+1]` — merge them into a single display entry with the combined line range. The merged entry's score is the maximum of the individual scores.

**User-visible behavior:** Three rows `auth_validator.py:42-67`, `auth_validator.py:68-91`, `auth_validator.py:92-114` collapse into one row `auth_validator.py:42-114`. One result slot is consumed instead of three, freeing space for results from other files.

**Dependency:** Requires v2 `start_line`/`end_line` in LanceDB schema (CHUNK-01, in progress Phase 17).

---

## Feature Landscape — Cluster A

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Same-file chunk deduplication | Returning 5 chunks from one file when asking a broad query is the top UX complaint in semantic search tools | MEDIUM | Can be implemented as a simpler variant of MMR: post-filter to max 1–2 chunks per file path. Lower complexity than full MMR. `--diversity none/file/mmr` flag |
| Contiguous sub-chunk merging | v2 creates `ClassName.method_name` sub-chunks; adjacent methods from same class appear as separate results — confusing for the user | LOW | Sort by `(file_path, start_line)` after retrieval; merge if adjacent and same class prefix. Display layer only, no schema change |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Full MMR with `--diversity` flag and lambda control | Guarantees architectural spread — query returns results from different files/constructs even when one file dominates relevance scores | MEDIUM | Fetch `fetch_k=50` candidates from LanceDB; run Python MMR loop using stored embeddings (or re-embed candidates via cosine similarity). Default `λ=0.5`. Expose `--diversity 0.0-1.0` flag |
| Per-file chunk count cap as a simpler fallback | `--max-per-file N` limits results per `file_path` without MMR computation overhead. Zero extra dependencies. | LOW | Post-filter on sorted result list. Useful when user just wants breadth without tuning λ |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Always-on MMR (no flag, no opt-out) | Diversity seems universally better | For `--name` and `--construct` filtered queries, the user is looking for all occurrences of a specific construct — deduplication works against them. MMR should be opt-in or have a sensible default that is overridable. | Default to `--max-per-file 3` (simple, fast); expose `--diversity` as an explicit flag for full MMR |
| MMR using re-embedded candidates at query time | More accurate inter-candidate similarity | Requires storing raw embeddings in a queryable format and running O(k*fetch_k) dot products. Adds 50–200ms latency. LanceDB does not expose stored vectors directly in `to_list()` output by default. | Implement MMR using the existing RRF score as the relevance proxy and cosine sim of retrieved chunk text via `sentence-transformers` encode — only if embeddings are already available in memory |

---

## Cluster B: Graph-Enriched Results

### How Graph Expansion Works in Practice

Graph-expanded search augments top search hits with their immediate neighbors from the dependency graph. The UX pattern (seen in Sourcegraph, GraphRAG local search, and LSP-based tools) is:

1. Run vector/hybrid search to get top-k primary results
2. For each primary result, query the graph store for immediate neighbors (indegree and outdegree)
3. Present neighbors as a separate labeled section: `[Depends On]` or `[Imported By]`
4. Neighbors are not ranked against primary results — they appear as contextual annotations

The user sees:
```
auth_validator.py:42-67 [skill] score:0.024
  Depends On: token_store.py, crypto_utils.py
  Imported By: session_middleware.py, api_gateway.py
```

This surfaces files that are architecturally related but may have low lexical/semantic similarity to the query — they are related by structure, not by content.

**`--expand-graph` as an opt-in flag** is the correct UX: graph expansion adds 1–3 SQLite queries per result. For 10 results that is 10–30 queries on `graph.sqlite`, each sub-millisecond. Total overhead is under 5ms. The flag keeps default output clean for users who do not use the graph layer.

### Recursive Graph Walk / Blast Radius

The `corpus graph --depth N` feature expands the existing `corpus graph <slug>` from immediate neighbors to N-hop traversal. This is the "blast radius" pattern: "if I change `token_store.py`, what else might break?"

**BFS traversal is the standard approach** (not DFS): level-by-level expansion naturally gives users the proximity of impact. Tools like `axon impact SYMBOL` implement this with configurable depth.

**Hub node detection:** High-indegree nodes (files imported by many others) are architectural hubs. Labeling them with `[hub: 12 inbound]` warns users they are looking at a widely-shared dependency. The indegree count is already computable from `graph.sqlite` `relationships` table.

**User-visible behavior at depth 2:**
```
corpus graph auth_validator --depth 2

auth_validator.py
  → (level 1) token_store.py [hub: 8 inbound]
  → (level 1) crypto_utils.py
  → (level 2) base64_encoder.py
  → (level 2) key_rotation.py
  ← (level 1) session_middleware.py
  ← (level 1) api_gateway.py
  ← (level 2) route_handler.py
```

### Graph Centrality as a Ranking Signal

Centrality scoring gives high-indegree files a score multiplier in hybrid search. The rationale: if 15 other files import `agent_registry.py`, it is likely a foundational file — when a user queries "agent registration", the foundational file should rank higher than a leaf file with similar text.

**Implementation:** At `corpus index` time, compute indegree per node from `graph.sqlite`. Store the count in LanceDB as a `centrality` float column (normalized 0–1 against max indegree in the graph). At search time, multiply the RRF score by `(1 + centrality_weight * centrality)` where `centrality_weight` is a tunable constant (suggested default: 0.2).

**Dependency:** Requires `corpus index` to populate centrality scores and LanceDB schema v5 to store the `centrality` column.

### `--within-graph <slug>`

Soft-scoping a search to files in the same graph component as a reference file. Results inside the component get a +20% score boost; results outside are not excluded. This answers: "find authentication patterns, but weight things in the same subsystem as `auth_validator.py` higher."

---

## Feature Landscape — Cluster B

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `--expand-graph` flag on `corpus search` | Users who have indexed with the graph layer expect to be able to see relationships alongside search hits | MEDIUM | 1–3 SQLite queries per result against existing `graph.sqlite`; `GraphStore.search_paths(fragment)` already exists; output as indented annotation below each result row |
| `corpus graph --depth N` recursive walk | `corpus graph <slug>` already ships; depth-1 only is incomplete for architectural analysis | MEDIUM | BFS loop on `relationships` table; stop at depth N; deduplicate visited nodes; label hub nodes (indegree > threshold) |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Centrality score boost in hybrid search | Foundational files surface higher for broad queries; reduces need to manually navigate the graph | HIGH | Requires: indegree computation at index time, LanceDB schema v5 migration for `centrality` column, score multiplier in `CorpusSearch`; not trivial but the value is high for multi-repo agent libraries |
| `--within-graph <slug>` soft scope | Keeps search focused on an architectural subsystem without hard filtering | MEDIUM | Requires: graph component membership query (BFS from slug, collect all reachable nodes), then post-search score boosting for results whose path is in the component set |
| Hub node labeling in graph walk output | Warns users they are touching a widely-shared dependency | LOW | Indegree count is one aggregation query on `relationships`; display as `[hub: N inbound]` annotation |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Always-including graph neighbors in every search result | Richer results by default | Adds SQLite round-trips for every result on every search. For users who do not use the graph layer at all, these are wasted queries returning empty results. Clutters output with empty `Depends On: (none)` lines. | Opt-in `--expand-graph` flag; skip neighbor queries entirely when flag absent |
| Hard filtering to graph-reachable files only | "Only show results from files in the same component" seems focused | Excludes genuinely relevant files that happen not to be linked in the graph. Graph coverage is never 100%. A skill file might be relevant but not have `## Related Skills` links. | Soft boost (`--within-graph` +20%) rather than hard filter |
| PageRank / betweenness centrality | More sophisticated than indegree | PageRank and betweenness require iterative computation across the whole graph. For agent libraries with hundreds of files (not millions), indegree is sufficient and O(n) to compute. PageRank adds a dependency and complexity without measurable quality gain at this scale. | Indegree centrality only; revisit if graph grows beyond ~10K nodes |

---

## Cluster C: Multi-Query Composition

### How Multi-Query AND Intersection Works

Standard vector databases do not natively support AND-intersection of semantic spaces. The implementation pattern for multi-query composition is:

1. Execute each query independently: `results_A = search("auth")`, `results_B = search("saml")`
2. Intersect by `chunk_id` or `file_path`: keep only results that appear in ALL query result sets
3. Score the intersection: sum or average the individual RRF scores, re-rank

For two queries with `top_k=50` each, the intersection might be 3–15 chunks. Re-rank by combined score and return top-k final results.

**User-visible behavior:**
```bash
corpus search --query "authentication" --query "saml" --limit 5
```
Returns only chunks that are semantically relevant to BOTH authentication AND SAML. Prevents noisy results for one term drowning out the intersection.

**Dependency:** Requires two independent search calls inside `CorpusSearch.search()`. No schema changes needed. The existing `--source`, `--construct`, `--min-score` filters apply after intersection.

**Milvus and other production vector DBs** support this via `hybrid_search()` with multiple `AnnSearchRequest` objects — but this is a higher-level API that LanceDB does not expose directly. The Python-level intersection is functionally equivalent and fully compatible with LanceDB's `table.search()`.

### `--exclude-path <glob>`

Negative path filter: `--exclude-path "*/tests/*"` removes results whose `file_path` matches the glob pattern. This is a post-search structural filter, not a semantic operation.

**User-visible behavior:** Prevents test files from dominating results when the user wants production code examples. Complements `--source` (which filters by named source config) for users who do not have a separate source config for tests.

---

## Feature Landscape — Cluster C

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `--exclude-path <glob>` | Users frequently want to exclude test directories, generated files, or `node_modules` from search results | LOW | `fnmatch.fnmatch(result.file_path, pattern)` post-filter; multiple `--exclude-path` flags use OR logic (exclude if any pattern matches) |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Multiple `--query` AND intersection | Enables compound intent queries that single-query search cannot express: "find authentication AND token AND refresh" | MEDIUM | Two or more `table.search().limit(fetch_k)` calls; set intersection on `chunk_id`; combined RRF score; result count can be zero (user-facing hint: "no results matched all N queries simultaneously") |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| OR union of multiple `--query` flags | "More results from more queries" seems useful | OR union doubles result count and re-introduces the same problem as a single broad query. The value of multi-query is precisely the intersection — more focused results. | If the user wants broader results, a single combined query ("authentication saml token") already captures OR semantics via the vector space |
| `--query` flag with boolean operators in the string (`--query "auth AND saml"`) | Familiar SQL-style syntax | Parsing boolean operators from a query string is fragile and conflicts with natural language queries. "auth AND saml" as a natural language query to the embedding model is valid — the model processes "AND" as a conjunction word, not a boolean operator. | Separate `--query` flags for each term. CLI-level boolean is clear and unambiguous. |

---

## Cluster D: Quality-of-Life Display

### Cross-Source Labeling

When a user has multiple sources configured (e.g., `personal-skills`, `work-agents`, `oss-prompts`), every result should display which source it came from. This is the primary navigation signal for multi-source setups.

**CLI format:**
```
[personal-skills] auth/validator.py:42-67 [skill] score:0.024
  def validate_token(token: str) -> bool:
```

**MCP format:** Add `"source": "personal-skills"` field to each result object in `corpus_search` response. Already tracked in LanceDB schema (`source_name` column exists per `corpus.toml` source config).

**Dependency:** `source_name` is already stored in LanceDB per chunk (indexed at `index_source()` time with the `SourceConfig.name`). This is a display-layer change only.

**Confidence:** HIGH — `source_name` column existence confirmed by reading `PROJECT.md` architecture section (SourceConfig with `.name`).

---

## Feature Landscape — Cluster D

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Source name prefix on CLI results | Users with 2+ source configs cannot tell which library a result came from without the prefix | LOW | Read `source_name` from the LanceDB result dict; prepend `[source_name]` to the CLI output line. No schema change. |
| `source` field in MCP `corpus_search` response | MCP callers (LLMs) need to cite provenance; "this skill comes from personal-skills library" is essential context for an agent making decisions | LOW | Add `source` key to the `SearchResult` dataclass and MCP response dict. `source_name` already in LanceDB row. |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| `--within-graph <slug>` soft scope (also listed in Cluster B) | Cross-cutting: both a graph feature and a result quality feature | MEDIUM | See Cluster B for full details |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Source-specific score normalization (normalize within each source separately) | Prevents one source from dominating if it has more documents | Source-level normalization makes cross-source comparison meaningless. A score of 0.8 from `personal-skills` would be incomparable to a score of 0.8 from `work-agents`. | Per-query min-max normalization (v2 NORM-01 already planned) is global and keeps scores comparable across sources. The `--source` filter already provides source isolation when needed. |

---

## Optional Two-Stage Re-ranking (`--rerank`)

### How Cross-Encoder Re-ranking Works

Cross-encoder re-ranking is a standard two-stage pipeline in production search systems:

**Stage 1 (existing):** Fast bi-encoder retrieval via LanceDB hybrid search — returns top-50 candidates in <100ms.

**Stage 2 (new, `--rerank`):** A cross-encoder processes each `(query, chunk_text)` pair jointly through a transformer, producing a relevance score with full cross-attention. Candidates are re-sorted by this score. The cross-encoder's deeper semantic reasoning corrects ranking errors from the bi-encoder (which compresses query and document to fixed vectors independently).

**User-visible behavior:** The `--rerank` flag is absent by default. When used:
```bash
corpus search "validate JWT token with RSA key" --rerank --limit 5
```
The tool retrieves top-50 from LanceDB, passes all 50 `(query, chunk)` pairs to the cross-encoder, re-ranks, and returns the top-5. Latency increases by 200–500ms (TinyBERT-based cross-encoder on CPU for 20 docs), or 50ms for `cross-encoder/ms-marco-MiniLM-L-6-v2` on a modern CPU.

**Recommended model for offline use:** `cross-encoder/ms-marco-MiniLM-L-6-v2` from sentence-transformers. This model:
- Ships as a pre-trained Hugging Face model downloadable once, used offline
- Processes 20 candidates in ~50ms on CPU (MiniLM-L6 architecture)
- Is designed specifically for passage reranking (MS MARCO training data)
- Integrates via `sentence-transformers`: `CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2").predict(pairs)`
- Returns logits (not 0–1); apply sigmoid for score display

**Latency budget:** 50ms for re-ranking 20 candidates is acceptable for a CLI tool. The v2 MCP `corpus_search` response already adds chunk text to the payload, which is what the cross-encoder needs — no extra file reads required.

**Confidence:** HIGH (sentence-transformers docs confirm model, API, and CPU latency; MS MARCO model confirmed on sbert.net official docs)

### Table Stakes (if `--rerank` ships at all)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Optional, off by default | Adds 50–500ms latency — must be opt-in | LOW | CLI flag only; zero impact on users who don't use it |
| Works offline after one-time model download | Project constraint: offline/Ollama-first | LOW | sentence-transformers caches model to `~/.cache/huggingface/`. One-time 70MB download for MiniLM-L6. |
| Candidate set: top-50 from stage-1 | Diminishing returns above 50 candidates on CPU; corpus is local so top-50 covers well | LOW | `fetch_k=50` in stage-1 search; pass all 50 to cross-encoder; return top-k |

### Differentiators (for `--rerank`)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| `--rerank` flag with `cross-encoder/ms-marco-MiniLM-L-6-v2` | 20–35% accuracy improvement for complex natural language queries vs pure bi-encoder | MEDIUM | Requires `sentence-transformers` as a new optional dependency; add to `pyproject.toml` extras; lazy import so non-rerank users have zero overhead |
| LLM-based re-ranking via Ollama as alternative | Uses the already-configured Ollama instance; no new model download | HIGH | Ollama re-ranking adds 1–5 seconds latency (LLM inference per candidate). Only viable if candidate set is very small (top-5). NOT recommended as primary path. |

### Anti-Features (for `--rerank`)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Always-on re-ranking | Better results always | Adds 200–500ms to every search. For `--name`-filtered queries the user already knows the construct; bi-encoder ranking is sufficient and precise. Re-ranking adds cost without benefit when the user is not doing natural language retrieval. | Off by default; `--rerank` flag for when the user cares about ranking quality over latency |
| Re-ranking with a large cross-encoder (BERT-base or larger) | Better accuracy than MiniLM | On CPU, BERT-base takes 1.5+ seconds for 20 candidates. Unacceptable CLI latency. | MiniLM-L6 achieves 95%+ of BERT-base accuracy on MS MARCO with 10x faster inference |

---

## Feature Dependencies

```
[MMR diversity -- Cluster A]
    └──requires──> [v2 chunk-level results: start_line, end_line in LanceDB (CHUNK-01)]
    └──requires──> [candidate embeddings accessible for cosine sim, OR use RRF score as proxy]

[Contiguous sub-chunk merging -- Cluster A]
    └──requires──> [v2 sub-chunking: ClassName.method_name chunks (SUB-01, SUB-02, SUB-03)]
    └──requires──> [v2 start_line/end_line in search results (CHUNK-02)]
    └──independent of──> [MMR]

[--expand-graph -- Cluster B]
    └──requires──> [graph.sqlite with relationships table (v1.2, already shipped)]
    └──requires──> [GraphStore.search_paths() (v1.2, already shipped)]
    └──enhances──> [corpus search result display]

[corpus graph --depth N -- Cluster B]
    └──requires──> [GraphStore existing (v1.2)]
    └──extends──> [corpus graph <slug> (v1.2)]
    └──independent of──> [--expand-graph]

[Centrality scoring -- Cluster B]
    └──requires──> [graph.sqlite with indegree data (v1.2 relationships table)]
    └──requires──> [LanceDB schema v5: centrality column in chunk records]
    └──requires──> [corpus index computes and stores centrality at index time]
    └──enhances──> [hybrid search scoring]

[--within-graph -- Cluster B]
    └──requires──> [GraphStore BFS traversal (can reuse --depth N logic)]
    └──requires──> [search results have file_path for set membership check]
    └──independent of──> [centrality scoring]

[Multi-query --query --query -- Cluster C]
    └──requires──> [CorpusSearch.search() callable multiple times independently]
    └──requires──> [chunk_id or file_path+start_line as intersection key in results]
    └──independent of──> [graph features, MMR]

[--exclude-path -- Cluster C]
    └──requires──> [file_path in search result (already present)]
    └──independent of──> [everything else]

[Cross-source labeling -- Cluster D]
    └──requires──> [source_name stored in LanceDB chunk records (already present)]
    └──enhances──> [CLI result display, MCP corpus_search response]
    └──independent of──> [all other v3 features]

[--rerank -- optional]
    └──requires──> [chunk_text in search results (v2 CHUNK-03 MCP, or CHUNK-02 CLI)]
    └──requires──> [sentence-transformers installed (new optional dependency)]
    └──independent of──> [MMR, graph, multi-query]
    └──conflicts with──> [--max-per-file and MMR applied before rerank (apply diversity first, then rerank the diverse set)]
```

### Dependency Notes

- **Cross-source labeling has zero new dependencies** — `source_name` is already in LanceDB. This is the safest v3 feature to ship first.
- **Contiguous merging requires v2 to complete** — cannot merge adjacent method chunks if sub-chunking (SUB-01–SUB-03) is not yet in the index. Phase ordering: v2 closes, then contiguous merging.
- **Centrality scoring is the highest-dependency v3 feature** — requires a new LanceDB schema migration (v5) and changes to `corpus index`. Should be its own phase.
- **Multi-query AND intersection has no new dependencies** — pure Python post-processing on existing search. Low-risk to ship early in v3.
- **`--rerank` is fully independent** — can be its own phase, deferred if scope is tight. Optional dependency on `sentence-transformers` should be an extras group in `pyproject.toml`.
- **Graph features build on v1.2** — `graph.sqlite` and `GraphStore` already exist. `--expand-graph` and `--depth N` are extensions of existing infrastructure.

---

## MVP Definition for v3

### Launch With (v3 core)

The minimum that makes v3 a meaningful milestone — solves the "result flooding" problem and adds the most-asked-for graph UX:

- [ ] Cross-source labeling (CLI prefix + MCP `source` field) — zero risk, zero new dependencies
- [ ] `--exclude-path <glob>` — single post-filter, trivial to implement
- [ ] Same-file chunk cap (simplified diversity: `--max-per-file N`, default 3) — addresses the most common complaint without MMR complexity
- [ ] Contiguous sub-chunk merging — display quality fix for v2 method chunks
- [ ] `--expand-graph` on `corpus search` — surfaces graph neighbors alongside hits; 1 SQLite query per result
- [ ] `corpus graph --depth N` — extends existing `corpus graph` to recursive walks

### Add After Core Validates

Features that require more infrastructure or have higher risk:

- [ ] Full MMR with `--diversity` flag — needs numpy cosine sim on candidate embeddings or RRF-score proxy
- [ ] Multiple `--query` AND intersection — two search calls + set intersection
- [ ] `--within-graph <slug>` soft scope — BFS + score boosting
- [ ] Hub node labeling in graph walk — trivial addition once `--depth N` ships

### Defer to v3.x or v4

- [ ] Centrality scoring — requires LanceDB schema v5 migration + index-time computation; high value but high complexity; own milestone
- [ ] `--rerank` cross-encoder — requires new optional dependency; 20–35% quality gain for complex queries; useful but not blocking the core v3 goal

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Cross-source labeling (CLI + MCP) | HIGH — multi-source users | LOW — display only | P1 |
| `--exclude-path <glob>` | HIGH — test file exclusion | LOW — post-filter | P1 |
| Same-file chunk cap (`--max-per-file`) | HIGH — solves result flooding | LOW — post-filter | P1 |
| Contiguous sub-chunk merging | HIGH — display quality | LOW — sort+merge display pass | P1 |
| `--expand-graph` flag | HIGH — graph layer users | MEDIUM — SQLite lookups per result | P1 |
| `corpus graph --depth N` | HIGH — architectural analysis | MEDIUM — BFS traversal loop | P1 |
| Full MMR with lambda | MEDIUM — power users | MEDIUM — cosine sim computation | P2 |
| Multi-query AND intersection | MEDIUM — compound queries | MEDIUM — two search calls + intersect | P2 |
| `--within-graph <slug>` soft scope | MEDIUM — subsystem scoping | MEDIUM — BFS + score boost | P2 |
| Hub node labeling | LOW-MEDIUM — nice annotation | LOW — one aggregation query | P2 |
| `--rerank` cross-encoder | MEDIUM — accuracy for NL queries | MEDIUM — new optional dependency | P3 |
| Centrality scoring | HIGH (eventually) — hub-aware ranking | HIGH — schema v5 + index changes | P3 |

---

## Sources

- [OpenSearch Native MMR — OpenSearch 3.3 announcement](https://opensearch.org/blog/improving-vector-search-diversity-through-native-mmr/) — MEDIUM confidence (article confirms native MMR ships in OpenSearch 3.3; lambda parameter semantics confirmed)
- [Maximum Marginal Relevance — Full Stack Retrieval](https://community.fullstackretrieval.com/retrieval-methods/maximum-marginal-relevance) — MEDIUM confidence (search_type="mmr", k, fetch_k parameters confirmed; LangChain-LanceDB integration)
- [LanceDB LangChain integration docs — max_marginal_relevance_search](https://reference.langchain.com/v0.3/python/community/vectorstores/langchain_community.vectorstores.lancedb.LanceDB.html) — HIGH confidence (official LangChain API reference; `lambda_mult` parameter confirmed)
- [Pinecone — Rerankers and Two-Stage Retrieval](https://www.pinecone.io/learn/series/rag/rerankers/) — HIGH confidence (official Pinecone learning series; candidate set sizing, latency tradeoffs confirmed)
- [Sentence Transformers — Cross-Encoder MS MARCO models](https://www.sbert.net/docs/pretrained-models/ce-msmarco.html) — HIGH confidence (official sbert.net docs; MiniLM-L6 model confirmed offline-capable)
- [Sentence Transformers — Retrieve and Re-Rank](https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html) — HIGH confidence (official sbert.net example; two-stage pipeline implementation pattern)
- [ZeroEntropy — Reranking model guide 2026](https://www.zeroentropy.dev/articles/ultimate-guide-to-choosing-the-best-reranking-model-in-2025) — MEDIUM confidence (latency numbers: 50ms for TinyBERT/20 docs confirmed)
- [Axon — Graph-powered code intelligence engine](https://github.com/harshkedia177/axon) — MEDIUM confidence (blast radius BFS traversal pattern; `axon impact SYMBOL` with depth control)
- [GraphRAG — Microsoft local search pattern](https://microsoft.github.io/graphrag/) — MEDIUM confidence (fan-out to neighbors as local search pattern; community context)
- [Sourcegraph cross-repository code navigation](https://webflow.sourcegraph.com/blog/cross-repository-code-navigation) — MEDIUM confidence (source prefix display pattern in multi-repo search)
- [Milvus multi-vector hybrid search](https://milvus.io/docs/multi-vector-search.md) — MEDIUM confidence (multi-query AND composition via multiple AnnSearchRequest; RRF fusion; Python-level intersection is equivalent approach for LanceDB)
- [NetworkX in_degree_centrality documentation](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.centrality.in_degree_centrality.html) — HIGH confidence (official NetworkX docs; indegree centrality implementation)
- Project `PROJECT.md` direct audit — HIGH confidence (existing features, schema state, planned v3 requirements confirmed)

---

*Feature research for: v3 Intelligent Search — corpus-analyzer*
*Researched: 2026-02-24*

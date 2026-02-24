# Feature Research

**Domain:** Search precision controls — score display, sorting, and relevance filtering for a developer CLI search tool
**Researched:** 2026-02-24
**Confidence:** HIGH (existing code audited directly; CLI tool conventions verified against ripgrep, fzf, qmd, and Elasticsearch/OpenSearch documentation; RRF score semantics verified against LanceDB source behavior)

---

## Context: What Already Exists

The v1.3 codebase already has partial implementations of the v1.4 features. Understanding the current state is required before classifying what is "table stakes" vs "differentiator":

| Already built | State |
|--------------|-------|
| `--sort relevance\|construct\|confidence\|date\|path` on `corpus search` CLI | DONE — `engine.py` supports all five values |
| Score extracted into `SearchResult.score` in Python API | DONE — `float(r.get("_relevance_score", 0.0))` |
| Score passed through in MCP `corpus_search` result dict | DONE — `"score": float(row.get("_relevance_score", 0.0))` |
| Score displayed in CLI output | DONE — `score: {result.get('_relevance_score', 0.0):.3f}` in dim text inline with filename |
| `sort_by` parameter on `hybrid_search()` engine method | DONE |

What is **not** yet built:
- `--min-score` CLI flag (hard filter below a threshold)
- `min_score` parameter on Python `search()` API
- `min_score` parameter on MCP `corpus_search` tool
- `sort_by` parameter on Python `search()` API (engine supports it; API wrapper does not pass it through)
- `min_score` parameter on MCP `corpus_search` tool (same gap)

The v1.4 milestone is therefore narrower than it might appear: score display already works, `--sort` already works at the CLI layer, and both the API and MCP already receive scores. The remaining work is: add `--min-score` everywhere, and expose `sort_by` through the API and MCP wrappers.

---

## Critical Score Semantics Note

**RRF scores are not 0–1 normalized percentages.** LanceDB's `RRFReranker` produces `_relevance_score` values computed as `1 / (K + rank)` where K defaults to 60. For a result list of 10 items, scores range roughly from 0.0164 (rank 1) to 0.0099 (rank 10). Scores do not carry absolute meaning — they only encode relative rank within a single query's result set.

Consequences for feature design:
1. Displaying scores as-is (e.g., `score: 0.016`) is technically correct but confusing to users who expect 0–100% or 0–1.0 scales.
2. `--min-score` with RRF scores requires documentation: "0.01 is a reasonable threshold" is not intuitive. Users need either an example or a note that scores are rank-based.
3. The threshold is useful even with opaque scores — it lets users suppress near-miss results after observing the score column in practice.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features a developer search tool must have. Missing these makes the milestone feel incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Score visible in CLI output per result | Users need to see scores to calibrate a min-score threshold; invisible scores make filtering unintuitive | LOW | Already done inline as dim text. Acceptable as-is; no change required unless formatting is improved. |
| `--min-score <float>` on `corpus search` CLI | Every comparable semantic search tool (qmd, Elasticsearch, OpenSearch) exposes a score cutoff flag; users reaching for precision controls expect this lever | LOW | Filter applied post-retrieval, before rendering; one guard clause in `search_command()` |
| `min_score` parameter on Python `search()` API | API users (scripts, agents) need parity with CLI; inconsistent APIs break the principle of one engine powering all surfaces | LOW | Pass-through to `hybrid_search()` which then filters; `SearchResult` already includes `score` |
| `min_score` parameter on MCP `corpus_search` tool | Claude Code and other MCP clients issue search calls that may return noise at the bottom of the list; exposing `min_score` gives agents control without requiring workarounds | LOW | One new optional parameter on the `@mcp.tool` function; filter applied same as CLI |
| `sort_by` parameter on Python `search()` API | `hybrid_search()` engine already supports `sort_by`; the `search()` wrapper does not pass it through — this is a parity gap, not a new feature | LOW | Add `sort_by: str = "relevance"` kwarg and pass to `hybrid_search()` |

### Differentiators (Competitive Advantage)

Features that add user value beyond baseline parity.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Score column format with contextual hint | Show score value plus a dim note "(rank-based, not %) " the first time it appears — prevents user confusion about what 0.016 means | LOW | One-time inline note in CLI output; does not apply to API/MCP (machine consumers) |
| `--sort path` as explicit default alternative | Users scanning results alphabetically (e.g., diffing two queries) benefit from stable path ordering; ripgrep users expect this convention | LOW | Already implemented in engine and CLI; no additional work |
| `sort_by` parameter on MCP `corpus_search` tool | Agents requesting deterministic orderings (e.g., always path-sorted for diffing) can get consistent results without post-processing | LOW | One new optional parameter alongside `min_score`; follows same pattern |

### Anti-Features (Commonly Requested, Often Problematic)

Features that appear useful but create more problems than they solve in this context.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Percentage-style score display (0–100%) | Users expect scores to read like similarity percentages | RRF scores are rank-based, not similarity measures. Displaying `0.016` as `1.6%` implies near-zero similarity; displaying `(rank 1 of 10)` as `100%` is dishonest. Any normalization to 0–100% would be per-query minmax, making scores incomparable across queries and misleading for `--min-score` thresholds. | Display raw RRF score with a one-time parenthetical note that scores are rank-based |
| `--min-score` with a smart default above 0 | Seems user-friendly: "auto-filter junk" | The score at which a result is "junk" is query-dependent and corpus-dependent. A default of 0.01 might discard all results for some queries and include all results for others. Silent filtering without user intent surprises users who get no results and can't tell why. | Default to 0 (no filtering) and document with an example threshold |
| Caching `--sort path` results separately from `--sort relevance` | Performance optimization for repeated queries | Adds caching complexity for a tool that already completes in under a second; the LanceDB index is embedded (no network call for sorted results). Single-threaded sort penalty that ripgrep documents does not apply here — corpus is not a grep-over-files operation. | No caching; sort is a post-retrieval in-memory sort on a list that is already limited to ≤20 results |
| `--sort score` as a separate flag from `--sort relevance` | Users want explicit score-based sorting | Relevance order IS score descending for RRF — the two are synonymous. A separate `--sort score` flag would do identical work and confuse the semantics. | Keep `--sort relevance` as the canonical name; document that it means "highest RRF score first" |
| Interactive TUI score slider (fzf-style) | Power users want to explore score thresholds interactively | Significant complexity (requires a TUI library or fzf integration); the target user is already comfortable with flags. The corpus tool's value is CLI + MCP programmatic access, not interactive TUI. | Document that users can iterate: run with `--min-score 0`, observe scores, re-run with threshold |

---

## Feature Dependencies

```
[Score display in CLI output]
    └──already done──> no dependency

[--min-score CLI flag]
    └──requires──> [Score already in result dict (_relevance_score)]  ← already done
    └──independent of──> [--sort flag]  ← already done

[min_score on Python search() API]
    └──requires──> [SearchResult.score already populated]  ← already done
    └──mirrors──> [--min-score CLI flag logic]

[min_score on MCP corpus_search tool]
    └──requires──> [score in MCP result dict]  ← already done
    └──mirrors──> [--min-score CLI flag logic]

[sort_by on Python search() API]
    └──requires──> [sort_by on hybrid_search() engine]  ← already done
    └──independent of──> [min_score]

[sort_by on MCP corpus_search tool]
    └──requires──> [sort_by on hybrid_search() engine]  ← already done
    └──independent of──> [min_score]
```

### Dependency Notes

- **`--min-score` is independent of `--sort`**: filtering happens after retrieval, before sorting. Either can be used alone. Order of operations: `hybrid_search()` retrieves ranked results → filter by min_score → sort by sort_by → render/return.
- **All three surfaces share the same engine**: the filter logic should live in `hybrid_search()` (not duplicated in CLI, API, and MCP). One parameter addition to `hybrid_search()`, three thin callers updated.
- **API `sort_by` gap is trivially closed**: the engine already accepts it; the `search()` wrapper just doesn't forward it. No new design needed.

---

## MVP Definition

### Launch With (v1.4)

These five items constitute the complete v1.4 scope. All are required — the milestone goal is full parity across CLI, API, and MCP.

- [ ] `--min-score <float>` on `corpus search` CLI — core user-facing feature
- [ ] `min_score` parameter on `hybrid_search()` engine method — single implementation point
- [ ] `min_score` parameter on Python `search()` API — API parity
- [ ] `min_score` parameter on MCP `corpus_search` tool — MCP parity
- [ ] `sort_by` parameter on Python `search()` API — closes existing parity gap

### Add After Validation (v1.x)

- [ ] `sort_by` on MCP `corpus_search` tool — low-value for agent consumers unless a specific use case is identified; agents typically prefer relevance order and apply their own sorting

### Future Consideration (v2+)

- [ ] Score normalization experiment — if users consistently report confusion about score values, a per-query minmax normalization could be added as an opt-in display mode (never affects filtering logic)
- [ ] Interactive `--min-score` tuning via fzf integration — explore if TUI users become a significant segment
- [ ] Chunk-level score display — when chunk-level results ship (v2 candidate per PROJECT.md), scores per chunk become more meaningful than per-file scores

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| `--min-score` CLI flag | HIGH — primary user-facing control | LOW — one guard clause, one CLI param | P1 |
| `min_score` on `hybrid_search()` engine | HIGH — single source of truth | LOW — one parameter, one filter | P1 |
| `min_score` on Python `search()` API | HIGH — API consumers need parity | LOW — pass-through, no new logic | P1 |
| `min_score` on MCP `corpus_search` | HIGH — agent consumers reduce noise | LOW — one optional parameter | P1 |
| `sort_by` on Python `search()` API | MEDIUM — closes parity gap | LOW — kwarg passthrough only | P1 |
| Score format with contextual hint | MEDIUM — reduces user confusion about RRF scores | LOW — one line in CLI formatter | P2 |
| `sort_by` on MCP `corpus_search` | LOW — agents rarely need sorted order | LOW — one optional parameter | P2 |

**Priority key:**
- P1: Required for v1.4 milestone
- P2: Nice to have, add if time permits or if specifically requested
- P3: Future consideration

---

## Competitor Feature Analysis

| Feature | ripgrep (`rg`) | qmd (local doc search) | codespelunker (`cs`) | Corpus v1.4 Approach |
|---------|---------------|----------------------|---------------------|----------------------|
| Score display | Not applicable (exact match, no ranking score) | Yes — color-coded percentage per result | Results ordered by rank; scores not shown by default | Already shown as `score: 0.016` inline with result; keep as-is |
| Sorting | `--sort path\|modified\|accessed\|created\|none` | Automatic descending by relevance; no override | `--ranker` algorithm selection; no post-retrieval sort flag | `--sort relevance\|construct\|confidence\|date\|path` already done |
| Min-score threshold | Not applicable | `--min-score <num>` (default 0) | Not exposed | Add `--min-score <float>` (default 0.0) |
| API parity with CLI | Not applicable | `--json` output for scripting | `--json` output for scripting | `search()` Python API + MCP tool; `min_score` and `sort_by` must match CLI |
| Score semantics transparency | Not applicable | Shown as percentage but is internally normalized RRF | Rank-ordered, score not surfaced | Raw RRF score with optional inline note about rank-based nature |

---

## Sources

- Direct audit of `/src/corpus_analyzer/search/engine.py`, `/src/corpus_analyzer/api/public.py`, `/src/corpus_analyzer/mcp/server.py`, `/src/corpus_analyzer/cli.py` — HIGH confidence
- [qmd CLI tool — `--min-score` flag and score display](https://github.com/tobi/qmd) — MEDIUM confidence (via WebFetch of README)
- [codespelunker (`cs`) — filtering and ranking flags](https://github.com/boyter/cs) — MEDIUM confidence (via WebFetch of README)
- [ripgrep `--sort` flag behavior and parallelism trade-off](https://github.com/BurntSushi/ripgrep/blob/master/FAQ.md) — HIGH confidence (multiple sources agree)
- [Elasticsearch: semantic precision with min_score](https://www.elastic.co/search-labs/blog/semantic-precision-minimum-score) — HIGH confidence (official Elastic blog)
- [LanceDB RRFReranker `_relevance_score` field](https://docs.lancedb.com/integrations/reranking/rrf) — MEDIUM confidence (official docs; score formula inferred from RRF algorithm K=60 constant)
- [OpenSearch hybrid search and RRF](https://opensearch.org/blog/introducing-reciprocal-rank-fusion-hybrid-search/) — HIGH confidence (official OpenSearch blog)

---
*Feature research for: v1.4 Search Precision — score display, sorting, min-score filtering*
*Researched: 2026-02-24*

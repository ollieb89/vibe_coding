# Project Research Summary

**Project:** corpus-analyzer v1.4 — Search Precision
**Domain:** Hybrid search precision controls (score display, sort, min-score filtering) across CLI/API/MCP surfaces
**Researched:** 2026-02-24
**Confidence:** HIGH

## Executive Summary

Corpus-analyzer v1.4 adds relevance score visibility and filtering to the existing LanceDB hybrid search system. The core insight from research is that most of the required features are already partially or fully implemented in v1.3: `_relevance_score` is already populated by the RRFReranker, already displayed in the CLI, already captured in `SearchResult.score`, and already returned by the MCP server. The remaining gap is narrow — only `--min-score` filtering and the passthrough of `sort_by`/`min_score` through the Python API and MCP wrappers remain to be built.

The recommended approach is to implement all changes as a single cohesive layer-by-layer update, starting at the engine (the single source of truth), then wiring each caller (API, MCP, CLI) in the same phase. No new libraries or schema migrations are required. All filtering must be done as post-retrieval Python list comprehensions — LanceDB's `.where()` cannot reference `_relevance_score` because it is a reranker-computed column injected after retrieval, not a stored schema field. There is no LanceDB-native sort or score threshold API for hybrid search.

The primary risk is UX confusion around RRF score semantics. RRF scores are not percentages — the practical range is approximately 0.009–0.033, and thresholds that work for one query may filter everything or nothing on another. This must be documented in `--min-score` help text from the first commit, with a default of 0.0 (no filtering). A secondary risk is cross-surface parity: v1.4 requirements explicitly require CLI, Python API, and MCP to all expose the same controls. Implementing one surface without the others would be an incomplete milestone.

## Key Findings

### Recommended Stack

No new technologies are required for v1.4. All changes are pure Python modifications to the existing stack. LanceDB 0.29.2 already provides `_relevance_score` on every hybrid search result via `RRFReranker(return_score="relevance")`. Typer and FastMCP already have the infrastructure to accept new optional parameters. Rich already formats the score column correctly at `:.3f` precision.

**Core technologies (unchanged):**
- **LanceDB 0.29.2:** Hybrid BM25+vector search; `RRFReranker` injects `_relevance_score` as `pa.float32()` into every result row — no API changes needed; `LanceHybridQueryBuilder` has no native sort or score-filter method (verified by source inspection)
- **Typer 0.12+:** CLI option parsing; add `--min-score` as a `float` option with default `0.0`
- **Rich 13.7+:** Terminal formatting; score already displayed at `:.3f` on cli.py:366 — no format change needed
- **FastMCP 2.14.4+:** MCP server; add `min_score: Optional[float] = None` with `# noqa: UP045` to match existing parameter pattern in `corpus_search()`

**Critical implementation note:** Post-retrieval Python sorting and filtering is the correct and only approach. LanceDB's `LanceHybridQueryBuilder` exposes no `sort_by`, `order_by`, or score-predicate methods for hybrid search.

### Expected Features

The v1.4 scope is well-bounded. Score display is already done. The remaining work is the `min_score` filter and closing the API/MCP parity gap on `sort_by`.

**Must have (table stakes — required for v1.4 milestone):**
- `--min-score <float>` on `corpus search` CLI — primary user-facing precision control; default 0.0 with RRF range documented in help text
- `min_score` parameter on `hybrid_search()` engine — single implementation point; filters all surfaces; applied after text-match gate, before sort
- `min_score` parameter on Python `search()` API — required for milestone parity; currently absent
- `min_score` parameter on MCP `corpus_search` tool — required for milestone parity; currently absent
- `sort_by` parameter on Python `search()` API — closes existing parity gap; engine already supports it, wrapper does not forward it

**Should have (add if time permits):**
- Contextual hint in CLI score display explaining RRF rank-based nature — reduces user confusion about 0.016 scores
- `sort_by` parameter on MCP `corpus_search` tool — useful for agents needing deterministic ordering; low priority for agent consumers

**Defer (v2+):**
- Score normalisation to 0–1 range — only if UX testing shows consistent user confusion; per-query minmax is misleading for cross-query comparisons
- Interactive `--min-score` tuning (fzf-style TUI) — significant complexity, niche audience
- Chunk-level score display — only meaningful when chunk-level results ship in v2

**Anti-features to avoid:**
- Percentage-style score display (0–100%) — RRF scores are rank-based, not similarity measures; normalisation would be dishonest and make `--min-score` thresholds meaningless across queries
- `--min-score` default above 0.0 — silent filtering without user intent breaks queries and surprises users with empty results
- Separate `--sort score` flag — `--sort relevance` is already synonymous with score-descending ordering; a duplicate flag would confuse semantics
- Narrowing `_VALID_SORT_VALUES` in the engine to only `{relevance, path}` — existing `construct`, `confidence`, `date` sort modes are already shipped and tested; only the CLI help text should scope to `relevance|path`

### Architecture Approach

The pipeline has a clear layered structure: LanceDB retrieves results with RRFReranker injecting `_relevance_score`, the engine applies post-retrieval filtering and sorting in Python, and three thin callers (CLI, API, MCP) pass parameters down and render results up. The engine is the single source of truth for validation and filtering logic. All new v1.4 parameters should be added at the engine layer first with additive defaults, then wired through each caller. No new files or modules are needed.

**Major components (all modified in-place):**
1. `search/engine.py` — add `min_score: float = 0.0`; insert filter step after text-match gate (~line 104), before sort block (~line 106)
2. `api/public.py` — add `sort_by: str = "relevance"` and `min_score: float = 0.0` to `search()`; pass both to `hybrid_search()`
3. `mcp/server.py` — add `min_score: Optional[float] = None` to `corpus_search()`; pass as `min_score or 0.0` to engine
4. `cli.py` — add `--min-score` Typer option; pass `min_score` to `hybrid_search()`; update `--sort` help text to feature `relevance|path`

**Architectural patterns to follow:**
- Additive defaults: new parameters use defaults that reproduce current v1.3 behaviour exactly — existing callers require no changes
- Post-retrieval filter: score thresholding in Python after `.to_list()`, not as a LanceDB `.where()` predicate
- Thin caller passthrough: CLI/API/MCP pass parameters to engine without re-validating; engine owns `_VALID_SORT_VALUES` and filter logic

### Critical Pitfalls

1. **RRF score used as an absolute cross-query threshold** — Scores range approximately 0.009–0.033 and are relative to a single query's result set. A threshold calibrated on one query misfires on another. Prevention: default to 0.0, document the range in `--min-score` help text from the first commit, never recommend a specific threshold value in docs. Tell users to run without `--min-score` first, observe scores, then calibrate.

2. **`min_score` implemented via LanceDB `.where()` predicate** — `_relevance_score` is not a stored schema column; it is injected by `RRFReranker` after retrieval. Using it in `.where()` causes a runtime error or silent no-op. Prevention: always apply as a Python list comprehension after `.to_list()` and after the text-match gate, not before it.

3. **API surface left behind — parity gap persists into v1.5** — This gap already exists for `sort_by` in v1.3: `api/public.py:search()` does not forward `sort_by` to the engine. Implementing CLI + MCP without the API wrapper is an incomplete milestone. Prevention: implement all three surfaces atomically in the same phase. Do not accept "API to follow" as a plan.

4. **`SearchResult` exact-set test breaks on any new field** — `tests/api/test_public.py:18` uses `==` (not superset check) against `{"path", "file_type", "construct_type", "summary", "score", "snippet"}`. Any new field causes immediate CI failure. Prevention: update the test in the same commit as any `SearchResult` field change. For v1.4, no new fields should be added — `score` already exists.

5. **FastMCP `# noqa: UP045` pattern omitted on new parameter** — The existing `corpus_search()` parameters all use `Optional[X]` with `# noqa: UP045`. Adding `min_score` without the noqa comment fails `uv run ruff check .`. Prevention: copy the existing parameter pattern exactly: `min_score: Optional[float] = None,  # noqa: UP045`.

## Implications for Roadmap

The scope is small and dependencies are clear. A two-phase approach is recommended: engine first, then all three callers together in one atomic phase.

### Phase 1: Engine Min-Score Filter

**Rationale:** The engine is the hard dependency for all three caller layers. Implementing and testing here first means CLI, API, and MCP work can proceed with confidence. The additive default (`min_score=0.0`) ensures zero regression against the 281 existing tests.

**Delivers:** `CorpusSearch.hybrid_search()` with `min_score: float = 0.0` parameter; Python list comprehension filter after text-match gate and before sort block; unit tests covering: 0.0 returns all results, 99.0 returns empty list, seeded score data filters correctly.

**Addresses:** `--min-score` core capability (P1 table stakes item #2 from FEATURES.md)

**Avoids:** Pitfall 2 (`.where()` predicate approach — filter is Python, not LanceDB); Pitfall 1 (score semantics — engine tests use real RRF score values to verify behaviour, not hardcoded 0.016 thresholds)

### Phase 2: API, MCP, and CLI Parity

**Rationale:** All three caller surfaces must ship together to satisfy the v1.4 milestone requirement. Pitfall 3 (API surface left behind) is explicitly prevented by treating this as one atomic phase. Engine changes from Phase 1 are a hard prerequisite. The `sort_by` parity gap for the Python API also closes here.

**Delivers:**
- Python `search()` API with `sort_by: str = "relevance"` and `min_score: float = 0.0` parameters — closes existing parity gap
- MCP `corpus_search` tool with `min_score: Optional[float] = None` and `# noqa: UP045`
- CLI `--min-score` Typer option (type `float`, default `0.0`) with RRF score range documented in help text
- CLI empty-result hint when `min_score` filters all results: "No results above {min_score}. Run without --min-score to see available scores."
- Updated `--sort` help text featuring `relevance|path` (existing sort values unchanged in engine)
- All affected `assert_called_once_with` tests updated to include new kwargs (`sort_by`, `min_score`)

**Uses:** Typer (CLI option), FastMCP (tool parameter pattern), Rich (score format already done)

**Avoids:** Pitfall 3 (parity gap — all three surfaces in one phase); Pitfall 4 (SearchResult test — no new fields added, existing `score` field used); Pitfall 5 (noqa pattern — copy existing `corpus_search()` parameter style); Pitfall 1 (score range caveat required in `--min-score` help text from first commit)

### Phase Ordering Rationale

- Engine must come before callers: callers forward `min_score` to `hybrid_search()`; the parameter must exist at the engine layer first
- CLI, API, and MCP must not be split across phases: the milestone requirement is explicit cross-surface parity; splitting produces a state where the milestone is "partially done" with no clean verification point
- Score display needs no phase: it is already fully implemented in v1.3 across all three surfaces; the roadmap should verify this is correct but plan no implementation work for it

### Research Flags

No phases require `/gsd:research-phase` during planning. All implementation details are resolved by this research.

Phases with standard patterns (no additional research needed):
- **Phase 1 (Engine):** Insertion point is precisely identified (after text-match gate ~line 104, before sort block ~line 106); existing text-match gate is the model; additive default pattern is clear
- **Phase 2 (Callers):** Thin passthrough pattern is well-established; existing `--sort` wiring in CLI is the template; FastMCP parameter pattern is already present in `corpus_search()` for all other optional params

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Verified against LanceDB 0.29.2 installed source; `LanceHybridQueryBuilder` methods enumerated by direct inspection; `RRFReranker.rerank_hybrid()` score column behaviour confirmed; no external sources needed |
| Features | HIGH | Current codebase audited line-by-line; existing partial implementations confirmed; competitor analysis (ripgrep, qmd, Elasticsearch) validates UX conventions; scope is narrow with explicit milestone checklist |
| Architecture | HIGH | All findings from direct source inspection of engine, API, MCP, CLI files; insertion points identified by line number; test contracts enumerated by test name and line |
| Pitfalls | HIGH | RRF score semantics confirmed by Azure AI Search official docs and LanceDB docs; code-inspection pitfalls confirmed by reading actual test assertions; FastMCP issue #1015 identified from GitHub |

**Overall confidence:** HIGH

### Gaps to Address

- **RRF score range under different `--limit` values:** The range 0.009–0.033 is calibrated at `limit=10`. At higher limits, the distribution spreads differently. The `--min-score` help text should note that scores vary with `--limit`. Low risk — the 0.0 default means this only affects users who explicitly set a threshold.

- **FastMCP optional parameter default handling (issue #1015):** A known FastMCP issue sometimes causes optional parameters with non-None defaults to receive `None` at the MCP boundary. For `min_score: Optional[float] = None`, this is not a problem (None is the intended default, handled by `min_score or 0.0`). Verify with a live MCP test after implementation.

- **`sort_by` on MCP:** The milestone spec does not explicitly require `sort_by` on the MCP tool (only `min_score` and CLI/API `sort_by`). Classified as P2. The roadmap should mark this optional and note it was deferred to v1.x if not included in v1.4.

## Sources

### Primary (HIGH confidence)

- `src/corpus_analyzer/search/engine.py` — `hybrid_search()` signature, `_VALID_SORT_VALUES`, post-sort block, text-match gate position (direct inspection)
- `src/corpus_analyzer/api/public.py` — `SearchResult` dataclass (6 fields), `search()` signature, missing `sort_by` and `min_score` gap confirmed (direct inspection)
- `src/corpus_analyzer/mcp/server.py` — `corpus_search()` params, existing `Optional[X] # noqa: UP045` pattern, score extraction at line 95 (direct inspection)
- `src/corpus_analyzer/cli.py` lines 300–373 — `search_command()` params, score display at line 366, `--sort` flag (direct inspection)
- `src/corpus_analyzer/store/schema.py` — `ChunkRecord` fields; confirms `_relevance_score` not a stored column (direct inspection)
- LanceDB 0.29.2 installed source — `LanceHybridQueryBuilder` method list (no sort/filter confirmed); `RRFReranker.rerank_hybrid()` column injection confirmed
- `tests/api/test_public.py:18` — exact-set field assertion confirmed as `==` not superset
- `tests/search/test_engine.py:282` — `TestHybridSearchSort` class; 7 sort tests that must remain green
- Azure AI Search hybrid scoring documentation — RRF score range formula and cross-query variability confirmed

### Secondary (MEDIUM confidence)

- [qmd CLI tool](https://github.com/tobi/qmd) — `--min-score` flag and score display UX conventions
- [codespelunker `cs`](https://github.com/boyter/cs) — filtering and ranking flag comparison
- [ripgrep `--sort` flag behavior](https://github.com/BurntSushi/ripgrep/blob/master/FAQ.md) — sort flag UX conventions
- [OpenSearch hybrid search and RRF](https://opensearch.org/blog/introducing-reciprocal-rank-fusion-hybrid-search/) — RRF score characteristics

### Tertiary (LOW confidence)

- FastMCP GitHub issue #1015 — optional parameter default handling edge case; not yet verified against FastMCP 2.14.4+ in this project; verify post-implementation with a live MCP test

---
*Research completed: 2026-02-24*
*Ready for roadmap: yes*

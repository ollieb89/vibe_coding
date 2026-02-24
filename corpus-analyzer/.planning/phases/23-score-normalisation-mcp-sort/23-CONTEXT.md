# Phase 23: Score Normalisation and MCP Sort - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Normalise raw RRF scores to a consistent 0–1 range across all search surfaces (CLI `corpus search`, Python API `SearchResult.score`, MCP `corpus_search`). Add `sort_by` parameter parity to MCP `corpus_search`. Extend `test_round_trip.py` with Python class and TypeScript class fixtures to close the Phase 20-21 round-trip test gap. Score presentation and MCP interface only — no new search capabilities.

</domain>

<decisions>
## Implementation Decisions

### Score normalisation formula
- Fixed linear scale: divide raw RRF score by ~0.033 (observed two-list fusion ceiling: 1/60 + 1/60)
- After dividing, clamp result to [0.0, 1.0] to guard against edge cases if RRF parameters change
- Do NOT use min-max per query (scores must be comparable across separate searches)

### Normalisation location
- Apply normalisation at the search layer — the function that constructs `SearchResult` objects
- One place to change; CLI, Python API, and MCP all automatically receive normalised scores
- Do NOT normalise independently at each consumer surface

### MCP sort_by parameter
- Add `sort_by` as an **optional** parameter in the MCP tool schema with a description listing valid values: `relevance | construct | confidence | date | path`
- Default when omitted: `relevance` (matches CLI default)
- Sort direction is **fixed per sort key** — no separate `sort_order` parameter
- This matches existing CLI behaviour

### MCP response schema
- Keep the existing `score` field name unchanged — silent upgrade to 0–1 range
- Do NOT add `raw_score` or rename to `normalised_score`
- No breaking change for existing MCP callers

### Claude's Discretion
- Exact RRF constant value (0.033 vs derived from k=60 two-list formula) — pick whichever matches the actual RRF implementation in the codebase
- Round-trip fixture design (Python class and TypeScript class shape, method count) — use minimal but realistic fixtures that exercise `ClassName.method_name` chunk paths
- `--min-score` backwards compatibility handling — update help text to reference 0–1 range; whether to warn users about changed thresholds is implementation discretion

</decisions>

<specifics>
## Specific Ideas

- The normalisation constant should be derived from or documented alongside the actual `k` parameter used in the RRF implementation — keep them co-located so they don't drift
- MCP schema description for `sort_by` should list all five valid values explicitly so LLM callers can discover them without guessing

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 23-score-normalisation-mcp-sort*
*Context gathered: 2026-02-24*

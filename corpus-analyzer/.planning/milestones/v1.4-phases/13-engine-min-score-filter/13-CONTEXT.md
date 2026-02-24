# Phase 13: Engine Min-Score Filter - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Add `min_score: float = 0.0` parameter to `CorpusSearch.hybrid_search()`. Apply post-retrieval Python list comprehension filter. Unit tests only. No CLI, API, or MCP changes — those are Phase 14.

</domain>

<decisions>
## Implementation Decisions

### Threshold semantics
- Operator is `>=` (inclusive) — a result at exactly `min_score` passes the filter
- Matches standard search tool convention (Elasticsearch, OpenSearch, etc.)
- Avoids user surprise when threshold is calibrated from an observed score

### Zero default contract
- `min_score=0.0` is a guaranteed no-op — returns identical results to not filtering
- Any real RRF score is > 0.0, so this is a hard zero-regression guarantee for existing callers
- Default must be 0.0 (not None) — callers should not need to handle optional

### Filter placement in pipeline
- Filter is applied **after** the existing text-match gate, **before** the sort block
- Consistent with the existing pipeline order (text gate → score filter → sort)
- Do not apply before text-match gate

### Post-filter sort
- Sort the remaining survivors normally — min_score just shrinks the pool
- Sort ordering logic is unchanged

### Claude's Discretion
- Exact Python expression for the filter (`score >= min_score` in a list comprehension)
- Whether to add a comment explaining RRF score range at the filter site
- Test fixture approach (seeded mock scores vs real RRF values)

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches for the list comprehension and test design.

</specifics>

<deferred>
## Deferred Ideas

- Input validation for negative `min_score` values — not discussed; Claude's discretion (recommend: accept silently, since 0.0 default covers the common case and negative values are a no-op)
- CLI empty-result hint — Phase 14
- API/MCP parity — Phase 14

</deferred>

---

*Phase: 13-engine-min-score-filter*
*Context gathered: 2026-02-24*

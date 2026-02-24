# Phase 14: API / MCP / CLI Parity - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire `min_score` filtering and `sort_by` ordering into all three call surfaces: CLI `corpus search`, Python `search()` API, and MCP `corpus_search` tool. Phase 13 built the engine capability; this phase exposes it uniformly. No new engine logic — interface parity only.

</domain>

<decisions>
## Implementation Decisions

### sort_by values
- Valid values: `score`, `date`, `title`
- Default when omitted: `score`
- Invalid values raise `ValueError` with a message listing valid options

### sort_by exposure
- `--sort-by` flag added to CLI `corpus search` in this phase (full parity across all three surfaces)
- `sort_by` parameter on Python `search()` API
- `sort_by` parameter on MCP `corpus_search` tool

### Claude's Discretion
- Empty-results hint behavior for Python API and MCP (only CLI hint message was specified in requirements)
- `--min-score` help text depth and RRF explanation wording
- MCP response shape when `min_score` filters all results

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches for the undiscussed areas.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 14-api-mcp-cli-parity*
*Context gathered: 2026-02-24*

# Phase 19: MCP Chunk Response - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Modify the `corpus_search` MCP tool to return self-contained result objects: add `text` (full untruncated chunk content), `start_line`, and `end_line` to each result. An LLM caller should need no follow-up file-read to understand a result. Creating new MCP tools and sub-chunking are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Existing preview field
- Remove the existing truncated ~200-char preview field entirely — `text` makes it redundant
- Removal is safe: no existing MCP callers depend on it
- Scope is isolated to `corpus_search` only — no other tools return the preview field
- Add a test assertion that the preview field does NOT appear in results (guard against regression)

### Field naming
- New fields named exactly as spec: `text`, `start_line`, `end_line`
- No alternatives (`content`, `chunk_text`, `lines` object) — spec names are final

### Response field ordering
- `text` appears first, then `start_line`, then `end_line`
- Content-first ordering: what an LLM reads should come before metadata

### Schema documentation
- Add descriptions to the result type/schema documenting that `text` is the full untruncated chunk body
- Document `start_line`/`end_line` as source file line boundaries for navigation
- Aim: LLM callers understand field purpose without guessing

### Claude's Discretion
- Legacy row handling: `text` returns empty string (locked by success criteria); `start_line`/`end_line` values for legacy rows (0 vs null vs omitted)
- Whether to add a `is_legacy` indicator or keep legacy rows silent
- Exact wording of schema field descriptions
- Test fixture design for legacy row assertions

</decisions>

<specifics>
## Specific Ideas

- No specific references or "I want it like X" moments — open to standard MCP result patterns
- The self-contained result design goal is clear: LLM caller should never need to call a file-read tool after receiving a search result

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 19-mcp-chunk-response*
*Context gathered: 2026-02-24*

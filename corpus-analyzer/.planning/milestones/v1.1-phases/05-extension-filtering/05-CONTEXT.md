# Phase 5: Extension Filtering - Context

**Gathered:** 2026-02-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Users control which file types get indexed per-source via `extensions = [".md", ".py"]` in a source block in `corpus.toml`. When no extensions are configured for a source, a default allowlist applies. The indexer silently skips non-allowlisted files. Changing the extensions config and re-running `corpus index` reconciles the index.

</domain>

<decisions>
## Implementation Decisions

### Re-indexing behavior
- On every `corpus index` run, purge files from the index that are no longer covered by the current extension config for that source
- The index always reflects what the current config allows — no stale entries
- Show a count summary when files are removed: e.g. "Removed 12 files no longer in extension allowlist."
- On first index of a source (when default allowlist applies), always display the active extension list so the user knows what defaults are in effect and can adjust `corpus.toml` if needed

### Claude's Discretion
- Config edge case handling (empty list, typo extensions, missing dot prefix) — handle gracefully
- Extension format normalization (case sensitivity, leading dot)
- Verbose flag behavior for subsequent runs
- Internal implementation of per-source reconciliation

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-extension-filtering*
*Context gathered: 2026-02-23*

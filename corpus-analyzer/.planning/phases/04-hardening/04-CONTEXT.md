# Phase 4: Defensive Hardening - Context

**Gathered:** 2026-02-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix all silent failure paths and crash risks identified in the v1.0 audit, and clear accumulated tech debt before archiving the milestone. This phase does not add new features — it hardens existing behaviour and cleans up deferred items.

Specific audit items in scope:
- CLI-02-partial: `result['_relevance_score']` direct key access (KeyError risk) → 1-line fix
- INGEST-07-silent: bare `except Exception: pass/return {}` in `_delete_stale_chunks()` and `_get_existing_files()`
- MCP-02-silent: OSError silently swallowed in `full_content` → no error signal to MCP client
- Tech debt: `needs_reindex()` dead code, redundant FTS rebuild, `use_llm_classification` unexposed, `DATA_DIR` dual source-of-truth
- Process: retroactive VERIFICATION.md files for phases 1–3

</domain>

<decisions>
## Implementation Decisions

### MCP error signaling
- When `full_content` cannot read a file (OSError): **both** log a warning server-side AND return a `content_error` field in the response
- `content_error` contains a human-readable error message string (e.g. `"File not found: /path/to/file"`)
- `content_error` is **omitted from the response when there is no error** (not included as null or empty string)
- For the indexer's silent swallow (stale chunk deletion, `_get_existing_files`): **log warning only** — these are internal operations with no caller-facing return, so `logging.warning()` is sufficient

### use_llm_classification exposure
- Expose as a **config key only** — add `use_llm_classification: bool` to `SourceConfig`, consistent with how `summarize` works (SUMM-03 pattern)
- Default value: `False` — preserves current behaviour, users opt in per source
- No CLI flag and no API parameter override — `SourceConfig` is the single control point

### DATA_DIR consolidation
- Move `DATA_DIR` definition to `config/schema.py` — the natural owner of data paths alongside `CorpusConfig`
- Both `cli.py` and `api/public.py` import from `config/schema.py`
- `mcp/server.py` already imports from `cli.py` — update it to import from `config/schema.py` too
- Variable name stays `DATA_DIR` — no rename (reduces churn, already used in existing imports)

### Retroactive VERIFICATION.md
- Write VERIFICATION.md for phases 1, 2, and 3 as part of Phase 4
- Detail level: **summary-level** — extract requirement IDs and status from existing SUMMARY.md frontmatter and the audit data; mark files as retroactive
- These capture the audit trail before v1.0 is archived

### Claude's Discretion
- Exact warning message wording in `logging.warning()` calls
- Whether to add a single `content_error: Optional[str]` field or restructure the MCP response dict
- Order of operations when writing retroactive VERIFICATION.md (which phase first)

</decisions>

<specifics>
## Specific Ideas

- The `content_error` field pattern mirrors how tools like LanceDB surface partial failures: present only when relevant, string message sufficient
- Retroactive VERIFICATION.md files should note "retroactively captured" in their frontmatter so the audit trail is honest

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-hardening*
*Context gathered: 2026-02-23*

# Phase 3: Agent Interfaces - Context

**Gathered:** 2026-02-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Expose the Phase 2 search engine to external consumers via two interfaces: an MCP server (for Claude Code and other agents) and a Python API (for scripts). Add a `corpus status` CLI command for index visibility. No new search logic — purely interface work over an existing engine.

</domain>

<decisions>
## Implementation Decisions

### MCP response shape
- Each search result contains **both** the matching chunk/snippet AND full file content
- Results returned as structured objects with fields: `path`, `score`, `snippet`, `full_content`, `construct_type`, `summary`, `file_type`
- No results → return `{ results: [], message: "No results found for query: X" }` (empty array + message field, not an error)
- Index missing or embedding model unreachable → raise an MCP error with descriptive, actionable message (e.g. "Index not found. Run corpus index first.")

### MCP tool surface
- Single tool: `corpus_search` — agents search, humans use CLI for indexing and status
- No MCP resources exposed (Claude's discretion — tool already returns content)
- Server invocation: `corpus mcp serve` (CLI subcommand over stdio)
- Claude Code config: `{ "command": "corpus", "args": ["mcp", "serve"] }`
- Config discovery: reads `corpus.toml` from CWD (same discovery as the CLI)
- Embedding model pre-warmed at startup (MCP-06 — eliminates cold-start latency)

### Python API ergonomics
- Function-based: `from corpus import search` — `results = search("my query")`
- Also expose `from corpus import index` for programmatic re-indexing (API-02)
- Config discovery: walk up from CWD to git root to find `corpus.toml` (pyproject.toml-style)
- Returns **dataclasses** — `result.path`, `result.score`, `result.snippet`, `result.summary`, `result.construct_type`, `result.file_type`
- Sync only — no async variant needed for v1 scripting use cases
- Same underlying query engine as CLI and MCP (API-03 — no divergence)

### Index status UX
- `corpus status` CLI command (standalone, not embedded in other commands)
- Shows all of:
  - **Sources**: name, path, file count, per-source staleness indicator (✅ current / ⚠️ stale)
  - **Last indexed**: timestamp + human-readable age ("2 hours ago")
  - **Health/staleness**: overall health indicator + count of changed files since last index
  - **Embedding model**: name and reachability status (connected / unreachable)
  - **Index stats**: total file count, total chunk count
  - **Database**: path and size
- Default: Rich-formatted table with color health indicators (✅ ⚠️ ❌)
- `--json` flag: structured JSON output for scripting and CI/CD pipelines

### Claude's Discretion
- Whether to expose any MCP resources (leaning toward none — tool is sufficient)
- Rich table layout and exact column formatting for `corpus status`
- Exact dataclass field names for Python API result objects (must include: path, file_type, construct_type, summary, score, snippet per API-01)
- Staleness threshold definition (how many hours/minutes before "stale" warning triggers)

</decisions>

<specifics>
## Specific Ideas

- `corpus status` output style inspired by the user's detailed example: grouped sections (Index Status, Sources, Model), health icons per row, per-source staleness detection
- JSON output from `corpus status --json` should include `health`, `files`, `chunks`, `last_indexed`, `stale_hours`, `model.name`, `model.status`, `sources[]`, `database.path`, `database.size_bytes`
- MCP error messages should be actionable — tell the agent what to do, not just what failed

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-agent-interfaces*
*Context gathered: 2026-02-23*

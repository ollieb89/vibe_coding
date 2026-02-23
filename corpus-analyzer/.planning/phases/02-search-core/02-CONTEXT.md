# Phase 2: Search Core - Context

**Gathered:** 2026-02-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can query the indexed corpus with natural language and get ranked, relevant results — filterable by source, file type, and construct type. Delivers hybrid BM25+vector search, construct classification, AI summaries at index time, and CLI commands (`corpus search`, `corpus status`). MCP server and Python API are Phase 3.

</domain>

<decisions>
## Implementation Decisions

### Search result display
- Default limit: 10 results (overridable with `--limit`)
- Each result shows: file path, snippet, construct type, and score
- Snippet: 2-4 lines of surrounding context, truncated at word boundaries
- Output uses Rich for terminal formatting — path highlighted, score dimmed
- Rich output degrades gracefully when output is piped

### BM25 + vector fusion
- Combine scores using Reciprocal Rank Fusion (RRF) — no raw score normalization needed
- Exact name/filename matches should dominate: boost exact title and filename matches in BM25 step so known-item searches always surface first
- Score display format: Claude's discretion (raw float or normalized — pick what's most honest and readable)
- Zero results: show clear message echoing the query back, e.g. `No results for "systematic debugging"`

### Construct classification
- Hybrid approach: rule-based heuristics first, LLM for files rules can't classify
- Rule signals: file path segments (e.g. `skills/` → skill), file extension (.py → code), frontmatter fields (YAML with `name:` + `description:` → agent_config)
- LLM fallback runs only when rules produce no confident label
- Unclassified fallback: label as `documentation` (safe default, keeps files visible)
- Classification stored at file level — all chunks from a file inherit the same construct type

### AI summaries
- Generated at index time, stored alongside the indexed document, regenerated only when file content changes
- Summary content: 1-2 sentences covering what the file does and when to use it (agent-actionable)
- Summaries shown by default in every search result — first-class part of the output
- Model: uses `CORPUS_OLLAMA_MODEL` (same config as embeddings) — no separate summary model setting

### Claude's Discretion
- Exact score display format (raw float vs. normalized 0-1 — pick what reads best in Rich output)
- Prompt template for summary generation
- How `corpus status` output is laid out
- How multiple `--source`/`--type`/`--construct` filters compose (AND semantics assumed)

</decisions>

<specifics>
## Specific Ideas

- Exact name search should feel predictable: if a user types a skill name, it appears first — no surprises
- Summaries are primarily for agents deciding whether to fetch a file, not for human reading pleasure

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-search-core*
*Context gathered: 2026-02-23*

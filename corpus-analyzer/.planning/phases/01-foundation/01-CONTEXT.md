# Phase 1: Foundation - Context

**Gathered:** 2026-02-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the embedding pipeline and LanceDB index foundation: ingest configured source directories, chunk and embed files, store in LanceDB with per-chunk metadata, and support incremental re-indexing with ghost document removal. Phase 1 does NOT include search, classification, or AI summaries — those are Phase 2.

</domain>

<decisions>
## Implementation Decisions

### corpus.toml schema
- Format: `[[sources]]` array of tables (not `[sources.name]` named sections)
- Location: `~/.config/corpus/corpus.toml` (global XDG config — tool works from any directory)
- Per-source fields: `name`, `path`, `include` (glob patterns list), `exclude` (glob patterns list)
- Example:
  ```toml
  [embedding]
  model = "nomic-embed-text"
  provider = "ollama"
  host = "http://localhost:11434"

  [[sources]]
  name = "my-skills"
  path = "~/skills"
  include = ["*.md", "*.py"]
  exclude = ["**/node_modules/**", "**/.git/**"]
  ```
- Global `[embedding]` section for model config — one model for the whole index

### Embedding model setup
- Phase 1: local Ollama only (no OpenAI/Cohere in Phase 1)
- Default model: Claude's Discretion (nomic-embed-text or mxbai-embed-large — pick best fit for semantic search of agent files)
- First-run missing model handling: Claude's Discretion (fail fast with clear pull instructions is the right pattern)
- LanceDB index stored at: `~/.local/share/corpus/` (XDG data dir, separate from config)

### Indexing output UX
- While running: progress bar with file counts (e.g. `Indexing my-skills... [=====>  ] 45/120 files`)
- On completion: per-source summary — `✔ Indexed my-skills: 45 files, 312 chunks (8.2s)` — plus total skipped count for unchanged files
- `--verbose` flag: enables per-file output for debugging
- Default (no flags): progress bar + summary only

### corpus add behavior
- Default name when `--name` not given: directory basename (e.g. `~/skills` → name = `"skills"`)
- Duplicate path/name: error with clear message, suggest `--force` to re-add
- Success output: confirm the add + suggest running `corpus index` as next step
- Flags: supports `--include` and `--exclude` at add time (matches config options)

### Claude's Discretion
- Default embedding model choice (nomic-embed-text vs mxbai-embed-large — pick for quality/speed balance)
- First-run error message wording and whether to auto-detect if Ollama is not running
- Chunk size limits and overlap for heading-based (md) and AST-based (py) chunking
- Exact progress bar library/implementation

</decisions>

<specifics>
## Specific Ideas

- The completion summary format should feel like: `✔ Indexed my-skills: 45 files, 312 chunks (8.2s)` with a total line at the end
- Config lives globally (`~/.config/corpus/`) so the tool is usable from any working directory
- Index data lives separately (`~/.local/share/corpus/`) so it's easy to find and delete to reset

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-02-23*

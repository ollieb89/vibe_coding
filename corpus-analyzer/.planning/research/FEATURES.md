# Feature Research

**Domain:** Local semantic search engine for AI agent libraries (skills, workflows, prompts, code) — queried by code agents via MCP
**Researched:** 2026-02-23
**Confidence:** MEDIUM-HIGH (MCP spec verified via official docs; search feature patterns from multiple real tools; agent-specific patterns from ecosystem observation + LOW confidence where single-source)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that any serious local code/doc search tool must have. Missing these means the product feels broken, not just incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Hybrid search (BM25 + vector) | Pure keyword misses semantic matches; pure vector misses exact names like `run_shell_tool`. Developers expect both. | MEDIUM | Standard 2025 pattern: two routes + RRF fusion. SQLite FTS5 for BM25 already exists. Vector store TBD. |
| Absolute file path in results | Agents need a path they can immediately pass to `read_file`. Relative paths require the agent to resolve context. | LOW | Always return absolute path. Never relative. |
| Relevance score in results | Agents use score to decide whether a result is worth consuming. Without it, they must guess relevance. | LOW | Normalize to 0.0–1.0 range. RRF produces unnormalized scores — normalize before returning. |
| Snippet / excerpt in results | Agents need context to decide if a file is relevant WITHOUT reading the whole file. Snippet = one LLM call saved per result. | MEDIUM | Extract top-matching chunk, not always the top of file. Preserve surrounding context (3–5 lines). |
| File metadata in results | File type, last modified, size — used by agents to filter stale or irrelevant results before reading. | LOW | Already available from filesystem stat. |
| Multi-file-type indexing | Agent libraries are mixed: `.md` skills, `.py` agents, `.json`/`.yaml` configs, `.ts`/`.js` wrappers. Missing any type = incomplete library picture. | MEDIUM | Existing extractor handles `.md`, `.py`. Need JSON/YAML/TS/JS extractors. |
| Incremental indexing (mtime+hash) | Full re-index of large agent repos is too slow to be practical. Tool must detect only changed files. | MEDIUM | Two-tier detection: compare mtime first (cheap), then SHA-256 hash (confirms real change). Pattern confirmed by DeepContext, files-db, cocoindex. |
| CLI search command | Developers need to test search interactively without writing code. | LOW | `corpus search "query"` — already have Typer CLI. |
| MCP server exposing search | Claude Code and other agents query tools automatically via MCP. Without MCP, agents can't use Corpus without custom integration. | MEDIUM | MCP spec (2025-06-18) is stable and well-documented. Use FastMCP or raw JSON-RPC over stdio/SSE. |
| Source directory management | Developers need to register permanent source dirs and add ad-hoc dirs. Without this, every index operation requires re-specifying paths. | LOW | Config file (`sources.toml` or similar) + `corpus add <dir>` CLI. |
| Result count limiting | Agents have context window limits. Returning 50 results will overflow context and waste tokens. | LOW | Default `top_k=5`, configurable. DeepContext specifically reduces token consumption 40% by limiting results. |

### Differentiators (Competitive Advantage)

Features that set Corpus apart from generic file search MCP servers. These are specifically relevant to the AI agent library use case.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Document category in results | Agents can immediately understand _what_ a result is (skill, runbook, howto, ADR) without reading it. Filters downstream decisions. | LOW | Already exists in the classifier pipeline (`DocumentCategory` enum). Expose it in search results. |
| Domain tag filtering | Agent building a frontend workflow should be able to filter to `domain:frontend` or `domain:typescript`. Reduces irrelevant noise. | LOW | `DomainTag` enum already exists. Expose as search filter parameter. |
| File type / extension filter | A query for "authentication" should be filterable to Python-only, or markdown-only. Reduces signal-to-noise. | LOW | Filter on stored extension metadata. |
| Directory scope filter | Agent can scope search to a specific repo or subdirectory it's working within. Prevents cross-repo confusion. | LOW | Filter on file path prefix. |
| Chunk-level results (not just file-level) | Return the specific section of a large file that matches, not the whole file. Saves tokens; agents read less. | HIGH | Requires chunk storage (already in `Chunk` model), chunk-level embedding, and chunk-level search. This is the hard path but highest agent value. |
| Configurable embedding provider | Developers offline must use Ollama; developers who want quality prefer OpenAI/Cohere. Flexibility removes a blocker for adoption. | MEDIUM | Already planned in PROJECT.md. Abstract provider interface; Ollama first, OpenAI/Cohere optional. |
| Python API for programmatic search | Developers building their own agent orchestration can call Corpus as a library without going through MCP. | LOW | Thin wrapper over the same search logic. Natural given Python codebase. |
| Quality score / gold standard flag in results | An agent querying for "how to write a skill" should prefer exemplary files. Quality signal distinguishes canonical from draft. | LOW | `quality_score` and `is_gold_standard` already exist on `Document`. Expose in results, allow filter `gold_standard_only=true`. |
| is_gold_standard filter | Let agents request only high-quality exemplary files — useful for "show me the best example of X" queries. | LOW | Simple boolean filter on existing field. |
| Source-aware search (search a specific named source) | A developer with 20 cloned repos wants to search "only my anthropic repos". Named sources enable this without path guessing. | MEDIUM | Requires source tagging in the index at ingest time. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem natural but should be deliberately excluded from v1.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Real-time file watching | Developers assume search is always up-to-date. Feels modern. | Adds daemon process complexity, requires background service management, startup/shutdown lifecycle, and OS-specific watcher APIs. For agent use, agents call `corpus index` before a session; real-time is over-engineering for v1. | Explicit `corpus index --refresh` command. Fast incremental re-index makes this painless enough. |
| Web UI / browser search interface | Looks impressive in demos. | Target users are developers + code agents. CLI is faster; MCP is the agent interface. Web UI adds a server process, frontend build, and maintenance surface for zero user benefit in this context. | CLI with rich terminal output (already have `rich`). |
| Cloud/hosted index sync | Enterprise teams want shared indexes. | Introduces auth, networking, privacy concerns, latency, and backend infrastructure. v1 is explicitly local-only by design (PROJECT.md Out of Scope). | Document how to share the SQLite file over a shared filesystem if teams need it. Defer cloud to v2+. |
| Multi-modal search (images, audio, PDFs) | Agent libraries sometimes include diagrams or design docs. | Agent library files are overwhelmingly text. PDFs with embedded text are edge cases. Supporting binary blobs requires heavy extraction dependencies and inflates scope significantly. | Text extraction from `.pdf` can be added as a separate extractor later if needed. Not v1. |
| LLM-generated query expansion | Improving recall by expanding queries with synonyms sounds like a quality win. | Adds an LLM call per search query — kills the "under a second" latency target from PROJECT.md. Agents issue many rapid queries; each LLM round-trip adds 1–5 seconds. | Good hybrid search (BM25+vector) already handles synonyms via semantic embedding. No LLM needed. |
| Exposing all corpus-analyzer rewriter commands via MCP | Rewriting is a power feature; exposing it seems natural. | Agents auto-invoke MCP tools. Auto-invoked LLM rewriting on agent queries is unpredictable, expensive, and destructive without explicit human approval. MCP tool budget: fewer focused tools beat many sprawling tools. | Keep rewriter as CLI-only, human-initiated. MCP exposes search only. |
| Per-result explanation ("why did this match?") | Developers debugging search quality want to understand scoring. | Generating explanations requires additional LLM calls or complex scoring decomposition. Adds latency and complexity for a debugging use case that belongs in a `corpus explain` CLI command, not in hot-path search. | Add a `corpus explain <file_path> <query>` CLI debug command separately. |

---

## Feature Dependencies

```
[Source Management (config file + corpus add)]
    └──requires──> [Incremental Indexing]
                       └──requires──> [File extraction pipeline (existing)]
                       └──requires──> [Embedding generation]
                                          └──requires──> [Embedding provider abstraction]

[MCP Server]
    └──requires──> [Search core (hybrid BM25+vector)]
                       └──requires──> [Incremental Indexing]
                       └──requires──> [Embedding generation]

[Domain tag filter] ──requires──> [Classifier pipeline (existing)]
[Category filter] ──requires──> [Document type classifier (existing)]
[Quality score filter] ──requires──> [Quality analyzer (existing)]

[Chunk-level results]
    └──requires──> [Search core]
    └──requires──> [Chunk-level embeddings] (new work — chunks must be embedded separately from docs)

[Python API] ──enhances──> [Search core] (thin wrapper, no new deps)

[is_gold_standard filter] ──requires──> [Quality analyzer (existing)]
[Source-aware search] ──requires──> [Source Management]
```

### Dependency Notes

- **MCP Server requires Search core:** The MCP tool is a transport layer over the search engine. Search must be complete and tested before MCP is meaningful.
- **Chunk-level results requires separate chunk embedding:** The existing `Chunk` model and chunks table exist, but embeddings must be generated and stored per chunk, not just per document. This is the highest-complexity differentiator.
- **Classifier-dependent filters (domain tag, category, quality) are zero-cost:** The classification pipeline already runs. Only change is exposing these as search filter parameters — no new classifier work needed.
- **Source-aware search requires source tagging at ingest:** Every indexed document must record which named source it came from. This must be built into the indexing pipeline, not added later.

---

## MVP Definition

### Launch With (v1)

Minimum viable product — what validates the core value proposition ("surface relevant agent files instantly").

- [ ] **Hybrid search (BM25 + vector, RRF fusion)** — without this, search quality is not good enough to be useful to agents
- [ ] **Absolute file path + relevance score + snippet in every result** — minimum result shape for agent consumption
- [ ] **Multi-file-type indexing: `.md`, `.py`, `.json`, `.yaml`** — covers 95%+ of agent library file types
- [ ] **Incremental indexing with mtime+hash detection** — large repos make full re-index impractical; this is required for the tool to be usable
- [ ] **MCP server with `search` tool** — this is the primary interface for code agents (Claude Code target user)
- [ ] **Source directory management** — `corpus add <dir>` + config file; without this, every index call requires manual path specification
- [ ] **File type and category metadata in results** — agents need these to filter without additional tool calls
- [ ] **`top_k` parameter (default 5)** — token budget management; non-negotiable for MCP agent consumption

### Add After Validation (v1.x)

Features to add once core search is working and real agent usage observed.

- [ ] **Domain tag filter + category filter in search** — adds agent precision but not required to validate search quality
- [ ] **Quality score / gold standard filter** — add when agents are observed fetching too many low-quality files
- [ ] **Python API** — add when developers ask for programmatic access
- [ ] **Directory scope filter** — add when multi-repo users report cross-repo noise

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] **Chunk-level results** — highest value but highest complexity; validate file-level search first
- [ ] **Source-aware search (named source filter)** — useful for large multi-org collections; premature without knowing collection sizes
- [ ] **OpenAI/Cohere embedding providers** — Ollama works for v1; cloud providers deferred until offline constraint is validated

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Hybrid search (BM25+vector) | HIGH | MEDIUM | P1 |
| Absolute path + score + snippet | HIGH | LOW | P1 |
| Multi-file-type indexing (.md, .py, .json, .yaml) | HIGH | MEDIUM | P1 |
| Incremental indexing (mtime+hash) | HIGH | MEDIUM | P1 |
| MCP server with search tool | HIGH | MEDIUM | P1 |
| Source directory management | HIGH | LOW | P1 |
| top_k parameter | HIGH | LOW | P1 |
| Category in results | MEDIUM | LOW | P2 |
| Domain tag filter | MEDIUM | LOW | P2 |
| File type filter | MEDIUM | LOW | P2 |
| Quality score / gold standard filter | MEDIUM | LOW | P2 |
| Directory scope filter | MEDIUM | LOW | P2 |
| Python API | MEDIUM | LOW | P2 |
| Chunk-level results | HIGH | HIGH | P3 |
| Cloud embedding providers | MEDIUM | MEDIUM | P3 |
| Source-aware named search | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | QMD (tobi/qmd) | DeepContext MCP | files-db MCP | Our Approach |
|---------|----------------|-----------------|--------------|--------------|
| Search method | BM25 + vector + LLM rerank | Vector + BM25 + Jina rerank | Vector (semantic) | BM25 + vector + RRF (no LLM rerank in hot path) |
| Result fields | path, title, score, snippet, context | Snippets only | Not documented | path, score, snippet, category, domain_tags, file_type, quality_score |
| File type filter | Collection scope only | TypeScript + Python AST | Not documented | Extension-based filter, configurable |
| Directory filter | `-c` collection flag | Single repo | Not documented | Path prefix filter |
| Category/domain filter | Context tag | No | No | Yes — from existing classifiers |
| Incremental indexing | Not documented | mtime + SHA-256 hash | Yes (real-time monitoring) | mtime + SHA-256 (batch, not real-time daemon) |
| MCP interface | Yes | Yes | Yes | Yes |
| Offline support | Yes (node-llama-cpp local) | No (Jina API) | Yes | Yes (Ollama) |
| Agent library awareness | No — generic docs | No — code only | No — generic files | Yes — category + domain tags purpose-built for agent files |
| Chunk-level results | Not documented | Yes — snippets not whole files | No | P3 (planned) |
| Quality signal | Score (0–100) | Token efficiency claim | No | is_gold_standard + quality_score fields |

**Key differentiation:** Corpus is the only tool in this comparison that is purpose-built for AI agent library files and exposes agent-specific metadata (document category like `persona`/`howto`/`runbook`, domain tags like `ai`/`backend`/`typescript`) as first-class search filter dimensions.

---

## MCP Tool Interface Design Notes

Based on the official MCP specification (2025-06-18) and observed search MCP implementations:

**Recommended tool shape for `corpus_search`:**

```json
{
  "name": "corpus_search",
  "description": "Search indexed AI agent files (skills, workflows, prompts, code) by semantic query. Returns ranked results with file paths, relevance scores, and content snippets.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Natural language or keyword search query"
      },
      "top_k": {
        "type": "integer",
        "description": "Maximum number of results to return (default: 5, max: 20)",
        "default": 5
      },
      "file_type": {
        "type": "string",
        "description": "Filter by file extension (e.g. 'md', 'py', 'json'). Optional.",
        "enum": ["md", "py", "json", "yaml", "ts", "js"]
      },
      "category": {
        "type": "string",
        "description": "Filter by document category. Optional.",
        "enum": ["persona", "howto", "runbook", "architecture", "reference", "tutorial", "adr", "spec"]
      },
      "domain": {
        "type": "string",
        "description": "Filter by domain tag. Optional.",
        "enum": ["ai", "backend", "frontend", "testing", "devops", "python", "typescript"]
      },
      "min_score": {
        "type": "number",
        "description": "Minimum relevance score threshold (0.0–1.0). Default: 0.0. Useful to filter low-confidence matches.",
        "default": 0.0
      }
    },
    "required": ["query"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "results": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "file_path": {"type": "string", "description": "Absolute path to the file"},
            "score": {"type": "number", "description": "Relevance score 0.0–1.0"},
            "snippet": {"type": "string", "description": "Matching excerpt from the file"},
            "category": {"type": "string"},
            "domain_tags": {"type": "array", "items": {"type": "string"}},
            "file_type": {"type": "string"},
            "is_gold_standard": {"type": "boolean"},
            "last_modified": {"type": "string", "format": "date-time"}
          },
          "required": ["file_path", "score", "snippet"]
        }
      },
      "total_indexed": {"type": "integer"},
      "query_time_ms": {"type": "integer"}
    }
  }
}
```

**Design rationale:**
- Tool name is snake_case (per MCP tool naming convention)
- Description explains what's indexed (agent files) and what's returned — critical because agents use description for tool selection decisions
- All filters are optional with documented defaults — agents can call with just `query`
- `outputSchema` is provided for structured content (MCP 2025-06-18 supports this; enables client validation)
- `query_time_ms` and `total_indexed` give agents context to decide if they should re-index before searching
- Error responses use `isError: true` with agent-actionable messages ("index is empty — run corpus index first")

**What makes results useful to an agent (vs a human):**
1. **Absolute paths** — an agent passes the path directly to `read_file`; relative paths require context the agent may not have
2. **Score, not rank** — an agent can decide "score 0.4 is too low to be relevant" and stop early; rank alone doesn't convey confidence
3. **Snippet (not full content)** — agents have token budgets; snippets allow relevance judgement without consuming a full read_file call
4. **Machine-readable category/domain metadata** — agents can branch on `category == "runbook"` without parsing natural language
5. **Structured output** — JSON over freeform text; avoids agent needing to parse prose (confirmed by MCP spec recommendation for `structuredContent`)
6. **Minimal result set (top_k=5 default)** — humans browse; agents consume. Five high-quality results beat twenty mediocre ones every time.

---

## Incremental Indexing Patterns

**Standard pattern (confirmed across DeepContext, files-db, cocoindex):**

1. On `corpus index`: walk all registered source directories
2. For each file: check stored `mtime` against filesystem `mtime`
3. If `mtime` unchanged: skip (fast path — no I/O beyond stat)
4. If `mtime` changed: compute SHA-256 hash of file content
5. If hash unchanged (mtime changed but content identical): update stored mtime, skip re-embedding (saves expensive embedding call)
6. If hash changed: re-extract, re-classify, re-embed, update index
7. For deleted files: detect files in index with no filesystem counterpart, remove from index

**Why two-tier (mtime + hash):**
- mtime alone has false positives (copy operations, backup tools touching timestamps)
- hash alone is expensive (must read every file on every index run)
- Combined: cheap fast path (mtime check) with accurate slow path (hash only when mtime changes)

**Explicit re-index over file watching (v1 decision):**
- File watchers require background daemon, OS-specific APIs (inotify, FSEvents, ReadDirectoryChangesW), and complex lifecycle management
- For agent use: agents call `corpus index --refresh` once before a session; fast incremental makes this under 1 second for typical collections
- File watching is a v2+ feature if user research confirms the pain

---

## Sources

- [MCP Tools Specification (2025-06-18)](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) — HIGH confidence, official spec
- [QMD: local hybrid search tool](https://github.com/tobi/qmd) — MEDIUM confidence, real implementation reference
- [DeepContext MCP Server](https://skywork.ai/skypage/en/deepcontext-mcp-server-ai-engineers/1980841962807820288) — MEDIUM confidence, product documentation
- [Files-DB MCP Server](https://www.pulsemcp.com/servers/randomm-files-db) — MEDIUM confidence, product documentation
- [MCP Tool Descriptions Best Practices](https://www.merge.dev/blog/mcp-tool-description) — MEDIUM confidence, community article
- [MCP Server Best Practices 2026](https://www.cdata.com/blog/mcp-server-best-practices-2026) — MEDIUM confidence, community article
- [Hybrid Search Explained (Weaviate)](https://weaviate.io/blog/hybrid-search-explained) — HIGH confidence, authoritative vendor docs
- [Incremental IVF Index Maintenance](https://arxiv.org/abs/2411.00970) — MEDIUM confidence, research paper
- [CocoIndex: incremental indexing for AI agents](https://medium.com/@cocoindex.io/building-a-real-time-data-substrate-for-ai-agents-the-architecture-behind-cocoindex-729981f0f3a4) — LOW confidence, single vendor blog

---
*Feature research for: Corpus — local semantic search engine for AI agent libraries*
*Researched: 2026-02-23*

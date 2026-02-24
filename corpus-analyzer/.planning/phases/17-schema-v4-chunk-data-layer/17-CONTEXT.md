# Phase 17: Schema v4 — Chunk Data Layer - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Add four new fields to LanceDB chunks: `start_line`, `end_line`, `chunk_name`, and `chunk_text`. Migrate existing tables idempotently (column-presence check, defaults only — no re-index). Wire all three chunkers (Markdown, Python, TypeScript) to populate these fields on every new index run. Establish the zero-hallucination line-range contract via a round-trip test. Creating or modifying search, CLI display, or MCP responses are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Line number convention
- **1-indexed** — `start_line = 1` means the first line of the file. Matches grep output, editor line numbers, and the Phase 18 CLI display format (`file.md:42-67`)
- **Inclusive end_line** — `end_line = 67` means line 67 is the last line of the chunk (not line 68 exclusive)
- **Markdown section end** — `end_line` lands at the last non-blank content line before the next heading. No trailing blank lines included; no overlap between adjacent sections

### chunk_text content
- **Markdown:** full section text including the heading line — `## Section Title\n\nBody content...`. Self-contained so LLM consumers immediately know the section context
- **Python/TypeScript:** raw file slice from `start_line` to `end_line` (1-indexed, inclusive) — `def my_func(args):\n    body...`. Full `def`/`class` signature + body. No AST reconstruction
- **Source method:** raw file lines slice (`lines[start_line-1:end_line]`). Exact source preservation — comments, docstrings, and formatting intact
- **No size cap** — `chunk_text` stores the full text unconditionally. Phase 19 MCP requires untruncated text

### Migration strategy
- **Strict defaults only** — `ensure_schema_v4()` adds missing columns (`start_line INT DEFAULT 0`, `end_line INT DEFAULT 0`, `chunk_name STRING DEFAULT ''`, `chunk_text STRING DEFAULT ''`). Existing rows are left with default zeros/empty strings; no backfill
- **Silent migration** — no output printed during migration. Schema change is an implementation detail; consistent with prior schema migrations
- **Column-presence detection** — migration checks if each of the four columns exists in the LanceDB schema. Adds any missing ones. Idempotent: re-running on an already-migrated table is a no-op. No version column

### Round-trip test fixtures
- **Synthetic tmp_path files** — test writes known content to tmp_path, indexes it, queries LanceDB directly, asserts `start_line`/`end_line` match expected values. No dependency on repo files whose line numbers could drift
- **All three chunkers covered** — parametrised test hits Markdown (`.md`), Python (`.py`), and TypeScript (`.ts`) fixtures in Phase 17. Zero-hallucination contract established for all chunkers, not deferred
- **Python fixture includes a class** — the synthetic `.py` file has a top-level function AND a class with a method. Tests both chunk shapes; more coverage without waiting for Phase 20 method sub-chunking

### Claude's Discretion
- Exact LanceDB column-addition API (e.g., whether to use `add_columns`, schema merge, or table recreation)
- TypeScript fixture content and construct type for round-trip test
- Whether `ensure_schema_v4()` lives in `ingest/indexer.py`, a new `ingest/schema.py`, or `ingest/lancedb_utils.py`

</decisions>

<specifics>
## Specific Ideas

- Line numbers should match what a user would see in their editor or `grep -n` output — 1-indexed, inclusive range
- chunk_text is the exact bytes from the file — "raw file slice" is the implementation contract, not reconstructed/pretty-printed source

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 17-schema-v4-chunk-data-layer*
*Context gathered: 2026-02-24*

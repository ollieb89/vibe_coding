# Phase 17: Schema v4 — Chunk Data Layer - Research

**Researched:** 2026-02-24
**Domain:** LanceDB schema evolution, chunker API extension, TDD RED-GREEN cycle
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Line number convention**
- 1-indexed — `start_line = 1` means the first line of the file. Matches grep output, editor line numbers, and the Phase 18 CLI display format (`file.md:42-67`)
- Inclusive end_line — `end_line = 67` means line 67 is the last line of the chunk (not line 68 exclusive)
- Markdown section end — `end_line` lands at the last non-blank content line before the next heading. No trailing blank lines included; no overlap between adjacent sections

**chunk_text content**
- Markdown: full section text including the heading line — `## Section Title\n\nBody content...`. Self-contained so LLM consumers immediately know the section context
- Python/TypeScript: raw file slice from `start_line` to `end_line` (1-indexed, inclusive) — `def my_func(args):\n    body...`. Full `def`/`class` signature + body. No AST reconstruction
- Source method: raw file lines slice (`lines[start_line-1:end_line]`). Exact source preservation — comments, docstrings, and formatting intact
- No size cap — `chunk_text` stores the full text unconditionally. Phase 19 MCP requires untruncated text

**Migration strategy**
- Strict defaults only — `ensure_schema_v4()` adds missing columns (`start_line INT DEFAULT 0`, `end_line INT DEFAULT 0`, `chunk_name STRING DEFAULT ''`, `chunk_text STRING DEFAULT ''`). Existing rows are left with default zeros/empty strings; no backfill
- Silent migration — no output printed during migration. Schema change is an implementation detail; consistent with prior schema migrations
- Column-presence detection — migration checks if each of the four columns exists in the LanceDB schema. Adds any missing ones. Idempotent: re-running on an already-migrated table is a no-op. No version column

**Round-trip test fixtures**
- Synthetic tmp_path files — test writes known content to tmp_path, indexes it, queries LanceDB directly, asserts `start_line`/`end_line` match expected values. No dependency on repo files whose line numbers could drift
- All three chunkers covered — parametrised test hits Markdown (`.md`), Python (`.py`), and TypeScript (`.ts`) fixtures in Phase 17. Zero-hallucination contract established for all chunkers, not deferred
- Python fixture includes a class — the synthetic `.py` file has a top-level function AND a class with a method. Tests both chunk shapes; more coverage without waiting for Phase 20 method sub-chunking

### Claude's Discretion
- Exact LanceDB column-addition API (e.g., whether to use `add_columns`, schema merge, or table recreation)
- TypeScript fixture content and construct type for round-trip test
- Whether `ensure_schema_v4()` lives in `ingest/indexer.py`, a new `ingest/schema.py`, or `ingest/lancedb_utils.py`

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CHUNK-01 | `ChunkRecord` schema updated to v4: `start_line: int`, `end_line: int`, `chunk_name: str`, and `chunk_text: str` persisted in LanceDB; `ensure_schema_v4()` idempotent migration adds columns to existing tables without data loss; existing rows default to `start_line=0`, `end_line=0`, `chunk_name=""`, `chunk_text=""` | LanceDB `add_columns` API verified to work; existing v2/v3 pattern is the exact template; column-presence check pattern established. `chunk_name` and `chunk_text` are new ChunkRecord fields; `start_line`/`end_line` already exist in ChunkRecord but need `chunk_name`/`chunk_text` added alongside. Indexer already reads `start_line`/`end_line` from chunk dicts; needs to also read `chunk_name` and `chunk_text`. Chunkers need to populate `chunk_name` (Markdown: heading text; Python: function/class name; TypeScript: already done) and `chunk_text` (raw file slice). |
</phase_requirements>

---

## Summary

Phase 17 adds four fields to the LanceDB `ChunkRecord` schema and wires all chunkers to populate them. The domain is entirely within the project's existing LanceDB schema evolution pattern — the `ensure_schema_v2()` and `ensure_schema_v3()` functions in `store/schema.py` are the exact template to follow for `ensure_schema_v4()`.

A critical finding from live testing: `lancedb>=0.29.2` (the installed version) does NOT support `cast(0 as int32)` or `cast(0 as int64)` in `add_columns` SQL expressions. Integer columns must use `cast(0 as bigint)` or `cast(0 as int)` — both produce `int64` (matching Python `int`). String columns use `cast('' as string)`. Attempting to add a column that already exists raises a `RuntimeError`, so idempotency MUST be implemented by pre-checking `{field.name for field in table.schema}` before each `add_columns` call.

The gap analysis reveals: `ChunkRecord` already has `start_line` and `end_line` fields (they are existing schema fields, not new). The four v4 fields to add are `chunk_name: str` and `chunk_text: str` (new to `ChunkRecord`), plus the `ensure_schema_v4()` migration for existing LanceDB tables. The indexer (`ingest/indexer.py`) already reads `chunk["start_line"]` and `chunk["end_line"]` from chunk dicts and writes them to LanceDB — it needs to also read `chunk.get("chunk_name", "")` and `chunk.get("chunk_text", "")`. The TypeScript chunker already emits `chunk_name`; Markdown and Python chunkers do not.

**Primary recommendation:** Follow the `ensure_schema_v2`/`v3` pattern exactly. Place `ensure_schema_v4()` in `store/schema.py`. Add `chunk_name: str = ""` and `chunk_text: str = ""` to `ChunkRecord`. Use `cast('' as string)` for both string columns. Update `chunk_markdown` to emit `chunk_name` (heading text) and `chunk_text` (section text). Update `chunk_python` to emit `chunk_name` (function/class name) and `chunk_text` (raw lines slice). Update the indexer to pass these fields through.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| lancedb | 0.29.2 | Vector store — schema evolution via `add_columns` | Project's existing vector index; no change |
| lancedb.pydantic | 0.29.2 | `LanceModel`, `Vector` for typed schema | All schema definitions use this — `ChunkRecord` inherits `LanceModel` |
| pytest | installed | TDD RED-GREEN test cycles | Project standard: `uv run pytest -v` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pyarrow | transitive | LanceDB's internal column type system | Referenced when debugging `add_columns` type errors |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `add_columns` in-place migration | Drop + recreate table | Drop+recreate loses all data; `add_columns` is zero-downtime and follows established project pattern |
| `add_columns` in-place migration | Schema version column | User decided no version column; column-presence check is sufficient and simpler |

**Installation:** No new dependencies. Everything is already installed.

---

## Architecture Patterns

### Recommended Project Structure

No new files are strictly required. The natural location for all changes:

```
src/corpus_analyzer/
├── store/
│   └── schema.py          # add ensure_schema_v4(), extend ChunkRecord
├── ingest/
│   ├── chunker.py         # chunk_markdown + chunk_python emit chunk_name + chunk_text
│   └── indexer.py         # pass chunk_name + chunk_text through to ChunkRecord dict
tests/
├── store/
│   └── test_schema.py     # TDD: ensure_schema_v4() + ChunkRecord v4 fields
└── ingest/
    └── test_chunker.py    # TDD: chunk_name + chunk_text from all three chunkers
```

For `ensure_schema_v4()` location — Claude's discretion per CONTEXT.md. The established pattern puts schema migration functions in `store/schema.py` alongside `ensure_schema_v2` and `ensure_schema_v3`. This is the recommended location.

### Pattern 1: LanceDB Column-Presence + add_columns (established project pattern)

**What:** Check schema for missing column names, add only missing ones. Never call `add_columns` if column already exists (raises RuntimeError).
**When to use:** Every `ensure_schema_vN()` function.
**Example:**

```python
# Source: live-tested against lancedb==0.29.2 (2026-02-24)
def ensure_schema_v4(table: lancedb.table.Table) -> None:
    """Add Phase 17 v4 columns to an existing chunks table if they don't exist.

    Uses LanceDB's add_columns API for in-place schema evolution — no data loss
    and no table rebuild required. Safe to call on every CorpusIndex.open() call.

    Args:
        table: The LanceDB chunks table to upgrade.
    """
    existing_cols = {field.name for field in table.schema}
    if "chunk_name" not in existing_cols:
        table.add_columns({"chunk_name": "cast('' as string)"})
    if "chunk_text" not in existing_cols:
        table.add_columns({"chunk_text": "cast('' as string)"})
```

Note: `start_line` and `end_line` already exist in `ChunkRecord` as required fields (int). They do NOT need to be added by `ensure_schema_v4()` — they were present since table creation. Only `chunk_name` and `chunk_text` are genuinely new.

### Pattern 2: ChunkRecord v4 Field Extensions

**What:** Add `chunk_name` and `chunk_text` as fields with empty-string defaults so existing rows remain valid.
**When to use:** When extending `ChunkRecord` with fields that must be backward-compatible.
**Example:**

```python
# Source: store/schema.py — following existing Phase 2/6 nullable field pattern
# Phase 17 fields (non-nullable, defaulting to empty string for existing rows)
chunk_name: str = ""
"""Heading text (Markdown), function/class name (Python), or construct name (TypeScript)."""

chunk_text: str = ""
"""Raw file lines slice from start_line to end_line (1-indexed, inclusive).
No size cap — Phase 19 MCP requires untruncated text.
"""
```

Using `str = ""` (not `str | None`) because the CONTEXT.md decision specifies non-null defaults. The existing `construct_type: str | None = None` uses nullable; v4 fields use empty-string defaults.

### Pattern 3: Chunker dict augmentation

**What:** Each chunker function adds `chunk_name` and `chunk_text` keys to its returned dicts.
**When to use:** Modifying `chunk_markdown`, `chunk_python`. `chunk_typescript` already emits `chunk_name`.
**Example for chunk_markdown:**

```python
# chunk_name = heading text (e.g., "## Overview" → "## Overview" or just "Overview"?)
# CONTEXT.md says "heading text" — use the full heading line text (e.g., "## Overview")
chunks.append({
    "text": section_text,      # (existing — may be modified by summary prepend)
    "chunk_name": lines[start_idx],  # heading line verbatim
    "chunk_text": section_text,      # exact section text (same as text before summary prepend)
    "start_line": start_idx + 1,
    "end_line": actual_end_line + 1,
})
```

**IMPORTANT distinction:** `text` is what gets embedded (may be prepended with summary by indexer). `chunk_text` is the raw file slice — it must be captured BEFORE any summary prepend. The indexer currently does `chunks[0]["text"] = f"{summary_text}\n\n{chunks[0]['text']}"` — `chunk_text` must not be mutated by this.

**Example for chunk_python:**

```python
# chunk_name = node.name (function/class name from AST)
# chunk_text = raw lines slice (lines[start_line-1:end_line] joined)
chunk_name_str = node.name  # ast.FunctionDef/ClassDef both have .name attribute
chunk_text_str = "\n".join(lines[start_line - 1:actual_end_line]).rstrip()

chunks.append({
    "text": chunk_text_str,    # existing
    "chunk_name": chunk_name_str,
    "chunk_text": chunk_text_str,
    "start_line": start_line,
    "end_line": actual_end_line,
})
```

**For chunk_typescript:** Already emits `chunk_name`. Add `chunk_text` = same as `text` (already the raw slice). Also add `chunk_text` to the export-default branch.

### Pattern 4: Indexer pass-through for v4 fields

**What:** Read `chunk_name` and `chunk_text` from chunk dict using `.get()` with empty-string defaults; write to `chunk_dict`.
**When to use:** Inside the `for chunk, vector in zip(chunks, embeddings)` loop in `CorpusIndex.index_source`.
**Example:**

```python
chunk_dict = {
    # ... existing fields ...
    "chunk_name": chunk.get("chunk_name", ""),
    "chunk_text": chunk.get("chunk_text", ""),
}
```

### Pattern 5: Round-trip test structure

**What:** Write known content to `tmp_path`, index it via `CorpusIndex`, query LanceDB directly, assert fields.
**When to use:** The zero-hallucination contract test.
**Example:**

```python
def test_round_trip_markdown(tmp_path):
    # Write known content
    md_file = tmp_path / "test.md"
    md_file.write_text("# Section One\n\nSome body text.\n\n## Section Two\n\nMore content.\n")
    # Index
    index = CorpusIndex.open(tmp_path, MockEmbedder())
    source = SourceConfig(name="test", path=str(tmp_path))
    index.index_source(source)
    # Query LanceDB directly
    rows = index.table.search().where("file_type = '.md'").limit(10).to_list()
    row = next(r for r in rows if r["chunk_name"] == "# Section One")
    assert row["start_line"] == 1
    assert row["chunk_text"].startswith("# Section One")
```

### Anti-Patterns to Avoid

- **Using `cast(0 as int32)` in `add_columns`:** LanceDB 0.29.2 does not support `int32` in SQL expressions. Use `cast(0 as bigint)` or `cast(0 as int)` instead. HOWEVER: `start_line` and `end_line` already exist in the schema as `int64` fields — no integer columns need to be added by `ensure_schema_v4()` at all.
- **Calling `add_columns` unconditionally:** Will raise `RuntimeError: Column X already exists`. Always check `{field.name for field in table.schema}` first.
- **Mutating `chunk_text` in the indexer summary-prepend path:** The indexer does `chunks[0]["text"] = f"{summary_text}\n\n{chunks[0]['text']}"`. `chunk_text` must be set before this mutation and must not be touched by it. Capture `chunk_text` from the chunk dict before the summary prepend occurs.
- **`chunk_text` as a truncated version of `text`:** CONTEXT.md is explicit — no size cap. Do not apply `_enforce_char_limit` to `chunk_text`. (The existing `text` field already goes through `_enforce_char_limit`; `chunk_text` should be the pre-limit raw slice.)
- **Setting `chunk_text` to the post-limit `text` value:** `_enforce_char_limit` can split a chunk into multiple sub-chunks. If `chunk_text` is derived from the split `text`, it will be wrong. `chunk_text` should be the original raw file slice for the line range, not the truncated version.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Schema migration tracking | Custom version table | `{field.name for field in table.schema}` column-presence check | Project's established pattern; zero state to manage |
| Integer column defaults | Custom SQL | `cast(0 as bigint)` in `add_columns` | Verified working with lancedb 0.29.2 |
| String column defaults | Custom SQL | `cast('' as string)` in `add_columns` | Same pattern as v2/v3 migrations |

**Key insight:** The `ensure_schema_v2`/`v3` functions in `store/schema.py` are the complete reference implementation. Copy the pattern exactly.

---

## Common Pitfalls

### Pitfall 1: Integer type mismatch in add_columns
**What goes wrong:** `add_columns({"start_line": "cast(0 as int32)"})` raises `RuntimeError: Unsupported data type: Int32`.
**Why it happens:** LanceDB 0.29.2 SQL expression parser does not support `int32`. Supported integer alias: `int` (→ int32), `bigint` (→ int64). Python `int` on a `LanceModel` maps to `int64`.
**How to avoid:** Use `cast(0 as bigint)` for integer defaults. BUT: `start_line` and `end_line` are existing ChunkRecord fields — `ensure_schema_v4()` does NOT need to add them. Only `chunk_name` and `chunk_text` (both string) need migration.
**Warning signs:** `RuntimeError` mentioning `Unsupported data type`.

### Pitfall 2: Double add_columns call raises
**What goes wrong:** Calling `ensure_schema_v4()` twice (or on an already-migrated table) raises `RuntimeError: Column chunk_name already exists`.
**Why it happens:** LanceDB raises rather than silently skipping duplicate column additions.
**How to avoid:** Always guard with `if "chunk_name" not in existing_cols:` before each `add_columns` call.
**Warning signs:** `RuntimeError: Column X already exists in the dataset`.

### Pitfall 3: chunk_text contaminated by summary prepend
**What goes wrong:** `chunk_text` contains the LLM summary prefix instead of the raw file slice.
**Why it happens:** The indexer modifies `chunks[0]["text"]` with `f"{summary_text}\n\n{chunks[0]['text']}"` after chunking. If `chunk_text` is read from `chunk["text"]` after this mutation, it captures the contaminated value.
**How to avoid:** The indexer should read `chunk.get("chunk_text", "")` from the chunk dict — this is populated by the chunker BEFORE the indexer's summary prepend. The chunkers must set `chunk_text` before returning; the indexer reads it unchanged.
**Warning signs:** Round-trip test fails because `chunk_text` starts with LLM summary text.

### Pitfall 4: chunk_text duplicates existing text field logic
**What goes wrong:** Developer sets `chunk_text = chunk["text"]` in the indexer after summary prepend.
**Why it happens:** Confusion between `text` (embeddable, may include summary) and `chunk_text` (raw source slice, no summary, no truncation).
**How to avoid:** `chunk_text` is set by chunkers (raw content) and read by the indexer as-is. `text` is also set by chunkers but may be modified by the indexer. These are two separate fields with two separate contracts.
**Warning signs:** `chunk_text` starts with summary content in stored rows.

### Pitfall 5: Missing chunk_text field in _enforce_char_limit output
**What goes wrong:** `_enforce_char_limit` splits a large chunk into sub-chunks but does not preserve or split `chunk_text`. Sub-chunks have no `chunk_text` key.
**Why it happens:** `_enforce_char_limit` only handles `text`, `start_line`, `end_line`. Adding `chunk_text` support requires modifying it.
**How to avoid:** Two options: (a) `_enforce_char_limit` passes `chunk_text` through unchanged from the original chunk for each sub-chunk (sub-chunks of the same section all share the same raw `chunk_text`); (b) `_enforce_char_limit` is not applied to `chunk_text` and each sub-chunk uses `chunk.get("chunk_text", "")`. The simplest correct approach is (a): when splitting, carry the parent `chunk_text` into every sub-chunk. This maintains the contract that `chunk_text` is the raw file slice for the original section even if `text` was truncated.
**Warning signs:** Sub-chunks (from large sections) have empty `chunk_text` in LanceDB.

### Pitfall 6: test_all_required_fields_present in test_schema.py will RED unless updated
**What goes wrong:** The existing test `test_all_required_fields_present` enumerates expected field names. It will fail when `chunk_name` and `chunk_text` are added to `ChunkRecord` because they are not in the expected set.
**Why it happens:** Explicit field-set comparison in test. This is the DESIRED RED state for TDD Plan 17-01.
**How to avoid (GREEN):** Add `"chunk_name"` and `"chunk_text"` to the expected set in that test. This is the GREEN fix for Plan 17-02.

---

## Code Examples

Verified patterns from official sources (live-tested against lancedb==0.29.2):

### ensure_schema_v4() — complete implementation

```python
# Source: live-tested 2026-02-24, lancedb==0.29.2
def ensure_schema_v4(table: lancedb.table.Table) -> None:
    """Add Phase 17 v4 columns to an existing chunks table if they don't exist.

    Adds chunk_name and chunk_text with empty-string defaults.
    start_line and end_line already exist (created with ChunkRecord schema).
    Idempotent: re-running on an already-migrated table is a no-op.

    Args:
        table: The LanceDB chunks table to upgrade.
    """
    existing_cols = {field.name for field in table.schema}
    if "chunk_name" not in existing_cols:
        table.add_columns({"chunk_name": "cast('' as string)"})
    if "chunk_text" not in existing_cols:
        table.add_columns({"chunk_text": "cast('' as string)"})
```

### ChunkRecord v4 fields addition

```python
# In store/schema.py, after Phase 6 fields:
# --- Phase 17 fields (non-nullable, empty-string defaults for existing rows) ---
chunk_name: str = ""
"""Heading text (Markdown), function/class name (Python), or construct name (TypeScript).

Empty string for chunks indexed before Phase 17.
"""

chunk_text: str = ""
"""Raw file slice from start_line to end_line (1-indexed, inclusive).

Exact source text — comments, docstrings, and formatting intact. No size cap.
Empty string for chunks indexed before Phase 17.
"""
```

### chunk_markdown — emit chunk_name and chunk_text

```python
# In chunker.py chunk_markdown(), inside the section loop:
heading_line = lines[start_idx]  # verbatim heading text, e.g. "## Overview"
# section_text is already computed (heading + body, stripped)
chunks.append({
    "text": section_text,
    "chunk_name": heading_line,
    "chunk_text": section_text,   # same as text here; indexer may modify text separately
    "start_line": start_idx + 1,
    "end_line": actual_end_line + 1,
})
```

### chunk_python — emit chunk_name and chunk_text

```python
# In chunker.py chunk_python(), inside the node loop:
chunk_name_str = node.name  # FunctionDef.name or ClassDef.name
chunk_text_str = "\n".join(lines[start_line - 1:actual_end_line]).rstrip()
chunks.append({
    "text": chunk_text_str,
    "chunk_name": chunk_name_str,
    "chunk_text": chunk_text_str,
    "start_line": start_line,
    "end_line": actual_end_line,
})
```

### chunk_typescript — add chunk_text (chunk_name already present)

```python
# In ts_chunker.py, where chunk is appended:
chunks.append({
    "text": chunk_text,
    "start_line": start_line,
    "end_line": end_line,
    "chunk_name": chunk_name,
    "chunk_text": chunk_text,   # raw source slice (same value as text before summary prepend)
})
# Also add chunk_text to the export-default branch (currently missing chunk_name too)
```

### Indexer pass-through — read v4 fields

```python
# In indexer.py, inside CorpusIndex.index_source(), the chunk_dict construction:
chunk_dict = {
    "chunk_id": make_chunk_id(...),
    # ... existing fields ...
    "chunk_name": chunk.get("chunk_name", ""),
    "chunk_text": chunk.get("chunk_text", ""),
}
```

### _enforce_char_limit — carry chunk_text through

```python
# When splitting an oversized chunk, carry parent chunk_text unchanged:
result.append({
    "text": "\n".join(current_lines),
    "chunk_name": chunk.get("chunk_name", ""),   # carry parent's name
    "chunk_text": chunk.get("chunk_text", ""),    # carry full parent text unchanged
    "start_line": current_start,
    "end_line": current_line_num - 1,
})
```

### LanceDB column-presence check — verified idempotency

```python
# DO: check before adding
existing_cols = {field.name for field in table.schema}
if "chunk_name" not in existing_cols:
    table.add_columns({"chunk_name": "cast('' as string)"})

# DON'T: call unconditionally — raises RuntimeError if column exists
table.add_columns({"chunk_name": "cast('' as string)"})  # WRONG — fails on re-run
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `chunk_name` only in ts_chunker | All three chunkers emit `chunk_name` | Phase 17 | Markdown and Python chunks get named |
| No `chunk_text` field | `chunk_text` persisted in LanceDB | Phase 17 | Phase 19 MCP can return full chunk text without reading file |
| `text` field dual-purpose (embed + display) | `text` for embedding, `chunk_text` for display/MCP | Phase 17 | Clear separation: summary can contaminate `text` without affecting `chunk_text` |

**Deprecated/outdated:**
- `test_all_required_fields_present` in `tests/store/test_schema.py`: current expected set is missing `chunk_name` and `chunk_text` — this test is the RED signal for Plan 17-01.

---

## Open Questions

1. **chunk_text vs text for sub-chunks from _enforce_char_limit**
   - What we know: `_enforce_char_limit` splits large chunks into sub-chunks. Each sub-chunk gets a slice of the parent `text`. `chunk_text` should be the full original slice (no size limit).
   - What's unclear: Should each sub-chunk carry the same parent `chunk_text`, or should `chunk_text` also be the sub-chunk's slice?
   - Recommendation: Carry the parent `chunk_text` unchanged for all sub-chunks. The `chunk_text` field's contract is "raw file slice for the line range covered by start_line..end_line" — for sub-chunks, the line range is a sub-range but `chunk_text` would be the full parent. This is a minor inconsistency but acceptable; Phase 19 MCP consumers get at least the correct containing text. An alternative: set sub-chunk `chunk_text` to the sub-chunk's `text` value (the truncated slice). Either is defensible; the planner should pick one and document it in Plan 17-02.

2. **chunk_markdown preamble merge: what chunk_name to use?**
   - What we know: `chunk_markdown` merges pre-heading preamble content into the first chunk's text. The merged chunk's `start_line` is 1, `end_line` is the first heading's end_line.
   - What's unclear: The `chunk_name` for this merged preamble+first-heading chunk. Options: the first heading's heading text, or `""` (no heading for preamble), or `"(preamble)"`.
   - Recommendation: Use the first heading's text (the heading that was merged into). The preamble is prepended to the heading chunk — the heading is still the dominant content identifier.

---

## Sources

### Primary (HIGH confidence)
- Live codebase inspection — `store/schema.py` (ensure_schema_v2, ensure_schema_v3 pattern), `ingest/chunker.py` (chunk_markdown, chunk_python, chunk_lines return shapes), `ingest/ts_chunker.py` (already emits chunk_name), `ingest/indexer.py` (chunk dict consumption, summary prepend location)
- Live API test — lancedb==0.29.2 `add_columns` behavior verified: `cast('' as string)` works; `cast(0 as bigint)` and `cast(0 as int)` work for integers; `cast(0 as int32)` raises `RuntimeError`; double-add raises `RuntimeError: Column X already exists`
- `pyproject.toml` — confirms `lancedb>=0.29.2` installed at 0.29.2

### Secondary (MEDIUM confidence)
- CONTEXT.md decisions — user-locked choices for line convention, chunk_text contract, migration strategy, round-trip test fixtures

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — lancedb version confirmed, add_columns API live-tested
- Architecture: HIGH — existing ensure_schema_v2/v3 pattern is the direct template, all source files read
- Pitfalls: HIGH — integer type issue, double-add behavior, summary contamination all verified via live code inspection

**Research date:** 2026-02-24
**Valid until:** 2026-03-24 (lancedb API is stable; project code is at known state)

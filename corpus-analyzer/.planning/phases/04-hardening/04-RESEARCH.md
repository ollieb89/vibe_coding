# Phase 4: Defensive Hardening - Research

**Researched:** 2026-02-23
**Domain:** Python error handling, logging, Pydantic config, dead code removal, process documentation
**Confidence:** HIGH — all findings are from direct codebase inspection; no external library APIs required

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **MCP error signaling:** When `full_content` cannot read a file (OSError): both log a warning server-side AND return a `content_error` field in the response. `content_error` contains a human-readable error message string (e.g. `"File not found: /path/to/file"`). `content_error` is omitted from the response when there is no error (not included as null or empty string). For the indexer's silent swallow (stale chunk deletion, `_get_existing_files`): log warning only — these are internal operations with no caller-facing return, so `logging.warning()` is sufficient.
- **use_llm_classification exposure:** Expose as a config key only — add `use_llm_classification: bool` to `SourceConfig`, consistent with how `summarize` works (SUMM-03 pattern). Default value: `False` — preserves current behaviour, users opt in per source. No CLI flag and no API parameter override — `SourceConfig` is the single control point.
- **DATA_DIR consolidation:** Move `DATA_DIR` definition to `config/schema.py` — the natural owner of data paths alongside `CorpusConfig`. Both `cli.py` and `api/public.py` import from `config/schema.py`. `mcp/server.py` already imports from `cli.py` — update it to import from `config/schema.py` too. Variable name stays `DATA_DIR` — no rename.
- **Retroactive VERIFICATION.md:** Write VERIFICATION.md for phases 1, 2, and 3 as part of Phase 4. Detail level: summary-level — extract requirement IDs and status from existing SUMMARY.md frontmatter and the audit data; mark files as retroactive.

### Claude's Discretion

- Exact warning message wording in `logging.warning()` calls
- Whether to add a single `content_error: Optional[str]` field or restructure the MCP response dict
- Order of operations when writing retroactive VERIFICATION.md (which phase first)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CLI-02 | `corpus search` returns ranked results with file path, snippet, and score — no crash on KeyError | Fix `result['_relevance_score']` → `result.get('_relevance_score', 0.0)` at `cli.py:203`; existing `test_search_status.py` test patterns cover this |
| INGEST-07 | Re-index detects and removes stale chunks — failures must be logged, not swallowed | Replace bare `except Exception: pass/return {}` in `_delete_stale_chunks()` and `_get_existing_files()` with `logging.warning()`; indexer already imports nothing for logging, `import logging` needed |
| MCP-02 | MCP `search` tool returns full file content for top matches — file read errors must surface | Add `content_error` field to result dict when `OSError` occurs in `server.py:86-88`; log warning to stderr; omit field on success |
</phase_requirements>

---

## Summary

Phase 4 is a pure hardening and cleanup phase. All 37 v1.0 requirements are already functionally wired — this phase closes the audit's identified failure paths and removes tech debt before the v1.0 milestone is archived. There are no new capabilities to add.

The work divides into five precise, bounded interventions: (1) a one-line KeyError fix in `cli.py`, (2) logging additions to two bare-except blocks in `indexer.py`, (3) a `content_error` field + warning in `mcp/server.py`, (4) three tech debt removals (dead code, redundant FTS call, `DATA_DIR` consolidation, `use_llm_classification` config exposure), and (5) three retroactive VERIFICATION.md documents for phases 1–3. Each intervention is localized to a single file or a pair of files, with no cross-cutting refactors required.

The risk profile is very low. All changes are either additive (new fields, new logging calls, new config field) or strictly subtractive (dead code removal). No interfaces change their signatures; no data schemas change their storage format.

**Primary recommendation:** Work in dependency order — critical safety fixes first (CLI-02, INGEST-07, MCP-02), then tech debt (dead code, FTS, config, DATA_DIR), then documentation (VERIFICATION.md files).

---

## Standard Stack

### Core (existing — no new dependencies needed)

| Library | Current Usage | Phase 4 Usage |
|---------|--------------|---------------|
| Python `logging` | Used in `mcp/server.py` (`logging.basicConfig`, `logging.warning`, `logging.error`) | Add `import logging` to `indexer.py`; use `logging.warning()` in two exception handlers |
| `pydantic` | `SourceConfig`, `EmbeddingConfig`, `CorpusConfig` in `config/schema.py` | Add `use_llm_classification: bool = False` field to `SourceConfig` — follows existing `summarize: bool = True` pattern exactly |
| `platformdirs` | `user_data_dir("corpus")` in `cli.py` and `api/public.py` | Move definition to `config/schema.py`; importers change to `from corpus_analyzer.config.schema import DATA_DIR` |

### No New Installations

```bash
# No new dependencies required — all libraries already in pyproject.toml
uv sync  # to verify existing deps are satisfied
```

---

## Architecture Patterns

### Pattern 1: Logging in Silent Exception Handlers

**What:** Replace bare `except Exception: pass` and `except Exception: return {}` with a warning log before the fallback return.

**Current code (`indexer.py` lines 299-301, 353-355):**
```python
# _get_existing_files():
except Exception:
    # Table might be empty or query failed
    return {}

# _delete_stale_chunks():
except Exception:
    # If deletion fails, continue (not critical)
    pass
```

**Fixed pattern:**
```python
import logging

# _get_existing_files():
except Exception as exc:
    logging.warning("Failed to query existing files for source '%s': %s", source_name, exc)
    return {}

# _delete_stale_chunks():
except Exception as exc:
    logging.warning("Failed to delete stale chunks for source '%s': %s", source_name, exc)
```

**When to use:** Any internal operation where failure is non-critical but silence is dangerous (can mask data loss or misconfiguration).

### Pattern 2: Conditional Field in MCP Response Dict

**What:** Add `content_error` to result dict only when an OSError occurs. Omit the key entirely on success (not `None`, not empty string — absent).

**Current code (`mcp/server.py` lines 85-88):**
```python
try:
    full_content = Path(file_path).read_text(errors="replace")
except OSError:
    full_content = ""
```

**Fixed pattern (per locked decision: both log AND return field):**
```python
content_error: str | None = None
try:
    full_content = Path(file_path).read_text(errors="replace")
except OSError as exc:
    logging.warning("Cannot read file after indexing: %s — %s", file_path, exc)
    full_content = ""
    content_error = f"File not found: {file_path}"

result_dict: dict[str, Any] = {
    "path": file_path,
    "score": float(row.get("_relevance_score", 0.0)),
    "snippet": extract_snippet(str(row.get("text", "")), query),
    "full_content": full_content,
    "construct_type": str(row.get("construct_type") or "documentation"),
    "summary": str(row.get("summary") or ""),
    "file_type": str(row.get("file_type", "")),
}
if content_error is not None:
    result_dict["content_error"] = content_error
results.append(result_dict)
```

**Key:** The `content_error` key must be absent (not `None`) when there is no error. The locked decision says "omitted from the response when there is no error."

### Pattern 3: Safe dict access with .get() fallback

**What:** Change direct key access to `.get()` with a safe default for fields that may be absent from LanceDB result rows.

**Current code (`cli.py` line 203):**
```python
f"[dim]score: {result['_relevance_score']:.3f}[/]"
```

**Fixed (1-line change):**
```python
f"[dim]score: {result.get('_relevance_score', 0.0):.3f}[/]"
```

**Why safe default:** MCP server (`server.py:92`) and Python API (`api/public.py:113`) already use `row.get('_relevance_score', 0.0)`. This change makes CLI consistent with the other two interfaces.

### Pattern 4: SourceConfig Field Addition (SUMM-03 pattern)

**What:** Add `use_llm_classification: bool = False` to `SourceConfig` exactly following how `summarize: bool = True` was added.

**Current `summarize` field in `config/schema.py` (lines 56-61):**
```python
summarize: bool = True
"""Whether to generate AI summaries for files in this source at index time.

Set to False for large repos where LLM summary generation cost is prohibitive.
Defaults to True. When False, summary column remains None for all chunks.
"""
```

**New field to add:**
```python
use_llm_classification: bool = False
"""Whether to use LLM-based classification for files in this source at index time.

Set to True to enable richer construct type classification via Ollama.
Defaults to False. When False, rule-based classification is used.
"""
```

**Downstream wiring:** `indexer.py` `index_source()` already accepts `use_llm_classification: bool = True` as a parameter (line 136). The caller just needs to pass `source.use_llm_classification` instead of the hardcoded default.

**Note:** The parameter default in `index_source()` must be updated from `True` to `False` to match the new config default. Or the config field can override the parameter — either way, the config value must flow through.

### Pattern 5: DATA_DIR Consolidation

**What:** Move the `DATA_DIR` constant from `cli.py` to `config/schema.py` (alongside `CorpusConfig`), then update importers.

**Current state:**
- `cli.py:36`: `DATA_DIR = Path(user_data_dir("corpus"))` (source of truth)
- `api/public.py:68`: `data_dir = Path(user_data_dir("corpus"))` (inline, not imported)
- `mcp/server.py:18`: `from corpus_analyzer.cli import CONFIG_PATH, DATA_DIR` (imports from cli)

**Target state:**
```python
# config/schema.py (new lines, after imports):
from pathlib import Path
from platformdirs import user_config_dir, user_data_dir

CONFIG_PATH = Path(user_config_dir("corpus")) / "corpus.toml"
DATA_DIR = Path(user_data_dir("corpus"))
```

Then update importers:
- `cli.py`: remove local `CONFIG_PATH` and `DATA_DIR` definitions; add `from corpus_analyzer.config.schema import CONFIG_PATH, DATA_DIR`
- `api/public.py`: remove inline `data_dir = Path(user_data_dir("corpus"))`; add `from corpus_analyzer.config.schema import DATA_DIR`; use `DATA_DIR` directly
- `mcp/server.py`: change `from corpus_analyzer.cli import CONFIG_PATH, DATA_DIR` → `from corpus_analyzer.config.schema import CONFIG_PATH, DATA_DIR`

**Note:** `config/schema.py` currently only imports `pydantic`. Adding `platformdirs` is a new import, but the package is already in `pyproject.toml` (used in `cli.py`).

### Pattern 6: Dead Code Removal

**What:** Delete `needs_reindex()` function from `ingest/scanner.py` (lines 33-56).

**Evidence it is dead code (from audit):** The function is exported but never called anywhere. `indexer.py` implements its own inline hash comparison at line 171 (`if current_hash == stored_hash: files_skipped += 1`). `needs_reindex()` uses a two-stage mtime+hash check; the indexer uses hash-only. The approaches are different by design — the indexer's approach was the deliberate choice.

**Verification before deletion:**
```bash
grep -r "needs_reindex" /home/ollie/Development/Tools/vibe_coding/corpus-analyzer/src/
grep -r "needs_reindex" /home/ollie/Development/Tools/vibe_coding/corpus-analyzer/tests/
```

**Expected result:** Only found in `ingest/scanner.py` itself (definition). If found in tests, those tests also need removal.

### Pattern 7: FTS Index Deduplication

**What:** Remove `self._table.create_fts_index("text", replace=True)` from `CorpusSearch.__init__()` in `search/engine.py` (lines 29-35). The FTS index is already rebuilt at the end of each `index_source()` call in `indexer.py` (line 260). Creating it again on every `CorpusSearch` construction is redundant.

**Risk:** After removal, the FTS index only exists if `corpus index` has been run at least once. If a user constructs `CorpusSearch` before any indexing, no FTS index exists → hybrid search fails. This was the original reason for building it in `__init__()`.

**Resolution:** The use case of "search before any indexing" results in an empty table anyway (no results). The `CorpusSearch.__init__()` FTS call can be removed safely because:
1. Any index-having table will have had `index_source()` called, which builds the FTS index.
2. An empty table has nothing to FTS-search.
3. The existing `# This is idempotent` comment was the only justification — it is idempotent but wasteful.

**Implication for existing test:** `tests/ingest/test_indexer.py:test_index_rebuilds_fts_index` (line 320-334) patches `create_fts_index` and asserts it is called once during `index_source()`. That test remains valid. However, `tests/search/test_engine.py` may have a test that depends on `CorpusSearch.__init__()` building the FTS index — check before removal.

### Anti-Patterns to Avoid

- **Do not restructure the MCP response dict shape** — only add the conditional `content_error` field. Changing `full_content` to `None` (instead of `""`) would break MCP clients already handling the existing response shape.
- **Do not rename `needs_reindex` to something else** — remove it entirely. No callers.
- **Do not add `DATA_DIR` to `__all__` in `config/__init__.py`** unless `CONFIG_PATH` is also added — export them together or neither.
- **Do not change `index_source()` signature** — the `use_llm_classification` parameter stays on the method. The config field just provides the value.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Logging | Custom stderr writer | `import logging; logging.warning(fmt, *args)` | stdlib, already used in `mcp/server.py` |
| Optional dict keys | `result["key"] = None if no_error else val` | Conditional `if error: result["key"] = val` | Keeps key absent on success as required |
| Config field | New config file section | Pydantic `bool` field with default on `SourceConfig` | Existing pattern (`summarize`); TOML round-trips cleanly |

**Key insight:** Every problem in this phase has an existing solution already present in the codebase. No new patterns are needed.

---

## Common Pitfalls

### Pitfall 1: Logging Format — % vs f-string

**What goes wrong:** Using f-strings in `logging.warning(f"msg {val}")` instead of `logging.warning("msg %s", val)`.

**Why it matters:** f-strings are eagerly evaluated even if the log level is filtered out. `%` lazy formatting is the Python logging convention and avoids unnecessary string construction.

**How to avoid:** Always use `logging.warning("text %s", variable)` form — consistent with how `mcp/server.py` already uses it (`logging.warning("Pre-warm failed: %s — ...", exc)`).

### Pitfall 2: content_error as Empty String vs Absent Key

**What goes wrong:** Setting `content_error = ""` in the no-error path and always including it. This contradicts the locked decision that the key is "omitted from the response when there is no error."

**How to avoid:** Use conditional dict key insertion (`if content_error is not None: result_dict["content_error"] = content_error`). Initialize `content_error: str | None = None` before the try/except.

### Pitfall 3: FTS Removal Breaking Hybrid Search

**What goes wrong:** Removing the `CorpusSearch.__init__()` FTS call causes hybrid search to fail on a freshly-opened (but never indexed) table because `query_type="hybrid"` requires an FTS index to exist.

**How to avoid:** This is acceptable — a freshly-opened table with zero records produces zero results whether or not hybrid mode fails gracefully. Verify the existing `test_engine.py` tests pass after removal. If any test constructs `CorpusSearch` on an empty table and expects hybrid search to succeed (rather than return empty), that test assumption is already incorrect.

### Pitfall 4: use_llm_classification Default Mismatch

**What goes wrong:** `SourceConfig.use_llm_classification` defaults to `False` (per locked decision), but `CorpusIndex.index_source()` has `use_llm_classification: bool = True` as its parameter default. If the config field is added but `index_source()` is called without passing `source.use_llm_classification`, the hardcoded parameter default (`True`) wins — breaking the locked "default off" behaviour.

**How to avoid:** When adding the config field, simultaneously update the `index_source()` call site in `indexer.py` (line 152 in `cli.py` actually calls this) to pass `use_llm_classification=source.use_llm_classification`. Also update the parameter default in `index_source()` from `True` to `False` for consistency.

### Pitfall 5: Import Circular Dependency on DATA_DIR Move

**What goes wrong:** `config/schema.py` importing `platformdirs` while `config/__init__.py` imports from `config/schema.py` and `cli.py` imports from `config/__init__.py` — circular import if `cli.py` also defines the constants.

**How to avoid:** Move the definitions to `config/schema.py` and remove them from `cli.py` and `api/public.py`. There is no circular dependency because `config/schema.py` only imports standard library + `pydantic` + `platformdirs` — none of which import from corpus_analyzer. Confirm with a quick import trace before committing.

### Pitfall 6: Tests That Verify the Redundant FTS Call

**What goes wrong:** `tests/ingest/test_indexer.py:test_index_rebuilds_fts_index` patches `create_fts_index` and asserts it is called exactly once. If `CorpusSearch.__init__()` is also calling it (via the `CorpusSearch(index.table, embedder)` construction inside other tests), the call count may differ.

**How to avoid:** Check whether any test in `test_engine.py` or `test_indexer.py` patches or asserts on `create_fts_index` beyond the one explicit test. The explicit test specifically patches `type(index.table).create_fts_index` which targets the LanceDB table method — this test will remain valid after the engine constructor change because it only calls `index.index_source()` and not `CorpusSearch()`.

---

## Code Examples

### CLI-02 Fix (cli.py:203)

```python
# Before (KeyError risk):
f"[dim]score: {result['_relevance_score']:.3f}[/]"

# After (safe):
f"[dim]score: {result.get('_relevance_score', 0.0):.3f}[/]"
```

Source: Direct audit finding in `v1.0-MILESTONE-AUDIT.md`, confirmed by reading `cli.py:203`.

### INGEST-07 Fix (indexer.py)

```python
# Add at top of file:
import logging

# _get_existing_files() — replace lines 299-301:
except Exception as exc:
    logging.warning("Failed to query existing files for source '%s': %s", source_name, exc)
    return {}

# _delete_stale_chunks() — replace lines 353-355:
except Exception as exc:
    logging.warning("Failed to delete stale chunks for source '%s': %s", source_name, exc)
```

### MCP-02 Fix (mcp/server.py:85-98)

```python
# Replace the per-row processing block:
content_error: str | None = None
try:
    full_content = Path(file_path).read_text(errors="replace")
except OSError as exc:
    logging.warning("Cannot read file after indexing: %s — %s", file_path, exc)
    full_content = ""
    content_error = f"File not found: {file_path}"

result_dict: dict[str, Any] = {
    "path": file_path,
    "score": float(row.get("_relevance_score", 0.0)),
    "snippet": extract_snippet(str(row.get("text", "")), query),
    "full_content": full_content,
    "construct_type": str(row.get("construct_type") or "documentation"),
    "summary": str(row.get("summary") or ""),
    "file_type": str(row.get("file_type", "")),
}
if content_error is not None:
    result_dict["content_error"] = content_error
results.append(result_dict)
```

### SourceConfig Extension (config/schema.py)

```python
# Add after existing summarize field (line 61):

use_llm_classification: bool = False
"""Whether to use LLM-based classification for construct type detection.

When True, Ollama is called to classify each changed file during indexing.
When False (default), rule-based classification is used.
Set to True per source for richer classification when LLM cost is acceptable.
"""
```

### Wiring use_llm_classification in indexer.py

```python
# index_source() — update parameter default (line 136) and downstream call:
def index_source(
    self,
    source: SourceConfig,
    progress_callback: Callable[[int], None] | None = None,
    use_llm_classification: bool = False,  # changed from True
) -> IndexResult:
    ...
    # Line 197 — pass source config value:
    construct_type = classify_file(
        file_path,
        full_text,
        model=self._embedder.model,
        use_llm=source.use_llm_classification,  # use config, not parameter
    )
```

**Note:** The `use_llm_classification` parameter on `index_source()` becomes redundant once `source.use_llm_classification` is the control point. It can remain for backward compatibility or be removed — the locked decision says no CLI flag and no API override, so removing the parameter is cleaner. The `api/public.py` and `cli.py` call sites don't pass it anyway.

### VERIFICATION.md Template (retroactive)

```markdown
---
phase: 01-foundation
verification: retroactive
captured: 2026-02-23
audit_source: v1.0-MILESTONE-AUDIT.md
---

# Phase 01: Foundation — Verification (Retroactive)

**Note:** This VERIFICATION.md was captured retroactively as part of Phase 4 (Defensive Hardening).
Verification was performed inline during phase execution and documented in SUMMARY.md frontmatter.
The audit source is `v1.0-MILESTONE-AUDIT.md`, which cross-references all evidence.

## Requirements Status

| Requirement ID | Description | Status | Evidence |
|---------------|-------------|--------|----------|
| CONF-01 | Configure source directories via corpus.toml | SATISFIED | ... |
...
```

---

## State of the Art

| Old Approach | Current Approach | Impact on Phase 4 |
|---|---|---|
| Silent exception swallow | Log + fallback | INGEST-07 fix: adds logging, keeps fallback return |
| Direct dict key access | `.get()` with default | CLI-02 fix: one character change |
| Global constant in CLI module | Constant in config module | DATA_DIR consolidation: move to `config/schema.py` |
| Constructor-time FTS build | Post-index FTS build | FTS dedup: remove one `create_fts_index` call |

---

## Open Questions

1. **Should `needs_reindex()` be in `__all__` or re-exported anywhere?**
   - What we know: The function is defined in `scanner.py` and not called anywhere in the codebase (`grep` confirmed).
   - What's unclear: Whether any external user of the library calls it via `from corpus_analyzer.ingest.scanner import needs_reindex`.
   - Recommendation: Delete it. The package is pre-v1.0 with no published stable API. The CLAUDE.md and REQUIREMENTS.md do not mention a public library API for `ingest.scanner`.

2. **Should `use_llm_classification` parameter be removed from `index_source()` after config wiring?**
   - What we know: The locked decision says "SourceConfig is the single control point." The parameter exists for the current `use_llm_classification: bool = True` default. After the config field is wired, callers (CLI, API) don't pass the parameter.
   - What's unclear: Whether removing a parameter is a breaking change worth caring about at this stage.
   - Recommendation: Remove the parameter from `index_source()` (source is the single control point). Simplifies the method signature and eliminates ambiguity. If needed, it can be re-added as a v2 override.

3. **What is the right `content_error` message format?**
   - What we know: The locked decision says `"File not found: /path/to/file"` as the example format.
   - What's unclear: Whether to include the OSError message itself (e.g. `errno`) for diagnostics.
   - Recommendation (Claude's discretion): `f"File not found: {file_path}"` matches the locked example exactly. Including the raw `exc` message could expose internal paths or OS-specific text — the simple form is safer for MCP clients.

---

## Affected Files — Complete Map

| File | Change Type | What Changes |
|------|-------------|--------------|
| `src/corpus_analyzer/cli.py` | 2-line fix + 1-line import change | Line 203: `.get()` fix; remove `DATA_DIR`/`CONFIG_PATH` definitions; add import from `config/schema` |
| `src/corpus_analyzer/ingest/indexer.py` | 3-line addition | Add `import logging`; replace 2 bare excepts with warning logs; update `use_llm_classification` default + wiring |
| `src/corpus_analyzer/mcp/server.py` | ~10-line refactor | OSError handler adds warning + `content_error` field; update import from `config/schema` |
| `src/corpus_analyzer/config/schema.py` | +20 lines | Add `DATA_DIR`, `CONFIG_PATH` constants; add `use_llm_classification` field to `SourceConfig` |
| `src/corpus_analyzer/api/public.py` | 2-line change | Remove inline `data_dir` definition; import `DATA_DIR` from `config/schema` |
| `src/corpus_analyzer/ingest/scanner.py` | Delete 24 lines | Remove `needs_reindex()` function entirely |
| `src/corpus_analyzer/search/engine.py` | Delete 7 lines | Remove `create_fts_index` call from `CorpusSearch.__init__()` |
| `tests/cli/test_search_status.py` | 1 new test | Add test verifying `.get()` fallback doesn't raise when `_relevance_score` absent |
| `tests/ingest/test_indexer.py` | 2 new tests | Test warning logged on `_delete_stale_chunks` exception; test warning logged on `_get_existing_files` exception |
| `tests/mcp/test_server.py` | 2 new tests | Test `content_error` present on OSError; test `content_error` absent on success |
| `tests/config/test_schema.py` | 1 new test | Test `use_llm_classification` defaults to `False` and is wired through to `index_source()` |
| `tests/ingest/test_scanner.py` | Verify no `needs_reindex` test | Check if any test targets the dead function — delete if so |
| `.planning/phases/01-foundation/01-VERIFICATION.md` | Create (new) | Retroactive capture of phase 1 requirements |
| `.planning/phases/02-search-core/02-VERIFICATION.md` | Create (new) | Retroactive capture of phase 2 requirements |
| `.planning/phases/03-agent-interfaces/03-VERIFICATION.md` | Create (new) | Retroactive capture of phase 3 requirements |

---

## Sources

### Primary (HIGH confidence)

- Direct codebase inspection — `cli.py`, `indexer.py`, `mcp/server.py`, `config/schema.py`, `api/public.py`, `ingest/scanner.py`, `search/engine.py`
- `.planning/v1.0-MILESTONE-AUDIT.md` — audit findings, severity ratings, line-number references
- `.planning/phases/04-hardening/04-CONTEXT.md` — locked decisions

### Secondary (MEDIUM confidence)

- Python stdlib `logging` module conventions — `%`-style lazy formatting is documented standard practice; consistent with existing usage in `mcp/server.py`

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — no new libraries; all changes use existing dependencies
- Architecture: HIGH — all patterns directly visible in codebase; no external API uncertainty
- Pitfalls: HIGH — identified from codebase analysis, not speculation

**Research date:** 2026-02-23
**Valid until:** This research describes code at a specific git state. Valid indefinitely unless the files listed in "Affected Files" are modified by other means.

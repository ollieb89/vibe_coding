# Phase 14: API / MCP / CLI Parity - Research

**Researched:** 2026-02-24
**Domain:** Python public API, FastMCP server, Typer CLI — parameter forwarding and help-text additions
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### sort_by values
- Valid values: `score`, `date`, `title`
- Default when omitted: `score`
- Invalid values raise `ValueError` with a message listing valid options

#### sort_by exposure
- `--sort-by` flag added to CLI `corpus search` in this phase (full parity across all three surfaces)
- `sort_by` parameter on Python `search()` API
- `sort_by` parameter on MCP `corpus_search` tool

### Claude's Discretion
- Empty-results hint behavior for Python API and MCP (only CLI hint message was specified in requirements)
- `--min-score` help text depth and RRF explanation wording
- MCP response shape when `min_score` filters all results

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FILT-02 | `--min-score` help text documents the RRF score range (~0.009–0.033) so users can calibrate thresholds | CLI `search_command` in `cli.py` needs `--min-score` option added with descriptive help string |
| FILT-03 | When `--min-score` filters all results, user sees: "No results above X.xxx. Run without --min-score to see available scores." | CLI `search_command` must detect filtered-all state and print contextual hint |
| PARITY-01 | Python `search()` API accepts `sort_by` parameter (engine already supports it; wrapper does not currently forward it) | `api/public.py` `search()` must accept `sort_by` and forward to `engine.hybrid_search()` |
| PARITY-02 | Python `search()` API accepts `min_score` parameter | `api/public.py` `search()` must accept `min_score` and forward to `engine.hybrid_search()` |
| PARITY-03 | MCP `corpus_search` tool accepts `min_score` parameter | `mcp/server.py` `corpus_search()` must add `min_score: Optional[float]` parameter |
</phase_requirements>

## Summary

Phase 14 is pure interface-parity work. The engine (`CorpusSearch.hybrid_search()`) already accepts both `min_score` (Phase 13, complete) and `sort_by` (pre-existing). The task is to wire these parameters through the three call surfaces: the Typer CLI command, the Python public API wrapper, and the FastMCP tool. No new engine logic is needed.

The scope is well-bounded: five requirements, four files to modify (`cli.py`, `api/public.py`, `mcp/server.py`, and tests across `tests/cli/test_search_status.py`, `tests/api/test_public.py`, `tests/mcp/test_server.py`). The largest risk is the `sort_by` value mismatch between the locked CONTEXT.md decisions (`score`, `date`, `title`) and the engine's existing valid set (`relevance`, `construct`, `confidence`, `date`, `path`). The resolution is a translation layer in each caller surface, or a new API-level sort-value set applied only to the public API and MCP while keeping the CLI's existing `--sort` flag unchanged and adding `--sort-by` as the new parity flag.

**Primary recommendation:** Add `--min-score` to the CLI with in-flag help text quoting the RRF range, detect the filtered-all case post-call to print the FILT-03 hint, then add `sort_by` and `min_score` to `search()` and `corpus_search()` with direct forwarding to `engine.hybrid_search()`. Keep the test for `SearchResult` fields passing (it uses exact-set `==`; no new fields on the dataclass are needed).

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Typer | project-pinned | CLI parameter declarations | Already used; `typer.Option()` with `help=` is the established pattern |
| FastMCP | project-pinned | MCP tool parameter declarations | Already used; `Optional[float]` + `# noqa: UP045` is the established pattern from existing params |
| pytest | project-pinned | Test runner | Project standard; all tests use pytest only (no unittest) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `unittest.mock` (stdlib) | stdlib | Patching `_open_engine`, `CorpusSearch`, etc. | All existing API and CLI tests already use this pattern |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Translation layer (API values → engine values) | Extend engine `_VALID_SORT_VALUES` | Extending engine is out of scope for Phase 14; translation layer is self-contained in each caller |

**Installation:** No new dependencies required.

---

## Architecture Patterns

### Recommended Project Structure

No new files needed. All changes are in-place modifications:

```
src/corpus_analyzer/
├── cli.py                  # Add --min-score option + FILT-03 hint + --sort-by option
├── api/public.py           # Add sort_by, min_score params to search()
└── mcp/server.py           # Add min_score: Optional[float] to corpus_search()

tests/
├── cli/test_search_status.py   # New tests: FILT-02, FILT-03, --sort-by
├── api/test_public.py          # New tests: PARITY-01, PARITY-02
└── mcp/test_server.py          # New test: PARITY-03
```

### Pattern 1: Typer Option with Descriptive Help (FILT-02)

**What:** Add `--min-score` as an `Annotated[float, typer.Option(...)]` parameter to `search_command`. Help text must quote the RRF range.

**When to use:** Any new CLI parameter — follows existing style in the file.

**Example (based on existing patterns in `cli.py`):**
```python
min_score: Annotated[
    float,
    typer.Option(
        "--min-score",
        help=(
            "Exclude results below this RRF score threshold. "
            "RRF scores range approximately 0.009–0.033; "
            "0.0 keeps all results (default)."
        ),
    ),
] = 0.0,
```

The value is then forwarded directly to `hybrid_search(min_score=min_score)`.

### Pattern 2: FILT-03 Contextual Hint (filtered-all detection)

**What:** After `hybrid_search()` returns results, check if `min_score > 0.0` AND results are empty (the call returned `[]`). If so, print the FILT-03 message.

**When to use:** Only in the CLI `search_command`, not in API or MCP (left to discretion).

**Key insight:** The detection must happen AFTER the engine call. The engine itself returns `[]` when all results are filtered; the caller checks the combination of `(results == [] and min_score > 0.0)` to decide between "genuinely no results" and "filtered-all".

```python
results = search.hybrid_search(query, ..., min_score=min_score)

if not results:
    if min_score > 0.0:
        console.print(
            f"No results above {min_score:.3f}. "
            "Run without --min-score to see available scores."
        )
    else:
        console.print(f'[yellow]No results for "[bold]{query}[/bold]"[/yellow]')
    return
```

Note: The exact FILT-03 message from REQUIREMENTS.md is:
`"No results above X.xxx. Run without --min-score to see available scores."`
The `X.xxx` placeholder is the threshold value formatted to 3 decimal places.

### Pattern 3: sort_by Translation Layer

**What:** The CONTEXT.md locks `sort_by` values to `score`, `date`, `title` for the public API/MCP. The engine's `_VALID_SORT_VALUES` is `{relevance, construct, confidence, date, path}`.

**Resolution:** The locked decision values map to engine values as follows:
- `score` → `relevance` (default RRF order)
- `date` → `date` (direct passthrough)
- `title` → `path` (alphabetical by file path — closest meaningful equivalent)

**Implementation pattern for `api/public.py` and `mcp/server.py`:**
```python
_API_SORT_MAP: dict[str, str] = {
    "score": "relevance",
    "date": "date",
    "title": "path",
}
_VALID_API_SORT_VALUES = frozenset(_API_SORT_MAP.keys())

def search(query, ..., sort_by: str = "score") -> list[SearchResult]:
    if sort_by not in _VALID_API_SORT_VALUES:
        raise ValueError(
            f"Invalid sort_by value: {sort_by!r}. "
            f"Allowed values: {sorted(_VALID_API_SORT_VALUES)}"
        )
    engine_sort = _API_SORT_MAP[sort_by]
    raw = engine.hybrid_search(query, ..., sort_by=engine_sort)
```

Alternatively, the translation could live in `api/public.py` only, and the MCP server could reuse the same mapping. A shared helper in `api/public.py` (or even inline in each file) is acceptable given the small size.

**Important:** The CLI's existing `--sort` flag uses the engine's native values and MUST NOT be changed — it is marked out of scope in REQUIREMENTS.md ("Already fully implemented in v1.3"). The NEW `--sort-by` flag added to the CLI for Phase 14 should use the API-level values (`score`, `date`, `title`).

### Pattern 4: FastMCP Optional Parameter (PARITY-03)

**What:** Add `min_score: Optional[float] = None` to `corpus_search()` in `mcp/server.py`.

**Critical detail from STATE.md:** FastMCP `Optional[float]` parameters require `# noqa: UP045` comment to pass ruff. Copy the existing parameter pattern exactly.

```python
@mcp.tool
async def corpus_search(
    query: str,
    source: Optional[str] = None,  # noqa: UP045
    type: Optional[str] = None,  # noqa: UP045
    construct: Optional[str] = None,  # noqa: UP045
    top_k: Optional[int] = 5,  # noqa: UP045
    min_score: Optional[float] = None,  # noqa: UP045
    ctx: Context = None,  # type: ignore[assignment]
) -> dict[str, Any]:
```

The `min_score` value is passed to `engine.hybrid_search()` as `min_score=min_score if min_score is not None else 0.0`. A `None` default is used rather than `0.0` so the MCP schema signals "optional" to clients.

### Pattern 5: Python API Parameter Addition (PARITY-01, PARITY-02)

**What:** Add `sort_by: str = "score"` and `min_score: float = 0.0` to the `search()` function in `api/public.py`.

**Key constraint from STATE.md:** `tests/api/test_public.py:18` uses exact-set `==` for `SearchResult` fields — no new fields may be added to the `SearchResult` dataclass. Both `sort_by` and `min_score` are parameters of the `search()` *function*, not fields of the `SearchResult` dataclass. No dataclass change is needed. The constraint is satisfied.

**Existing test that must continue to pass (`test_search_passes_filters_to_hybrid_search`):**
```python
mock_engine.hybrid_search.assert_called_once_with(
    "q",
    source="my-source",
    file_type=".py",
    construct_type="code",
    limit=5,
)
```
This test does NOT pass `sort_by` or `min_score`, so after the change, `hybrid_search` will be called with additional kwargs. **This existing test will BREAK** if the new parameters are added to the call signature unconditionally — it uses `assert_called_once_with` which is an exact-match assertion.

**Resolution:** The existing test must be updated to include the new keyword arguments in its assertion:
```python
mock_engine.hybrid_search.assert_called_once_with(
    "q",
    source="my-source",
    file_type=".py",
    construct_type="code",
    limit=5,
    sort_by="relevance",   # mapped from default "score"
    min_score=0.0,
)
```
Similarly, `test_search_calls_hybrid_search_and_maps_to_dataclasses` must be updated.

**MCP parallel:** `test_corpus_search_passes_filters_to_hybrid_search` also uses `assert_called_once_with` — it must be updated to include `min_score=0.0` (or the resolved `None`-to-default value) when `min_score` is added.

### Anti-Patterns to Avoid

- **Adding fields to `SearchResult`:** The exact-set test at `tests/api/test_public.py:18` will fail. `sort_by` and `min_score` are function parameters, not result fields.
- **Modifying the engine's `_VALID_SORT_VALUES`:** Phase 14 is interface-only; engine changes are out of scope and could break Phase 13 tests.
- **Changing the existing `--sort` CLI option:** It is explicitly marked out of scope in REQUIREMENTS.md as "Already fully implemented in v1.3".
- **Using `UP045` ruff rule violation:** FastMCP requires `Optional[float]` syntax (not `float | None`) — always add `# noqa: UP045`.
- **Forgetting to update existing `assert_called_once_with` tests:** Adding new kwargs to `hybrid_search()` calls will break the exact-match assertions in existing tests.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| `sort_by` validation | Custom validation logic | Inline `if sort_by not in _VALID_API_SORT_VALUES: raise ValueError` | Engine already has a working precedent; copy the pattern |
| `min_score` detection | New database query or secondary call | Post-call check `(not results and min_score > 0.0)` | Engine already does the filtering; the caller just inspects the empty result |
| FastMCP parameter registration | Manual schema injection | Standard `Optional[float] = None` with `# noqa: UP045` | FastMCP infers parameter schema from Python type annotations |

**Key insight:** Every required capability is already in the engine. This phase is entirely about plumbing.

---

## Common Pitfalls

### Pitfall 1: Breaking Exact-Match Assertion Tests
**What goes wrong:** Adding `sort_by` and `min_score` to `hybrid_search()` calls breaks `assert_called_once_with()` in existing tests.
**Why it happens:** `assert_called_once_with` is an exact-match assertion — any extra kwargs cause failure.
**How to avoid:** When adding kwargs to an existing `hybrid_search()` call in a tested function, update the corresponding `assert_called_once_with` to include the new kwargs.
**Affected tests:**
- `tests/api/test_public.py::test_search_calls_hybrid_search_and_maps_to_dataclasses`
- `tests/api/test_public.py::test_search_passes_filters_to_hybrid_search`
- `tests/mcp/test_server.py::test_corpus_search_passes_filters_to_hybrid_search`

### Pitfall 2: ruff UP045 Violation in FastMCP Params
**What goes wrong:** Writing `min_score: float | None = None` instead of `Optional[float]` causes ruff to fail.
**Why it happens:** FastMCP parameter inference requires `Optional[T]` syntax; ruff UP045 would normally flag `Optional` as old-style, creating a contradiction.
**How to avoid:** Copy the existing `Optional[str] = None  # noqa: UP045` pattern from all other `corpus_search` parameters.

### Pitfall 3: sort_by Value Mismatch
**What goes wrong:** Passing API-level `sort_by` value (`score`) directly to the engine raises `ValueError` because `score` is not in `_VALID_SORT_VALUES`.
**Why it happens:** The API-level vocabulary (`score`, `date`, `title`) differs from the engine vocabulary (`relevance`, `construct`, `confidence`, `date`, `path`).
**How to avoid:** Apply the translation map before calling `engine.hybrid_search()`.

### Pitfall 4: FILT-03 Hint Message Format
**What goes wrong:** Hint message doesn't match the REQUIREMENTS.md specification.
**Why it happens:** Improvised wording.
**How to avoid:** Requirements.md specifies exactly: `"No results above X.xxx. Run without --min-score to see available scores."` where `X.xxx` is `f"{min_score:.3f}"`.

---

## Code Examples

### CLI: Adding --min-score (FILT-02)

Current `search_command` signature ends with:
```python
sort: Annotated[
    str,
    typer.Option("--sort", help="Sort order: relevance|construct|confidence|date|path"),
] = "relevance",
```

Add after `sort`:
```python
min_score: Annotated[
    float,
    typer.Option(
        "--min-score",
        help=(
            "Exclude results below this RRF score threshold. "
            "RRF scores range approximately 0.009–0.033 (K=60); "
            "0.0 keeps all results (default)."
        ),
    ),
] = 0.0,
sort_by: Annotated[
    str,
    typer.Option(
        "--sort-by",
        help="Sort order for API/MCP parity: score|date|title",
    ),
] = "score",
```

### CLI: FILT-03 Hint Detection

Replace the current "no results" block in `search_command`:
```python
# BEFORE:
if not results:
    console.print(f'[yellow]No results for "[bold]{query}[/bold]"[/yellow]')
    return

# AFTER:
if not results:
    if min_score > 0.0:
        console.print(
            f"No results above {min_score:.3f}. "
            "Run without --min-score to see available scores."
        )
    else:
        console.print(f'[yellow]No results for "[bold]{query}[/bold]"[/yellow]')
    return
```

### Python API: Adding sort_by + min_score (PARITY-01, PARITY-02)

```python
_API_SORT_MAP: dict[str, str] = {
    "score": "relevance",
    "date": "date",
    "title": "path",
}
_VALID_API_SORT_VALUES = frozenset(_API_SORT_MAP.keys())


def search(
    query: str,
    *,
    source: str | None = None,
    file_type: str | None = None,
    construct_type: str | None = None,
    limit: int = 10,
    sort_by: str = "score",
    min_score: float = 0.0,
) -> list[SearchResult]:
    if sort_by not in _VALID_API_SORT_VALUES:
        raise ValueError(
            f"Invalid sort_by value: {sort_by!r}. "
            f"Allowed values: {sorted(_VALID_API_SORT_VALUES)}"
        )
    engine, _ = _open_engine()
    raw = engine.hybrid_search(
        query,
        source=source,
        file_type=file_type,
        construct_type=construct_type,
        limit=limit,
        sort_by=_API_SORT_MAP[sort_by],
        min_score=min_score,
    )
    return [...]
```

### MCP: Adding min_score (PARITY-03)

```python
@mcp.tool
async def corpus_search(
    query: str,
    source: Optional[str] = None,  # noqa: UP045
    type: Optional[str] = None,  # noqa: UP045
    construct: Optional[str] = None,  # noqa: UP045
    top_k: Optional[int] = 5,  # noqa: UP045
    min_score: Optional[float] = None,  # noqa: UP045
    ctx: Context = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """..."""
    ...
    raw_results = engine.hybrid_search(
        query,
        source=source,
        file_type=type,
        construct_type=construct,
        limit=limit,
        min_score=min_score if min_score is not None else 0.0,
    )
```

For MCP empty-results hint (Claude's discretion): include a `"filtered_by_min_score": true` key in the `{"results": [], "message": "..."}` response when `min_score` is set and results are empty. This gives agents a programmatic signal without requiring message parsing.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Engine without min_score | Engine with min_score (Phase 13) | 2026-02-24 | Callers can now forward `min_score`; no engine work needed in Phase 14 |
| CLI only for min_score | CLI + API + MCP (Phase 14) | This phase | Full parity |

---

## Open Questions

1. **Does `--sort-by` on CLI replace or coexist with `--sort`?**
   - What we know: CONTEXT.md says "full parity across all three surfaces"; REQUIREMENTS.md marks `--sort` as out of scope and already complete.
   - What's unclear: Whether the existing `--sort` flag is kept alongside `--sort-by`, or if `--sort-by` supersedes it.
   - Recommendation: Keep `--sort` as-is (existing CLI flag, fully implemented) and add `--sort-by` as a separate flag with the API-level vocabulary (`score|date|title`). Both are forwarded to `hybrid_search()` via their respective maps. If both are supplied, `--sort-by` should take precedence (or they could be mutually exclusive — planner to decide).

2. **MCP empty-results hint response shape**
   - What we know: Requirements only specify the CLI hint. MCP response shape is Claude's discretion.
   - Recommendation: Add `"filtered_by_min_score": true` boolean to the no-results dict when `min_score` is set and non-zero.

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection of `src/corpus_analyzer/cli.py` — `search_command` signature and body
- Direct code inspection of `src/corpus_analyzer/api/public.py` — `search()` function and `SearchResult` dataclass
- Direct code inspection of `src/corpus_analyzer/mcp/server.py` — `corpus_search()` tool signature
- Direct code inspection of `src/corpus_analyzer/search/engine.py` — `hybrid_search()` signature and `_VALID_SORT_VALUES`
- Direct code inspection of `tests/api/test_public.py` — exact-set constraint on `SearchResult` fields
- Direct code inspection of `tests/mcp/test_server.py` — `assert_called_once_with` patterns
- Direct code inspection of `tests/cli/test_search_status.py` — existing CLI test patterns
- `.planning/STATE.md` — accumulated decisions (FastMCP noqa pattern, SearchResult field constraint)
- `.planning/REQUIREMENTS.md` — FILT-02, FILT-03, PARITY-01, PARITY-02, PARITY-03 specifications

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in use; no new dependencies
- Architecture: HIGH — all four files directly inspected; call sites identified
- Pitfalls: HIGH — exact-match test failures and ruff noqa pattern verified from live code

**Research date:** 2026-02-24
**Valid until:** 2026-03-25 (stable internal codebase — 30 days)

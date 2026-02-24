---
phase: 14-api-mcp-cli-parity
verified: 2026-02-24T07:30:00Z
status: passed
score: 8/8 must-haves verified
re_verification: false
---

# Phase 14: API / MCP / CLI Parity Verification Report

**Phase Goal:** Users can control min-score filtering and result sort order through all three interfaces — CLI, Python API, and MCP — with a contextual hint when filtering eliminates all results
**Verified:** 2026-02-24T07:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | `corpus search --min-score` only shows results with RRF score >= threshold | VERIFIED | `cli.py:386` forwards `min_score=min_score` to `hybrid_search()`; Phase 13 engine applies the filter |
| 2 | `corpus search --help` shows RRF score range (~0.009–0.033) in `--min-score` help text | VERIFIED | `cli.py:337-342`: help text contains "RRF scores range approximately 0.009–0.033 (K=60); 0.0 keeps all results (default)"; `test_min_score_option_help_text` passes |
| 3 | `corpus search --min-score 99` (filters everything) prints FILT-03 hint, not generic no-results message | VERIFIED | `cli.py:392-400`: branch on `min_score > 0.0` prints "No results above {min_score:.3f}. Run without --min-score to see available scores."; `test_min_score_filters_all_prints_hint` passes |
| 4 | `corpus search --sort-by score|date|title` is accepted and forwarded to `hybrid_search()` via translation map | VERIFIED | `cli.py:300-305` defines `_CLI_SORT_BY_MAP`; `cli.py:367-376` validates and translates; `test_sort_by_option_forwards_to_engine` confirms score→relevance, title→path |
| 5 | Python `search()` API accepts `sort_by` and `min_score` and forwards them to `hybrid_search()` via translation map | VERIFIED | `api/public.py:79-84` defines `_API_SORT_MAP`; `api/public.py:94-95` adds params; `api/public.py:127-128` forwards translated values; `test_search_sort_by_translates_and_forwards` and `test_search_min_score_forwarded` pass |
| 6 | Invalid `sort_by` values raise `ValueError` listing the three valid options | VERIFIED | `api/public.py:115-119` raises `ValueError(f"Invalid sort_by value: {sort_by!r}. Allowed values: {sorted(_VALID_API_SORT_VALUES)}")` before engine call; `test_search_invalid_sort_by_raises_value_error` passes |
| 7 | MCP `corpus_search` tool accepts `min_score: Optional[float]` and passes it to `hybrid_search()` as 0.0 when None | VERIFIED | `mcp/server.py:49`: `min_score: Optional[float] = None  # noqa: UP045`; `mcp/server.py:68`: `effective_min_score = min_score if min_score is not None else 0.0`; `mcp/server.py:77`: `min_score=effective_min_score`; `test_corpus_search_min_score_forwarded` and `test_corpus_search_min_score_none_uses_zero` pass |
| 8 | All 293 tests pass; `ruff check .` and `mypy src/` both exit 0 | VERIFIED | `uv run pytest -q`: 293 passed; `uv run ruff check .`: All checks passed; `uv run mypy src/`: Success: no issues found in 53 source files |

**Score:** 8/8 truths verified

---

## Required Artifacts

### Plan 01 Artifacts (FILT-02, FILT-03)

| Artifact | Provides | Status | Details |
|----------|----------|--------|---------|
| `src/corpus_analyzer/cli.py` | `_CLI_SORT_BY_MAP`, `_VALID_CLI_SORT_BY_VALUES`, `--min-score` option, `--sort-by` option, FILT-03 hint logic | VERIFIED | `_CLI_SORT_BY_MAP` at line 300; `--min-score` at lines 333-343; `--sort-by` at lines 344-350; FILT-03 branch at lines 392-400; "No results above" at line 395 |
| `tests/cli/test_search_status.py` | Tests for FILT-02 help text, FILT-03 hint, `--sort-by` forwarding | VERIFIED | `test_min_score_option_help_text` (line 202), `test_min_score_filters_all_prints_hint` (line 217), `test_sort_by_option_forwards_to_engine` (line 242) — all 3 pass |

### Plan 02 Artifacts (PARITY-01, PARITY-02, PARITY-03)

| Artifact | Provides | Status | Details |
|----------|----------|--------|---------|
| `src/corpus_analyzer/api/public.py` | `_API_SORT_MAP`, `_VALID_API_SORT_VALUES`, `sort_by` + `min_score` params on `search()` | VERIFIED | `_API_SORT_MAP` at line 79; `_VALID_API_SORT_VALUES` at line 84; params at lines 94-95; validation at lines 115-119; forwarding at lines 127-128 |
| `src/corpus_analyzer/mcp/server.py` | `min_score: Optional[float] = None` parameter on `corpus_search()` | VERIFIED | `Optional[float] = None` at line 49 with `# noqa: UP045`; None→0.0 conversion at line 68; `min_score=effective_min_score` at line 77; `filtered_by_min_score: True` at line 90 |
| `tests/api/test_public.py` | Tests for PARITY-01, PARITY-02; updated exact-match assertions | VERIFIED | `test_search_sort_by_translates_and_forwards` (line 128), `test_search_invalid_sort_by_raises_value_error` (line 151), `test_search_min_score_forwarded` (line 165); updated `assert_called_once_with` at lines 60-68 and 82-90 include `sort_by="relevance"` and `min_score=0.0` |
| `tests/mcp/test_server.py` | Test for PARITY-03; updated exact-match assertion | VERIFIED | `test_corpus_search_min_score_forwarded` (line 166), `test_corpus_search_min_score_none_uses_zero` (line 182); updated `assert_called_once_with` at lines 156-163 includes `min_score=0.0` |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `cli.py search_command` | `engine.hybrid_search()` | `min_score=min_score` kwarg | WIRED | `cli.py:386`: `min_score=min_score,` inside `search.hybrid_search(query, ...)` call |
| `cli.py search_command` | FILT-03 hint | `if not results and min_score > 0.0:` branch | WIRED | `cli.py:392-400`: exact branch and message format confirmed |
| `api/public.py search()` | `engine.hybrid_search()` | `sort_by=_API_SORT_MAP[sort_by], min_score=min_score` kwargs | WIRED | `api/public.py:127-128`: both kwargs in the `raw = engine.hybrid_search(...)` call |
| `mcp/server.py corpus_search()` | `engine.hybrid_search()` | `min_score=min_score if min_score is not None else 0.0` | WIRED | `mcp/server.py:68-77`: `effective_min_score` computed then passed as `min_score=effective_min_score` |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| FILT-02 | 14-01 | `--min-score` help text documents the RRF score range (~0.009–0.033) | SATISFIED | `cli.py:337-342` contains exact range string; `test_min_score_option_help_text` asserts "RRF scores range approximately", "0.009", "0.0 keeps all results" |
| FILT-03 | 14-01 | When `--min-score` filters all results, user sees contextual hint "No results above X.xxx. Run without --min-score to see available scores." | SATISFIED | `cli.py:394-397` prints exact message; `test_min_score_filters_all_prints_hint` asserts both message tokens and absence of generic no-results message |
| PARITY-01 | 14-02 | Python `search()` API accepts `sort_by` parameter | SATISFIED | `api/public.py:94` adds `sort_by: str = "score"`; translation map at lines 79-84; ValueError on invalid value at lines 115-119 |
| PARITY-02 | 14-02 | Python `search()` API accepts `min_score` parameter | SATISFIED | `api/public.py:95` adds `min_score: float = 0.0`; forwarded at line 128 |
| PARITY-03 | 14-02 | MCP `corpus_search` tool accepts `min_score` parameter | SATISFIED | `mcp/server.py:49` adds `min_score: Optional[float] = None`; None→0.0 conversion and forwarding at lines 68-77 |

All 5 requirement IDs from plan frontmatter are accounted for. REQUIREMENTS.md confirms all are marked Complete with Phase 14 assignment. No orphaned requirements found.

---

## Anti-Patterns Found

No anti-patterns found in Phase 14 source files (`cli.py`, `api/public.py`, `mcp/server.py`).

Scan of `return []`, `return {}`, `TODO`, `FIXME`, `PLACEHOLDER` patterns found matches only in pre-existing files outside Phase 14 scope (`llm/rewriter.py`, `generators/advanced_rewriter.py`, `ingest/chunker.py`). These are not introduced by this phase and represent legitimate business logic (template placeholder handling in the LLM rewriting subsystem).

---

## Human Verification Required

None. All behaviors are verifiable via unit tests and static analysis:

- CLI option presence and help text: tested via `CliRunner` with `["search", "--help"]`
- FILT-03 hint: tested via mocked engine returning empty list
- `--sort-by` translation: tested via `call_args.kwargs` assertion
- API `ValueError`: tested via `pytest.raises`
- MCP None→0.0 conversion: tested via `call_args[1]["min_score"]` assertion

---

## Summary

Phase 14 goal is fully achieved. All three interfaces (CLI, Python API, MCP) now expose min-score filtering and sort-order control with consistent API vocabulary, and the FILT-03 contextual hint fires correctly when filtering eliminates all results.

- CLI: `--min-score` with RRF range help text and `--sort-by score|date|title` translation map, both wired to `hybrid_search()`
- Python API: `search()` gains `sort_by` (with `_API_SORT_MAP` translation and `ValueError` on invalid values) and `min_score` forwarded directly
- MCP: `corpus_search()` gains `min_score: Optional[float]` with explicit None→0.0 conversion and `filtered_by_min_score` programmatic signal on empty filtered results
- 293 tests pass, ruff clean, mypy clean

---

_Verified: 2026-02-24T07:30:00Z_
_Verifier: Claude (gsd-verifier)_

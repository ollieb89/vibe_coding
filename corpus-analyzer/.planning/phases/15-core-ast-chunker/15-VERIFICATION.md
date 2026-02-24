---
phase: 15-core-ast-chunker
verified: 2026-02-24T09:00:00Z
status: passed
score: 5/5 success criteria verified
gaps: []
human_verification: []
---

# Phase 15: Core AST Chunker Verification Report

**Phase Goal:** Users can index `.ts`, `.tsx`, `.js`, and `.jsx` files with AST-aware chunking that extracts named top-level constructs at the same precision as the Python chunker
**Verified:** 2026-02-24T09:00:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `uv sync` succeeds after adding `tree-sitter>=0.25.0` and `tree-sitter-language-pack>=0.13.0` to `pyproject.toml` with no C toolchain required | VERIFIED | `pyproject.toml` lines 20-21 contain both deps; `uv run python -c "from tree_sitter_language_pack import get_parser; get_parser('typescript')"` prints "OK" |
| 2 | `chunk_typescript()` extracts all eight target node types as separate chunks with correct 1-indexed line boundaries | VERIFIED | `_TARGET_TYPES` frozenset in `ts_chunker.py` lines 24-33 contains all 8 types; 8 test methods each pass GREEN (test_function_extraction, test_generator_extraction, test_class_extraction, test_abstract_class_extraction, test_interface_extraction, test_type_alias_extraction, test_lexical_declaration_extraction, test_enum_extraction) |
| 3 | `export function foo()` and `export class Bar` produce chunks with the full exported text — export-unwrapping verified by test assertion | VERIFIED | `ts_chunker.py` lines 130-155 unwrap `export_statement`; `test_export_function_unwrapping` asserts `"export function foo" in chunks[0]["text"]` and `chunk_name == "foo"` — PASSED; `test_export_class_unwrapping` asserts `"export class Bar" in chunks[0]["text"]` — PASSED; `test_export_default_function` asserts `chunk_name == "default"` — PASSED |
| 4 | `.tsx` and `.jsx` files parse JSX syntax without fallback; `.ts` uses the TypeScript grammar; `.js` uses the JavaScript grammar | VERIFIED | `_DIALECT` map in `ts_chunker.py` lines 17-22: `{".ts": "typescript", ".tsx": "tsx", ".js": "javascript", ".jsx": "tsx"}`; `test_jsx_in_tsx_parses` and `test_jsx_in_jsx_parses` both PASSED; `TestChunkFile` dispatch tests for all four extensions PASSED |
| 5 | `TestChunkTypeScript` passes with all cases adapted from `TestChunkPython`; `has_error` partial tree does NOT fall back; catastrophic failure DOES fall back; `TestChunkFile` dispatch assertions cover all four extensions | VERIFIED | `uv run pytest tests/ingest/test_chunker.py::TestChunkTypeScript tests/ingest/test_chunker.py::TestChunkFile -v` → 29/29 PASSED; `test_has_error_does_not_fall_back` PASSED; `test_catastrophic_failure_falls_back` PASSED |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/corpus_analyzer/ingest/ts_chunker.py` | `chunk_typescript`, `_get_cached_parser`, `_extract_name`, `_DIALECT`, `_TARGET_TYPES` | VERIFIED | 198 lines; all five exports present; substantive implementation with real AST logic; imported and called by `chunker.py` |
| `src/corpus_analyzer/ingest/chunker.py` | Updated `chunk_file()` dispatch for `.ts/.tsx/.js/.jsx` | VERIFIED | Lines 355-357 contain `elif ext in (".ts", ".tsx", ".js", ".jsx"):` with lazy import of `chunk_typescript` |
| `pyproject.toml` | `tree-sitter>=0.25.0` and `tree-sitter-language-pack>=0.13.0` + mypy overrides | VERIFIED | Lines 20-21 contain both deps; `[[tool.mypy.overrides]]` block for `tree_sitter` and `tree_sitter_language_pack` present |
| `tests/ingest/test_chunker.py` | `TestChunkTypeScript` (21 methods) + updated `TestChunkFile` (4 dispatch tests) | VERIFIED | 22 methods in `TestChunkTypeScript` (plan specified 21; one extra `test_jsdoc_blank_line_not_included` added); 4 dispatch tests for `.ts/.tsx/.js/.jsx` present |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/corpus_analyzer/ingest/chunker.py` | `src/corpus_analyzer/ingest/ts_chunker.py` | lazy import in `chunk_file()` elif branch | WIRED | `from corpus_analyzer.ingest.ts_chunker import chunk_typescript` at line 356; all 4 dispatch tests pass |
| `src/corpus_analyzer/ingest/ts_chunker.py` | `tree_sitter_language_pack` | `_get_cached_parser(dialect)` calling `get_parser(dialect)` | WIRED | `get_parser` imported at module level (line 15); `@lru_cache` on `_get_cached_parser` (line 36); `test_parser_cache` PASSED |
| `tests/ingest/test_chunker.py` | `src/corpus_analyzer/ingest/ts_chunker.py` | `from corpus_analyzer.ingest.ts_chunker import chunk_typescript` | WIRED | Module-level import at line 15; all 22 `TestChunkTypeScript` tests PASSED |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DEP-01 | 15-02-PLAN.md | `pyproject.toml` updated with tree-sitter deps; `uv sync` succeeds with pre-compiled wheels | SATISFIED | Both deps in `pyproject.toml`; `get_parser('typescript')` prints "OK" with no C toolchain errors |
| IDX-01 | 15-02-PLAN.md | `chunk_file()` dispatch routes `.ts`, `.tsx`, `.js`, `.jsx` to `chunk_typescript()` | SATISFIED | `chunker.py` line 355 elif branch; all 4 `TestChunkFile` dispatch tests PASSED |
| IDX-02 | 15-02-PLAN.md | `chunk_typescript()` extracts 8 top-level construct types | SATISFIED | `_TARGET_TYPES` contains all 8; 8 extraction test methods PASSED |
| IDX-03 | 15-02-PLAN.md | `export_statement` nodes unwrapped — full exported text + inner line boundaries | SATISFIED | Lines 130-155 of `ts_chunker.py`; `test_export_function_unwrapping` and `test_export_class_unwrapping` PASSED |
| IDX-04 | 15-02-PLAN.md | Grammar dispatched by extension: `typescript`/`tsx`/`javascript` | SATISFIED | `_DIALECT` map; `test_jsx_in_tsx_parses`, `test_jsx_in_jsx_parses` PASSED |
| IDX-05 | 15-02-PLAN.md | Fallback to `chunk_lines()` on exception or zero constructs; NOT on `has_error` alone | SATISFIED | `ts_chunker.py` line 194 fallback on empty chunks; no fallback on `has_error`; `test_has_error_does_not_fall_back` and `test_catastrophic_failure_falls_back` PASSED |
| IDX-06 | 15-02-PLAN.md | Returned chunk dict includes `chunk_name` field | SATISFIED | Every `chunks.append()` call includes `"chunk_name": chunk_name`; `test_chunk_name_field_present` PASSED |
| IDX-07 | 15-02-PLAN.md | Parser loader uses `@lru_cache` — grammar loaded once per dialect per process | SATISFIED | `@lru_cache(maxsize=8)` on `_get_cached_parser()` at line 36; `test_parser_cache` PASSED |
| TEST-01 | 15-01-PLAN.md | `TestChunkTypeScript` at full parity with `TestChunkPython` — all construct types, line-range accuracy, JSX, non-ASCII, `has_error`, catastrophic failure | SATISFIED | 22 test methods covering all named cases; all PASSED |
| TEST-02 | 15-01-PLAN.md | `TestChunkFile` dispatch assertions for all four extensions; `.ts` line-based test updated | SATISFIED | `test_dispatches_ts_to_chunk_typescript`, `test_dispatches_tsx_to_chunk_typescript`, `test_dispatches_js_to_chunk_typescript`, `test_dispatches_jsx_to_chunk_typescript` all PASSED |

**Orphaned requirements check:** `IDX-08`, `IDX-09`, and `QUAL-01` are mapped to Phase 16 in REQUIREMENTS.md. They do not appear in any Phase 15 plan's `requirements` field. This is correct — these requirements are explicitly deferred, not orphaned.

### Anti-Patterns Found

No blockers or warnings found.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | — | — | — |

Stub scan: `ts_chunker.py` contains no `return null`, `return {}`, `return []`, or `=> {}` stubs. `chunk_typescript()` contains real AST traversal logic. No `TODO`/`FIXME`/`PLACEHOLDER` comments. `ruff check` and `mypy --strict` both exit 0.

### Human Verification Required

None. All success criteria are mechanically verifiable. The full test suite (318 tests) runs in 3.53 seconds with no external service dependencies — all grammar binaries ship as pre-compiled wheels in `tree-sitter-language-pack`.

### Gaps Summary

No gaps. All five success criteria are verified, all ten requirement IDs are satisfied, all key links are wired, all artifacts are substantive and connected.

---

## Full Suite Result

```
318 passed in 3.53s
```

Commits verified:
- `232bb0b` — test(15-01): add failing tests for chunk_typescript
- `603b19a` — chore(15-02): add tree-sitter and tree-sitter-language-pack dependencies
- `2d70c29` — feat(15-02): implement chunk_typescript with tree-sitter AST chunking
- `1da7410` — docs(15-02): complete core AST chunker GREEN phase

---

_Verified: 2026-02-24T09:00:00Z_
_Verifier: Claude (gsd-verifier)_

---
phase: 20-python-method-sub-chunking
verified: 2026-02-24T17:00:00Z
status: passed
score: 12/12 must-haves verified
re_verification: false
---

# Phase 20: Python Method Sub-Chunking Verification Report

**Phase Goal:** Python chunker sub-chunks classes into header + per-method chunks, making individual class methods independently searchable via LanceDB.
**Verified:** 2026-02-24T17:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth                                                                                                    | Status     | Evidence                                                                                               |
|----|----------------------------------------------------------------------------------------------------------|------------|--------------------------------------------------------------------------------------------------------|
| 1  | `chunk_python()` produces a `ClassName` header chunk for every class in a .py file                       | VERIFIED   | `_chunk_class()` always prepends a header dict with `chunk_name=node.name`; 10 SUB-01 tests pass      |
| 2  | Header chunk covers decorators, signature, class-level attrs, docstring, `__init__` self-assignments     | VERIFIED   | `_chunk_class()` lines 220-268; `start_line` from `decorator_list[0].lineno`; init-scan loop stops at first non-assignment |
| 3  | Header chunk named exactly `ClassName` (not `ClassName.__init__`)                                        | VERIFIED   | `chunk_name: node.name` at line 267; `test_class_with_methods_produces_header_chunk` passes            |
| 4  | A class with no methods produces a header-only chunk                                                     | VERIFIED   | `if not method_nodes: header_end_line = node.end_lineno` (line 226); `test_class_with_no_methods_header_only` passes |
| 5  | A class with `__init__` having only self-assignments includes all of them in the header                  | VERIFIED   | `test_class_header_includes_init_self_assignments` passes; loop includes all self-assign stmts         |
| 6  | Top-level functions alongside classes are unaffected — still one chunk per function                      | VERIFIED   | `chunk_python()` only delegates `ClassDef` to `_chunk_class()`; FunctionDef path unchanged; `test_top_level_function_unchanged_alongside_class` passes |
| 7  | `chunk_python()` produces one `ClassName.method_name` chunk per method                                   | VERIFIED   | `result.append({"chunk_name": f"{node.name}.{method.name}", ...})` at line 288; `test_class_methods_produce_dot_name_chunks` passes |
| 8  | All method types (`__init__`, dunders, `@property`, `@classmethod`, `@staticmethod`, `async def`) produce dot-notation chunks | VERIFIED   | 6 dedicated tests in `TestChunkPythonMethodChunks` all pass                                            |
| 9  | Monolithic class chunk is gone — replaced by header + per-method chunks                                  | VERIFIED   | `test_monolithic_class_chunk_absent` asserts `>= 3` chunks for 2-method class; passes                 |
| 10 | Re-indexing the same file produces deterministic output                                                  | VERIFIED   | `test_deterministic_output` asserts `result1 == result2`; passes                                      |
| 11 | Multi-class files: every class gets sub-chunked                                                          | VERIFIED   | `test_multi_class_file_all_classes_sub_chunked` passes; both `Alpha.run` and `Beta.go` present         |
| 12 | Nested classes inside a class body are opaque (not recursively sub-chunked)                              | VERIFIED   | Direct `node.body` iteration (line 273) skips nested `ClassDef`; `test_nested_class_treated_as_opaque` passes |

**Score:** 12/12 truths verified

---

### Required Artifacts

| Artifact                                              | Expected                                                | Status     | Details                                                                                   |
|-------------------------------------------------------|---------------------------------------------------------|------------|-------------------------------------------------------------------------------------------|
| `src/corpus_analyzer/ingest/chunker.py`               | `_chunk_class()` helper for ClassDef AST extraction     | VERIFIED   | Function at lines 205-293; 89 lines; returns header + per-method chunks; PEP 257 docstring present |
| `src/corpus_analyzer/ingest/chunker.py`               | `_chunk_class()` returns header + per-method chunks     | VERIFIED   | Lines 261-293: header dict + method loop producing `ClassName.method_name` chunks          |
| `tests/ingest/test_chunker.py`                        | `TestChunkPythonSubChunking` class (SUB-01, 10 tests)   | VERIFIED   | Lines 624-748; 10 test methods; all pass                                                  |
| `tests/ingest/test_chunker.py`                        | `TestChunkPythonMethodChunks` class (SUB-02, 14 tests)  | VERIFIED   | Lines 756-924; 14 test methods; all pass                                                  |

---

### Key Link Verification

| From               | To                            | Via                                                    | Status  | Details                                                                                    |
|--------------------|-------------------------------|--------------------------------------------------------|---------|--------------------------------------------------------------------------------------------|
| `chunk_python()`   | `_chunk_class()`              | Called for each `ClassDef` node in `tree.body`         | WIRED   | `chunks.extend(_chunk_class(node, lines))` at line 332; guarded by `isinstance(node, ast.ClassDef)` at line 331 |
| `_chunk_class()`   | AST `ClassDef` node inspection | `isinstance` checks on `node.body` members            | WIRED   | `method_nodes = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]` at line 223; decorators via `node.decorator_list` |
| `_chunk_class()`   | Method chunks                 | Iterating `FunctionDef`/`AsyncFunctionDef` in `node.body` | WIRED   | `for method in node.body: if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)): continue` at lines 273-275 |
| `chunk_name`       | `ClassName.method_name`       | `f"{node.name}.{method.name}"`                         | WIRED   | Line 288: `"chunk_name": f"{node.name}.{method.name}"`                                    |

---

### Requirements Coverage

| Requirement | Source Plan | Description                                                                                                                        | Status    | Evidence                                                                                                    |
|-------------|-------------|------------------------------------------------------------------------------------------------------------------------------------|-----------|-------------------------------------------------------------------------------------------------------------|
| SUB-01      | 20-01-PLAN  | Python AST chunker produces a class header chunk (`ClassName`) containing docstring + `__init__` body up to first non-assignment statement; replaces monolithic class chunk | SATISFIED | `_chunk_class()` implemented and wired; 10 `TestChunkPythonSubChunking` tests pass; REQUIREMENTS.md marks `[x]` |
| SUB-02      | 20-02-PLAN  | Python AST chunker produces per-method chunks (`ClassName.method_name`) for each method; `__init__`, `__str__`, etc. follow dot-notation | SATISFIED | Method loop in `_chunk_class()` produces dot-notation chunks; 14 `TestChunkPythonMethodChunks` tests pass; REQUIREMENTS.md marks `[x]` |

No orphaned requirements found — both IDs declared in plan frontmatter match REQUIREMENTS.md entries mapped to Phase 20.

---

### Anti-Patterns Found

None. No `TODO`, `FIXME`, `PLACEHOLDER`, `return null`, empty handlers, or stub patterns found in the modified files.

---

### Human Verification Required

None. All behaviours are deterministic and verifiable programmatically. LanceDB searchability improvement is a downstream effect; it is not a testable contract within this phase's scope (no LanceDB integration test was specified).

---

### Regression Check

- **Full suite (excluding pre-existing `test_debug.py` collection error unrelated to phase 20):** 369 passed
- The `test_debug.py` error (`CorpusIndex.__init__() missing 1 required positional argument: 'data_dir'`) originates from commit `8177df5` which pre-dates phase 20 and is not caused by this phase's changes.
- **ruff check:** All checks passed (zero violations)
- **mypy:** Success — no issues found in `chunker.py`
- `test_nested_not_separate` in `TestChunkPython` was correctly migrated during phase execution (SUB-02 deviation) to reflect new chunk count semantics.

---

### Summary

Phase 20 fully achieves its goal. The Python chunker now sub-chunks every `ClassDef` into:

1. A header chunk (`ClassName`) — covers decorators, class signature, class-level attributes, and `__init__` self-assignments up to the first non-assignment statement.
2. One method chunk per `FunctionDef`/`AsyncFunctionDef` (`ClassName.method_name`) — covers all method types including dunders, decorated methods, and `async def`.

Both requirements (SUB-01 and SUB-02) are satisfied with full TDD coverage (24 new tests), clean ruff and mypy output, and a full regression-free test suite of 369 tests.

---

_Verified: 2026-02-24T17:00:00Z_
_Verifier: Claude (gsd-verifier)_

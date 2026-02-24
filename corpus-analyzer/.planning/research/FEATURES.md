# Feature Research

**Domain:** Python code quality pass — zero mypy errors + zero ruff violations on an existing codebase
**Researched:** 2026-02-24
**Confidence:** HIGH (errors enumerated from live tool output; fix patterns from official mypy/ruff docs + Python typing conventions)

---

## Note on Template Reuse

This milestone is a code quality pass, not a product feature build. The template sections are repurposed:
- "Table Stakes" = fix categories that are mandatory for the milestone goal (zero errors)
- "Differentiators" = approach choices that determine quality and safety of the fix pass
- "Anti-Features" = fix approaches that look correct but introduce risk

---

## Feature Landscape

### Table Stakes (Users Expect These)

Fix categories that must be addressed to reach the milestone goal. All are mandatory — skipping any leaves a non-zero error count.

| Fix Category | Rule(s) | Count | Auto-Fix? | Notes |
|-------------|---------|-------|-----------|-------|
| Blank line whitespace | W293, W291 | 297 (264+33) | YES — `ruff check --fix` | Largest single category. `[*]` marker on most; 11 W293 and 1 W291 have no `[*]` — need manual check. Concentrated in `llm/` and `classifiers/` modules. |
| Import sorting | I001 | 26 | YES — `ruff check --fix` | All 26 are auto-fixable `[*]`. Sorting enforced by isort-compatible rules. |
| Unused imports | F401 | 33 | YES — `ruff check --fix` | All auto-fixable. Split: test files have `pytest`/`mock` imports; source files have leftover `Optional`, `typing.Any`, `DocumentCategory`, progress bar components. None are in `__init__.py` re-export position — safe to auto-remove. |
| UP045 Optional modernisation | UP045 | 21 | YES — `ruff check --fix` | All auto-fixable. `Optional[X]` → `X \| None`. Concentrated in `.windsurf/` assets and `extractors/__init__.py`. After fix, `from typing import Optional` imports become unused and F401 will catch them. Run ruff twice or in sequence. |
| f-string without placeholders | F541 | 2 | YES — `ruff check --fix` | Trivial. Strip the `f` prefix. |
| Invalid escape sequence | W605 | 1 | YES — `ruff check --fix` | `\s` in a raw string context. Change to `r"\s"` or `"\\s"`. |
| Line too long | E501 | 104 | NO — manual only | Ruff cannot auto-wrap lines. Distribution: `llm/unified_rewriter.py` (91 violations), `cli.py` (49), `llm/rewriter.py` (45), `llm/chunked_processor.py` (42). The milestone plan is: set `per-file-ignores` for `llm/` at 120 chars, which will eliminate the bulk of violations. Remaining lines in `cli.py` and test files need manual wrapping. |
| mypy: union-attr on sqlite-utils Table\|View | union-attr | 8 | NO — manual | `db["table"]` returns `Table \| View` per sqlite-utils type stubs (py.typed is present). `View` lacks `insert`, `update`, `delete_where`. Fix: `cast(sqlite_utils.Table, self.db["documents"])` at each call site, OR assign `tbl: sqlite_utils.Table = self.db["table"]` once per method. Cast is safer — runtime type is always `Table` for these named tables. |
| mypy: no-any-return | no-any-return | 3 | NO — manual | `sqlite_utils` execute returns `sqlite3.Cursor`; `.fetchone()[0]` is `Any`. Fix: add explicit `int(...)` cast or assign to typed variable before return. All three are in `core/database.py`. |
| mypy: untyped nested functions | no-untyped-def, no-untyped-call | 11 | NO — manual | `finalize_atom`, `get_chunk_text`, `chain_lines` are nested closures inside `chunked_processor.py`. They reference outer mutable state via `nonlocal`. Fix: add parameter + return type annotations to each. Signatures are straightforward: `list[str]` in, `None` or `list[str]` out. |
| mypy: missing return type annotations | no-untyped-def | 4 | NO — manual | `utils/ui.py` has two public functions missing both arg types and return types. `table_obj` arg is a `sqlite_utils.Table`; return type is `None` for both. Plus `rewriter.py` line 245 (one arg untyped). |
| mypy: missing generic type params | type-arg | 6 | NO — manual | `dict` and `list` used without type parameters (e.g., `params: list = []`). Fix: `list[Any]` or specific element type. Locations: `database.py` (4 instances), `markdown.py` (1), `shape.py` (1). |
| mypy: import-untyped (python-frontmatter) | import-untyped | 1 | NO — config | `python-frontmatter` has no stubs and no `py.typed`. Fix: add `[[tool.mypy.overrides]]` section with `module = "frontmatter"` and `ignore_missing_imports = true`. Do NOT add `# type: ignore` inline — pyproject.toml config is cleaner and reusable. |
| mypy: abstract class instantiation | abstract | 1 | NO — manual | `extractors/__init__.py` line 34 calls `extractor_class()` where mypy infers the type as `type[BaseExtractor]` (the abstract base). Both `MarkdownExtractor` and `PythonExtractor` do implement `extract()` — mypy's abstract check is triggered because the dict value type is `type[BaseExtractor]`. Fix: annotate the dict as `dict[str, type[MarkdownExtractor] \| type[PythonExtractor]]` or use `type[BaseExtractor]` with a `# type: ignore[abstract]` comment on the instantiation line (acceptable here — the dict values are always concrete subclasses). |
| mypy: arg-type on float() | arg-type | 2 | NO — manual | `database.py` lines 318/320: `float(row.get("category_confidence") if ... else 0.0)`. `row.get()` returns `Any \| None`; the conditional expression produces `Any \| float \| None`. mypy rejects `None` as a `float()` arg. Fix: use `float(row.get("category_confidence") or 0.0)` — the `or` coerces falsy to `0.0` and guarantees a numeric argument. |
| mypy: attr-defined (OllamaClient.db) | attr-defined | 1 | NO — manual | `rewriter.py` line 414: `adv_rewriter.client.db = db` — dynamically assigning an attribute not defined on `OllamaClient`. Fix: add `db: Optional[CorpusDatabase] = None` field to `OllamaClient` class. This is a design smell (dynamic attribute injection) — adding a typed field is the correct fix, not `# type: ignore`. |
| mypy: operator error (tuple + str) | operator | 1 | NO — manual | `rewriter.py` line 406: variable inferred as `str \| tuple[str]`; the code appends a `str` to it as if it were always a `tuple`. Fix: inspect the branch logic and either use a `list[str]` or ensure the variable is always one type. This is a genuine bug — the type error reflects real ambiguity. |
| mypy: var-annotated | var-annotated | 1 | NO — manual | `chunker.py` line 271: `current_lines = []` with no type annotation. Fix: `current_lines: list[str] = []`. |
| mypy: no-any-return on ollama_client | no-any-return | 1 | NO — manual | `ollama_client.py` line 42: method declared to return `str` but returns `Any` from Ollama SDK. Fix: explicit `str(...)` cast on the return value. |
| E402 imports not at top | E402 | 5 | NO — manual | `rewriter.py` has deferred imports inside a function (conditional import for optional heavy dep). `test_debug.py` configures logging before imports. Fix for rewriter: move imports to top or add `# noqa: E402` with explanation. Fix for test_debug.py: restructure to configure logging after imports or use `# noqa: E402`. |
| Bugbear B-series | B006/B007/B008/B017/B023/B904/B905 | 14 | MIXED | See detailed breakdown below. |

**B-series breakdown:**

| Rule | Count | Auto-Fix? | What it flags | Fix pattern |
|------|-------|-----------|---------------|-------------|
| B905 | 3 | NO | `zip()` without `strict=` | Add `strict=False` (explicit opt-out) or `strict=True` if lengths must match. |
| B007 | 3 | NO | Loop variable not used in body | Rename to `_` or `_text`, `_i`, `_chunk`. |
| B017 | 2 | NO | `pytest.raises(Exception)` — too broad | Change to specific exception class, e.g. `pytest.raises(ValueError)`. |
| B006 | 2 | NO | Mutable default arg (e.g., `def f(x=[])`) | Change to `None` default + `if x is None: x = []` pattern. |
| B023 | 1 | NO | Closure captures loop variable | Capture at definition time: `lambda v=task_id: ...` |
| B904 | 1 | NO | `raise X` inside `except` without `from` | Change to `raise X from err` or `raise X from None`. |
| B008 | 1 | NO | `Query(...)` in function default arg | Move to module-level constant or compute inside function body. |
| F841 | 4 | NO | Variable assigned but never used | Delete the assignment or prefix with `_`. |
| E741 | 4 | NO | Ambiguous variable name `l` | Rename to `line`, `link`, or `el`. All four are in `database.py` and `chunked_processor.py` using `l` as a loop variable in list comprehensions. |

---

### Differentiators (Approach Choices That Matter)

Decisions about HOW to do the fix pass that determine quality, safety, and maintainability of the result.

| Approach | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Run auto-fix first, manual second | Eliminates 383 violations in one command (`ruff check --fix`). Prevents wasted effort manually fixing things ruff would auto-fix. | LOW | Command: `uv run ruff check . --fix`. Then commit the auto-fix separately before manual changes — keeps diff reviewable. |
| `per-file-ignores` for llm/ at 120 chars | Eliminates ~180 E501 violations (bulk of llm/ module) without manual line-wrapping. The `llm/` code is legacy rewriter logic, not the v1.3 focus. | LOW | In pyproject.toml: `[tool.ruff.lint.per-file-ignores]` with `"src/corpus_analyzer/llm/*.py" = ["E501"]` or set line-length = 120 for that path. |
| mypy overrides for untyped third-party libs | Correct way to silence `import-untyped` for `python-frontmatter`. Keeps `# type: ignore` out of source files. | LOW | `[[tool.mypy.overrides]]` in pyproject.toml: `module = "frontmatter"`, `ignore_missing_imports = true`. |
| cast() for sqlite-utils union-attr | More explicit than `# type: ignore`. Communicates intent ("we know this is a Table, not a View"). Type-safe: will catch if the return type changes. | LOW | `from typing import cast; import sqlite_utils; tbl = cast(sqlite_utils.Table, self.db["name"])` |
| Fix the OllamaClient.db attr-defined as a real field | Better than `# type: ignore` — adds the field properly so the type system tracks it. Signals the design intent explicitly. | LOW | Add `db: Optional["CorpusDatabase"] = None` to `OllamaClient`. Uses quoted forward reference to avoid circular import. |
| Separate auto-fix commit from manual fix commit | Keeps the diff reviewable. Auto-fix produces whitespace/import churn that obscures real changes if mixed. | LOW | Two commits: (1) `ruff check --fix` output, (2) manual fixes. |

---

### Anti-Features (Fix Approaches to Avoid)

Fix strategies that seem expedient but introduce risk or reduce quality.

| Anti-Feature | Why Requested | Why Problematic | Alternative |
|--------------|---------------|-----------------|-------------|
| `# type: ignore` on union-attr errors | Fastest way to silence mypy union-attr errors | Hides a genuine ambiguity. If sqlite-utils ever returns a View, runtime errors become silent. Future mypy runs also flag `warn_unused_ignores` — unused ignores become new errors. | Use `cast(sqlite_utils.Table, ...)` at each call site. Explicit, safe, communicates intent. |
| `# type: ignore[import-untyped]` inline in markdown.py | Inline suppression silences the error | `warn_unused_ignores = true` in pyproject.toml means if stubs are added later, the ignore becomes an error. Pollutes source file. | Use `[[tool.mypy.overrides]]` in pyproject.toml — one place, no source file pollution. |
| Bulk `# noqa: E501` inline comments for line length | Fastest per-line fix | 104 individual `# noqa` comments creates massive diff noise and obscures real violations in future. `warn_unused_ignores` may not apply to ruff noqa but visual noise is high. | Use `per-file-ignores` config for the `llm/` directory. For remaining violations, actually wrap the line. |
| Annotating dynamic `dict`/`list` with bare `Any` | `list[Any]` satisfies mypy `type-arg` | `Any` suppresses all downstream type checking on that variable. Better to use `list[str]` or `dict[str, int]` when the actual type is known. | Use the specific type. Fall back to `list[Any]` only when the content is genuinely heterogeneous (e.g., raw sqlite row data). |
| Fixing the rewriter.py operator bug with a type cast | `cast(tuple[str], var)` silences the error | The operator error on line 406 reflects a real ambiguity in the code — the variable can be `str` or `tuple[str]`. A cast papers over a genuine bug. | Inspect the branch logic, determine the correct type, fix the code. This is the one error that might reveal a latent bug. |
| Running `ruff check --fix --unsafe-fixes` | Fixes more violations automatically | Unsafe fixes modify code semantics, not just formatting. On a production codebase with 281 passing tests, unsafe fixes risk introducing failures. | Stick to safe auto-fixes. Do unsafe fixes manually, one at a time. |
| Fixing all mypy errors in a single commit | Simpler commit history | One large commit makes review hard and makes bisecting regressions difficult if a test breaks. | Group by file or by error category. |

---

## Feature Dependencies

```
[Auto-fix pass (ruff --fix)]
    └──before──> [Manual E501 fixes]
                     └──before──> [per-file-ignores config]
    └──before──> [Manual B-series fixes]
    └──before──> [Manual F841/E741 fixes]

[mypy overrides config (frontmatter)]
    └──independent of──> [mypy source fixes]

[sqlite-utils cast fixes (database.py)]
    └──enables──> [no-any-return fixes (database.py)]
    (fixing union-attr exposes that the cast return is still Any)

[OllamaClient.db field addition]
    └──required before──> [rewriter.py type annotations]

[UP045 auto-fix]
    └──triggers──> [F401 auto-fix] (Optional imports become unused after UP045 fix)
    (run ruff --fix twice, or in a single pass — ruff handles chains)
```

### Dependency Notes

- **Auto-fix before manual:** Running `ruff check --fix` first eliminates 383 violations and resets the baseline. Manual work on a pre-fix codebase is wasted effort if ruff would have changed the same lines.
- **per-file-ignores before E501 manual fixes:** Set the `llm/` line-length override first, then run ruff to see the true residual E501 count. Don't manually wrap lines in `llm/` that the config would suppress.
- **UP045 triggers F401:** After `Optional[X]` is converted to `X | None`, the `from typing import Optional` import becomes unused. Ruff handles this in the same `--fix` pass, but verify with a second `ruff check` to confirm.
- **sqlite-utils union-attr and no-any-return are coupled:** Casting `db["table"]` to `sqlite_utils.Table` does not automatically fix the `no-any-return` errors. The cursor's `.fetchone()[0]` still returns `Any`. Address union-attr first, then no-any-return separately.

---

## MVP Definition

### Must Fix (Required for Zero-Error Milestone)

All of these must be done. None are optional.

- [ ] **`ruff check --fix`** — eliminates W293, W291, I001, F401 (most), UP045, F541, W605 in one pass
- [ ] **`per-file-ignores` for `llm/` at 120 chars** — eliminates bulk of E501 without manual line-wrapping
- [ ] **Manual E501 fixes in `cli.py`, tests, non-llm source** — residual line-length violations after config change
- [ ] **Manual B-series fixes** — B905, B007, B017, B006, B023, B904, B008 (14 violations, none auto-fixable)
- [ ] **Manual F841/E741 fixes** — unused variables and ambiguous names `l` in comprehensions
- [ ] **Manual E402 fixes** — deferred imports in rewriter.py and test_debug.py
- [ ] **mypy `[[overrides]]` for `frontmatter` module** — one config block, silences import-untyped
- [ ] **mypy: sqlite-utils union-attr** — cast to `sqlite_utils.Table` at 8 call sites in `database.py`
- [ ] **mypy: no-any-return in database.py** — explicit `int()` cast on cursor row access
- [ ] **mypy: nested function type annotations in chunked_processor.py** — add types to `finalize_atom`, `get_chunk_text`, `chain_lines`
- [ ] **mypy: utils/ui.py function signatures** — add arg types (`sqlite_utils.Table`) and return types (`None`)
- [ ] **mypy: generic type params** — `list[str]` and `dict[str, Any]` where bare `list`/`dict` used
- [ ] **mypy: abstract class instantiation in extractors/__init__.py** — `# type: ignore[abstract]` or typed dict
- [ ] **mypy: arg-type for float() in database.py** — use `or 0.0` pattern instead of conditional
- [ ] **mypy: OllamaClient.db attr-defined** — add `db: Optional["CorpusDatabase"] = None` field to class
- [ ] **mypy: operator error in rewriter.py** — investigate and fix the `str | tuple[str]` ambiguity
- [ ] **mypy: var-annotated in chunker.py** — annotate `current_lines: list[str] = []`
- [ ] **mypy: no-any-return in ollama_client.py** — explicit `str(...)` cast on return value
- [ ] **mypy: rewriter.py untyped arg** — add type annotation to missing argument

### Add After Validation (v1.x)

- [ ] **Stub generation for python-frontmatter** — if the overrides approach ever becomes insufficient, a proper stub package would be better. Not needed now.
- [ ] **Refactor OllamaClient.db injection** — the dynamic attribute injection is a design smell. Proper fix would be constructor injection. Defer — not in scope for a quality pass.

### Future Consideration (v2+)

- [ ] **Full strict mypy on `llm/` module** — the `llm/` module has the most violations and is legacy code. A fuller refactor would be v2 work.
- [ ] **Proper typing for sqlite-utils rows** — sqlite-utils rows are `dict[str, Any]`; adding row-level TypedDict models would eliminate the `Any` cascade from database reads. High value, high effort.

---

## Feature Prioritization Matrix

| Fix Category | Milestone Value | Implementation Cost | Priority |
|-------------|-----------------|---------------------|----------|
| ruff auto-fix pass (383 violations) | HIGH | LOW | P1 |
| per-file-ignores for llm/ E501 | HIGH | LOW | P1 |
| sqlite-utils union-attr (8 errors) | HIGH | LOW | P1 |
| mypy overrides for frontmatter | HIGH | LOW | P1 |
| Nested function type annotations (11 errors) | HIGH | MEDIUM | P1 |
| utils/ui.py signatures (4 errors) | HIGH | LOW | P1 |
| Generic type params (6 errors) | HIGH | LOW | P1 |
| Manual E501 fixes (residual after config) | HIGH | MEDIUM | P1 |
| B-series fixes (14 violations) | HIGH | LOW-MEDIUM | P1 |
| F841/E741 fixes (8 violations) | HIGH | LOW | P1 |
| E402 fixes (5 violations) | HIGH | LOW | P1 |
| no-any-return in database.py (3 errors) | HIGH | LOW | P1 |
| arg-type float() fix (2 errors) | HIGH | LOW | P1 |
| OllamaClient.db field (1 error) | HIGH | LOW | P1 |
| abstract class fix (1 error) | HIGH | LOW | P1 |
| operator error rewriter.py (1 error) | HIGH | MEDIUM | P1 |
| var-annotated chunker.py (1 error) | HIGH | LOW | P1 |
| no-any-return ollama_client (1 error) | HIGH | LOW | P1 |
| rewriter.py untyped arg (1 error) | HIGH | LOW | P1 |

**Priority key:**
- P1: Must have for milestone (zero errors is binary — all are P1)
- P2: Not applicable — this milestone has no optional fixes
- P3: Not applicable

---

## Auto-Fix vs Manual Fix Split

**Auto-fixable via `ruff check --fix` (383 violations):**

| Rule | Count | Notes |
|------|-------|-------|
| W293 | 253 | Blank line whitespace (auto-fixable subset) |
| W291 | 32 | Trailing whitespace (auto-fixable subset) |
| I001 | 26 | Import sorting |
| F401 | 33 | Unused imports (all in this codebase) |
| UP045 | 21 | Optional[X] → X \| None |
| F541 | 2 | f-string without placeholders |
| W605 | 1 | Invalid escape sequence |

**Manual fix required (146 violations + 42 mypy errors):**

| Category | Count | Effort |
|----------|-------|--------|
| E501 line length (after per-file-ignores) | ~20-30 residual | MEDIUM |
| W293/W291 without [*] marker | 12 | LOW |
| B-series bugbear | 14 | LOW-MEDIUM |
| F841/E741 | 8 | LOW |
| E402 | 5 | LOW |
| mypy union-attr (database.py) | 8 | LOW |
| mypy nested function types | 11 | MEDIUM |
| mypy generic type params | 6 | LOW |
| mypy no-any-return | 4 | LOW |
| mypy untyped functions | 6 | LOW |
| mypy overrides config | 1 | LOW |
| mypy abstract class | 1 | LOW |
| mypy arg-type float() | 2 | LOW |
| mypy attr-defined | 1 | LOW |
| mypy operator error | 1 | MEDIUM |
| mypy var-annotated | 1 | LOW |

---

## Risky Fixes (Require Extra Care)

These fixes could break tests or change runtime behaviour if done incorrectly:

1. **rewriter.py operator error (line 406)** — the `str | tuple[str]` ambiguity is a real code bug. Any fix requires understanding the control flow, not just satisfying the type checker. Test coverage for this path must be confirmed before changing.

2. **B006 mutable defaults** — changing `def f(x=[])` to `def f(x=None)` with an interior `if x is None: x = []` is semantically identical for new callers, but changes behaviour for existing code that relies on shared mutable default (intentional or not). Verify no test depends on the mutation.

3. **B017 blind exception** — changing `pytest.raises(Exception)` to a specific exception class tightens the test contract. If the code raises a different exception for a different reason, the test will now fail where before it passed silently. This is the correct outcome but must be verified.

4. **OllamaClient.db field addition** — adding a new field to `OllamaClient` requires checking if `__init__` uses `**kwargs` or has `model_config = ConfigDict(...)` (Pydantic model) vs plain dataclass. If it's a Pydantic model with `extra = "forbid"`, adding the field is required and must be done correctly.

5. **extractors/__init__.py abstract fix** — if the `# type: ignore[abstract]` approach is used, future concrete subclasses added without implementing `extract()` will be silently accepted at this call site. The dict-with-specific-types approach is safer but more verbose.

---

## Sources

- Live `uv run ruff check .` output — HIGH confidence (direct enumeration, 529 violations)
- Live `uv run mypy src/` output — HIGH confidence (direct enumeration, 42 errors in 9 files)
- [ruff rule W293](https://docs.astral.sh/ruff/rules/whitespace-before-comment/) — HIGH confidence
- [ruff rule E501 per-file-ignores](https://docs.astral.sh/ruff/settings/#lint_per-file-ignores) — HIGH confidence
- [ruff rule B-series (flake8-bugbear)](https://docs.astral.sh/ruff/rules/#flake8-bugbear-b) — HIGH confidence
- [mypy union-attr](https://mypy.readthedocs.io/en/stable/error_code_list.html#check-validity-of-types-in-attr-defined-attr-defined) — HIGH confidence
- [mypy overrides for missing stubs](https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports) — HIGH confidence
- [sqlite-utils py.typed presence](https://github.com/simonw/sqlite-utils) — HIGH confidence (verified at runtime: `py.typed` present in package)
- [sqlite-utils Table | View union type](https://github.com/simonw/sqlite-utils/blob/main/sqlite_utils/db.py) — HIGH confidence (verified via `__getitem__` source inspection)

---
*Feature research for: v1.3 code quality pass — Python mypy + ruff zero-error baseline*
*Researched: 2026-02-24*

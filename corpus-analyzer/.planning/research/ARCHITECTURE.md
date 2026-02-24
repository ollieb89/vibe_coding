# Architecture Research

**Domain:** Code quality fix — mypy + ruff across existing Python codebase
**Researched:** 2026-02-24
**Confidence:** HIGH (error analysis from live mypy/ruff output), HIGH (sqlite-utils type system),
HIGH (fix ordering strategy — derived from module dependency graph)

---

## Context: What This Research Covers

This is a SUBSEQUENT MILESTONE research file. The overall system architecture is documented in the
v1.0–v1.2 research (same file, replaced below). This research focuses on **how to structure the
v1.3 code quality milestone**: fix ordering, integration points, risk zones, and validation strategy.

The goal: zero `mypy --strict` errors + zero `ruff check` violations across all 53 source files,
with 281 tests staying green throughout.

---

## Current Error Inventory

### mypy errors by file (42 total, 9 files)

| File | Count | Primary Error Types |
|------|-------|---------------------|
| `core/database.py` | 17 | `Table | View` union-attr (8×), `no-any-return` (3×), `type-arg` (3×), `arg-type` (2×) |
| `llm/chunked_processor.py` | 12 | `no-untyped-def` (3×), `no-untyped-call` (9×) — nested functions |
| `ingest/chunker.py` | 1 | `var-annotated` |
| `utils/ui.py` | 4 | `no-untyped-def` (4×) — missing arg/return types |
| `extractors/markdown.py` | 3 | `import-untyped` (frontmatter), `type-arg` |
| `analyzers/shape.py` | 1 | `type-arg` |
| `extractors/__init__.py` | 1 | `abstract` — cannot instantiate abstract class |
| `llm/ollama_client.py` | 1 | `no-any-return` — `response["message"]["content"]` |
| `llm/rewriter.py` | 7 | `no-untyped-def`, `operator` (tuple + str), `attr-defined` (`.db`) |

### ruff errors by file (529 total)

**Auto-fixable (382):** W293 whitespace, W291 trailing space, I001 import sort, UP045/UP006/UP035
modernisation, F401 unused imports, F541 f-string, W605 escape sequence.

**Manual fixes in src/ (101):**

| Rule | Count | Files |
|------|-------|-------|
| E501 (line too long) | 93 | `cli.py` (45), `classifiers/document_type.py` (13), `generators/advanced_rewriter.py` (9), `llm/` (15), `core/database.py` (4), others |
| B905 (zip no strict) | 3 | `core/database.py` |
| B006 (mutable default) | 2 | `cli.py` |
| E741 (ambiguous var) | 4 | `core/database.py` (2), `llm/chunked_processor.py` (2) |
| E402 (import not at top) | 2 | `llm/rewriter.py` |
| B023 (loop var closure) | 1 | `cli.py` |
| B904 (raise without from) | 1 | `cli.py` |
| F841 (unused var) | 3 | `classifiers/`, `extractors/` |
| SIM102 (nested if) | 2 | `core/scanner.py`, `extractors/python.py` |
| E402 (import not at top) | 2 | `llm/rewriter.py` |

---

## Module Dependency Graph

Understanding which modules import which is critical for fix ordering.
Fixing a module that has dependents requires re-checking those dependents after each change.

```
settings.py (leaf — no project imports)
    ↑
llm/ollama_client.py
    ↑
core/models.py (leaf — stdlib + pydantic only)
    ↑
core/database.py          ← central hub, imported by 10 files
    ↑                           classifiers/document_type.py
    │                           classifiers/domain_tags.py
    │                           cli.py
    │                           core/__init__.py
    │                           core/samples.py
    │                           generators/templates.py
    │                           llm/unified_rewriter.py
    │                           llm/rewriter.py
    │                           analyzers/shape.py
    │                           analyzers/quality.py
    ↑
llm/rewriter.py → llm/ollama_client.py, core/database.py, core/models.py
    ↑
llm/__init__.py (re-exports from llm/rewriter.py)
    ↑
cli.py (terminal — imports almost everything)

llm/chunked_processor.py (standalone — no project imports, imported by llm/rewriter.py)
utils/ui.py (standalone — rich only)
extractors/markdown.py (imports core/models.py, extractors/base.py)
ingest/chunker.py (standalone section, imports core models)
analyzers/shape.py (imports core/database.py)
```

**Key observation:** `core/database.py` is the hub. It is imported by 10 modules. Fixing it first
means all dependents continue to type-check correctly. Any type annotation changes in `database.py`
propagate to all 10 dependents — those must be re-checked after `database.py` is fixed.

---

## Fix Order Architecture

### Recommended Sequencing

The correct order is **leaves before hubs, hubs before dependents, formatters before type checkers**.

```
Phase 1 — Auto-fix ruff (all files, one pass)
    ruff --fix src/ tests/ scripts/
    Clears 382 errors: whitespace, import sort, modernisation, F401, F541, W605
    Risk: ZERO — purely mechanical transforms, no semantic change
    Gate: run tests immediately after

Phase 2 — pyproject.toml config (before manual E501 work)
    Add per-file-ignores for llm/ (120-char limit)
    Add per-file-ignores for tests/ (E501 acceptable in test strings)
    Gate: ruff check re-run to confirm E501 count drops correctly

Phase 3 — Manual ruff fixes, leaf/standalone files first
    Batch A (standalone, no dependents): utils/ui.py, llm/chunked_processor.py,
             ingest/chunker.py, extractors/markdown.py, extractors/python.py,
             core/scanner.py, llm/quality_scorer.py, llm/unified_rewriter.py
    Batch B (shared module): core/database.py
    Batch C (dependents of database.py): analyzers/shape.py, analyzers/quality.py,
             classifiers/document_type.py, generators/advanced_rewriter.py,
             generators/templates.py
    Batch D (CLI and llm/rewriter.py — most complex):
             llm/rewriter.py, cli.py
    Gate: run tests after each batch

Phase 4 — mypy fixes, same ordering
    Same leaf-first order. database.py before its dependents.
    Gate: run mypy after each file, run tests after each batch
```

**Why ruff auto-fix first:** Whitespace and import sort changes are noise when reading diffs.
Clean those up unconditionally before any manual work begins. Auto-fixes never break tests.

**Why pyproject.toml config second:** The `llm/` files have 15 E501 violations that disappear
under a 120-char limit. Setting `per-file-ignores` before touching `llm/` means you never
manually wrap lines that the config would already excuse. Avoids wasted effort.

**Why database.py before its dependents:** `database.py` fixes introduce proper type annotations
(e.g. `cast(Table, ...)` instead of `Table | View`). Dependents that use database methods will
get cleaner type inference once `database.py` is annotated. Fixing dependents before `database.py`
means potentially fixing them twice.

---

## sqlite-utils Type Problem: The Correct Fix

`database.py` has 8 `union-attr` errors because `self.db["table_name"]` returns `Table | View`
(per sqlite-utils type stubs), but `View` lacks `insert`, `update`, `delete_where`. The code
always uses table-name strings that correspond to real tables, not views.

### Option A: `cast(Table, ...)` at each call site — RECOMMENDED

```python
from sqlite_utils.db import Table
from typing import cast

cast(Table, self.db["documents"]).insert(data, alter=True)
cast(Table, self.db["chunks"]).delete_where("document_id = ?", [doc_id])
```

**Verdict:** Best option. Narrows the type at the exact call site, documents the invariant,
no mypy overrides needed, zero runtime cost, immediately obvious to readers why the cast is there.
Affects only `database.py` — no changes to callers.

### Option B: Helper method returning `Table`

```python
def _table(self, name: str) -> Table:
    result = self.db[name]
    assert isinstance(result, Table)
    return result
```

**Verdict:** Acceptable but heavier. `_table("documents")` at every call site is verbose. Useful
if you want the assertion to catch real bugs; unnecessary here since table names are all hardcoded
string literals. Use `cast()` instead.

### Option C: `# type: ignore[union-attr]` — AVOID

**Verdict:** Suppresses the error but provides no documentation and fails `warn_unused_ignores`
if the stubs ever improve. The point of v1.3 is a clean baseline, not a suppression baseline.

### Option D: `Any` annotation for `self.db` — AVOID

**Verdict:** Loses all sqlite-utils type checking across the entire class. Overly broad.

**Conclusion:** Use `cast(Table, self.db["name"])` for every call site that triggers `union-attr`.
Add `from sqlite_utils.db import Table` to the import block.

---

## mypy Fix Strategies by Error Type

### `no-untyped-def` in `llm/chunked_processor.py` (nested functions)

The three untyped functions are nested closures inside `split_on_headings()`:
`finalize_atom()`, `get_chunk_text()`, `chain_lines()`. Mypy strict mode requires type annotations
even for nested functions.

```python
# Before (triggers no-untyped-def + no-untyped-call)
def finalize_atom(force_heading=None, force_level=0, is_code_atom=False):
    ...

# After
def finalize_atom(
    force_heading: str | None = None,
    force_level: int = 0,
    is_code_atom: bool = False,
) -> None:
    ...
```

Similarly `chain_lines(atoms_list: list[Atom]) -> list[str]` and
`get_chunk_text(atoms_list: list[Atom]) -> str`.

**Note on `Atom` being a nested dataclass:** `Atom` is defined inside `split_on_headings()`.
Moving it to module level makes the type annotations cleaner and avoids any forward-reference
issues with nested class annotations. This is the recommended refactor.

### `no-any-return` in `llm/ollama_client.py`

```python
# Line 42: response["message"]["content"] returns Any
return response["message"]["content"]  # triggers no-any-return

# Fix: explicit cast
from typing import cast
return cast(str, response["message"]["content"])
```

### `no-untyped-def` in `utils/ui.py`

Both functions missing annotations. `table_obj` is a `sqlite_utils.db.Table`:

```python
def print_table_schema(table_name: str, table_obj: Table) -> None:
def print_sample_data(table_name: str, table_obj: Table, limit: int = 5) -> None:
```

### `import-untyped` in `extractors/markdown.py` (python-frontmatter)

`python-frontmatter` has no type stubs. Two options:

**Option A:** Add `# type: ignore[import-untyped]` on the import line. Acceptable here because
the library is well-established and the stubs situation is unlikely to change.

**Option B:** Add `python-frontmatter` to mypy's `[[overrides]]` with `ignore_missing_imports`.

```toml
# pyproject.toml
[[tool.mypy.overrides]]
module = "frontmatter"
ignore_missing_imports = true
```

**Recommended:** Option B — centralises the suppression in config rather than scattering
`# type: ignore` comments in source. If stubs eventually ship, the override becomes redundant
and `warn_unused_ignores` will flag it cleanly.

### `operator` error in `llm/rewriter.py` line 406

`Left operand is of type "str | tuple[str]"` trying to concat a `str`. The variable assignment
earlier is ambiguous. Fix is to ensure the variable is typed as `str` consistently, or narrow it
before the concatenation.

### `attr-defined` for `adv_rewriter.client.db` in `llm/rewriter.py` line 414

`OllamaClient` does not have a `db` attribute — it is being monkey-patched at runtime:
```python
adv_rewriter.client.db = db
```

This is an architectural smell in the legacy `llm/rewriter.py`. The correct fix depends on
whether this path is tested or exercised:

- If the monkey-patch is the only way to pass `db` to `AdvancedRewriter`, add a `db` attribute
  to `OllamaClient` typed as `CorpusDatabase | None = None`.
- Alternatively, refactor `AdvancedRewriter` to accept `db` in its constructor.
- The `llm/rewriter.py` module is superseded by `llm/unified_rewriter.py` per the CLAUDE.md;
  minimal invasive fix (add optional attribute) is the pragmatic choice for v1.3.

### `abstract` in `extractors/__init__.py`

Cannot instantiate `BaseExtractor` directly. Likely a stale import or test helper. Inspect the
call site and replace with a concrete extractor or `MarkdownExtractor`.

### `type-arg` errors (missing generic parameters)

Replace bare `dict` with `dict[str, Any]`, bare `list` with `list[Any]` (or more specific type
if context makes the element type clear). These are in `core/database.py`, `analyzers/shape.py`,
`extractors/markdown.py`.

### `arg-type` in `core/database.py` lines 318 and 320

```python
# Triggers: "Any | float | None" not compatible with float()
float(row.get("category_confidence") if row.get("category_confidence") is not None else 0.0)
```

The `row.get()` returns `Any | None`. `float()` from typeshed expects `str | Buffer |
SupportsFloat | SupportsIndex`. The `Any` branch causes the error. Fix: use `or` shorthand which
mypy handles better, or apply a cast:

```python
# Cleaner and type-safe:
category_confidence: float = row.get("category_confidence") or 0.0
```

Because `row` is now `dict[str, Any]` after fixing the `type-arg` error, `row.get()` returns
`Any`, and `Any or float` narrows to `float` acceptably in most mypy versions.

---

## E501 Handling: llm/ vs rest of codebase

### The split

- `llm/` files: 15 E501 violations, mostly in string literals (prompts, docstrings) and long
  function signatures. These legitimately read better at 120 chars.
- Non-llm src/ files: 78 E501 violations. `cli.py` has 45 of them — mostly long option help
  strings and Rich console print calls. `classifiers/document_type.py` has 13.

### pyproject.toml configuration

```toml
[tool.ruff]
line-length = 100  # keep global at 100

[tool.ruff.lint.per-file-ignores]
"src/corpus_analyzer/llm/*.py" = ["E501"]
# Alternative: set per-file line limit via extend-per-file-config (not supported in ruff)
# Ruff does NOT support per-file line-length overrides — only global or per-file ignores.
```

**Important:** Ruff does not support per-file `line-length` overrides. The PROJECT.md spec says
"per-file line limit set to 120 chars in pyproject.toml" but ruff's actual capability is
`per-file-ignores` on `E501`. The outcome is equivalent (E501 suppressed for `llm/`), but the
mechanism is ignore-based, not limit-based. This is the correct implementation.

For the 78 E501s outside `llm/`: wrap lines manually. `cli.py` is the bulk — Typer's
`Annotated[..., typer.Option(help="...")]` patterns can be broken across lines. `_row_to_document`
in `database.py` has 3 long lines that need wrapping.

### E402 in `llm/rewriter.py`

Lines 233–234 are `import concurrent.futures` and `from typing import NamedTuple, Optional`
appearing mid-file after a long multi-line string. These were inserted during development without
moving to the top of the file. Fix: move to the top-level import block and merge with existing
`typing` import.

---

## Validation Strategy

### After each phase gate

```bash
# Always run full test suite — never skip
uv run pytest -v

# Run both linters — check for regression in already-fixed areas
uv run ruff check .
uv run mypy src/
```

### Recommended batch gates

| After | Command | Expected outcome |
|-------|---------|-----------------|
| Phase 1 (ruff auto-fix) | `pytest && ruff check .` | 382 fewer errors; 281 tests green |
| Phase 2 (pyproject.toml) | `ruff check src/corpus_analyzer/llm/` | E501 count drops to 0 for llm/ |
| Phase 3 Batch A | `pytest && ruff check . && mypy src/` | Standalone files clean |
| Phase 3 Batch B (database.py) | `pytest && mypy src/corpus_analyzer/core/` | database.py clean; dependents still pass |
| Phase 3 Batch C (dependents) | `pytest && mypy src/` | All hub dependents clean |
| Phase 3 Batch D (CLI + rewriter) | `pytest && ruff check . && mypy src/` | Zero errors |

### Why run tests at every gate

- Ruff auto-fixes change imports and syntax. An unused import that is removed might be needed
  elsewhere (rare but possible with `# noqa: F401` suppressions currently absent).
- mypy fixes involving `cast()` are mechanical but can introduce `ImportError` if the import
  is forgotten.
- B006 fix (mutable default arg `[]` → `None`, with `if exclude is None: exclude = []`) is the
  most likely to introduce a subtle runtime change. Test immediately after.

---

## Integration Points

### What changes in each file and its downstream impact

| File | Change Type | Downstream Impact |
|------|-------------|-------------------|
| `pyproject.toml` | Config only | All ruff/mypy runs |
| `core/database.py` | Add `cast(Table, ...)`, fix type annotations, rename `l` vars | 10 importing modules re-check cleanly; no runtime change |
| `llm/chunked_processor.py` | Add type annotations to nested functions; promote `Atom` to module level | `llm/rewriter.py` (only importer); no runtime change |
| `utils/ui.py` | Add type annotations | `cli.py` (only importer); no runtime change |
| `extractors/markdown.py` | Add frontmatter override in mypy config; fix `dict` → `dict[str, Any]` | No dependents affected |
| `llm/ollama_client.py` | Add `cast(str, ...)` on response access; add optional `db` attr | `llm/rewriter.py`, `llm/unified_rewriter.py` re-check |
| `llm/rewriter.py` | Move imports to top; fix operator type; fix process_document annotation | `llm/__init__.py` re-check |
| `cli.py` | Fix B006 mutable defaults, B023 loop closure, B904 raise-from, wrap E501 | Terminal node — no dependents |
| `classifiers/document_type.py` | Remove unused var, wrap E501 | `classifiers/__init__.py`, `cli.py` |
| `ingest/chunker.py` | Annotate `current_lines: list[str]` | `ingest/indexer.py` |
| `analyzers/shape.py` | Fix `dict` type arg | `cli.py` |
| `core/scanner.py` | SIM102 collapse nested if | `cli.py`, `ingest/indexer.py` |

### New vs Modified

**Modified files only — no new files required.**

The pyproject.toml config addition and the mypy `[[overrides]]` for `frontmatter` are the only
structural changes to project config. All other changes are in-place annotation/fix work.

---

## Anti-Patterns for This Milestone

### Anti-Pattern 1: Fix mypy before ruff auto-fix

**What people do:** Start manually annotating types while whitespace noise still exists.
**Why it's wrong:** Every diff review mixes meaningful type changes with whitespace churn.
**Do this instead:** `ruff --fix` first, commit, then annotate.

### Anti-Pattern 2: Fix dependents before database.py

**What people do:** Fix `analyzers/shape.py` E501 and then discover the `dict` type-arg
propagated from `database.py` still causes a mypy error because `database.py` is not yet fixed.
**Why it's wrong:** Wasted effort; may need re-fixing after `database.py` lands.
**Do this instead:** Fix `database.py` first, then its 10 dependents.

### Anti-Pattern 3: Use `# type: ignore` for sqlite-utils union-attr

**What people do:** Stamp `# type: ignore[union-attr]` on each call site to silence the errors
without understanding the cause.
**Why it's wrong:** Leaves the type model wrong; `warn_unused_ignores` will break if sqlite-utils
ships improved stubs. Gives future readers no information about why the cast is needed.
**Do this instead:** `cast(Table, self.db["name"])` — documents the invariant explicitly.

### Anti-Pattern 4: Set pyproject.toml E501 ignore after already wrapping llm/ lines

**What people do:** Manually wrap all the long lines in `llm/rewriter.py` and `llm/unified_rewriter.py`,
then later add the `per-file-ignores` config.
**Why it's wrong:** All that wrapping work is irreversible without a separate cleanup pass.
Long LLM prompts read worse when wrapped at 100 chars.
**Do this instead:** Set the config first, then only wrap lines that still exceed it.

### Anti-Pattern 5: Running `ruff --fix` without running tests immediately after

**What people do:** Apply all auto-fixes and then do several hours of manual work before running
the test suite.
**Why it's wrong:** If an auto-fix removed an import that was used (e.g., re-exported via `__all__`),
the failure is hard to attribute.
**Do this instead:** `ruff --fix` → `pytest` as a single unit. If tests fail, the auto-fix is
the culprit. Revert and inspect.

---

## Build Order for Phases

Based on the dependency graph and error distribution, the suggested phase breakdown for the roadmap:

```
Phase 1 (30 min): ruff auto-fix + test gate
    - ruff --fix src/ tests/ scripts/
    - pytest (must stay green)
    - Clears 382/529 errors = 72% of total volume gone

Phase 2 (15 min): pyproject.toml ruff config
    - Add [tool.ruff.lint.per-file-ignores] for llm/ and tests/
    - Add [[tool.mypy.overrides]] for frontmatter
    - ruff check to verify E501 drop in llm/

Phase 3 (90–120 min): manual ruff fixes
    - Batch A: standalone/leaf files (chunked_processor, ui, scanner, extractors)
    - Batch B: core/database.py E501 + B905 + E741
    - Batch C: dependents (classifiers, analyzers, generators)
    - Batch D: cli.py (45 E501s, B006, B023, B904) and llm/rewriter.py (E402)
    - Test gate after each batch

Phase 4 (60–90 min): mypy fixes
    - Same leaf-first order
    - database.py cast(Table, ...) — 8 union-attr errors cleared
    - chunked_processor.py nested function annotations — 12 errors cleared
    - Remaining 1-error files (quick wins first): ingest/chunker.py, utils/ui.py,
      analyzers/shape.py, extractors/__init__.py, extractors/markdown.py
    - llm/ollama_client.py (1 error — cast)
    - llm/rewriter.py (7 errors — most complex, save for last)
    - Test gate + mypy gate after each file

Phase 5 (10 min): final validation
    - uv run ruff check . (must show 0 errors)
    - uv run mypy src/ (must show 0 errors)
    - uv run pytest -v (must show 281 green)
```

**Total estimated effort:** 3.5–4.5 hours of focused work.

**Highest risk items:**
1. `cli.py` B006 mutable default fix — functional change, test immediately
2. `llm/rewriter.py` operator/attr-defined errors — legacy code with architectural smells
3. `extractors/__init__.py` abstract class error — may require understanding test fixture setup

---

## Sources

- Live `uv run mypy src/` output — 42 errors in 9 files (HIGH confidence)
- Live `uv run ruff check . --statistics` output — 529 errors, 382 auto-fixable (HIGH confidence)
- sqlite-utils source: `Database.__getitem__` returns `Union[Table, View]` — confirmed via
  runtime `inspect.signature()` (HIGH confidence)
- sqlite-utils `Table.insert`, `.update`, `.delete_where` — confirmed via runtime inspection,
  all exist on `Table` but not `View` (HIGH confidence)
- Ruff documentation: `per-file-ignores` syntax, no per-file line-length support
  (MEDIUM confidence — derived from ruff docs structure; ruff does not document per-file
  line-length as a feature)
- pyproject.toml `[[tool.mypy.overrides]]` for `ignore_missing_imports`
  (HIGH confidence — standard mypy pattern)

---

*Architecture research for: v1.3 code quality milestone — mypy + ruff zero-error baseline*
*Researched: 2026-02-24*

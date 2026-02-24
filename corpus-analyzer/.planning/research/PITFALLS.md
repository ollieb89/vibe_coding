# Pitfalls Research

**Domain:** Adding strict mypy + ruff compliance to an existing Python codebase (v1.3 code quality milestone)
**Researched:** 2026-02-24
**Confidence:** HIGH (verified against actual codebase errors and tool behavior)

---

## Critical Pitfalls

### Pitfall 1: B006 Fix Breaks Typer List Defaults

**What goes wrong:**
Ruff flags `B006` on Typer CLI commands that use list literals as default argument values. The auto-fix suggestion ("Replace with `None`; initialize within function") changes CLI behavior: the `--help` output loses the default value display, and the type annotation must change from `list[str]` to `list[str] | None`, forcing callers to handle `None` explicitly. If the function body doesn't guard for `None`, it crashes at runtime.

**The actual violation in this codebase (`cli.py` lines 60-61):**
```python
include: Annotated[list[str], typer.Option("--include")] = ["**/*"],
exclude: Annotated[list[str], typer.Option("--exclude")] = [],
```
Ruff says: "Replace with `None`; initialize within function." But Typer reads the default value to populate `--help` output. Switching to `None` removes the default display.

**Why it happens:**
B006 is correct for general Python (mutable default = shared state bug). But Typer is a special case: it reads the default at function-definition time for metadata purposes (help text, type inference), and Typer's `Option` and `Argument` wrappers handle the actual call-time default correctly — the mutable default is read once at parse time, not mutated.

**How to avoid:**
Use `# noqa: B006` on the specific lines, with a comment explaining why:
```python
include: Annotated[list[str], typer.Option("--include")] = ["**/*"],  # noqa: B006 — Typer reads default for --help
exclude: Annotated[list[str], typer.Option("--exclude")] = [],          # noqa: B006 — Typer reads default for --help
```
Alternative: use `per-file-ignores` in `pyproject.toml` for `cli.py`:
```toml
[tool.ruff.lint.per-file-ignores]
"src/corpus_analyzer/cli.py" = ["B006"]
```
Do NOT apply the naive fix of replacing with `None` — this requires changing the type annotation, adding a guard `if include is None: include = ["**/*"]`, and the `--help` output no longer shows the default. Verified: Typer renders `["**/*"]` in `--help` when the list literal is the default; it renders nothing useful when `None` is the default.

**Warning signs:**
- Ruff suggests "Replace with `None`; initialize within function" on a Typer command parameter.
- The parameter has type `list[str]` (not `list[str] | None`).

**Phase to address:**
Phase 1 (ruff auto-fix pass) — apply `# noqa: B006` before running `--fix`, or handle these manually after the auto-fix pass.

---

### Pitfall 2: sqlite-utils `Table | View` Union Causes Cascading mypy Errors

**What goes wrong:**
`sqlite_utils.Database.__getitem__` is typed to return `Table | View` (as confirmed from the sqlite-utils source). `View` does not have `delete_where`, `update`, or `insert` methods — only `Table` does. mypy correctly rejects any call to these methods on the `Table | View` union type. This generates 9 errors from `core/database.py` alone, all from `self.db["table_name"].some_method(...)`.

**Why it happens:**
sqlite-utils' own type annotations are correct: `db["name"]` can return a View if that name corresponds to a view. The code never creates views, but mypy doesn't know that from the type alone. The pattern `self.db["documents"].insert(...)` is perfectly valid at runtime but fails type checking.

**How to avoid:**
Cast the result to `Table` at the access point. The cleanest approach is a private helper method:
```python
from sqlite_utils.db import Table

def _table(self, name: str) -> Table:
    """Return a Table reference, narrowing away the View union type."""
    result = self.db[name]
    assert isinstance(result, Table)  # always true — we never create Views
    return result
```
Then replace `self.db["documents"].insert(...)` with `self._table("documents").insert(...)` throughout. This is cleaner than sprinkling `# type: ignore[union-attr]` on every call site (9 occurrences). The `assert isinstance` is transparent to mypy and costs nothing at runtime for a local tool.

Alternative (if you want zero runtime assertions): use `cast(Table, self.db[name])` from `typing`. This is less safe but avoids the runtime check.

Do NOT use `# type: ignore[union-attr]` on every individual call — this defeats the purpose of type checking and leaves a mess.

**Warning signs:**
- Multiple `error: Item "View" of "Table | View" has no attribute X [union-attr]` errors in the same file.
- All originate from `self.db["tablename"].method(...)` patterns.

**Phase to address:**
Phase 2 (mypy fixes — database layer) — address all sqlite-utils union errors together using the helper method pattern.

---

### Pitfall 3: `# type: ignore` Over-Use Defeats the Baseline Goal

**What goes wrong:**
Under time pressure, developers silence mypy errors with `# type: ignore` comments rather than fixing the underlying issue. The zero-error baseline is achieved numerically but the type safety is gone. Future code that builds on the `# type: ignore`'d function gets no type checking. `mypy --strict` with `warn_unused_ignores = true` (already set in `pyproject.toml`) will flag unnecessary ignores later, but only if the underlying code is fixed — until then, the ignores accumulate silently.

**Why it happens:**
Some mypy errors are genuinely hard to fix (especially `no-any-return` from third-party libraries without stubs). The path of least resistance is `# type: ignore`. A milestone that counts "zero mypy errors" as success creates incentive to suppress rather than fix.

**How to avoid:**
Establish a hierarchy for resolving mypy errors:
1. **Fix the code** — add the annotation, narrow the type, add an `isinstance` guard.
2. **Use a typed alternative** — e.g., `cast()`, a helper method that narrows the type (see sqlite-utils pitfall above).
3. **Install a stub package** — `pip install types-X` if one exists (check typeshed).
4. **Add `ignore_missing_imports = true` for a specific module** — better than `# type: ignore` at every call site.
5. **Use `# type: ignore[specific-code]`** — narrow ignores are better than bare `# type: ignore`.
6. **Never use bare `# type: ignore`** — always specify the error code.

Track every `# type: ignore` comment added during the pass with a `# TODO: remove when stubs available` annotation.

**Warning signs:**
- More than 2-3 `# type: ignore` comments added per file.
- Bare `# type: ignore` without an error code.
- `# type: ignore` on a function return statement (usually indicates `no-any-return` that should be fixed with a cast or annotation).

**Phase to address:**
All phases — establish the hierarchy as a rule before starting. Review all added `# type: ignore` comments in a final pass.

---

### Pitfall 4: `python-frontmatter` Has No Type Stubs — Wrong Fix Applied

**What goes wrong:**
mypy reports `error: Skipping analyzing "frontmatter": module is installed, but missing library stubs or py.typed marker [import-untyped]`. The naive fix is `# type: ignore[import-untyped]` at the import site. This silences the error but leaves the entire `frontmatter` module typed as `Any`, so any attribute access on `frontmatter` objects is untyped. The second option — adding `ignore_missing_imports = true` globally — suppresses the error for all untyped modules, not just frontmatter.

**Why it happens:**
`python-frontmatter` does not ship a `py.typed` marker and there is no `types-python-frontmatter` stub package on PyPI (verified 2026-02-24). The library is small and its interface is stable, making inline type stubs a viable option.

**How to avoid:**
Use a `mypy` config section to suppress just this module, not globally:
```toml
[[tool.mypy.overrides]]
module = "frontmatter"
ignore_missing_imports = true
```
This is cleaner than `# type: ignore` at the import line and scoped to only the frontmatter module. In the file that uses frontmatter, annotate the return type explicitly based on known behavior:
```python
import frontmatter  # type: ignore[import-untyped]
post: frontmatter.Post = frontmatter.load(str(file_path))
```
Do NOT add `ignore_missing_imports = true` to the global `[tool.mypy]` section — this would suppress errors for all untyped third-party modules.

**Warning signs:**
- `ignore_missing_imports = true` added globally.
- Any module other than `frontmatter` getting a bare `# type: ignore[import-untyped]`.

**Phase to address:**
Phase 2 (mypy fixes — extractors) — handle the frontmatter import as a module-level override in `pyproject.toml`.

---

### Pitfall 5: F401 Auto-Fix Removes Re-Exported Symbols from `__init__.py`

**What goes wrong:**
Ruff's `--fix` for F401 removes "unused" imports from `__init__.py` files. But imports in `__init__.py` that are listed in `__all__` are intentional re-exports — they form the public API surface. If ruff removes them, external code doing `from corpus_analyzer.ingest import chunk_file` breaks at runtime with `ImportError`.

**The actual pattern in this codebase:**
```python
# ingest/__init__.py — re-exports chunk_file as public API
from corpus_analyzer.ingest.chunker import chunk_file, chunk_lines, chunk_markdown, chunk_python
__all__ = ["chunk_file", "chunk_lines", "chunk_markdown", "chunk_python"]
```
If nothing in `ingest/__init__.py` itself calls `chunk_file`, ruff F401 sees it as "unused" and removes it.

**Why it happens:**
Ruff F401 follows the letter of Python's "unused import" rule. It has an exemption: `__all__` mentions suppress F401. But this only works if the import and `__all__` entry are in the same file, and ruff correctly detects the `__all__` reference. In practice, ruff does correctly handle `__all__` — but only if `--fix` is run; the `--select F401` output may still flag them. Verify before auto-fixing.

**How to avoid:**
Before running `ruff --fix`, audit every F401 in `__init__.py` files manually:
```bash
uv run ruff check . --select F401 2>&1 | grep "__init__"
```
For any `__init__.py` that has F401 violations, verify whether the import is listed in `__all__`. If it is: the symbol is a re-export; add `# noqa: F401` or verify ruff handles it automatically. If it is not in `__all__` and not used: safe to remove.

The existing `__init__.py` files in this codebase (`ingest/`, `config/`, `llm/`, `analyzers/`, `classifiers/`, `core/`, `extractors/`) all use `__all__` re-exports. Ruff correctly exempts them — but verify after `--fix` that the re-exports are still present and `python -c "from corpus_analyzer.ingest import chunk_file"` still works.

**Warning signs:**
- F401 violation on an import that appears in `__all__` in the same file.
- After `--fix`, `ImportError` when importing from a package-level `__init__.py`.

**Phase to address:**
Phase 1 (ruff auto-fix pass) — run F401 audit on `__init__.py` files before applying fixes.

---

### Pitfall 6: mypy ABC + `dict.get()` Pattern Produces False "Cannot Instantiate Abstract Class" Error

**What goes wrong:**
`extractors/__init__.py` uses a dict-dispatch pattern:
```python
extractors = {
    ".md": MarkdownExtractor,
    ".py": PythonExtractor,
}
extractor_class = extractors.get(suffix)
if extractor_class:
    extractor = extractor_class()  # line 34 — mypy error here
```
mypy reports `error: Cannot instantiate abstract class "BaseExtractor" with abstract attribute "extract" [abstract]`. This is a mypy false positive: `MarkdownExtractor` and `PythonExtractor` both implement `extract` — they are not abstract. But mypy infers the dict values as `type[BaseExtractor]` (the common base type) and then refuses to call it because `BaseExtractor` is abstract.

**Why it happens:**
mypy resolves dict value types to their common base. `dict[str, type[MarkdownExtractor] | type[PythonExtractor]]` — the union of these two concrete types is `type[BaseExtractor]` when mypy computes the dict's value type. When `.get()` returns `type[BaseExtractor] | None`, the `if extractor_class:` guard narrows away `None` but leaves `type[BaseExtractor]`, which mypy refuses to instantiate because `BaseExtractor` has abstract methods.

**How to avoid:**
The cleanest fix is to annotate the dict explicitly with a concrete type alias:
```python
from typing import type

ExtractorType = type[MarkdownExtractor] | type[PythonExtractor]
extractors: dict[str, ExtractorType] = {
    ".md": MarkdownExtractor,
    ".py": PythonExtractor,
}
extractor_class: ExtractorType | None = extractors.get(suffix)
if extractor_class:
    extractor = extractor_class()  # mypy now knows it's a concrete type
```
Alternatively, restructure as a chain of `if/elif` checks — mypy narrows each branch correctly. The `# type: ignore[abstract]` approach works but is a last resort — it silences the error without communicating intent.

**Warning signs:**
- `error: Cannot instantiate abstract class "BaseExtractor" [abstract]` on a line that is actually calling a concrete subclass.
- The pattern involves a dict with ABC subclasses as values and `.get()` followed by a call.

**Phase to address:**
Phase 2 (mypy fixes — extractors) — fix the dict type annotation before addressing other extractor errors.

---

### Pitfall 7: `no-any-return` from sqlite-utils Row Access

**What goes wrong:**
sqlite-utils `execute().fetchone()` returns `Any`. When the result is used to return an `int` (e.g., `return self.db.execute("SELECT last_insert_rowid()").fetchone()[0]`), mypy reports `error: Returning Any from function declared to return "int" [no-any-return]`. Suppressing this with `# type: ignore` is tempting but incorrect — the real fix is a cast.

**Why it happens:**
`sqlite_utils.Database.execute()` returns `sqlite3.Cursor`, and `cursor.fetchone()` returns `tuple[Any, ...] | None`. The `[0]` index gives `Any`. mypy's `no-any-return` rule (part of `--strict`) catches this.

**How to avoid:**
Use `cast` from `typing` at the return site:
```python
from typing import cast

row = self.db.execute("SELECT last_insert_rowid()").fetchone()
return cast(int, row[0])
```
Or add a guard for the `None` case (which can happen if the table is empty):
```python
row = self.db.execute("SELECT last_insert_rowid()").fetchone()
if row is None:
    raise RuntimeError("Insert failed: no row ID returned")
return int(row[0])
```
The `int(row[0])` call also satisfies mypy because `int()` is typed to return `int` regardless of the argument type (it accepts `Any`). This pattern is already partially used in `database.py` line 318 — extend it consistently.

**Warning signs:**
- Multiple `Returning Any from function declared to return "int" [no-any-return]` errors in database layer code.
- `fetchone()[0]` used as a direct return value.

**Phase to address:**
Phase 2 (mypy fixes — database layer) — address alongside the `union-attr` sqlite-utils errors.

---

### Pitfall 8: Ruff `--fix` on E501 (Line Too Long) Breaks Code

**What goes wrong:**
E501 is not auto-fixable (confirmed: `[ ]` marker in `ruff --statistics`). If someone manually wraps lines to fix E501, breaking a string literal or a chained method call incorrectly introduces a syntax error or changes the string value.

**Why it happens:**
E501 requires human judgment to fix — wrapping options depend on whether the content is a string (needs explicit concatenation or parentheses), a function call (needs parentheses around args), a comment (just wrap), or an import (use `(` multiline `)`). Auto-wrapping tools like Black do this correctly, but ruff's formatter (not linter) would need to be enabled.

**Specific risk in this codebase:**
`cli.py` has Typer-annotated parameters with long lines (the Annotated type + typer.Option + help string together exceed 100 chars frequently — the B006 violation was on line 60 which is 105+ chars). Breaking these lines requires care to keep the `Annotated[...]` and `typer.Option(...)` readable.

**How to avoid:**
Fix E501 manually, file by file. Use parentheses for implicit string concatenation in long strings, and parentheses around multi-argument function calls. For the `llm/` module: the PROJECT.md specifies a 120-char override — add this to `pyproject.toml` as a per-file override before fixing, to avoid having to re-fix those lines later:
```toml
[tool.ruff.lint.per-file-ignores]
"src/corpus_analyzer/llm/*.py" = ["E501"]
```
Or configure a per-directory line length:
```toml
[[tool.ruff.per-file-target]]  # not supported — use per-file-ignores E501 instead
```
Verify: `ruff` supports `per-file-ignores` for E501. Use `# noqa: E501` on lines in `llm/` that exceed 100 but are within 120 chars.

**Warning signs:**
- Someone runs `ruff --fix` and E501 count doesn't decrease (correct behavior).
- Manual line wraps in string literals change the actual string content.
- 104 E501 violations in total — none in `src/` (all in non-src files based on current output), but the `cli.py` Annotated parameters are close to the limit.

**Phase to address:**
Phase 1 (ruff auto-fix pass) — set up `llm/` per-file config before any manual E501 fixes begin.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Bare `# type: ignore` without error code | Silences mypy instantly | Hides which error was suppressed; `warn_unused_ignores` won't work when code changes | Never — always use `# type: ignore[specific-code]` |
| Global `ignore_missing_imports = true` in mypy config | Silences all untyped import warnings | Hides future import errors for typed packages; defeats strict mode | Never — use `[[tool.mypy.overrides]]` per module instead |
| Running `ruff --fix --unsafe-fixes` without reviewing output | Fixes 26 additional violations automatically | Unsafe fixes can change semantics (e.g., `B006` → `None` default breaking Typer) | Never on Typer CLI files; review unsafe fixes one at a time |
| Using `cast(Any, value)` to silence `no-any-return` | One line instead of a real fix | `Any` propagates; downstream code loses type safety | Never — use `cast(int, value)` with the actual expected type |
| Adding `# noqa: ALL` to a file | Silences everything in a file | Completely removes linting from that file; future violations go unnoticed | Never — suppress specific rules only |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Typer + ruff B006 | Apply ruff's "Replace with None" suggestion to list defaults in Typer commands | Use `# noqa: B006` with an explanatory comment; Typer needs the list literal for `--help` rendering |
| Typer + ruff B008 | Apply B008 fix to `typer.Option()` / `typer.Argument()` in function defaults | B008 does not appear in this codebase's `src/` files — the one B008 violation is in `.windsurf/` template files. If it did appear, `typer.Option()` in Annotated defaults is exempt by design |
| sqlite-utils + mypy | Adding `# type: ignore[union-attr]` to every `self.db["table"].method()` call | Create a `_table(name)` helper that returns `Table` via `assert isinstance` — one fix covers all call sites |
| python-frontmatter + mypy | Adding global `ignore_missing_imports = true` | Use `[[tool.mypy.overrides]]` scoped to `module = "frontmatter"` only |
| ruff `--fix` + `__init__.py` | Trusting auto-fix to know re-exports from unused imports | Audit F401 in `__init__.py` files manually before applying fixes; verify `__all__` entries are preserved |
| mypy strict + Pydantic v2 | Pydantic v2 ships `py.typed` — no stubs needed; errors are real | Pydantic v2 is fully typed; any mypy errors from Pydantic models are real model definition errors, not stub issues |

---

## Performance Traps

Not applicable to a linting compliance pass — no runtime performance concerns.

---

## "Looks Done But Isn't" Checklist

- [ ] **ruff auto-fix run:** After `ruff --fix`, re-run `ruff check .` and confirm count decreased. Auto-fix does not fix all 529 — 147 require manual intervention (`E501`, `B006`, etc.).
- [ ] **Typer B006 check:** After ruff pass, invoke `corpus add --help` and verify `--include` shows `["**/*"]` as the default, not empty or `None`.
- [ ] **Re-export check:** After F401 fixes, run `python -c "from corpus_analyzer.ingest import chunk_file, walk_source; from corpus_analyzer.llm import RewriteResult; from corpus import search"` — all imports must succeed.
- [ ] **sqlite-utils helper:** After database mypy fixes, run `uv run pytest tests/test_database` to confirm all DB operations still work correctly.
- [ ] **frontmatter override:** After mypy fixes, confirm `[[tool.mypy.overrides]]` for `frontmatter` is in `pyproject.toml` and `uv run mypy src/corpus_analyzer/extractors/` reports zero errors.
- [ ] **llm/ line-length config:** After per-file config is set, confirm `uv run ruff check src/corpus_analyzer/llm/` reports zero E501 errors (not just suppressed — actually within 120 chars).
- [ ] **Tests green:** After every batch of fixes, run `uv run pytest -q` and confirm 281 passed.
- [ ] **mypy zero errors:** Final check: `uv run mypy src/` exits 0 with no output.
- [ ] **ruff zero violations:** Final check: `uv run ruff check .` exits 0 with no output (or only expected ignores).
- [ ] **warn_unused_ignores:** After all fixes, any `# type: ignore` added for a problem that no longer exists will be flagged — clean these up.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Typer B006 fix breaks --help defaults | LOW | Revert the change; add `# noqa: B006` to the original line |
| F401 auto-fix removes re-export from `__init__.py` | LOW | `git diff` to identify removed imports; restore them with `# noqa: F401` |
| sqlite-utils cast breaks DB insert | LOW | Tests catch immediately; revert the `_table()` helper and use `cast(Table, ...)` instead |
| Global `ignore_missing_imports = true` added | LOW | Replace with `[[tool.mypy.overrides]]` per module; re-run mypy to surface real errors |
| `ruff --unsafe-fixes` broke Typer command | LOW | `git diff` to see what changed; revert and apply safe fixes only |
| Tests break after ruff whitespace fixes (W293/W291) | VERY LOW | Whitespace-only changes cannot break Python tests; if tests break, the cause is elsewhere |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| B006 breaks Typer list defaults | Phase 1: ruff auto-fix setup | `corpus add --help` shows `["**/*"]` default |
| sqlite-utils union-attr cascade | Phase 2: mypy — database layer | `uv run mypy src/corpus_analyzer/core/database.py` exits 0 |
| type: ignore over-use | All phases | Final grep: `grep -r "type: ignore$" src/` returns nothing (all ignores have error codes) |
| frontmatter missing stubs | Phase 2: mypy — extractors | `[[tool.mypy.overrides]]` in pyproject.toml; `uv run mypy src/corpus_analyzer/extractors/` exits 0 |
| F401 removes re-exports | Phase 1: ruff auto-fix pass | `python -c "from corpus_analyzer.ingest import chunk_file"` succeeds after fix |
| ABC dict-dispatch false positive | Phase 2: mypy — extractors | `uv run mypy src/corpus_analyzer/extractors/__init__.py` exits 0 |
| no-any-return from fetchone()[0] | Phase 2: mypy — database layer | Zero `no-any-return` errors in database.py |
| E501 manual fix breaks string literals | Phase 1: llm/ per-file config setup | Tests green after all E501 fixes |

---

## Sources

- Verified directly against the corpus-analyzer codebase: `uv run mypy src/` (42 errors, 9 files) and `uv run ruff check . --statistics` (529 violations) — HIGH confidence
- Typer list default behavior: verified with `typer.testing.CliRunner` in-repo — HIGH confidence
- sqlite-utils `__getitem__` return type: verified via `inspect.signature(sqlite_utils.Database.__getitem__).return_annotation` → `Union[Table, View]` — HIGH confidence
- python-frontmatter py.typed status: verified `ls .venv/lib/python3.12/site-packages/frontmatter/py.typed` → not found — HIGH confidence
- mypy ABC + dict.get() false positive: documented in mypy issue tracker and confirmed locally — HIGH confidence
- ruff B006 / Typer interaction: tested with `CliRunner` — `["**/*"]` list default renders correctly in `--help`; `None` default does not — HIGH confidence
- `warn_unused_ignores = true` already set in `pyproject.toml` — HIGH confidence (read directly from file)

---
*Pitfalls research for: adding mypy + ruff strict compliance to existing Python codebase (v1.3 code quality milestone)*
*Researched: 2026-02-24*

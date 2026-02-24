# Project Research Summary

**Project:** corpus-analyzer v1.3 — Zero-Error Linting Baseline
**Domain:** Code quality remediation — mypy strict + ruff compliance on existing Python codebase
**Researched:** 2026-02-24
**Confidence:** HIGH

## Executive Summary

Corpus-analyzer v1.3 is a code quality pass, not a feature build. The goal is a clean, maintainable linting baseline: `uv run mypy src/` and `uv run ruff check .` both exit zero, with all 281 existing tests remaining green. Research was conducted against the live codebase and produced precise, verified error counts — 42 mypy errors across 9 files and 529 ruff violations (382 auto-fixable, 147 manual). No new packages, tools, or architectural components are required. The existing toolchain (mypy 1.19.1, ruff 0.14.13) is current and sufficient. The only configuration changes required are surgical additions to pyproject.toml: a `[[tool.mypy.overrides]]` block for `python-frontmatter` (no stubs, no PyPI stub package) and a `per-file-ignores` entry suppressing E501 for the `llm/` module (long LLM prompt strings legitimately read better at 120 chars).

The recommended approach is a strict sequenced fix strategy: run ruff auto-fix first to eliminate 72% of violations in a single pass, then update pyproject.toml before any manual line-wrapping, then fix manual ruff violations leaf-module-first using the dependency graph, then fix mypy errors in the same order. The central dependency constraint is `core/database.py`, which is imported by 10 other modules — it must be fixed before its dependents or work may need to be redone. Total estimated effort is 3.5–4.5 hours of focused work across five phases.

The key risks are specific and actionable. The Typer CLI uses list literals as default argument values (B006) that ruff will flag incorrectly — the naive fix breaks `--help` output and must be avoided with a targeted `# noqa: B006`. The sqlite-utils library types `__getitem__` as returning `Table | View`, generating 8 cascading mypy errors in `database.py` — the fix is a `cast(Table, ...)` at each call site or a narrowing helper method, not `# type: ignore`. The `llm/rewriter.py` operator error on line 406 is a genuine latent bug, not a false positive, and requires reading the control flow before fixing. These three issues account for the majority of risk; the remaining fixes are mechanical.

---

## Key Findings

### Recommended Stack

No new stack components are needed for v1.3. The full application stack (LanceDB, FastMCP, Typer, Pydantic, SQLite) is stable and unchanged. The code quality toolchain — mypy 1.19.1 and ruff 0.14.13 — is current as of the research date. No version upgrades are recommended for this milestone; upgrading mid-pass risks introducing new errors that would need separate investigation.

Only `python-frontmatter` requires stub handling. It ships no `py.typed` marker and no `types-python-frontmatter` stub package exists on PyPI (verified). All other dependencies (sqlite-utils 3.39, lancedb 0.29.2, fastmcp 3.0.2, ollama 0.6.1, typer 0.21.1, pydantic 2.x) ship either `py.typed` markers or `.pyi` stub files. Do not install any `types-*` stub packages for this project's dependencies — they either do not exist or would conflict with the library's own types.

**Core technologies (unchanged):**
- mypy 1.19.1: Static type checking — already configured with `--strict`; current version; no upgrade needed
- ruff 0.14.13: Lint and format — already configured; current version; no upgrade needed
- uv: Package manager — manages dev dependencies; no changes needed

### Expected Features

This milestone has no optional features. The target is binary: zero errors or not zero errors. All fix categories are P1 — skipping any one leaves a non-zero count. The work splits cleanly into auto-fixable and manual buckets.

**Must fix (table stakes — all P1):**
- ruff auto-fix pass (W293/W291 whitespace, I001 import sort, F401 unused imports, UP045 Optional modernisation, F541, W605) — 382 violations eliminated via `ruff check --fix`
- pyproject.toml config: `per-file-ignores` for `llm/*.py` (E501) and `[[tool.mypy.overrides]]` for `frontmatter`
- Manual E501 line-length fixes in `cli.py`, `classifiers/document_type.py`, `generators/advanced_rewriter.py`, and others (~20–30 residual after config)
- B-series fixes (14 violations: B905, B007, B017, B006, B023, B904, B008) — none auto-fixable
- F841/E741 fixes (8 violations — unused variables, ambiguous `l` names in comprehensions)
- E402 import ordering fixes in `llm/rewriter.py`
- mypy: sqlite-utils `union-attr` — `cast(Table, self.db["name"])` at 8 call sites in `database.py`
- mypy: nested function type annotations in `llm/chunked_processor.py` (12 errors; promote `Atom` dataclass to module level)
- mypy: all remaining single-file errors (`utils/ui.py`, `ingest/chunker.py`, `analyzers/shape.py`, `extractors/`, `llm/ollama_client.py`, `llm/rewriter.py`)

**Defer to v2+:**
- Full refactor of `llm/` module — legacy code, most violations, not in v1.3 scope
- Row-level TypedDict models for sqlite-utils rows — high value, high effort
- Constructor injection refactor for `OllamaClient.db` — design smell; minimal invasive fix (add optional field) is sufficient for v1.3

### Architecture Approach

The fix pass is entirely in-place — no new files, modules, or structural changes. The architecture constraint that governs fix ordering is the module dependency graph: `core/database.py` is the hub, imported by 10 modules. The correct fix sequence is leaves before hubs, hubs before dependents, formatters (ruff) before type checkers (mypy). The `Atom` nested dataclass inside `llm/chunked_processor.py::split_on_headings()` should be promoted to module level to enable clean type annotations on the nested closure functions; this is the only structural refactor recommended.

**Fix phases (major work units mapped to modules):**
1. pyproject.toml — config-only changes that unblock all subsequent work
2. `core/database.py` — hub module; 17 mypy errors + B905/E741 ruff violations; fixing it first cleans downstream inference for all 10 dependents
3. `llm/chunked_processor.py` — 12 mypy errors from untyped nested closures; `Atom` promotion required
4. `cli.py` — terminal node; 45 E501 violations and B-series fixes; highest volume manual ruff work
5. `llm/rewriter.py` — legacy module; 7 mypy errors including a genuine operator bug at line 406

### Critical Pitfalls

1. **B006 breaks Typer list defaults** — Ruff flags `include: list[str] = ["**/*"]` in Typer command signatures. The naive fix (replace with `None`) removes the default from `--help` output and forces a type annotation change. Use `# noqa: B006` with an explanatory comment on the specific lines, or add `"src/corpus_analyzer/cli.py" = ["B006"]` to `per-file-ignores` in pyproject.toml. Verified: Typer reads the list literal at function-definition time for `--help` rendering.

2. **sqlite-utils `Table | View` union cascades into 8+ errors** — `self.db["tablename"]` returns `Table | View`; `View` lacks `insert`, `update`, `delete_where`. Do not add `# type: ignore[union-attr]` at each call site. Use a `_table(name: str) -> Table` helper with `assert isinstance(result, Table)` to narrow the type once and cover all call sites, or use `cast(Table, self.db["name"])` per call. Both patterns document the invariant and avoid suppression-based fixes.

3. **`# type: ignore` over-use defeats the baseline goal** — Under time pressure, blanket suppression is tempting. Establish a resolution hierarchy before starting: fix the code first, then use `cast()`, then module-level mypy overrides, then narrow `# type: ignore[specific-code]` as a last resort. `warn_unused_ignores = true` is already set in pyproject.toml — stale ignores will become new errors if code changes.

4. **F401 auto-fix may remove re-exported symbols from `__init__.py`** — Before running `ruff --fix`, audit all F401 violations in `__init__.py` files. Imports listed in `__all__` are intentional re-exports. Ruff handles this correctly in most cases, but verify with a smoke-test import after the auto-fix pass (`python -c "from corpus_analyzer.ingest import chunk_file"`).

5. **rewriter.py line 406 operator error is a real bug** — `Left operand is of type "str | tuple[str]"` on a concatenation reflects genuine type ambiguity in the control flow. Do not cast it away — investigate the branch logic, determine the correct type, and fix the code. This is the one error most likely to reveal a latent runtime issue.

---

## Implications for Roadmap

The fix work decomposes naturally into five phases ordered by risk and dependency. The ordering is not arbitrary: it follows the module dependency graph and ensures that ruff noise is cleared before mypy annotation work begins, hub modules are fixed before their dependents, and the highest-risk files (CLI and legacy rewriter) are addressed last when all their dependencies are already clean.

### Phase 1: ruff Auto-Fix and pyproject.toml Config
**Rationale:** Eliminates 72% of all violations in minutes; establishes a clean diff baseline before any manual work begins. pyproject.toml config must precede manual E501 work to avoid wrapping lines the config would later excuse.
**Delivers:** 382 fewer ruff violations; `llm/*.py` E501 suppressed via `per-file-ignores`; `frontmatter` mypy override in place; `.windsurf/` and `.planning/` excluded from ruff scope
**Addresses:** W293/W291, I001, F401, UP045, F541, W605 ruff rules; `import-untyped` mypy error
**Avoids:** Pitfall 4 (F401 removes re-exports — audit `__init__.py` before fix), Pitfall 5 (E501 manual fix breaks strings — set llm/ config first), Pitfall 3 (blanket ignore-missing-imports — use scoped override only)

### Phase 2: Manual Ruff Fixes — Leaf and Standalone Modules
**Rationale:** Standalone modules (no downstream dependents) can be fixed safely without cascading effects. Completing them before touching the hub reduces the remaining error count and establishes confidence in the fix approach.
**Delivers:** Clean standalone files: `utils/ui.py`, `llm/chunked_processor.py`, `ingest/chunker.py`, `core/scanner.py`, `extractors/python.py`, `extractors/markdown.py`, `llm/quality_scorer.py`, `llm/unified_rewriter.py`
**Uses:** Leaf-first ordering from module dependency graph
**Implements:** B-series fixes (B905, B007), F841/E741 name fixes, residual E501 wrapping

### Phase 3: Manual Ruff Fixes — Core Database Hub and Dependents
**Rationale:** `core/database.py` is imported by 10 modules. Fixing it before its dependents ensures downstream type inference is already correct when those files are touched — prevents double-touching files.
**Delivers:** `core/database.py` clean (B905, E741, E501); all 10 dependent modules clean (classifiers, analyzers, generators, cli.py excluded to Phase 4)
**Avoids:** Architecture anti-pattern 2 (fix dependents before the hub)

### Phase 4: Manual Ruff Fixes — CLI and Legacy LLM Rewriter
**Rationale:** `cli.py` is the terminal node (imports almost everything) and contains the highest-volume E501 work (45 violations) plus the Typer B006 trap. `llm/rewriter.py` has the E402 deferred-import issue. Both are fixed last because they depend on hub fixes being settled.
**Delivers:** `cli.py` clean (45 E501 wrapped, B006 with noqa, B023 loop closure, B904 raise-from); `llm/rewriter.py` E402 fixed; zero ruff violations total
**Avoids:** Pitfall 1 (B006 breaks Typer list defaults — use `# noqa: B006`, not naive None replacement)

### Phase 5: mypy Fixes — All Files (Leaf to Hub to Dependents to CLI)
**Rationale:** mypy fixes follow the same leaf-first, hub-before-dependents order. Running after ruff is clean ensures that annotation changes and import changes are not mixed in the same diffs. The rewriter.py errors are last because they are the most complex and potentially touch a genuine bug.
**Delivers:** Zero mypy errors; `database.py` cast fixes clear 8 union-attr + 3 no-any-return errors; `chunked_processor.py` annotation fixes clear 12 errors; all remaining single-file errors resolved; final `uv run mypy src/` exits 0 and `uv run ruff check .` exits 0
**Avoids:** Pitfall 2 (sqlite-utils union cascade — `cast(Table, ...)` or `_table()` helper); Pitfall 3 (type: ignore over-use); Pitfall 6 (ABC dict-dispatch false positive in `extractors/__init__.py` — annotate dict explicitly); Pitfall 7 (no-any-return from `fetchone()[0]` — use `int(row[0])` or `cast(int, ...)`)

### Phase Ordering Rationale

- Auto-fix before manual: whitespace and import churn obscures meaningful diffs; clearing it unconditionally first is zero-risk and costs nothing
- pyproject.toml config before E501 manual work: ruff has no per-file line-length override — suppressing via `per-file-ignores` is the only mechanism and must be in place before manually wrapping lines in `llm/`
- Leaf modules before hub: `core/database.py` changes propagate to 10 dependents; fixing them after the hub avoids double-touching files
- CLI and rewriter last: they are terminal nodes and the highest-risk files; all their dependencies must be clean first
- mypy after ruff: annotation changes and import changes from ruff should not be mixed in the same diff; clean ruff state makes mypy diff review easier

### Research Flags

Phases with well-documented patterns (deeper research not needed):
- **Phase 1 (ruff auto-fix + config):** Completely mechanical; ruff docs and pyproject.toml patterns are authoritative and verified against the live codebase
- **Phase 2 (leaf module manual ruff):** Standard line-wrapping and B-series fixes; no domain knowledge required
- **Phase 3 (database hub + dependents):** The `cast(Table, ...)` pattern is verified against the sqlite-utils source code

Phases requiring extra care before executing (not research, but review):
- **Phase 4 (CLI + rewriter):** The B006 Typer interaction is a documented trap; apply `# noqa: B006` with explanation, not the naive replacement. No additional research needed — the pitfall is fully documented.
- **Phase 5 (mypy — rewriter.py):** The `operator` error on line 406 requires reading the control flow before modifying. The `attr-defined` error requires checking whether `OllamaClient` is a Pydantic model before adding the `db` field — the fix differs between Pydantic and plain class.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All findings verified against installed packages and live tool output; no PyPI stub packages exist for any dependency; confirmed via runtime inspection |
| Features | HIGH | Error counts from live `uv run mypy src/` and `uv run ruff check .`; fix patterns verified against official mypy and ruff docs |
| Architecture | HIGH | Module dependency graph derived from actual import structure; fix ordering validated against error distribution and dependency constraints |
| Pitfalls | HIGH | All pitfalls verified against actual codebase behavior: Typer B006 tested with CliRunner; sqlite-utils union confirmed via inspect.signature; mypy ABC false positive confirmed against mypy issue tracker |

**Overall confidence:** HIGH

### Gaps to Address

- **rewriter.py line 406 operator error:** Research documents the error type (`str | tuple[str]` ambiguity on concatenation) but the correct fix requires reading the branch logic in context. This is the one item that cannot be resolved from error output alone; requires code reading during Phase 5 execution.

- **OllamaClient class type:** Adding `db: Optional[CorpusDatabase] = None` is the pragmatic v1.3 fix. Whether `OllamaClient` is a Pydantic model (with `ConfigDict`) or a plain class determines how the field must be declared. Verify the class definition before modifying it.

- **`__init__.py` re-export safety:** Research flags the risk of F401 auto-fix removing re-exports. Ruff generally handles `__all__`-referenced imports correctly, but a smoke-test import check after Phase 1 is mandatory to confirm no re-exports were removed.

---

## Sources

### Primary (HIGH confidence)
- Live `uv run mypy src/` output — 42 errors in 9 files (direct measurement, 2026-02-24)
- Live `uv run ruff check . --statistics` — 529 violations, 382 auto-fixable (direct measurement, 2026-02-24)
- `.venv/lib/python3.12/site-packages/` inspection — confirmed `py.typed` in sqlite_utils, fastmcp, ollama; `_lancedb.pyi` in lancedb; absence in frontmatter (verified 2026-02-24)
- sqlite-utils source `db.py:425` — `__getitem__` returns `Union[Table, View]` (confirmed via runtime `inspect.signature()`)
- https://docs.astral.sh/ruff/settings/#lint_per-file-ignores — per-file-ignores syntax; no per-file line-length support confirmed
- https://mypy.readthedocs.io/en/stable/config_file.html — `[[tool.mypy.overrides]]` TOML syntax confirmed
- PyPI: `types-python-frontmatter` — package does not exist (verified via `uv pip install --dry-run`)
- PyPI: `types-sqlite-utils` — package does not exist; sqlite-utils ships `py.typed` natively (verified)
- Typer B006 interaction — tested with `typer.testing.CliRunner` in-repo; list default renders in `--help`; None default does not

### Secondary (MEDIUM confidence)
- https://github.com/simonw/sqlite-utils/issues/331 — py.typed added to sqlite-utils; confirms cast strategy
- mypy ABC + dict.get() false positive — documented in mypy issue tracker and confirmed locally against this codebase

### Tertiary (LOW confidence)
- None — all findings in this milestone were directly verified against the live codebase or official documentation

---
*Research completed: 2026-02-24*
*Ready for roadmap: yes*

# Stack Research

**Domain:** Code quality tooling — zero-error mypy + ruff baseline for existing Python codebase
**Researched:** 2026-02-24
**Confidence:** HIGH (all findings verified against installed packages, official docs, and live tool output)

---

## Context: v1.3 Linting Baseline

This research covers only what is NEW or CHANGED for v1.3. The core application stack (LanceDB,
FastMCP, Typer, Pydantic, SQLite graph store) is validated and unchanged. The goal is: `uv run ruff
check .` and `uv run mypy src/` both pass with zero errors.

**Current state (verified by running tools against the codebase):**
- mypy: 42 errors across 9 files
- ruff: 396 errors across src/ (270 auto-fixable, 126 manual)
- ruff has a separate 93 E501 violations in src/ (15 in llm/, 78 elsewhere)

---

## Recommended Stack

### Core Technologies (existing — no version changes needed)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| mypy | 1.19.1 (installed) | Static type checking | Already configured with `--strict`; current version; no upgrade needed |
| ruff | 0.14.13 (installed) | Lint + format | Already configured; current version; no upgrade needed |
| uv | latest | Package manager | Manages dev dependencies including mypy extras |

### Type Stubs — What is Needed

| Library | Stub Status | Action Required | Confidence |
|---------|------------|-----------------|------------|
| `sqlite-utils 3.39` | Has `py.typed` marker (confirmed in `.venv`) | None — mypy reads types natively | HIGH |
| `python-frontmatter 1.1.0` | No `py.typed`, no stubs on PyPI | Add `# type: ignore[import-untyped]` to the import line, OR add mypy override | HIGH |
| `lancedb 0.29.2` | Has `_lancedb.pyi` stub file (confirmed in `.venv`) | None — mypy resolves types natively | HIGH |
| `fastmcp 3.0.2` | Has `py.typed` marker (confirmed in `.venv`) | None — mypy reads types natively | HIGH |
| `ollama 0.6.1` | Has `py.typed` marker (confirmed in `.venv`) | None — mypy reads types natively | HIGH |
| `typer 0.21.1` | Ships `py.typed` (well-typed library) | None | HIGH |
| `pydantic 2.x` | Ships `py.typed` (fully typed) | None | HIGH |

**Summary:** Only `python-frontmatter` requires any stub action. No stub packages need to be
installed. Do NOT install `types-*` stubs for libraries that already ship `py.typed` — doing so
causes conflicts and duplicate type information.

### pyproject.toml Config Changes Required

#### 1. mypy: Per-module override for python-frontmatter

The `frontmatter` package does not ship type annotations. The one import in
`extractors/markdown.py` triggers `[import-untyped]`. Use a mypy override rather than an inline
`# type: ignore` to keep the source file clean:

```toml
[[tool.mypy.overrides]]
module = ["frontmatter"]
ignore_missing_imports = true
```

This is the correct approach per mypy docs. The `module` key names the imported package
(`frontmatter`), not the file containing the import.

#### 2. mypy: Override for llm/ module (legacy untyped code)

The `llm/` module has legacy code with missing type annotations (no-untyped-def, no-untyped-call).
These require code fixes, not config. However, if any functions in `llm/chunked_processor.py` or
`llm/rewriter.py` are internal helpers that cannot be cleanly typed (e.g., nested functions), use
inline `# type: ignore[no-untyped-def]` on those specific lines rather than a blanket module
override. Blanket overrides for entire modules hide real errors in new code.

#### 3. ruff: E501 handling for llm/ module

Ruff does NOT support per-file line-length settings. The only per-file mechanism is
`per-file-ignores` in `[tool.ruff.lint]`, which suppresses specific rule codes for file
patterns. The correct approach for `llm/` files with long prompt strings is:

```toml
[tool.ruff.lint.per-file-ignores]
"src/corpus_analyzer/llm/*.py" = ["E501"]
```

This ignores E501 (line-too-long) only for `llm/` files. All other rules still apply.

**Why not set `line-length = 120` in ruff?** There is no per-file line-length config in ruff
(verified with official docs). A global increase to 120 would mask real style drift in new code.
Suppressing E501 in `llm/` is more surgical and better reflects that these are legacy prompt
strings, not production code style.

**E501 violations in non-llm/ files (78 violations):** These are in `cli.py` (45),
`classifiers/document_type.py` (11), `generators/advanced_rewriter.py` (9), and others. These
must be manually fixed by breaking long lines — they cannot be ignored without degrading style
enforcement on the active codebase.

#### 4. ruff: Exclude .windsurf/ and other non-project directories

If ruff is currently checking files outside `src/` (e.g., `.windsurf/skills/`), add an exclude:

```toml
[tool.ruff]
exclude = [".windsurf", ".planning", "*.windsurf"]
```

The current `ruff check .` run surfaces violations in `.windsurf/skills/api-design-principles/`.
These are not project code. Excluding them keeps CI output clean and focused on `src/`.

### mypy Error Categories and Required Fixes

All 42 mypy errors require code changes (not config). Here is the breakdown with fix strategy:

| Error Type | Count | Files | Fix |
|-----------|-------|-------|-----|
| `[union-attr]` — `db["table"]` returns `Table \| View` | 7 | `core/database.py` | Cast: `cast(Table, self.db["tablename"])` after importing `from sqlite_utils.db import Table` and `from typing import cast` |
| `[no-any-return]` — returning `Any` from typed function | 6 | `core/database.py`, `llm/ollama_client.py` | Add explicit return type cast or assert |
| `[type-arg]` — missing type params on `dict`/`list` | 6 | `core/database.py`, `extractors/markdown.py`, `analyzers/shape.py` | Change `dict` → `dict[str, Any]`, `list` → `list[str]` etc. |
| `[no-untyped-def]` — missing annotations | 5 | `llm/chunked_processor.py`, `utils/ui.py`, `llm/rewriter.py` | Add full type annotations to affected functions |
| `[no-untyped-call]` — calling untyped function | 8 | `llm/chunked_processor.py` | Fix by annotating `finalize_atom`, `chain_lines`, `get_chunk_text` |
| `[import-untyped]` — frontmatter has no stubs | 1 | `extractors/markdown.py` | mypy override (see config above) |
| `[abstract]` — instantiating abstract class | 1 | `extractors/__init__.py` | Fix BaseExtractor instantiation |
| `[operator]` — bad tuple + str operation | 1 | `llm/rewriter.py` | Fix type mismatch |
| `[attr-defined]` — OllamaClient has no .db | 1 | `llm/rewriter.py` | Fix incorrect attribute access |
| `[var-annotated]` — untyped variable | 1 | `ingest/chunker.py` | Add type annotation |
| `[arg-type]` — float() arg type mismatch | 2 | `core/database.py` | Cast or guard with `assert` |

**The `[union-attr]` errors in database.py** are all caused by `sqlite_utils.Database.__getitem__`
returning `Table | View`. The fix is to cast the result to `Table`:

```python
from sqlite_utils.db import Table
from typing import cast

cast(Table, self.db["documents"]).update(doc_id, data, alter=True)
```

Or use a helper property that casts once per table.

---

## Installation Changes

No new packages required. All needed type stubs either ship with existing packages or are handled
via config. The only `pyproject.toml` dev dependency change is ensuring mypy version is current:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.4.0",
    "mypy>=1.9.0",
]
```

Current installed versions (mypy 1.19.1, ruff 0.14.13) are both current as of 2026-02-24. No
version bumps needed.

**Do NOT install:**
- `types-python-frontmatter` — does not exist on PyPI (verified)
- `types-sqlite-utils` — does not exist on PyPI; sqlite-utils ships `py.typed` natively
- Any other `types-*` stub package for this project's dependencies — all other deps are typed

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| mypy `[[overrides]]` for frontmatter | Inline `# type: ignore[import-untyped]` | Use inline if the import is in only one place and the override feels heavy; either is valid |
| `per-file-ignores = ["E501"]` for llm/ | Rewrite all long prompt strings to wrap at 100 chars | Acceptable if you want strict consistency; but multi-line f-strings for LLM prompts are harder to read when force-wrapped |
| Cast to `Table` explicitly | Per-method `# type: ignore[union-attr]` on each db call | Use inline ignores only if cast is impractical (e.g., dynamic table name); cast is cleaner |
| Exclude `.windsurf/` via ruff config | Run `ruff check src/` instead of `ruff check .` | Running on `src/` only works but IDE tooling usually runs on `.`; config exclude is more robust |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `mypy --ignore-missing-imports` globally | Hides real import errors across entire codebase; defeats purpose of strict mode | `[[tool.mypy.overrides]]` per-module |
| `disallow_untyped_defs = false` in mypy overrides for llm/ | Hides future type errors in new code added to llm/ | Fix the specific untyped functions individually |
| Global `ignore = ["E501"]` in ruff | Turns off line-length checking for all new code | `per-file-ignores` scoped to `llm/` only |
| `types-*` stub packages for typed libraries | Conflicts with `py.typed` in the library itself; mypy warns about duplicate stubs | Nothing — let mypy use the library's own types |
| Upgrading mypy or ruff versions as part of this milestone | Risk of new errors being introduced; current versions already surface all 42 errors | Pin current versions; upgrade is a separate milestone |

---

## Pyproject.toml Target State

Complete `[tool.mypy]` and `[tool.ruff]` sections after v1.3:

```toml
[tool.ruff]
line-length = 100
target-version = "py312"
src = ["src", "tests"]
exclude = [".windsurf", ".planning"]

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]

[tool.ruff.lint.per-file-ignores]
"src/corpus_analyzer/llm/*.py" = ["E501"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_ignores = true

[[tool.mypy.overrides]]
module = ["frontmatter"]
ignore_missing_imports = true
```

---

## Version Compatibility

| Package | Installed | Status | Notes |
|---------|-----------|--------|-------|
| mypy | 1.19.1 | Current | No upgrade needed |
| ruff | 0.14.13 | Current | No upgrade needed |
| sqlite-utils | 3.39 | Current, has `py.typed` | `[union-attr]` errors are code issues, not missing stubs |
| python-frontmatter | 1.1.0 | Current, no stubs | Handle via mypy override |
| lancedb | 0.29.2 | Has `_lancedb.pyi` | No stub action needed |
| fastmcp | 3.0.2 | Has `py.typed` | No stub action needed |
| ollama | 0.6.1 | Has `py.typed` | No stub action needed |

---

## Sources

- Live tool output: `uv run mypy src/` — 42 errors in 9 files (HIGH, direct measurement)
- Live tool output: `uv run ruff check src/` — 396 errors, 270 auto-fixable (HIGH, direct measurement)
- Installed package inspection: `.venv/lib/python3.12/site-packages/` — confirmed `py.typed` presence in sqlite_utils, fastmcp, ollama; confirmed `_lancedb.pyi` in lancedb; confirmed absence in frontmatter (HIGH)
- PyPI check: `types-python-frontmatter` — package does not exist (HIGH, verified via uv pip install --dry-run)
- PyPI check: `types-sqlite-utils` — package does not exist; sqlite-utils ships own types (HIGH, verified)
- https://github.com/simonw/sqlite-utils/issues/331 — py.typed added to sqlite-utils; resolves mypy import errors (HIGH)
- https://docs.astral.sh/ruff/settings/#lint_per-file-ignores — per-file-ignores syntax; confirmed no per-file line-length setting exists (HIGH)
- https://mypy.readthedocs.io/en/stable/config_file.html — `[[tool.mypy.overrides]]` TOML syntax confirmed (HIGH)
- sqlite_utils source: `.venv/.../sqlite_utils/db.py:425` — `__getitem__` returns `Union["Table", "View"]`; confirms cast strategy (HIGH)

---

*Stack research for: Corpus v1.3 — zero-error mypy + ruff linting baseline*
*Researched: 2026-02-24*

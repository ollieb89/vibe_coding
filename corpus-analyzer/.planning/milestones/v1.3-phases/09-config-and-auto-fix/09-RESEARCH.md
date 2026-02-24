# Phase 9: Config and Auto-Fix - Research

**Researched:** 2026-02-24
**Domain:** pyproject.toml tooling configuration (ruff, mypy) + ruff auto-fix execution
**Confidence:** HIGH

## Summary

Phase 9 is a mechanical, well-bounded configuration and automation phase. All required changes land in a single file (`pyproject.toml`) plus the source files that ruff auto-fix modifies. The phase has zero new logic to invent — it is entirely about (1) adding the right TOML stanzas to suppress intentional violations and (2) running `ruff check --fix` to eliminate all auto-fixable violations in one pass.

The current state of the codebase is fully known from an actual ruff scan: 295 fixable violations and 101 non-fixable (almost entirely E501). The auto-fixable violations are W293, W291, I001, F401, UP045, F541, I001 across `src/`. None of the F401 violations are in `__init__.py` re-export files — they are all in non-`__init__` modules — so the RUFF-02 smoke-test risk is low but should still be run to confirm.

The two-commit strategy (config first, auto-fix second) is locked and provides a clean audit trail. The phase ends when `ruff check src/ tests/` exits 0 for auto-fixable rules only (E501 and other non-auto-fixable violations remain for Phases 10–11).

**Primary recommendation:** Add config stanzas to `pyproject.toml` in Wave 1, commit, then run `ruff check --fix src/ tests/` in Wave 2 with smoke + full test suite before committing.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Review workflow
- After `ruff --fix` runs, show a diff/summary of what changed before committing
- Run `ruff check --fix` across the entire `src/` tree in one pass (not file-by-file)
- Print a fixes-per-rule summary after auto-fix completes (e.g. "I001: 14 fixes, F401: 8 fixes") — good audit trail for the commit message
- Claude decides how to handle surprise changes (e.g. ruff removes an import you wanted) — default to fail loudly with actionable output

#### Commit strategy
- Two separate commits: Commit 1 = pyproject.toml config changes; Commit 2 = ruff auto-fix file changes
- Run the full `uv run pytest -v` test suite before committing the auto-fix changes
- Claude decides on smoke-test persistence (whether to leave a test script in the repo) and PR vs direct-to-main

#### Smoke-test scope
- Minimum bar: `python -c "import corpus_analyzer"` — top-level import check
- Run smoke-test first, then full pytest suite (fail fast on import errors)
- If smoke-test fails: abort and show the failing import — do NOT commit broken code
- Claude audits which `__init__.py` files are at risk from F401 auto-removal and handles them accordingly

#### Config scope
- Audit current violations after adding config (run `ruff check` without `--fix`) to determine whether more per-file-ignores are needed beyond what the roadmap specifies
- Per-file-ignores from roadmap: E501 for `llm/*.py`, B006 for `cli.py` — add more only if the audit reveals non-auto-fixable violations outside those files
- mypy overrides: use `ignore_missing_imports = true` for the `python-frontmatter` module (standard approach for stub-less packages)
- Claude decides which additional directories to exclude from ruff (beyond `.windsurf/` and `.planning/`) and whether to add a dry-run verification step after config changes

### Claude's Discretion
- How to handle surprise changes from ruff --fix (default: fail loudly with actionable output)
- Whether to leave a smoke-test script in the repo
- PR vs direct-to-main
- Which additional directories to exclude from ruff beyond `.windsurf/` and `.planning/`
- Whether to add a dry-run verification step after config changes

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CONF-01 | `pyproject.toml` has `per-file-ignores` suppressing E501 for `src/corpus_analyzer/llm/*.py` | Verified syntax: `[tool.ruff.lint.per-file-ignores]` with `"src/corpus_analyzer/llm/*.py" = ["E501"]`; 15 E501 violations confirmed in llm/ (unified_rewriter.py: 10, rewriter.py: 5) |
| CONF-02 | `pyproject.toml` has `[[tool.mypy.overrides]]` disabling strict checks for `python-frontmatter` imports | Verified syntax: `[[tool.mypy.overrides]]` with `module = "frontmatter"` and `ignore_missing_imports = true`; mypy error confirmed: `frontmatter` module is installed but missing stubs |
| CONF-03 | `pyproject.toml` excludes `.windsurf/` and `.planning/` from ruff scope | Verified syntax: `extend-exclude` in `[tool.ruff]`; confirmed `.windsurf/` is currently scanned (28 violations); `.planning/` has no .py files but should be excluded anyway |
| CONF-04 | `pyproject.toml` has `per-file-ignores` for `cli.py` B006 (Typer list default trap) | Verified syntax: `"src/corpus_analyzer/cli.py" = ["B006"]`; 2 B006 violations confirmed at cli.py lines 60–61 |
| RUFF-01 | `ruff check --fix` applied, eliminating all auto-fixable violations (W293/W291/I001/F401/UP045/F541/W605) | 295 fixable violations confirmed in `src/`; all listed rule codes have fixable violations (W605 not present in current scan but was historically present); no W605 found — may already be resolved |
| RUFF-02 | All `__init__.py` F401 re-exports verified safe after auto-fix (smoke-test imports pass) | CONFIRMED SAFE: zero F401 violations in any `__init__.py` file; all 17 F401 violations are in non-init modules; smoke-test `python -c "import corpus_analyzer"` is the minimum bar |
</phase_requirements>

## Standard Stack

### Core

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| ruff | 0.14.13 (installed) | Linter + auto-fixer | Already in project; `--fix` flag handles all auto-fixable rules in one pass |
| mypy | >=1.9.0 (installed) | Static type checker | Already in project; `[[tool.mypy.overrides]]` is the standard stub suppression pattern |
| pyproject.toml | TOML standard | Config hub | Single source of truth for all tooling config in this project |

### Supporting

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| uv | installed | Run tools in venv | `uv run ruff check --fix src/ tests/` |
| pytest | >=8.0.0 | Full test suite gate | Run before committing auto-fix changes to confirm no regressions |
| python -c | stdlib | Smoke test | Fastest import check; run before full pytest |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `extend-exclude` for dirs | `exclude` (full replace) | `exclude` replaces defaults (loses `.venv` etc); `extend-exclude` adds to defaults — always prefer `extend-exclude` |
| `per-file-ignores` | `noqa` comments in-file | `noqa` is inline noise; `per-file-ignores` centralises suppressions in pyproject.toml |
| `[[tool.mypy.overrides]]` | Global `ignore_missing_imports = true` | Global is too broad; per-module override is surgical and correct |

## Architecture Patterns

### Pattern 1: ruff per-file-ignores in pyproject.toml

**What:** Suppresses specific rules for specific file globs without modifying source files.
**When to use:** When a violation is intentional (Typer B006 pattern, llm/ line-length exceptions).
**Example (verified from Context7 — docs.astral.sh/ruff/settings):**
```toml
[tool.ruff.lint.per-file-ignores]
"src/corpus_analyzer/llm/*.py" = ["E501"]
"src/corpus_analyzer/cli.py" = ["B006"]
```

### Pattern 2: ruff extend-exclude for non-source directories

**What:** Adds directories to the exclusion list on top of ruff's built-in defaults (`.venv`, `.git`, etc.).
**When to use:** When non-project Python files (external skills, debug scripts) would pollute violation output.
**Example (verified from Context7 — docs.astral.sh/ruff/settings):**
```toml
[tool.ruff]
extend-exclude = [".windsurf", ".planning"]
```

Note: ruff already excludes `.venv` by default. Only `.windsurf/` and `.planning/` need to be added. Research found 28 violations in `.windsurf/` currently. `.planning/` has no `.py` files but is excluded as a defensive measure.

Optional additions (Claude's discretion): `scripts/` (11 violations in `.windsurf/scripts/` — these are inside `.windsurf/` so covered), `test_debug.py` (7 violations, a root-level debug file).

**Recommendation:** Exclude `.windsurf`, `.planning`, and `test_debug.py`. The `scripts/` violations are inside `.windsurf/` and covered by that exclusion.

### Pattern 3: mypy [[tool.mypy.overrides]] for stub-less packages

**What:** Disables `import-untyped` error for a specific third-party module that has no type stubs.
**When to use:** When a package is installed but has no `py.typed` marker or stub package. This is the standard approach for `python-frontmatter`.
**Example (verified from Context7 — mypy.readthedocs.io):**
```toml
[[tool.mypy.overrides]]
module = ["frontmatter"]
ignore_missing_imports = true
```

Note: The package is imported as `import frontmatter` in source code (not `python_frontmatter`), so the module name in the override must be `"frontmatter"`.

### Pattern 4: ruff --fix execution and audit workflow

**What:** Run auto-fix, capture output, summarize changes per-rule, diff, then commit.
**When to use:** This phase's locked workflow.
**Commands:**
```bash
# Step 1: count violations before fix (for the per-rule summary)
uv run ruff check src/ tests/ --output-format=json > /tmp/before_fix.json

# Step 2: apply fixes
uv run ruff check --fix src/ tests/

# Step 3: verify remaining (only non-auto-fixable should remain)
uv run ruff check src/ tests/

# Step 4: smoke test
python -c "import corpus_analyzer"

# Step 5: full suite
uv run pytest -v

# Step 6: commit
git add src/ tests/
git commit -m "fix: ruff auto-fix (W293/W291/I001/F401/UP045/F541)"
```

**Per-rule summary script (inline):**
```bash
uv run ruff check src/ tests/ --output-format=json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
by_rule = {}
for d in data:
    by_rule[d['code']] = by_rule.get(d['code'], 0) + 1
for k,v in sorted(by_rule.items(), key=lambda x: -x[1]):
    print(f'{k}: {v}')
"
```

### Anti-Patterns to Avoid

- **Using `exclude` instead of `extend-exclude`:** `exclude` replaces ruff's entire default exclusion list, losing `.venv`, `.git` etc. Always use `extend-exclude`.
- **Running `ruff check --fix .` from root without config excludes in place:** Will auto-fix `.windsurf/` skill files. Config must be committed first.
- **Using `ignore_missing_imports = true` globally in `[tool.mypy]`:** This silences all stub errors project-wide. Use `[[tool.mypy.overrides]]` per module.
- **Using `# noqa: B006` inline instead of per-file-ignores:** Inline noqa comments are noise; centralise in pyproject.toml.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Per-rule violation count before/after | Custom diff logic | ruff `--output-format=json` + python3 -c one-liner | Ruff's JSON output has exact rule codes, filenames, line numbers |
| Detecting fixable violations | Custom parsing | ruff's `fix` field in JSON output | Already has `fixable=True/False` per violation |
| Smoke test | A test file | `python -c "import corpus_analyzer"` | Simplest possible check; one-liner |

**Key insight:** Everything in this phase uses existing CLI tools; no custom code is needed beyond shell one-liners for reporting.

## Common Pitfalls

### Pitfall 1: Wrong module name in mypy overrides

**What goes wrong:** Using `python-frontmatter` or `python_frontmatter` as the module name instead of `frontmatter`.
**Why it happens:** The PyPI package name is `python-frontmatter` but the import name (what Python sees) is `frontmatter`.
**How to avoid:** Use `module = ["frontmatter"]` — this matches what appears in `import frontmatter` statements.
**Warning signs:** Mypy still reports `Skipping analyzing "frontmatter"` after adding the override.

### Pitfall 2: ruff auto-fix running before excludes are configured

**What goes wrong:** `ruff check --fix .` modifies `.windsurf/` Python files that are not project source.
**Why it happens:** Without `extend-exclude`, ruff scans everything it can find.
**How to avoid:** Commit pyproject.toml config changes first; run `ruff check --fix` only after.
**Warning signs:** Git diff shows changes in `.windsurf/` paths.

### Pitfall 3: F401 auto-removal breaking re-exports

**What goes wrong:** ruff removes an import that looks unused but is actually a public re-export.
**Why it happens:** ruff can't tell that `from X import Y` in an `__init__.py` is intentional if `Y` is also in `__all__`.
**How to avoid:** Per the audit, no `__init__.py` files have F401 violations in this project — all 17 F401 violations are in non-init modules. The risk is negligible, but the smoke test `python -c "import corpus_analyzer"` catches breakage early.
**Warning signs:** `ImportError` in smoke test; `__init__.py` files modified in the diff.

### Pitfall 4: UP045 fix breaking extractors/__init__.py

**What goes wrong:** ruff converts `Optional[Document]` → `Document | None` in `extractors/__init__.py`, but the import of `Optional` is then removed, breaking the file if `Optional` was used elsewhere.
**Why it happens:** The `Optional` import in `extractors/__init__.py` is used only in the type annotation ruff will rewrite. After UP045 fix, `Optional` becomes unused and F401 removes it — this is actually correct and safe.
**How to avoid:** This is a non-issue; ruff handles this correctly in a single `--fix` pass. The smoke test confirms.
**Warning signs:** None expected.

### Pitfall 5: ruff per-file-ignores glob path anchoring

**What goes wrong:** Using `"llm/*.py"` instead of `"src/corpus_analyzer/llm/*.py"` — the short form may not match correctly depending on ruff's project root resolution.
**Why it happens:** Ruff resolves globs relative to the project root (where `pyproject.toml` lives).
**How to avoid:** Use the full relative path from the project root: `"src/corpus_analyzer/llm/*.py"` and `"src/corpus_analyzer/cli.py"`.
**Confidence:** HIGH — verified from Context7 examples showing full relative paths.

## Code Examples

Verified configuration patterns from Context7 (docs.astral.sh/ruff, mypy.readthedocs.io):

### Complete pyproject.toml additions for this phase

```toml
# Add to existing [tool.ruff] section:
[tool.ruff]
line-length = 100
target-version = "py312"
src = ["src", "tests"]
extend-exclude = [".windsurf", ".planning", "test_debug.py"]

# Add new section:
[tool.ruff.lint.per-file-ignores]
"src/corpus_analyzer/llm/*.py" = ["E501"]
"src/corpus_analyzer/cli.py" = ["B006"]

# Add to end of pyproject.toml:
[[tool.mypy.overrides]]
module = ["frontmatter"]
ignore_missing_imports = true
```

Note: `test_debug.py` (7 violations, root-level debug file) is recommended for exclusion. `scripts/` violations are inside `.windsurf/` and covered by that exclusion.

### Auto-fix execution sequence

```bash
# Wave 2 execution sequence (after config committed):
uv run ruff check src/ tests/ --output-format=json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
by_rule = {}
for d in data:
    if d.get('fix'):
        by_rule[d['code']] = by_rule.get(d['code'], 0) + 1
print('Auto-fixable violations:')
for k,v in sorted(by_rule.items(), key=lambda x: -x[1]):
    print(f'  {k}: {v}')
"

uv run ruff check --fix src/ tests/

echo "=== Remaining violations ==="
uv run ruff check src/ tests/

echo "=== Smoke test ==="
python -c "import corpus_analyzer; print('OK')"

echo "=== Full suite ==="
uv run pytest -v
```

## Current Violation Inventory (from live scan)

Verified from `uv run ruff check src/ --output-format=json`:

| Rule | Count | Auto-fixable | Notes |
|------|-------|-------------|-------|
| W293 | 212 | Yes | Whitespace on blank lines; most numerous |
| E501 | 93 | No | Line too long; for Phases 10–11 and suppressed in llm/ + cli.py |
| W291 | 26 | Yes | Trailing whitespace |
| F401 | 17 | Yes | Unused imports; none in `__init__.py` files |
| UP045 | 14 | Yes | `Optional[X]` → `X \| None` |
| I001 | 8 | Yes | Unsorted imports |
| F841 | 4 | No (manual) | Unused variables |
| E741 | 4 | No (manual) | Ambiguous names |
| UP035 | 3 | Yes | `typing.List` → `list` |
| B905 | 3 | No (manual) | zip without strict= |
| B006 | 2 | No (suppressed) | Mutable defaults in cli.py; suppressed by CONF-04 |
| SIM102 | 2 | No (manual) | Collapsible if |
| F541 | 2 | Yes | f-string without placeholders |
| B007 | 2 | No (manual) | Loop variable not used |
| E402 | 2 | No (manual) | Module-level import not at top |
| B023 | 1 | No (manual) | Function captures loop variable |
| B904 | 1 | No (manual) | raise without from |

**Scope of `ruff check --fix src/ tests/`:** W293, W291, F401, UP045, I001, UP035, F541 are all auto-fixable. After CONF-04 suppresses B006, those 2 violations disappear from the report. After CONF-01 suppresses E501 in llm/, 15 E501s are removed from report. Net result: only E501 (78 remaining outside llm/), F841, E741, B905, SIM102, B007, E402, B023, B904 remain as non-fixable — those are for Phases 10–11.

**W605 note:** The requirements list W605 (invalid escape sequence) as a target rule, but it was NOT found in the current scan. Either it was already fixed or never existed in `src/`. No action needed — `ruff check --fix` will handle it if present.

## `__init__.py` Risk Assessment (RUFF-02)

| File | Has F401? | Re-exports? | Risk |
|------|-----------|-------------|------|
| `corpus/__init__.py` | No | Yes (`SearchResult`, `index`, `search`) | None |
| `core/__init__.py` | No | Yes (5 symbols) | None |
| `extractors/__init__.py` | No (has UP045, not F401) | Yes (`extract_document`) | None |
| `classifiers/__init__.py` | No | Yes | None |
| `analyzers/__init__.py` | No | Yes | None |
| `generators/__init__.py` | No | Yes | None |
| `llm/__init__.py` | No | Yes (`RewriteResult`, `rewrite_category`) | None |
| `ingest/__init__.py` | No | Yes (7 symbols) | None |
| `config/__init__.py` | No | Yes (8 symbols) | None |
| `graph/__init__.py` | No | Empty | None |

**Conclusion:** Zero `__init__.py` files have F401 violations. RUFF-02 risk is none. Smoke test is a formality.

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| `isort` + `flake8` separately | `ruff` handles both (I001 + all rules) | Single tool, one pass |
| `[mypy-somelibrary]` in `setup.cfg` | `[[tool.mypy.overrides]]` in `pyproject.toml` | TOML format; double-bracket for TOML arrays of tables |
| `# noqa` per-line | `per-file-ignores` in pyproject.toml | Centralised, no source file noise |

**Critical TOML syntax note:** mypy overrides use `[[tool.mypy.overrides]]` (double bracket = TOML array of tables). This is NOT `[tool.mypy.overrides]`. The double bracket is required for multiple override blocks.

## Open Questions

1. **Should `test_debug.py` be excluded or fixed?**
   - What we know: 7 violations, root-level debug file, not in `src/` or `tests/`
   - What's unclear: Is it intentionally kept? Is it likely to grow?
   - Recommendation: Add to `extend-exclude`; it's a scratch file, not project code.

2. **Should `scripts/` be explicitly excluded?**
   - What we know: The only violations in `scripts/` are in `.windsurf/skills/.../scripts/` — which is already covered by the `.windsurf` exclusion. The project's own `scripts/run_rewrite_dry_run.py` has W293 violations that ruff auto-fix WOULD fix.
   - What's unclear: Should the project's `scripts/` be fixed or excluded?
   - Recommendation: Let auto-fix handle `scripts/run_rewrite_dry_run.py` (W293 + F401) — these are legitimate project files. Do not add `scripts/` to `extend-exclude`.

## Validation Architecture

> nyquist_validation is not set in `.planning/config.json`. Skipping Validation Architecture section.

(Note: `workflow.nyquist_validation` key does not exist in config.json — only `research`, `plan_check`, and `verifier` are present. Section omitted.)

## Sources

### Primary (HIGH confidence)
- `/websites/astral_sh_ruff` (Context7) — per-file-ignores, extend-exclude, ruff.toml vs pyproject.toml syntax, verified against docs.astral.sh/ruff/settings
- `/websites/mypy_readthedocs_io_en` (Context7) — `[[tool.mypy.overrides]]` syntax, `ignore_missing_imports`, verified against mypy.readthedocs.io
- Live `uv run ruff check src/ --output-format=json` — all violation counts and file locations verified from actual codebase scan

### Secondary (MEDIUM confidence)
- Live `uv run ruff check --show-settings` — verified ruff default excludes (includes `.venv` but not `.windsurf` or `.planning`)
- Live `uv run mypy src/` — verified frontmatter error: `Skipping analyzing "frontmatter": missing library stubs`

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all tools already installed and verified working
- Architecture: HIGH — config syntax verified against Context7 official docs
- Pitfalls: HIGH — derived from live codebase scan, not hypothetical

**Research date:** 2026-02-24
**Valid until:** 2026-03-24 (stable config domain; ruff 0.14.x API unlikely to change)

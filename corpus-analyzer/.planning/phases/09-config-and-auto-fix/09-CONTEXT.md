# Phase 9: Config and Auto-Fix - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Surgical `pyproject.toml` additions (per-file-ignores, mypy overrides, ruff excludes) followed by running `ruff check --fix` to automatically eliminate all auto-fixable violations. Phase ends when the config is committed, auto-fix changes are committed, and the smoke-test + full test suite pass. Manual violation fixes and mypy error resolution are out of scope (Phases 10–11).

</domain>

<decisions>
## Implementation Decisions

### Review workflow
- After `ruff --fix` runs, show a diff/summary of what changed before committing
- Run `ruff check --fix` across the entire `src/` tree in one pass (not file-by-file)
- Print a fixes-per-rule summary after auto-fix completes (e.g. "I001: 14 fixes, F401: 8 fixes") — good audit trail for the commit message
- Claude decides how to handle surprise changes (e.g. ruff removes an import you wanted) — default to fail loudly with actionable output

### Commit strategy
- Two separate commits: Commit 1 = pyproject.toml config changes; Commit 2 = ruff auto-fix file changes
- Run the full `uv run pytest -v` test suite before committing the auto-fix changes
- Claude decides on smoke-test persistence (whether to leave a test script in the repo) and PR vs direct-to-main

### Smoke-test scope
- Minimum bar: `python -c "import corpus_analyzer"` — top-level import check
- Run smoke-test first, then full pytest suite (fail fast on import errors)
- If smoke-test fails: abort and show the failing import — do NOT commit broken code
- Claude audits which `__init__.py` files are at risk from F401 auto-removal and handles them accordingly

### Config scope
- Audit current violations after adding config (run `ruff check` without `--fix`) to determine whether more per-file-ignores are needed beyond what the roadmap specifies
- Per-file-ignores from roadmap: E501 for `llm/*.py`, B006 for `cli.py` — add more only if the audit reveals non-auto-fixable violations outside those files
- mypy overrides: use `ignore_missing_imports = true` for the `python-frontmatter` module (standard approach for stub-less packages)
- Claude decides which additional directories to exclude from ruff (beyond `.windsurf/` and `.planning/`) and whether to add a dry-run verification step after config changes

</decisions>

<specifics>
## Specific Ideas

- No specific references or examples from discussion
- Phase is mechanical and well-bounded — decisions are process-oriented, not aesthetic

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 09-config-and-auto-fix*
*Context gathered: 2026-02-24*

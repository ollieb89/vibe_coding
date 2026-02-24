# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-24)

**Core value:** Surface relevant agent files instantly — query your entire local agent library and get ranked results in under a second
**Current focus:** Phase 9 — Config and Auto-Fix (v1.3)

## Current Position

Phase: 11 of 12 (Manual Ruff CLI + Mypy)
Plan: 1 of 5 in current phase
Status: In progress
Last activity: 2026-02-24 — Phase 11 Plan 1 complete (RUFF-07: all 47 ruff violations in cli.py fixed, project-wide zero violations, 281 tests passing)

Progress: [██░░░░░░░░] 20% (v1.3)

## Performance Metrics

**v1.0 Summary:**
- Total plans completed: 15
- Phases: 4
- Timeline: 41 days (2026-01-13 → 2026-02-23)

**v1.1 Summary:**
- Total plans completed: 4
- Phases: 2
- Timeline: 1 day (2026-02-23)

**v1.2 Summary:**
- Total plans completed: 1
- Phases: 2 (7–8)
- Timeline: 1 day (2026-02-24)

**v1.3 Summary (in progress):**
- Total plans completed: 5
- Phases: 4 (9–12)

## Accumulated Context

### Decisions

Recent decisions affecting current work:

- [09-01]: extend-exclude (not exclude) preserves ruff defaults; full relative paths required in per-file-ignores; frontmatter override uses import name not PyPI name
- [09-02]: Two-pass ruff fix strategy required (--fix then --unsafe-fixes); ruff skips F401 in __init__.py even with unsafe-fixes — manual removal needed
- [v1.3 planning]: Fix ordering is strict — ruff auto-fix before manual, pyproject.toml config before E501 wrapping, leaf modules before hub, ruff clean before mypy
- [v1.3 planning]: B006 Typer list defaults must use `# noqa: B006`, not naive `None` replacement (breaks `--help`)
- [v1.3 planning]: sqlite-utils union-attr — use `cast(Table, ...)` per call site, not `# type: ignore`
- [11-02]: cast(Table, self.db[...]) at every sqlite-utils Table call site (delete_where, insert, update) resolves union-attr; int(row[0]) fixes no-any-return on SQL row IDs
- [11-02]: params: list[str] (not list[Any]) — query parameter values in get_documents/get_gold_standard_documents are always strings
- [11-02]: Local variable guard _cc/_qs for float(row.get(...)) — avoids double .get() and satisfies mypy arg-type narrowing
- [v1.3 planning]: `llm/rewriter.py` line 406 operator error is a genuine bug — investigate control flow before fixing
- [10-01]: Use `lnk` (not `link2`) for database.py deserialization rename to avoid shadowing imported Link class
- [10-01]: Use `level_val` for chunked_processor.py rename to match semantics of force_level/current_level source variables
- [10-01]: ruff --fix (safe only) sufficient for scripts/ F401/W293; no --unsafe-fixes needed
- [Phase 10-02]: Wrap for-loop CLASSIFICATION_RULES unpacking by parenthesising the iterable, not the variables
- [Phase 10-02]: shape.py f-string: extract depth_rows local variable to avoid unreadable inline generator expression
- [10-03]: database.py ternary: use explicit 'is not None' for nullable float/bool fields — 'or' shortcut mishandles 0.0
- [10-03]: Long test docstrings: wrap as multi-line PEP 257 (summary + blank + detail), not noqa suppression
- [11-01]: B023 progress_callback fix: default-arg capture (_task_id=task_id) keeps external Callable[[int], None] signature unchanged
- [11-01]: B904 search_command: use `from None` (deliberate suppression), not `from e` (chaining)
- [11-01]: Two help strings shortened to fit 100 chars (construct filter, auto_category); all other E501 fixed by wrapping
- [11-03]: chain_lines local res variable typed as list[str] to satisfy mypy inference for extend() calls
- [11-04]: response.message.content (typed Optional[str]) not dict subscript (Any) for ollama ChatResponse access
- [11-04]: OllamaClient is a plain class — self.db: CorpusDatabase | None = None with TYPE_CHECKING guard resolves both no-any-return and unblocks plan 05

### Pending Todos

None.

### Blockers/Concerns

- [Phase 11]: rewriter.py line 406 operator error requires reading branch logic in context — cannot resolve from error output alone

## Session Continuity

Last session: 2026-02-24
Stopped at: Completed 11-01-PLAN.md (RUFF-07: all 47 ruff violations in cli.py fixed — project-wide zero ruff violations, 281 tests passing)
Resume file: None

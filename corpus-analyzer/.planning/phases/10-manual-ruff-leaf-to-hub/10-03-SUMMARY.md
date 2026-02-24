---
phase: 10-manual-ruff-leaf-to-hub
plan: "03"
subsystem: linting
tags: [ruff, e501, line-wrapping, database, generators, tests]

requires:
  - phase: 10-02
    provides: E501-clean leaf modules (classifiers, analyzers, ingest, utils, search)

provides:
  - E501-clean core/database.py (4 violations resolved)
  - E501-clean generators/advanced_rewriter.py (7 violations resolved)
  - E501-clean generators/templates.py (1 violation resolved)
  - E501-clean test suite (8 violations across 7 files resolved)
  - Zero E501 violations in all files outside cli.py

affects:
  - 11-cli-ruff-and-mypy
  - Any future modifications to database.py, generators, or test files

tech-stack:
  added: []
  patterns:
    - "Use explicit 'is not None' ternary (not 'or' shortcut) when wrapping nullable float/bool fields"
    - "Wrap long strings in parentheses with implicit concatenation — no backslash continuation"
    - "Wrap long docstrings as multi-line with blank line separator"

key-files:
  created: []
  modified:
    - src/corpus_analyzer/core/database.py
    - src/corpus_analyzer/generators/advanced_rewriter.py
    - src/corpus_analyzer/generators/templates.py
    - tests/cli/test_search_status.py
    - tests/config/test_schema.py
    - tests/ingest/test_indexer.py
    - tests/ingest/test_scanner.py
    - tests/search/test_engine.py
    - tests/test_analyzers/test_quality_logic.py
    - tests/test_core/test_db_migration.py

key-decisions:
  - "database.py ternary: use explicit 'is not None' guard for category_confidence/quality_score/is_gold_standard — 'or' shortcut changes semantics when value is 0.0 or 0"
  - "Long docstrings in tests: wrap as multi-line PEP 257 format (summary + blank + detail) rather than noqa suppression"

patterns-established:
  - "Nullable float fields: float(x if x is not None else 0.0) — safe for 0.0 values"
  - "Multi-line system_prompt strings: implicit concatenation in parentheses, split at sentence boundaries"

requirements-completed:
  - RUFF-03

duration: 4min
completed: "2026-02-24"
---

# Phase 10 Plan 03: Hub Module and Test E501 Wrapping Summary

**All E501 violations cleared from core/database.py, generators/, and 7 test files — zero non-cli.py ruff violations remain; 281 tests passing.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-24T04:33:52Z
- **Completed:** 2026-02-24T04:40:51Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments

- Wrapped 4 E501 violations in database.py (cols list comprehension + 3 nullable ternaries using explicit `is not None`)
- Wrapped 7 E501 violations in advanced_rewriter.py (FileNotFoundError, gold_docs ternary, system_prompt strings)
- Wrapped 1 E501 violation in templates.py (_generate_template_md multi-arg call)
- Wrapped 8 E501 violations across 7 test files using appropriate patterns (runner.invoke wrap, assertion list wrap, docstring splits)
- Phase 10 goal achieved: zero ruff violations outside cli.py

## Task Commits

Each task was committed atomically:

1. **Task 1: Wrap E501 violations in core/database.py and generators/** - `4a49d70` (fix)
2. **Task 2: Wrap E501 violations in all test files and run final ruff gate** - `12e62b8` (fix)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `src/corpus_analyzer/core/database.py` - L207 cols comprehension wrap; L318/320/321 nullable ternaries with explicit `is not None`
- `src/corpus_analyzer/generators/advanced_rewriter.py` - L43 FileNotFoundError wrap; L78 gold_docs ternary; L87/93-94/97/107-108/142 system_prompt string splits
- `src/corpus_analyzer/generators/templates.py` - L67 _generate_template_md call wrapped across lines
- `tests/cli/test_search_status.py` - L126 runner.invoke wrapped
- `tests/config/test_schema.py` - L75 extensions list assertion wrapped
- `tests/ingest/test_indexer.py` - L365 patch() classify_file args wrapped
- `tests/ingest/test_scanner.py` - L168 walk_source call wrapped
- `tests/search/test_engine.py` - L288/321 long docstrings split to multi-line PEP 257 format
- `tests/test_analyzers/test_quality_logic.py` - L35 CodeBlock in list wrapped
- `tests/test_core/test_db_migration.py` - L38 db.db.execute SQL string and args wrapped

## Decisions Made

- Used explicit `if x is not None else 0.0` form (not `or` shortcut) for database.py nullable float/bool fields — the `or` shortcut would incorrectly treat `0.0` as falsy, changing behavior when a document has `quality_score=0.0`.
- Wrapped long test docstrings as multi-line PEP 257 (summary line + blank + detail) rather than using `# noqa: E501` — keeps code clean without suppression comments.

## Deviations from Plan

None — plan executed exactly as written. The plan's `files_modified` list matched all files needing changes; no additional violations were found in src/ (prior phases had already resolved them).

## Final Ruff Gate Output

```
# Command: uv run ruff check . --output-format=concise 2>&1 | grep -v "cli.py" | grep -E "E501|E741|E402|B017"
# Output: (empty — zero violations)
```

Only cli.py violations remain (Phase 11 scope: E501 x45, B023 x1, B904 x1).

## Test Result

```
============================= 281 passed in 3.46s ==============================
```

## RUFF Requirements Status

- RUFF-03: E501 in core/database.py, generators/ — SATISFIED
- RUFF-04: E501 in test files — SATISFIED (via this plan + prior plans)
- RUFF-05: E741 semantic violations — SATISFIED (Phase 10 Plan 01)
- RUFF-06: E402/B017 violations — SATISFIED (Phase 10 Plan 01)

## Issues Encountered

None.

## Next Phase Readiness

- Phase 10 complete: zero ruff violations outside cli.py across all src/ and tests/ files
- Phase 11 scope: cli.py E501 (45 violations), B023 (1 violation), B904 (1 violation) + mypy strict
- No blockers from this phase

---
*Phase: 10-manual-ruff-leaf-to-hub*
*Completed: 2026-02-24*

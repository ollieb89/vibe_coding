# Phase 8: Cleanup - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Remove the dead `use_llm_classification` parameter from `index_source()` — its signature and every call site across the codebase. This is a pure internal cleanup; no new capabilities are being added.

</domain>

<decisions>
## Implementation Decisions

### Dead code scope
- Remove conditional branches gated on `use_llm_classification` entirely — don't make them unconditional
- Claude's discretion: if removal of a dead branch changes observable behaviour, assess the impact before deleting
- Remove ALL traces: env vars, config fields, settings, and documentation references that existed only to support this parameter
- No CHANGELOG entry needed — git commit message is sufficient

### Removal strategy
- One atomic commit: function signature + all call sites updated together
- Internal-only tool — no deprecation warning needed, remove directly
- Run the full test suite BEFORE making any changes to establish a green baseline, then again AFTER to confirm no regressions
- Update docs (README, CLAUDE.md, any other docs) if they reference `use_llm_classification`

### Test handling
- Update test call sites by removing the `use_llm_classification` argument — keep all behaviour assertions intact
- Do NOT add new tests to verify absence of the parameter; passing tests are sufficient
- Delete any test that is skipped or marked `xfail` because it was testing dead LLM classification behaviour
- Acceptance bar: all existing tests pass with zero failures

### Verification approach
- Search the entire repo with ripgrep for `use_llm_classification` before starting to find every occurrence
- After removal, run: `uv run pytest -v` + `uv run mypy src/` + `uv run ruff check .`
- Claude's discretion: if dynamic references (e.g., `getattr`, string interpolation) are found, handle them on a case-by-case basis
- Explicit completion signal: a final `grep -r use_llm_classification .` returns zero results

### Claude's Discretion
- Whether to flag dynamic/unusual references for human review or handle them inline
- How to handle any edge cases where removing a dead branch would change observable behaviour

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. This is a straightforward dead-code removal.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 08-cleanup*
*Context gathered: 2026-02-24*

# Phase 16: Integration Hardening - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the TypeScript chunker production-safe under two adversarial conditions — oversized files and missing tree-sitter install — then validate that the entire codebase passes the zero-violation quality gate. No new chunking features. No new CLI surface. Hardening only.

</domain>

<decisions>
## Implementation Decisions

### Size guard behavior
- Silent fallback — no user-visible output when a 50K+ char file is skipped
- 50,000 character threshold is a hardcoded constant (not configurable via corpus.toml)
- Fallback chunks are indistinguishable from normal line-based chunks (no special metadata)
- Guard lives inside `chunk_typescript()` — checks `len(content)` before invoking tree-sitter; returns `chunk_lines()` output directly

### ImportError fallback
- Silent fallback — no warning, no per-file output; `corpus index` completes normally
- ImportError caught inside `chunk_typescript()` (same module as the size guard, same pattern)
- Explicit separate branch from the `has_error` partial-tree fallback — both call `chunk_lines()` independently, not via a shared helper

### Test approach order
- TDD RED-first, matching phase 15 discipline: 16-01 writes failing tests, 16-02 implements
- Both size guard and ImportError tests go in one RED plan (same module, related features)
- Plan structure: 16-01 RED, 16-02 GREEN, 16-03 validation gate = 3 plans total
- ImportError test mocks using `unittest.mock.patch` to raise `ImportError` at the import site inside `chunk_typescript()`

### Quality gate scope
- Minimum test count assertion: ≥318 tests (phase 15 GREEN target; catches accidental deletion)
- Integration smoke test: run `corpus index` against a real TS fixture to confirm end-to-end dispatch wiring
- Validation plan also updates PROJECT.md: move v1.5 requirements from Active to Validated

### Claude's Discretion
- Exact mock patch target path (depends on how `chunk_typescript()` imports tree-sitter at runtime)
- TS fixture to use for smoke test (project's own TS files or a minimal temp file)

</decisions>

<specifics>
## Specific Ideas

- Size guard and ImportError should behave identically from the user's perspective: silent, correct output, no surprises
- The `has_error` branch (phase 15) and the new `ImportError` branch are distinct code paths in `chunk_typescript()` — do not merge them
- The validation plan is the last plan in v1.5; PROJECT.md update happens here, not at `complete-milestone`

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 16-integration-hardening*
*Context gathered: 2026-02-24*

# Phase 15: Core AST Chunker - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement `chunk_typescript()` — an AST-aware chunker for `.ts`, `.tsx`, `.js`, and `.jsx` files using tree-sitter that extracts named top-level constructs as separate chunks with correct 1-indexed line boundaries. Parallel in design to the existing `chunk_python()`. Wired into `chunk_file()` dispatch. This phase does NOT include size guards, ImportError fallback hardening (Phase 16), or ruff/mypy cleanup.

</domain>

<decisions>
## Implementation Decisions

### Lexical declarations
- All top-level `const` and `let` declarations become chunks — simple rule, no filtering by RHS type
- `var` declarations are excluded (legacy, not idiomatic TypeScript)
- Multi-declarator statements (`const a = 1, b = 2`) produce one chunk for the whole statement
- Chunk name: Claude's discretion (planner to match Python chunker convention)

### JSDoc inclusion
- Chunk text includes the immediately preceding `/** ... */` block comment if one exists directly above the construct (no intervening code or blank lines between comment and declaration)
- When multiple comments precede a construct (e.g. licence header + JSDoc), include only the `/** */` block comment that directly precedes the node
- Single-line `//` comments are NOT included in chunk text — JSDoc convention only
- If no JSDoc is present, chunk starts at the first line of the declaration keyword

### Name extraction
- `export default function() {}` → name: `"default"`
- `export default class {}` → name: `"default"` (same rule for all anonymous defaults)
- `export const fn = () => {}` → name: `fn` (the identifier, no type annotation)
- Generic type params in interface/type alias names: Claude's discretion (match Python chunker style)

### Module layout
- `chunk_typescript()` is a single public function handling all four extensions (`.ts`, `.tsx`, `.js`, `.jsx`); grammar selection is internal based on file suffix
- File location: Claude's discretion — planner to assess `ingest/chunker.py` size and decide whether to co-locate or split into `ingest/ts_chunker.py`
- `ImportError` (tree-sitter not installed) is caught in `chunk_file()` dispatch and falls back to `chunk_lines()` — the chunker itself does not need to handle missing deps

### Claude's Discretion
- Chunk name for lexical declarations (first declarator vs other convention — match Python chunker)
- Whether generic type params appear in interface/type alias chunk names
- File location for `chunk_typescript()` (same file as `chunk_python()` or new module)

</decisions>

<specifics>
## Specific Ideas

No specific references or "I want it like X" moments — implementation should mirror the existing `chunk_python()` function in style, field names, and return format. The Python chunker in `ingest/chunker.py` is the reference implementation.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 15-core-ast-chunker*
*Context gathered: 2026-02-24*

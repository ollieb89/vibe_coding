# Phase 21: TypeScript Method Sub-Chunking - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

When `corpus index` processes a `.ts`, `.tsx`, `.js`, or `.jsx` file, any class definitions are split into a header chunk plus one chunk per method. Top-level functions, interfaces, enums, and type aliases are unaffected. The monolithic class chunk is replaced entirely. This phase covers TypeScript/JavaScript only — Python was Phase 20.

</domain>

<decisions>
## Implementation Decisions

### Header chunk presence
- Every class gets a header chunk named `ClassName`, always — even if the class has no field declarations
- Header chunk contains: class signature (including `extends`/`implements` clauses, class-level JSDoc) + all field declarations (`public_field_definition`, property signatures, etc.) before the first `method_definition` node
- Boundary rule: header ends immediately before the first `method_definition` node in the class body
- If there are no field declarations, the header chunk is just the class opening (`class Foo {` line and any decorators/JSDoc); still always emitted
- Both `class_declaration` and `abstract_class_declaration` are sub-chunked identically

### Abstract methods
- Abstract method declarations (`abstract foo(): void`) are chunked as individual per-method chunks, just like concrete methods
- The chunk text for an abstract method is the signature line(s) — that IS the complete content
- Consistent rule: all `method_definition` nodes get chunked, regardless of whether they have a body
- Abstract classes with ONLY abstract method declarations produce: header chunk + one chunk per abstract method declaration

### Claude's Discretion
- Getter/setter naming strategy (e.g. `ClassName.foo` for both, or `ClassName.foo` vs `ClassName.foo_setter`, etc.)
- Private method naming (`#foo` → `ClassName.#foo` or `ClassName.foo`)
- Exact header chunk end boundary when no field declarations exist (just the `{` line vs the class signature line)
- Internal implementation approach for walking `class_body` children in tree-sitter
- Orphan chunk cleanup strategy (likely delete-then-replace, mirroring Phase 20)

</decisions>

<specifics>
## Specific Ideas

- Mirror Phase 20 (Python) as closely as possible — the pattern is already established in `chunker.py:_chunk_class()`; the TypeScript version should feel like a direct analogue
- No special treatment needed for the constructor beyond naming it `ClassName.constructor` (per roadmap success criterion)

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 21-typescript-method-sub-chunking*
*Context gathered: 2026-02-24*

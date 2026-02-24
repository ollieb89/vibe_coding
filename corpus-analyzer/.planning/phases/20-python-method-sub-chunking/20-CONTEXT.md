# Phase 20: Python Method Sub-Chunking - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

When `corpus index` processes a `.py` file, any class definitions are split into a header chunk plus one chunk per method. Top-level functions are unaffected. The monolithic class chunk is replaced entirely. This phase covers Python only — TypeScript is Phase 21.

</domain>

<decisions>
## Implementation Decisions

### Header chunk scope
- The header chunk contains: class decorators + class signature + class-level attributes (defined outside `__init__`) + class docstring + `__init__` `self.x = value` assignments
- Cut-off rule: stop at the **first non-assignment statement** in `__init__` (i.e. a method call, conditional, loop, `super()` call, etc.)
- Class-level attributes defined outside `__init__` (ClassVar, TYPE_CHECKING blocks, plain `KEY = "value"`) are included in the header chunk
- Class decorators (`@dataclass`, `@attrs.define`, `@pydantic` etc.) are included at the top of the header chunk
- Header chunk **always** exists, even when `__init__` has no self-assignments or is absent

### Edge-case methods
- `__init__`, `__str__`, `__repr__` and ALL other dunder/special methods follow the same `ClassName.method_name` naming (no special treatment)
- `@property`, `@classmethod`, `@staticmethod`, and `async def` methods are all chunked as regular methods — naming is `ClassName.method_name` regardless of decorator
- Nested classes inside a class are **not** recursively sub-chunked; they are treated as opaque content within the enclosing class header chunk (or the method chunk if nested inside a method)

### Multi-class files
- **All** classes in a `.py` file get sub-chunked — no "main class" heuristic
- Top-level functions sitting alongside classes are left entirely unchanged (no new chunking behaviour)
- Classes with no methods (enum-style, config classes, exception stubs) produce a **header-only** chunk with no method chunks — this is valid and expected

### Orphan chunk cleanup
- Re-indexing a file uses **delete-then-replace**: all existing chunks for that file are deleted from LanceDB before the new method chunks are written
- No migration command or flag — files indexed before this phase keep their old monolithic chunks until they are re-indexed (hash change or `--force`)
- Sub-chunking is **silent**: no extra log output when classes are split
- Hash-unchanged files are still skipped by the normal change detection — no forced upgrade of already-indexed files

### Claude's Discretion
- How to detect "first non-assignment statement" in `__init__` (AST node type matching)
- Exact chunk naming for `@property` getter vs setter (e.g. `ClassName.foo` vs `ClassName.foo.setter`)
- Chunk text format and boundaries (whether to include the `def` line of the next method as a terminator)
- Internal implementation of delete-then-replace in the LanceDB indexer

</decisions>

<specifics>
## Specific Ideas

- The header chunk should read like a "class contract" — decorators + attributes + `__init__` setup give an LLM caller everything needed to understand the class shape without reading all methods
- Nested classes: treat them like a blob of text rather than trying to recurse — they're rare enough that the complexity isn't worth it in this phase

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 20-python-method-sub-chunking*
*Context gathered: 2026-02-24*

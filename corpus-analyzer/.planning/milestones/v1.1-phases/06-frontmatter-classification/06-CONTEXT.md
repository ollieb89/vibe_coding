# Phase 6: Frontmatter Classification - Context

**Gathered:** 2026-02-23
**Status:** Ready for planning

<domain>
## Phase Boundary

The construct classifier gains the ability to read YAML frontmatter from markdown files as a high-confidence classification signal. Files with explicit frontmatter declarations (`type:`, `component_type:`) get classified at ≥0.95 confidence. Files with matching `tags` values get classified at ~0.70 confidence. Files without recognized frontmatter fall through to the existing rule-based classifier unchanged — zero regression.

</domain>

<decisions>
## Implementation Decisions

### Recognized frontmatter keys
- Hardcode exactly two keys: `type` and `component_type` (no configurable list for now)
- Key matching is case-insensitive (`Type:`, `TYPE:`, `type:` all recognized)
- Value matching is case-insensitive (`Skill`, `SKILL`, `skill` all map to `skill`)
- Support both snake_case (`component_type`) and camelCase (`componentType`) as equivalent

### Unknown / unmapped type values
- Unrecognized values are silently ignored — fall through to rule-based classifier
- No logging, no warnings — clean UX
- Exact match only: `skills` (plural) does NOT match `skill`. No plural normalization.
- Non-string values (e.g. `type: 42`) are coerced to string, attempt match, fall through if unrecognized

### Conflict resolution
- Frontmatter always wins over rule-based signals when a recognized type is found
- Fixed confidence of **0.95** for any frontmatter type match (no boosting from signal agreement)
- When both `type:` and `component_type:` are present and disagree, **`type:` takes priority**
- Store `classification_source` field to distinguish `frontmatter` vs `rule_based` classifications

### Tags field semantics
- Tags contribute at **~0.70 confidence** — lower than direct `type:` declarations
- Tag matching uses substring: tag `skill-template` matches construct `skill` (case-insensitive)
- Tags are **ignored** when `type:` already resolved a classification for this file
- Tags alone CAN produce a standalone classification (no `type:` required) at 0.70 confidence

### Claude's Discretion
- Exact YAML frontmatter parsing library choice (e.g. `python-frontmatter` or manual regex)
- How to handle malformed/invalid YAML frontmatter (parse error → treat as no frontmatter)
- Exact substring matching implementation for tags
- How `classification_source` integrates into the existing database schema

</decisions>

<specifics>
## Specific Ideas

- `classification_source` field is intended for debugging and future use — not required in search output
- Confidence of 0.95 (not 1.0) intentionally leaves room for potential future override mechanisms
- The 0.70 confidence for tags is meant to rank-order: explicit type declaration > tag hint > rule-based

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-frontmatter-classification*
*Context gathered: 2026-02-23*

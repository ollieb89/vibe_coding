# Phase 18: CLI Chunk Display - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Switch `corpus search` output to grep/compiler-error format: `path/to/file.md:42-67 [skill] score:0.021` on the primary line, followed by an indented chunk text preview on a second line. Format must be parseable by VSCode and IntelliJ problem matchers. All existing flags (`--limit`, `--min-score`, `--sort-by`, `--source`, `--type`, `--construct`) continue to work. JSON output and MCP changes are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Text preview line
- Indent the preview line with 4 spaces (visually separates snippet from path line, consistent with ripgrep style)
- If `chunk_text` is empty (legacy unmigrrated rows), skip the preview line entirely — no blank second line
- If `chunk_text` contains newlines, take only up to the first newline, then truncate to 200 chars
- Ellipsis rule: show up to 200 chars of content, then append `...` if truncated (200 chars + `...`, not 200 total)

### Score & field formatting
- Always 3 decimal places: `score:0.021`, `score:0.100` — consistent column width for scanning
- For legacy rows where `start_line=0` and `end_line=0`: omit the line range entirely — show `path/to/file.md [skill] score:0.021` not `:0-0`
- When construct type is empty/unknown: omit the `[brackets]` entirely — don't show `[]` or a fallback label

### Visual grouping
- Blank line between results — each path+preview pair is visually isolated
- No summary header — dive straight into results; no count line before or after
- No special grouping for consecutive results from the same file — each chunk is an independent entry (Phase 27 will handle same-file flooding)
- Use Rich for colour: path bold/white, construct type dimmed, score in cyan; Rich auto-suppresses when piped (TTY detection)

### Empty & edge states
- No results: `No results for "query"` — simple, matches existing FILT-03 hint style
- FILT-03 hint (`No results above X.xxx. Run without --min-score to see available scores.`) unchanged
- Empty database treated as zero results — same `No results for "query"` message, no special-casing

### Formatter module
- Implement as a standalone module (e.g. `ingest/formatters.py` or similar) — testable in isolation, keeps `cli.py` lean

### Claude's Discretion
- Exact Rich colour/style choices within the guidelines (bold path, dimmed construct, cyan score)
- Exact module path for the formatter (within project conventions)
- Indentation amount (2 or 4 spaces — 4 preferred based on user's selection)

</decisions>

<specifics>
## Specific Ideas

- Visual reference chosen: ripgrep-style indented preview with blank-line separation between results
- IDE-clickable format: `file.md:42-67` matches VSCode and IntelliJ problem matcher patterns (`file:line`)

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 18-cli-chunk-display*
*Context gathered: 2026-02-24*

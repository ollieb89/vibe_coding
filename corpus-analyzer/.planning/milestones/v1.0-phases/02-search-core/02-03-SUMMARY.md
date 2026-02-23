# Phase 02 Search Core — 02-03 Summary

## Import paths

- `from corpus_analyzer.search.classifier import classify_file, classify_by_rules`
- `from corpus_analyzer.search.formatter import extract_snippet`

## Rule signals implemented (priority order)

`classify_by_rules(file_path, text)` checks signals in this order:

1. File extension `.py`, `.ts`, `.js` -> `code`
2. Any path part equals `skills` or contains `skill` -> `skill`
3. Any path part equals `prompts` or contains `prompt` -> `prompt`
4. Any path part equals `workflows` or contains `workflow` -> `workflow`
5. `.md`/`.yaml`/`.yml` with frontmatter `name + description + tools` -> `agent_config`
6. `.md`/`.yaml`/`.yml` with frontmatter `name + description` -> `skill`
7. Filename stem contains `workflow` -> `workflow`
8. Filename stem contains `prompt` -> `prompt`
9. Otherwise -> `None` (LLM fallback path)

`classify_file(...)` behavior:

- Uses rule result when available.
- Uses LLM fallback only when rules return `None` and `use_llm=True`.
- Parses first token matching one of:
  `skill | prompt | workflow | agent_config | code | documentation`.
- Returns `documentation` when:
  - `use_llm=False`, or
  - LLM call fails, or
  - LLM output has no valid label.

## Snippet behavior implemented

`extract_snippet(text, query, max_lines=3)`:

- Returns full text when `len(lines) <= max_lines`.
- For non-empty query, finds highest scoring line by query-term hits and returns up to `max_lines` around it.
- For empty query, returns first `max_lines` lines.
- Truncates snippets longer than 200 chars at word boundary and appends `…`.

## Behavior deviations from plan

- No functional deviations.
- Additional hardening: tests also verify fallback to `documentation` when LLM call raises an exception.

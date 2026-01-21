# Corpus Analyzer - LLM Rewriter Logic & Patterns

## Project Context
- **Name**: `corpus-analyzer`
- **Stack**: Python 3.12, Typer, Pydantic, SQLite, Ollama (Mistral).
- **Execution**: Managed via `uv`.

## Key Implementations (Jan 2026)

### 1. Robust LLM Output Cleaning
Implemented `clean_model_output` in `rewriter.py` to handle common LLM (Mistral) artifacts:
- **Markdown Wrappers**: Strips ` ```markdown ` or ` ```md ` fences that wrap the entire document.
- **Echoed Instructions**: Uses `INSTRUCTION_ECHO_PATTERN` (`re.compile(r'## Instructions.*$', re.DOTALL | re.IGNORECASE)`) to strip prompt instructions that the LLM occasionally appends to the output.
- **Trailing Markers**: Cleans up stray ` ``` ` at the end of content.
- **Order of Operations**: Strips wrappers first, then applies regex cleaning to the extracted content.

### 2. Document Chunking
- **Limit**: `MAX_CONTENT_LENGTH = 16000` characters.
- **Logic**: Documents exceeding the limit are split using `split_on_headings` (in `chunked_processor.py`) to maintain semantic integrity.
- **Merging**: Sections are merged with heading deduplication via `merge_chunks`.

### 3. YAML Frontmatter Enforcement
- **Programmatic Fallback**: `ensure_frontmatter` function injects a basic YAML block if the LLM fails to provide one.
- **Validation**: `QualityReport` tracks `has_frontmatter` and penalizes missing blocks in the quality score.

### 4. Quality Assessment
- **Metrics**: Tracks placeholders, truncation (indicators like `...`), frontmatter, heading hierarchy skips (e.g., H1 to H3), and unclosed code blocks.
- **Scoring**: 100-point scale with letter grades (A-F).
- **CLI Feedback**: Warnings and low-quality scores are reported to the user during the `rewrite` command.

### 5. Pre-processing
- **Placeholders**: `$VAR_NAME` patterns are replaced with `[user-defined]` before sending to LLM to prevent confusion or leakage of literal symbols.

## Troubleshooting Notes
- If "Unclosed code block" warnings persist, check `clean_model_output` logic to ensure it's not returning early before stripping trailing markers or echoing instructions.
- Truncation warnings (`...`) can be false positives if present in valid code comments.

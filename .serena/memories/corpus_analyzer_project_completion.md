# Project: Document Corpus Analyzer

## Overview
A CLI tool designed to extract, categorize, analyze, and template documentation from Markdown and Python files, integrating with local LLMs (Ollama) for rewriting and consolidation.

## Technical Stack
- **Language**: Python 3.12
- **CLI**: `typer` with `rich` for formatting
- **Database**: SQLite via `sqlite-utils` for schema management and upserts
- **Models**: `pydantic` for strict data validation
- **Extraction**: `python-frontmatter` (MD) and `ast` (Python)
- **Classification**: Rule-based (regex/keywords) for category and domain detection
- **LLM**: `ollama-python` client for local inference

## Core Components
- `src/corpus_analyzer/core/database.py`: Manages idempotent document/chunk storage.
- `src/corpus_analyzer/extractors/`: Factory-based extraction for `.md` and `.py` files.
- `src/corpus_analyzer/analyzers/shape.py`: Generates structural reports (heading frequency, code density).
- `src/corpus_analyzer/generators/templates.py`: Auto-generates Markdown templates and YAML lint rules based on analysis.
- `src/corpus_analyzer/llm/rewriter.py`: Orchestrates document consolidation via Ollama.
- `src/corpus_analyzer/analyzers/quality.py`: Evaluates document quality and identifies "Gold Standards".

## Key Learnings & Debugging
1. **Frontmatter Robustness**: Some `.md` files contain malformed YAML. The extractor now includes a try-except fallback to prevent scanner crashes.
2. **Database Idempotency**: `sqlite-utils` `upsert` or manual path checks are essential when re-scanning directories to avoid `UNIQUE` constraint violations.
3. **Persistence**: Using `db.execute()` for updates in SQLite without explicit commits can lead to silent failures. Table-based `.update()` methods are preferred for reliability.
4. **Environment Awareness**: The LLM integration checks for Ollama availability early and provides actionable CLI feedback.
5. **Schema Evolution**: Using `alter=True` in `sqlite-utils` allows purely code-driven schema updates without manual migrations.
6. **Defensive Coding**: When adding new fields (like `quality_score`), always handle existing legacy rows with default values (`.get(key, default)`) to prevent `ValidationErrors`.

## Status
Core implementation complete. Optimization features added Jan 2026.
- Extraction: ✓
- Classification: ✓
- Shape Analysis: ✓
- Template Generation: ✓
- LLM Consolidation: ✓
- Optimization & Quality Analysis: ✓

## Optimization Features
- **Smart Categorization**: Detects Next.js, React, and UV stacks.
- **Quality Analysis**: Scores documents and identifies "Gold Standards".
- **Pattern Injection**: Rewriter uses gold standards as few-shot examples ( `--optimized` flag).

## Next Steps
1. **Prompt Tuning**: Refine LLM prompts to reduce "Low quality score" output warnings.
2. **Library Detection**: Expand `DomainTag` to cover more libraries (Pandas, FastAPI, etc.).
3. **Human Evaluation**: Add a CLI command to manually review/override gold standard selections.
4. **Performance**: Parallelize the rewriting process (currently sequential) for large corpora.
5. **Smart Splitting**: Improve the "Chunking" logic to split semantically rather than just by character count/headings.

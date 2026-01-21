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

## Key Learnings & Debugging
1. **Frontmatter Robustness**: Some `.md` files contain malformed YAML. The extractor now includes a try-except fallback to prevent scanner crashes.
2. **Database Idempotency**: `sqlite-utils` `upsert` or manual path checks are essential when re-scanning directories to avoid `UNIQUE` constraint violations.
3. **Persistence**: Using `db.execute()` for updates in SQLite without explicit commits can lead to silent failures. Table-based `.update()` methods are preferred for reliability.
4. **Environment Awareness**: The LLM integration checks for Ollama availability early and provides actionable CLI feedback if the service or model is missing.

## Status
All 7 implementation phases are complete and verified on a corpus of 400+ documents.
- Extraction: ✓
- Classification: ✓
- Shape Analysis: ✓
- Template Generation: ✓
- LLM Consolidation: ✓

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest -v

# Run a single test file
uv run pytest tests/test_extractors/test_markdown.py -v

# Run a single test by name
uv run pytest tests/test_classifiers/test_document_type.py::test_function_name -v

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run mypy src/

# Test with coverage
uv run pytest --cov=corpus_analyzer --cov-report=html
```

## Architecture

The tool follows a pipeline: **scan → extract → classify → analyze → rewrite**. Each stage persists results to a SQLite database (`corpus.sqlite` by default).

### Core Data Flow

1. `core/scanner.py` — walks a directory and yields file paths
2. `extractors/` — converts files to `Document` models (markdown, python extractors; `.txt`/`.rst` use the markdown extractor)
3. `core/database.py` — `CorpusDatabase` wraps `sqlite-utils`; JSON-serializes list fields (headings, links, code_blocks, symbols, domain_tags, imports)
4. `classifiers/` — rule-based classifiers update `category`/`category_confidence` and `domain_tags` on stored documents
5. `analyzers/` — reads documents to produce shape reports (structure patterns) and quality scores; marks `is_gold_standard`
6. `generators/` — produces markdown templates and lint rules from shape analysis
7. `llm/` — Ollama-backed rewriting; `unified_rewriter.py` is the current entrypoint (supersedes `rewriter.py`)

### Key Models (`core/models.py`)

- `Document` — central model; holds extracted metadata plus classification fields (`category`, `domain_tags`, `quality_score`, `is_gold_standard`)
- `DocumentCategory` — enum: `persona`, `howto`, `runbook`, `architecture`, `reference`, `tutorial`, `adr`, `spec`, `unknown`
- `DomainTag` — enum: `backend`, `frontend`, `graphql`, `testing`, `temporal`, `python`, `typescript`, `nextjs`, `react`, `uv`, `database`, `devops`, `security`, `ai`, `data_science`, `fastapi`, `other`
- `Chunk` — sub-document sections, stored in a separate `chunks` table

### CLI Structure (`cli.py`)

Built with Typer. Top-level commands: `extract`, `classify`, `analyze`, `analyze-quality`, `rewrite`, `review`. Sub-groups: `db` (initialize, inspect), `samples` (extract), `templates` (generate, freeze).

### LLM Integration

Requires a locally running Ollama instance (`CORPUS_OLLAMA_HOST`, default `http://localhost:11434`). `UnifiedRewriter` in `llm/unified_rewriter.py` handles template-based + LLM-fallback rewriting. `chunked_processor.py` handles documents too large for a single LLM call.

### Configuration

Settings via `pydantic-settings` with `CORPUS_` prefix (or `.env` file):
- `CORPUS_DATABASE_PATH` (default: `corpus.sqlite`)
- `CORPUS_OLLAMA_HOST` (default: `http://localhost:11434`)
- `CORPUS_OLLAMA_MODEL` (default: `mistral`)
- `CORPUS_REPORTS_DIR`, `CORPUS_TEMPLATES_DIR`

## Code Style

- All Python functions and classes must have type annotations (including return types) and PEP 257 docstrings
- Tests use pytest only (no `unittest`); test files go in `tests/` with `__init__.py` per subdirectory
- Line length: 100; linter: `ruff` with `E, F, I, N, W, UP, B, C4, SIM` rules; `mypy --strict`
- Dependency management: `uv`

# Technology Stack

**Analysis Date:** 2026-02-23

## Languages

**Primary:**
- Python 3.12 - All application code

**Markup/Config:**
- Markdown - Documentation and frontmatter support
- TOML - Project configuration and dependencies
- SQL - SQLite schema and queries

## Runtime

**Environment:**
- Python 3.12 (specified in `.python-version`)

**Package Manager:**
- uv (fast Python package manager) - Primary installer
- Lockfile: `uv.lock` (present and up-to-date)

## Frameworks

**Core Framework:**
- Typer 0.12.0+ - CLI framework with click underneath

**Data Validation:**
- Pydantic 2.6.0+ - Data models and validation (`src/corpus_analyzer/core/models.py`)
- Pydantic Settings 2.1.0+ - Environment configuration management (`src/corpus_analyzer/config.py`)

**LLM Integration:**
- Ollama 0.6.1 - Local LLM interaction (`src/corpus_analyzer/llm/ollama_client.py`)
  - Depends on: httpx (HTTP client for Ollama API)

**Text Processing:**
- python-frontmatter 1.1.0+ - YAML frontmatter parsing from Markdown files

**Database:**
- sqlite-utils 3.36+ - SQL helper library for SQLite operations (`src/corpus_analyzer/core/database.py`)

**UI/Output:**
- Rich 13.7.0+ - Terminal formatting and progress indicators (`src/corpus_analyzer/utils/ui.py`)

## Key Dependencies

**Critical:**
- ollama 0.6.1 - LLM text generation (core feature for document rewriting and analysis)
  - HTTP client: httpx (included as transitive dependency)
- pydantic 2.6.0+ - Foundational validation for Document, Chunk, and configuration models
- sqlite-utils 3.36+ - Database abstraction layer (replaces raw sqlite3)

**Infrastructure:**
- typer[all] 0.12.0+ - Rich CLI with auto-generated help and subcommand support
- python-frontmatter 1.1.0+ - Markdown metadata extraction
- rich 13.7.0+ - Terminal UI and pretty-printing

**Testing (dev only):**
- pytest 8.0.0+ - Test framework
- pytest-cov 4.1.0+ - Coverage reporting
- mypy 1.9.0+ - Static type checking
- ruff 0.4.0+ - Linting and formatting

## Configuration

**Environment:**
- Configuration system: Pydantic Settings with env prefix `CORPUS_`
- Env file: `.env` (optional, loaded if present at runtime)
- `.env.example` provided with defaults

**Key Configuration Variables:**
- `CORPUS_DATABASE_PATH` - SQLite database location (default: `corpus.sqlite`)
- `CORPUS_OLLAMA_HOST` - Ollama service URL (default: `http://localhost:11434`)
- `CORPUS_OLLAMA_MODEL` - Default LLM model name (default: `mistral`)
- `CORPUS_CHUNK_SIZE` - Text chunking size (default: `1000`)
- `CORPUS_CHUNK_OVERLAP` - Chunk overlap for processing (default: `100`)
- `CORPUS_REPORTS_DIR` - Output directory for analysis reports (default: `reports`)
- `CORPUS_TEMPLATES_DIR` - Output directory for templates (default: `templates`)

**Build Configuration:**
- `pyproject.toml` - Package metadata, dependencies, build system (hatchling)
- `Makefile` - Development task automation (test, lint, format, typecheck, clean)
- Tool configuration within pyproject.toml:
  - `[tool.ruff]` - Line length 100, Python 3.12 target
  - `[tool.pytest.ini_options]` - Test paths and pythonpath setup
  - `[tool.mypy]` - Strict mode enabled, all warnings on

## Platform Requirements

**Development:**
- Python 3.12+
- uv package manager
- SQLite3 (bundled with Python)

**Production:**
- Python 3.12+ runtime
- SQLite3 database engine (file-based, no server needed)
- Ollama service running at configured host (for LLM features)
- Network access to Ollama API endpoint

**Optional Dependencies:**
- Local Ollama server for LLM-powered features (document rewriting, quality scoring)
- File system access for reading/writing documents and reports

---

*Stack analysis: 2026-02-23*

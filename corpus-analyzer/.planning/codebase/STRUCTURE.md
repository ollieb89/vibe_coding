# Codebase Structure

**Analysis Date:** 2026-02-23

## Directory Layout

```
corpus-analyzer/
├── src/corpus_analyzer/           # Main source code
│   ├── __init__.py                # Package version
│   ├── cli.py                     # CLI entry point (Typer)
│   ├── config.py                  # Settings management
│   ├── core/                      # Core data structures and database
│   │   ├── __init__.py
│   │   ├── models.py              # Pydantic models (Document, Chunk, etc.)
│   │   ├── database.py            # CorpusDatabase SQLite wrapper
│   │   ├── scanner.py             # Directory scanning utility
│   │   └── samples.py             # Sample extraction logic
│   ├── extractors/                # Document extraction strategies
│   │   ├── __init__.py            # Factory dispatch function
│   │   ├── base.py                # BaseExtractor abstract class
│   │   ├── markdown.py            # MarkdownExtractor implementation
│   │   └── python.py              # PythonExtractor implementation
│   ├── classifiers/               # Document classification
│   │   ├── __init__.py
│   │   ├── document_type.py       # Category classification (TF-IDF + rules)
│   │   └── domain_tags.py         # Domain tag detection (pattern matching)
│   ├── analyzers/                 # Document analysis and metrics
│   │   ├── __init__.py
│   │   ├── shape.py               # Structural metrics per category
│   │   └── quality.py             # Quality scoring
│   ├── generators/                # Template and document generation
│   │   ├── __init__.py
│   │   ├── templates.py           # Template generation from analysis
│   │   └── advanced_rewriter.py   # Legacy rewriter (referenced in config)
│   ├── llm/                       # LLM integration
│   │   ├── __init__.py
│   │   ├── ollama_client.py       # Ollama API client wrapper
│   │   ├── unified_rewriter.py    # Main rewriting orchestrator
│   │   ├── quality_scorer.py      # LLM-based quality assessment
│   │   ├── chunked_processor.py   # Document chunking for LLM
│   │   └── rewriter.py            # Legacy rewriter module
│   └── utils/                     # Utility functions
│       └── ui.py                  # Terminal UI helpers
├── tests/                         # Test suite
│   ├── core/                      # Tests for core modules
│   ├── test_classifiers/          # Classifier tests
│   ├── test_analyzers/            # Analyzer tests
│   ├── test_extractors/           # Extractor tests
│   ├── llm/                       # LLM tests
│   └── test_core/                 # Core tests
├── pyproject.toml                 # Python project configuration
├── corpus.sqlite                  # Default database (generated)
├── templates/                     # Generated templates directory
├── reports/                       # Analysis reports directory
├── source_docs/                   # Sample extraction output
├── output/                        # Rewritten documents
└── rewrites/                      # Dry-run rewrite outputs
```

## Directory Purposes

**src/corpus_analyzer/:**
- Purpose: Main package containing all production code
- Contains: Modules for extraction, classification, analysis, generation, LLM integration
- Key files: `cli.py` (entry), `config.py` (settings)

**src/corpus_analyzer/core/:**
- Purpose: Core abstractions and persistence
- Contains: Pydantic models, SQLite database layer, file scanner
- Key files: `models.py` (all data structures), `database.py` (persistence)

**src/corpus_analyzer/extractors/:**
- Purpose: Format-specific document parsing strategies
- Contains: Abstract base class and implementations
- Key files: `base.py` (contract), `markdown.py`, `python.py`
- Factory function in `__init__.py` dispatches by file extension

**src/corpus_analyzer/classifiers/:**
- Purpose: Document categorization and tagging
- Contains: Rule-based and ML-inspired classification
- Key files: `document_type.py` (categorical classification), `domain_tags.py` (cross-cutting tags)

**src/corpus_analyzer/analyzers/:**
- Purpose: Extract metrics and patterns from document collections
- Contains: Shape analysis, quality assessment
- Key files: `shape.py` (structural metrics), `quality.py` (quality scoring)

**src/corpus_analyzer/generators/:**
- Purpose: Generate templates and rewritten documents
- Contains: Template contracts and generation logic
- Key files: `templates.py` (template generation), `advanced_rewriter.py` (legacy)

**src/corpus_analyzer/llm/:**
- Purpose: LLM-powered document processing
- Contains: Ollama client, unified rewriter, quality assessment
- Key files: `unified_rewriter.py` (main orchestration), `ollama_client.py` (API wrapper)

**src/corpus_analyzer/utils/:**
- Purpose: Shared utilities
- Contains: Terminal UI helpers
- Key files: `ui.py` (Rich console formatting)

**tests/:**
- Purpose: Test suite for all modules
- Contains: Unit and integration tests
- Location mirrors src structure: `tests/core/`, `tests/test_classifiers/`, etc.

**templates/:**
- Purpose: Generated document templates
- Generated: Yes (by `templates generate` command)
- Committed: No (gitignore)
- Contains: TEMPLATE_CONTRACTS embedded in Markdown frontmatter

**reports/:**
- Purpose: Analysis reports per category
- Generated: Yes (by `analyze` command)
- Committed: No
- Structure: Subdirectories per category

**output/:**
- Purpose: Rewritten documents from LLM processing
- Generated: Yes (by `rewrite` command)
- Committed: No
- Structure: Organized by category

## Key File Locations

**Entry Points:**
- `src/corpus_analyzer/cli.py`: Main CLI application (Typer)
- `pyproject.toml`: Script entry point defined as `corpus-analyzer = "corpus_analyzer.cli:app"`

**Configuration:**
- `src/corpus_analyzer/config.py`: Settings via Pydantic (database_path, ollama_host, ollama_model, chunk_size, chunk_overlap)
- `.env`: Optional environment variables (not committed)

**Core Logic:**
- `src/corpus_analyzer/core/database.py`: `CorpusDatabase` class (CRUD operations)
- `src/corpus_analyzer/core/models.py`: `Document`, `Chunk`, `DocumentCategory`, `DomainTag` enums
- `src/corpus_analyzer/core/scanner.py`: `scan_directory()` function

**Extraction:**
- `src/corpus_analyzer/extractors/__init__.py`: `extract_document()` factory function
- `src/corpus_analyzer/extractors/base.py`: `BaseExtractor` abstract class
- `src/corpus_analyzer/extractors/markdown.py`: Markdown/text file parsing
- `src/corpus_analyzer/extractors/python.py`: Python file parsing (AST + metadata)

**Classification:**
- `src/corpus_analyzer/classifiers/document_type.py`: Category classification logic
- `src/corpus_analyzer/classifiers/domain_tags.py`: Domain pattern matching dictionary

**Analysis & Generation:**
- `src/corpus_analyzer/analyzers/shape.py`: `ShapeReport` generation
- `src/corpus_analyzer/analyzers/quality.py`: `QualityAnalyzer` class
- `src/corpus_analyzer/generators/templates.py`: Template contracts and generation

**LLM Integration:**
- `src/corpus_analyzer/llm/ollama_client.py`: Ollama API wrapper
- `src/corpus_analyzer/llm/unified_rewriter.py`: Main rewriting orchestration
- `src/corpus_analyzer/llm/quality_scorer.py`: Quality assessment

## Naming Conventions

**Files:**
- `.py` extension for all Python files
- Lowercase with underscores: `document_type.py`, `ollama_client.py`
- Test files: `test_*.py` or `*_test.py` (pytest discovery)
- Packages have `__init__.py` for explicit exports

**Directories:**
- Lowercase with underscores matching module names: `llm/`, `core/`, `extractors/`
- Output directories use descriptive plural: `reports/`, `templates/`, `output/`
- Test directory mirrors source: `tests/core/`, `tests/classifiers/`

**Classes:**
- PascalCase: `CorpusDatabase`, `BaseExtractor`, `MarkdownExtractor`, `Document`
- Enums end with descriptive name: `DocumentCategory`, `DomainTag`
- Result/Report NamedTuples: `ClassificationResult`, `ShapeReport`, `RewriteResult`

**Functions:**
- snake_case: `scan_directory()`, `extract_document()`, `classify_documents()`
- Factory functions are verbs: `extract_document()`, `analyze_category()`
- Utility functions are descriptive: `estimate_tokens()`, `detect_domain_tags()`

**Variables:**
- snake_case: `database_path`, `chunk_size`, `document_id`
- Constants UPPERCASE: `MAX_CONTENT_LENGTH`, `TRUNCATION_INDICATORS`
- Private attributes start with underscore: `_doc_to_dict()`, `_extract_headings()`

## Where to Add New Code

**New Extraction Format (e.g., .json files):**
- Create: `src/corpus_analyzer/extractors/json.py`
- Implement: Class inheriting from `BaseExtractor`
- Register: Update dispatcher in `src/corpus_analyzer/extractors/__init__.py`
- Test: Add `tests/test_extractors/test_json.py`

**New Document Category:**
- Update: `DocumentCategory` enum in `src/corpus_analyzer/core/models.py`
- Add patterns: `DOMAIN_PATTERNS` dict in `src/corpus_analyzer/classifiers/domain_tags.py` if needed
- Add rules: Update `classify_documents()` in `src/corpus_analyzer/classifiers/document_type.py`
- Add template contract: `TEMPLATE_CONTRACTS` dict in `src/corpus_analyzer/generators/templates.py`

**New Domain Tag:**
- Update: `DomainTag` enum in `src/corpus_analyzer/core/models.py`
- Add patterns: New entry in `DOMAIN_PATTERNS` dict in `src/corpus_analyzer/classifiers/domain_tags.py`

**New CLI Command:**
- Add: Function in `src/corpus_analyzer/cli.py`
- Decorate: With `@app.command()` or add to subapp (e.g., `@db_app.command()`)
- Import: Dependencies at top of cli.py or use lazy imports in command function
- Test: Add test in `tests/` directory

**New Analysis Metric:**
- Location: `src/corpus_analyzer/analyzers/`
- Pattern: Create new module or extend existing (e.g., `complexity.py`)
- Integration: Callable from CLI command, produces report

**New LLM Feature:**
- Location: `src/corpus_analyzer/llm/`
- Pattern: Wrap/extend `OllamaClient` or create new processor
- Integration: Used by `UnifiedRewriter` or called from CLI

**Shared Utilities:**
- Location: `src/corpus_analyzer/utils/`
- Pattern: Grouping by concern (ui.py for Rich, add new files as needed)
- Import: From parent modules as `from corpus_analyzer.utils import *`

## Special Directories

**corpus.sqlite:**
- Purpose: SQLite database file
- Generated: Yes (by `db initialize` or first `extract`)
- Committed: No (typically in .gitignore)
- Overwritten: Yes, on re-initialization

**templates/:**
- Purpose: Generated document templates with contracts
- Generated: Yes (by `templates generate`)
- Committed: No
- Format: Markdown files with HTML comment contracts
- Versioning: Frozen templates end with `.v1.md`

**reports/:**
- Purpose: Analysis output (JSON shape reports)
- Generated: Yes (by `analyze`)
- Committed: No
- Structure: Subdirectories per category (e.g., `reports/howto/`, `reports/reference/`)

**output/:**
- Purpose: LLM-rewritten documents
- Generated: Yes (by `rewrite`)
- Committed: No
- Structure: Subdirectories per category (e.g., `output/howto/`, `output/tutorial/`)

**rewrites/dry-run/:**
- Purpose: Dry-run preview of rewrites
- Generated: Yes (for testing)
- Committed: No
- Structure: Mirrors output/ structure for category organization

---

*Structure analysis: 2026-02-23*

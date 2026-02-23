# Architecture

**Analysis Date:** 2026-02-23

## Pattern Overview

**Overall:** Multi-stage document pipeline with layered responsibility separation

**Key Characteristics:**
- Extract → Classify → Analyze → Generate → Rewrite workflow
- Domain-driven design with clear separation of concerns
- SQLite persistence layer for corpus storage
- Plugin-based extractor system for handling multiple file formats
- LLM integration through Ollama for intelligent rewriting

## Layers

**Presentation Layer (CLI):**
- Purpose: User interface for all operations
- Location: `src/corpus_analyzer/cli.py`
- Contains: Typer command definitions, user interaction, progress reporting
- Depends on: All underlying modules via orchestration
- Used by: End users and scripts

**Extraction Layer:**
- Purpose: Convert raw files into normalized Document models
- Location: `src/corpus_analyzer/extractors/` directory
- Contains: `BaseExtractor` abstract class, format-specific extractors (`MarkdownExtractor`, `PythonExtractor`)
- Depends on: Core models and utilities
- Used by: Scanner and extract command

**Persistence Layer:**
- Purpose: SQLite database operations with Pydantic models
- Location: `src/corpus_analyzer/core/database.py`
- Contains: `CorpusDatabase` class with CRUD operations
- Depends on: Core models, sqlite_utils
- Used by: All processing stages

**Core Models:**
- Purpose: Define all data structures
- Location: `src/corpus_analyzer/core/models.py`
- Contains: `Document`, `Chunk`, `DocumentCategory`, `DomainTag`, `CodeBlock`, `Heading`, `Link`, `PythonSymbol`
- Depends on: Pydantic
- Used by: All layers

**Classification Layer:**
- Purpose: Categorize documents by type and domain
- Location: `src/corpus_analyzer/classifiers/` directory
- Contains: `document_type.py` (TF-IDF and semantic classification), `domain_tags.py` (pattern-based tagging)
- Depends on: Core models, database
- Used by: Classify command, rewriter

**Analysis Layer:**
- Purpose: Extract metrics and patterns from document collections
- Location: `src/corpus_analyzer/analyzers/` directory
- Contains: `shape.py` (structural metrics per category), `quality.py` (quality scoring)
- Depends on: Core models, database
- Used by: Analyze and analyze-quality commands

**Generation Layer:**
- Purpose: Create templates and structured output
- Location: `src/corpus_analyzer/generators/` directory
- Contains: `templates.py` (template generation from analysis), `advanced_rewriter.py` (legacy rewriter)
- Depends on: Analyzers, database
- Used by: Templates generation command

**LLM Integration Layer:**
- Purpose: Interface with Ollama for intelligent content processing
- Location: `src/corpus_analyzer/llm/` directory
- Contains: `ollama_client.py` (Ollama API wrapper), `unified_rewriter.py` (main rewriting logic), `quality_scorer.py` (LLM-based quality assessment), `chunked_processor.py` (document chunking)
- Depends on: Core models, database, Ollama
- Used by: Rewrite command

**Support Layer:**
- Purpose: Configuration and utilities
- Location: `src/corpus_analyzer/config.py`, `src/corpus_analyzer/utils/ui.py`
- Contains: Settings management, UI helpers
- Depends on: Pydantic settings
- Used by: All layers

## Data Flow

**Extract Pipeline:**

1. `scan_directory()` (scanner.py) finds files matching extensions
2. `extract_document()` dispatches to format-specific extractor
3. Extractor parses file and returns `Document` model with:
   - Structural metadata (headings, code blocks, links)
   - Python-specific metadata (imports, symbols, docstrings)
   - Basic metrics (size, token estimate)
4. `db.insert_document()` stores to database

**Classification Pipeline:**

1. `classify_documents()` retrieves unclassified documents from database
2. Extracts document features using `extract_document_features()`
3. Uses TF-IDF and pattern matching to score against categories
4. Returns `ClassificationResult` with category, confidence, matched rules
5. `tag_documents()` detects domain tags via pattern matching
6. `db.update_document_classification()` persists results

**Analysis Pipeline:**

1. `analyze_category()` retrieves all documents for a category
2. Calculates structural metrics:
   - Heading frequency and depth distribution
   - Code block/link density
   - Size distribution (percentiles)
   - Token estimate distribution
   - Common section ordering
3. `generate_shape_reports()` creates report per category
4. Reports written to disk in `reports/` directory

**Rewrite Pipeline:**

1. `UnifiedRewriter.rewrite_category()` retrieves documents by category
2. For each document:
   - Loads template if `use_templates=True`
   - Passes to LLM with context about category/gold standards
   - LLM rewrites content using template as guide
   - `QualityReport` assesses output (placeholders, truncation, structure)
   - Results written to output directory
3. Aggregates quality scores and error handling
4. Returns `RewriteResult` with metrics

**State Management:**

- **Document State:** Immutable during extraction, mutations only through database updates
- **Classification State:** Stored in `documents.category`, `documents.category_confidence`, `documents.domain_tags`
- **Quality State:** Stored in `documents.quality_score`, `documents.is_gold_standard`
- **Chunk State:** Stored in separate `chunks` table, linked via `document_id` FK

## Key Abstractions

**BaseExtractor:**
- Purpose: Define contract for file format handlers
- Examples: `MarkdownExtractor`, `PythonExtractor`
- Pattern: Subclass implements `extract()` method, inherits `estimate_tokens()`

**Document:**
- Purpose: Unified representation of any file type
- Examples: `.md` files, `.py` files, `.txt` files
- Pattern: Rich object with extracted metadata, classification, quality scores

**DocumentCategory (Enum):**
- Purpose: Valid categories for documents
- Values: PERSONA, HOWTO, RUNBOOK, ARCHITECTURE, REFERENCE, TUTORIAL, ADR, SPEC, UNKNOWN
- Pattern: Used for filtering and routing

**DomainTag (Enum):**
- Purpose: Cross-cutting domain indicators
- Values: BACKEND, FRONTEND, PYTHON, TYPESCRIPT, DATABASE, AI, etc.
- Pattern: Multiple tags per document, pattern-matched

**CorpusDatabase:**
- Purpose: SQLite persistence with type safety
- Pattern: Wraps sqlite_utils, converts between Pydantic models and rows

**ClassificationResult:**
- Purpose: Package classification decision with confidence
- Contains: Primary/secondary categories, confidence scores, matched rules
- Pattern: Used to inform rewriting strategy

**RewriteResult:**
- Purpose: Aggregate rewriting outcomes
- Contains: Count of processed docs, output paths, errors, warnings, quality scores
- Pattern: CLI uses for progress reporting

## Entry Points

**CLI Application:**
- Location: `src/corpus_analyzer/cli.py`
- Triggers: User runs `corpus-analyzer <command>`
- Responsibilities: Route commands, manage output, handle errors

**Extract Command:**
- Location: `src/corpus_analyzer/cli.py:extract()`
- Triggers: `corpus-analyzer extract <source>`
- Responsibilities: Scan directory, extract documents, populate database

**Classify Command:**
- Location: `src/corpus_analyzer/cli.py:classify()`
- Triggers: `corpus-analyzer classify <database>`
- Responsibilities: Run classification pipeline, update database

**Analyze Command:**
- Location: `src/corpus_analyzer/cli.py:analyze()`
- Triggers: `corpus-analyzer analyze <database>`
- Responsibilities: Generate shape reports per category

**Rewrite Command:**
- Location: `src/corpus_analyzer/cli.py:rewrite()`
- Triggers: `corpus-analyzer rewrite <database>`
- Responsibilities: Orchestrate LLM rewriting, handle quality assessment

**Database Commands:**
- Location: `src/corpus_analyzer/cli.py:db_init()`, `db_inspect()`
- Triggers: `corpus-analyzer db initialize|inspect`
- Responsibilities: Schema creation, inspection

**Samples Command:**
- Location: `src/corpus_analyzer/cli.py:samples_extract()`
- Triggers: `corpus-analyzer samples extract`
- Responsibilities: Extract representative documents per category

**Templates Command:**
- Location: `src/corpus_analyzer/cli.py:templates_generate()`, `templates_freeze()`
- Triggers: `corpus-analyzer templates generate|freeze`
- Responsibilities: Generate templates from analysis, add contracts

## Error Handling

**Strategy:** Graceful degradation with detailed error reporting

**Patterns:**

- **Extraction Errors:** Catch and log per-file, continue processing others. Return None to skip problematic file.
  - Example: `MarkdownExtractor.extract()` catches frontmatter parsing errors, falls back to treating entire file as body

- **Classification Errors:** Log non-critical issues, assign UNKNOWN category if classification fails
  - Example: Pattern matching failures result in fallback to UNKNOWN with 0.0 confidence

- **Database Errors:** Transaction boundaries prevent partial updates
  - Example: `insert_document()` checks for existing path before INSERT to avoid duplicates

- **LLM Errors:** Fallback from template-based to LLM-based if templates unavailable
  - Example: `UnifiedRewriter` has `use_templates` and `use_llm_fallback` flags

- **Quality Assessment:** Nonblocking quality checks produce warnings, not failures
  - Example: Placeholders in output marked as issues but don't stop processing

## Cross-Cutting Concerns

**Logging:**
- Approach: Python logging module with per-module loggers
- Pattern: `logger = logging.getLogger(__name__)` in each module
- Usage: Primarily in analysis and LLM modules for debugging

**Validation:**
- Approach: Pydantic models enforce schema at serialization boundary
- Pattern: All external data converted to Pydantic models immediately on import
- Usage: Prevents invalid state from propagating through pipeline

**Configuration:**
- Approach: Environment variables via Pydantic Settings
- Pattern: `corpus_analyzer.config.settings` singleton
- Usage: Database path, Ollama host/model, chunk sizes

**Progress Reporting:**
- Approach: Rich library for terminal output
- Pattern: Direct console output in CLI layer
- Usage: Status messages, progress bars (in `unified_rewriter.py`)

**Token Estimation:**
- Approach: Simple heuristic (4 characters = 1 token)
- Pattern: `BaseExtractor.estimate_tokens()` inherited by all extractors
- Usage: Chunk sizing and LLM context window management

---

*Architecture analysis: 2026-02-23*

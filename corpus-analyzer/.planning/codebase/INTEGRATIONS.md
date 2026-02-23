# External Integrations

**Analysis Date:** 2026-02-23

## APIs & External Services

**Language Model (LLM):**
- Ollama (local/self-hosted) - Text generation and completion
  - SDK/Client: `ollama` Python package 0.6.1
  - Implementation: `src/corpus_analyzer/llm/ollama_client.py` (OllamaClient class)
  - Auth: None (assumes local/trusted network)
  - Configuration: `CORPUS_OLLAMA_HOST`, `CORPUS_OLLAMA_MODEL` env vars
  - Default host: `http://localhost:11434`
  - Default model: `mistral` (overridable)
  - Features:
    - Single-prompt completion: `generate(prompt, system, temperature)`
    - Streaming generation: `generate_stream(prompt, system, temperature)`
    - Model listing: `list_models()`
    - Health check: `is_available()`

**Document Content Processing:**
- Python-based text extraction and analysis
  - File types: `.md` (Markdown), `.py` (Python), `.txt`, `.rst`
  - Metadata extraction: Headings, links, code blocks, Python symbols
  - No external API dependencies for extraction

## Data Storage

**Databases:**
- SQLite (file-based)
  - Provider: Built-in Python sqlite3, accessed via sqlite-utils wrapper
  - Connection: File path `CORPUS_DATABASE_PATH` (default: `corpus.sqlite`)
  - Client: `sqlite-utils` 3.36+
  - Schema: Two main tables - `documents`, `chunks`
  - Location: `src/corpus_analyzer/core/database.py` (CorpusDatabase class)
  - Features:
    - Automatic table creation with schema
    - JSON serialization for complex fields (headings, links, code_blocks, symbols, domain_tags)
    - Query builders for filtering by category and file type
    - Document classification tracking
    - Gold standard document marking

**File Storage:**
- Local filesystem only
  - Extract source: Directory paths (recursive scanning)
  - Output: SQLite database file
  - Reports: Directory specified by `CORPUS_REPORTS_DIR`
  - Templates: Directory specified by `CORPUS_TEMPLATES_DIR`
  - No cloud storage or S3 integration

**Caching:**
- None - SQLite database serves as persistent cache
- No in-memory caching layer or Redis

## Authentication & Identity

**Auth Provider:**
- None - This is a local, single-user tool
- No user authentication required
- No API keys or credentials managed
- Ollama assumed to be in trusted network (localhost or internal)

## Monitoring & Observability

**Error Tracking:**
- None (no external service)
- Logging done to console/files only
- No error reporting service integration

**Logs:**
- Standard library `logging` module
- Console output via `rich` library
- Progress indicators via Rich console with visual feedback

## CI/CD & Deployment

**Hosting:**
- No cloud hosting required
- Self-contained CLI application
- Runs locally or on any system with Python 3.12+

**CI Pipeline:**
- None detected in codebase
- No GitHub Actions, GitLab CI, or similar config files

**Development Server:**
- No web server (CLI-only application)
- Ollama server runs separately (not part of this package)

## Environment Configuration

**Required env vars:**
- `CORPUS_DATABASE_PATH` - SQLite database location (has default)
- `CORPUS_OLLAMA_HOST` - Ollama service endpoint (has default: localhost:11434)
- `CORPUS_OLLAMA_MODEL` - Model name (has default: mistral)

**Optional env vars:**
- `CORPUS_CHUNK_SIZE` - Text chunk size (has default: 1000)
- `CORPUS_CHUNK_OVERLAP` - Chunk overlap (has default: 100)
- `CORPUS_REPORTS_DIR` - Reports output directory (has default: reports)
- `CORPUS_TEMPLATES_DIR` - Templates output directory (has default: templates)

**Secrets location:**
- No secrets managed - All environment variables are non-sensitive
- `.env` file can be created (see `.env.example`)
- `.env` is git-ignored

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Data Flow to External Services

**LLM Service (Ollama):**
- One-way HTTP POST requests to Ollama `/api/chat` endpoint
- Request contains: model name, message content, temperature setting
- Response: Text completion from local LLM
- No persistence of responses beyond application runtime (unless explicitly saved)
- Used in:
  - `src/corpus_analyzer/llm/rewriter.py` - Document rewriting
  - `src/corpus_analyzer/llm/unified_rewriter.py` - Unified rewriting approach
  - `src/corpus_analyzer/generators/advanced_rewriter.py` - Advanced template generation
  - `src/corpus_analyzer/llm/quality_scorer.py` - Quality assessment

**Document Extraction (File System):**
- Read-only filesystem scanning
- No uploads or network calls
- Parses:
  - Markdown headings, links, frontmatter
  - Python docstrings, imports, symbols
  - File metadata (mtime, size)

---

*Integration audit: 2026-02-23*

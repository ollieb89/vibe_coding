# Document Corpus Analyzer

Extract, categorize, analyze, and template documentation from folders of docs and scripts.

## Features

- **Extract**: Scan directories for Markdown and Python files, extract metadata (headings, links, code blocks, symbols)
- **Classify**: Rule-based document type classification (howto, runbook, architecture, reference, etc.)
- **Analyze**: Generate shape reports per category (heading frequency, code density, structure patterns)
- **Generate**: Create templates and lint rules based on analysis
- **Rewrite**: LLM-assisted document consolidation using local Ollama

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd corpus-analyzer

# Install with uv
uv sync

# Or install dev dependencies too
uv sync --all-extras
```

## Quick Start

```bash
# Extract documents from a directory
uv run corpus-analyzer extract /path/to/docs --output corpus.sqlite

# Classify documents by type
uv run corpus-analyzer classify corpus.sqlite

# Analyze document shapes
uv run corpus-analyzer analyze corpus.sqlite --output reports/

# Generate templates
uv run corpus-analyzer generate-templates corpus.sqlite --output templates/

# Rewrite with LLM (requires Ollama running)
uv run corpus-analyzer rewrite corpus.sqlite --category howto --model llama3.2
```

## Document Categories

| Category | Description |
|----------|-------------|
| `persona` | Agent/role definitions |
| `howto` | Step-by-step guides |
| `runbook` | Operational procedures |
| `architecture` | System design docs |
| `reference` | API/config reference |
| `tutorial` | Learning-focused content |
| `adr` | Architecture Decision Records |
| `spec` | Specifications |

## Development

```bash
# Run tests
make test

# Run linting
make lint

# Format code
make format

# Type checking
make typecheck
```

## Configuration

Set environment variables or create a `.env` file:

```env
CORPUS_DATABASE_PATH=corpus.sqlite
CORPUS_OLLAMA_HOST=http://localhost:11434
CORPUS_OLLAMA_MODEL=llama3.2
```

## License

MIT

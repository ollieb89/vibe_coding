# Agent Discovery System

🔍 An intelligent agent discovery and recommendation system that uses semantic search via Chroma to help users find the most relevant GitHub Copilot agents, prompts, instructions, and chatmodes for their codebase.

## Features

- **Semantic Search**: Find agents using natural language queries
- **Codebase Analysis**: Automatically detect languages, frameworks, and patterns
- **Interactive Discovery**: Guided questionnaire for tailored recommendations
- **Multiple Agent Types**: Search across agents, prompts, instructions, and chatmodes
- **Smart Ranking**: Results ranked by relevance to your specific needs

## Quick Start

### Installation

```bash
# From vibe-tools root (pyproject.toml lives here)
cd agent-discovery-system

# Install dependencies with uv (recommended)
uv sync

# Or install in development mode
uv pip install -e ".[dev]"
```text

### Prerequisites

Make sure you have Chroma running:

```bash
# Start Chroma server (from chroma directory)
cd ../chroma
docker compose -f docker-compose.yml up -d
# If you do not have the Docker Compose plugin, install it
# (e.g., sudo apt install docker-compose-plugin) or use docker-compose up -d
```text

### Usage

#### 1. Ingest Agents

First, ingest all agents from vibe-tools into Chroma:

```bash
# Auto-detect vibe-tools location
uv run agent-discover ingest

# Or specify the path
uv run agent-discover ingest --vibe-tools /vibe-tools

# Clear existing data first
uv run agent-discover ingest --clear
```

#### 2. Discover Agents

Interactive discovery mode:

```bash
# Analyze current directory and get recommendations
uv run agent-discover discover

# Analyze a specific codebase
uv run agent-discover discover --path /path/to/your/project
```

#### 3. Generate AGENTS.md

Generate configuration files from discovery:

```bash
# Generate AGENTS.md and configuration files
uv run agent-discover generate --path /path/to/project

# Preview without writing files
uv run agent-discover generate --dry-run

# Generate only AGENTS.md (no instructions/chatmode)
uv run agent-discover generate --agents-only
```

#### 4. Quick Search

Search by keyword:

```bash
uv run agent-discover search "playwright testing e2e"
uv run agent-discover search "security owasp authentication"
uv run agent-discover search "nextjs react frontend"
```

#### 5. List Agents

Browse available agents:

```bash
# List all agents
uv run agent-discover list

# Filter by type
uv run agent-discover list --type agent
uv run agent-discover list --type prompt
uv run agent-discover list --type instruction
uv run agent-discover list --type chatmode

# Filter by category
uv run agent-discover list --category testing
uv run agent-discover list --category security
```

#### 6. Statistics

View collection statistics:

```bash
uv run agent-discover stats
```

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system design.

```text
┌─────────────────────────────────────────────────────────────────┐
│                   Agent Discovery System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   CLI Interface → Discovery Engine → Chroma Collections         │
│         ↓              ↓                    ↓                   │
│   Questions ← Codebase Analysis     Semantic Search             │
│         ↓              ↓                    ↓                   │
│   Search Criteria → Agent Matches → Ranked Results              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Sources

The system ingests agents from these vibe-tools directories:

| Source | Type | Description |
|--------|------|-------------|
| `ghc_tools/agents/` | Agents | Specialist personas |
| `ghc_tools/prompts/` | Prompts | Reusable task workflows |
| `ghc_tools/instructions/` | Instructions | Domain-specific best practices |
| `ghc_tools/chatmodes/` | Chatmodes | Integrated experiences |
| `SuperAgent-MCP/agents/` | Agents | SuperAgent MCP definitions |
| `.github/agents/` | Agents | GitHub workflow agents |

## Categories

Agents are automatically classified into these categories:

- `frontend` - React, Next.js, Vue, UI/UX
- `backend` - API, Python, FastAPI, Express
- `architecture` - System design, patterns
- `testing` - Playwright, Vitest, QA
- `security` - OWASP, authentication
- `devops` - CI/CD, Docker, Kubernetes
- `database` - SQL, PostgreSQL, MongoDB
- `ai_ml` - AI/ML, LLM, prompt engineering
- `planning` - Requirements, PRD, task management
- `documentation` - README, docs, tutorials

## Development

### Running Tests

```bash
uv run pytest tests/ -v
```

### Code Quality

```bash
# Lint
uv run ruff check src/

# Type check
uv run mypy src/

# Format
uv run ruff format src/
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CHROMA_HOST` | `localhost` | Chroma server host |
| `CHROMA_PORT` | `9500` | Chroma server port |

## Related

- [CUSTOM_AGENTS_GUIDE.md](../CUSTOM_AGENTS_GUIDE.md) - Guide to creating custom agents
- [Chroma Ingestion](../chroma) - Chroma database setup
- [vibe-tools](../) - Parent repository

## License

MIT

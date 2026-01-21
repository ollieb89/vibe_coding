# Agent Discovery System - Architecture Plan

## Overview

An intelligent agent discovery and recommendation system that uses semantic search via Chroma to help users find the most relevant GitHub Copilot agents, prompts, instructions, and chatmodes for their codebase.

## Vision

Transform the fragmented collection of 300+ agents/prompts/instructions across vibe-tools into a discoverable, queryable system that:

1. **Semantically understands** user codebases and requirements
2. **Intelligently recommends** the most relevant agents
3. **Interactive guides** users through selection with multiple-choice questions
4. **Generates** customized `AGENTS.md` and instruction files

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Agent Discovery System                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │   CLI/UI     │───▶│  Discovery   │───▶│  Chroma Collections  │  │
│  │  Interface   │    │   Engine     │    │                      │  │
│  └──────────────┘    └──────────────┘    │  • agents_core       │  │
│                             │            │  • prompts_core      │  │
│                             ▼            │  • instructions_core │  │
│                      ┌──────────────┐    │  • chatmodes_core    │  │
│                      │  Question    │    └──────────────────────┘  │
│                      │  Generator   │                               │
│                      └──────────────┘                               │
│                             │                                       │
│                             ▼                                       │
│                      ┌──────────────┐    ┌──────────────────────┐  │
│                      │  Recommend   │───▶│  Output Generator    │  │
│                      │  Engine      │    │  • AGENTS.md         │  │
│                      └──────────────┘    │  • instructions/     │  │
│                                          │  • chatmodes/        │  │
│                                          └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Model

### Agent Schema (stored in Chroma)

```python
{
    # Core identity
    "agent_name": str,           # e.g., "security-engineer"
    "agent_type": str,           # "agent" | "prompt" | "instruction" | "chatmode"
    "description": str,          # One-line description

    # Classification
    "category": str,             # "frontend" | "backend" | "devops" | etc.
    "tech_stack": list[str],     # ["nextjs", "react", "typescript"]
    "languages": list[str],      # ["python", "javascript", "go"]
    "frameworks": list[str],     # ["fastapi", "nextjs", "playwright"]

    # Discovery metadata
    "use_cases": list[str],      # When to activate
    "complexity": str,           # "beginner" | "intermediate" | "advanced"
    "popularity_score": float,   # Based on usage patterns

    # Source tracking
    "source_path": str,          # Original file path
    "source_collection": str,    # "ghc_tools" | "superagent" | etc.
    "content_hash": str,         # For deduplication
}
```

### Question Schema

```python
{
    "id": str,
    "text": str,                 # Question to display
    "type": str,                 # "single" | "multi" | "text"
    "options": list[dict],       # [{"value": "...", "label": "...", "weight": {...}}]
    "depends_on": dict | None,   # Conditional display logic
    "maps_to": list[str],        # Chroma filter fields
}
```

---

## Components

### 1. Agent Collector (`collector.py`)

Scans vibe-tools directories and extracts agent definitions:

```python
class AgentCollector:
    """Collects and normalizes agents from all sources."""

    SOURCES = {
        "ghc_tools/agents": "ghc_agents",
        "ghc_tools/prompts": "ghc_prompts",
        "ghc_tools/instructions": "ghc_instructions",
        "ghc_tools/chatmodes": "ghc_chatmodes",
        "SuperAgent-MCP/agents": "superagent_agents",
        ".github/agents": "github_agents",
    }

    def collect_all(self) -> list[Agent]
    def deduplicate(self, agents: list[Agent]) -> list[Agent]
    def extract_metadata(self, file_path: str) -> dict
```

### 2. Chroma Ingester (`ingester.py`)

Uses existing `chroma_ingestion.AgentIngester` with extensions:

```python
class EnhancedAgentIngester(AgentIngester):
    """Extended ingester with discovery-specific metadata."""

    def ingest_for_discovery(self, agents: list[Agent]) -> int
    def create_category_collections(self) -> dict[str, Collection]
    def build_tech_stack_index(self) -> dict
```

### 3. Discovery Engine (`discovery.py`)

Semantic search and filtering:

```python
class DiscoveryEngine:
    """Find agents based on codebase analysis and user input."""

    def analyze_codebase(self, path: str) -> CodebaseProfile
    def suggest_questions(self, profile: CodebaseProfile) -> list[Question]
    def search_agents(self, criteria: dict) -> list[AgentMatch]
    def rank_results(self, matches: list[AgentMatch]) -> list[AgentMatch]
```

### 4. Question Generator (`questions.py`)

Dynamic question generation based on context:

```python
class QuestionGenerator:
    """Generate relevant questions based on codebase analysis."""

    QUESTION_BANK = [
        {
            "id": "project_type",
            "text": "What type of project are you building?",
            "type": "single",
            "options": [
                {"value": "frontend", "label": "Frontend Web App"},
                {"value": "backend", "label": "Backend API"},
                {"value": "fullstack", "label": "Full-Stack Application"},
                {"value": "cli", "label": "CLI Tool"},
                {"value": "library", "label": "Library/Package"},
            ]
        },
        {
            "id": "primary_language",
            "text": "What is your primary programming language?",
            "type": "single",
            "options": [...]
        },
        {
            "id": "needs",
            "text": "What kind of help do you need?",
            "type": "multi",
            "options": [
                {"value": "architecture", "label": "Architecture & Planning"},
                {"value": "testing", "label": "Testing & QA"},
                {"value": "security", "label": "Security Review"},
                {"value": "performance", "label": "Performance Optimization"},
                {"value": "debugging", "label": "Debugging & Troubleshooting"},
                {"value": "documentation", "label": "Documentation"},
            ]
        }
    ]

    def get_questions(self, context: CodebaseProfile) -> list[Question]
    def process_answers(self, answers: dict) -> SearchCriteria
```

### 5. Output Generator (`generator.py`)

Creates customized output files:

```python
class OutputGenerator:
    """Generate AGENTS.md and related files."""

    def generate_agents_md(self, agents: list[Agent], template: str) -> str
    def generate_instructions(self, instructions: list[Instruction]) -> dict[str, str]
    def generate_chatmode(self, profile: CodebaseProfile) -> str
```

### 6. CLI Interface (`cli.py`)

Interactive command-line experience:

```python
@click.group()
def cli():
    """Agent Discovery System - Find the perfect agents for your codebase."""
    pass

@cli.command()
@click.option("--path", default=".", help="Path to codebase to analyze")
@click.option("--interactive/--no-interactive", default=True)
def discover(path: str, interactive: bool):
    """Discover agents for your codebase."""
    pass

@cli.command()
def ingest():
    """Ingest agents into Chroma for discovery."""
    pass

@cli.command()
def list_agents():
    """List all available agents."""
    pass
```

---

## File Structure

```
vibe-tools/agent-discovery-system/
├── ARCHITECTURE.md           # This file
├── README.md                 # User documentation
├── pyproject.toml            # Dependencies
│
├── src/
│   └── agent_discovery/
│       ├── __init__.py
│       ├── cli.py            # Click CLI interface
│       ├── collector.py      # Agent collection
│       ├── discovery.py      # Discovery engine
│       ├── generator.py      # Output generation
│       ├── ingester.py       # Chroma ingestion
│       ├── questions.py      # Question bank
│       └── models.py         # Pydantic models
│
├── data/
│   ├── questions.yaml        # Question definitions
│   ├── categories.yaml       # Category taxonomy
│   └── templates/            # Output templates
│       ├── agents.md.j2
│       ├── chatmode.md.j2
│       └── instructions.md.j2
│
└── tests/
    └── ...
```

---

## Chroma Collection Design

### Collection: `agents_discovery`

Primary collection for all agent types:

```python
collection = client.get_or_create_collection(
    name="agents_discovery",
    metadata={
        "description": "All agents, prompts, instructions, chatmodes for discovery",
        "hnsw:space": "cosine",
    }
)
```

### Metadata Fields for Filtering

| Field | Type | Example | Used For |
|-------|------|---------|----------|
| `agent_type` | string | "agent" | Filter by type |
| `category` | string | "testing" | Filter by domain |
| `tech_stack` | string | "nextjs,react,typescript" | Filter by tech |
| `languages` | string | "python,javascript" | Filter by language |
| `complexity` | string | "intermediate" | Filter by level |
| `source_collection` | string | "ghc_tools" | Track origin |

---

## User Flow

### Flow 1: Interactive Discovery

```
$ uv run agent-discover

🔍 Agent Discovery System
=========================

Analyzing your codebase... ✓

Detected:
  • Languages: Python, TypeScript
  • Frameworks: FastAPI, Next.js
  • Patterns: REST API, React components

? What type of project are you building?
  ○ Frontend Web App
  ○ Backend API
  ● Full-Stack Application
  ○ CLI Tool

? What kind of help do you need? (select multiple)
  ☑ Architecture & Planning
  ☐ Testing & QA
  ☑ Security Review
  ☐ Performance Optimization

? Any specific focus areas? (free text)
> authentication and API design

🎯 Recommended Agents (5 matches):

1. system-architect (⭐ 95% match)
   Full-stack architecture planning and design patterns

2. security-engineer (⭐ 88% match)
   OWASP, threat modeling, auth security

3. backend-architect (⭐ 85% match)
   API design, microservices, data modeling

4. python-expert (⭐ 78% match)
   FastAPI, async patterns, Python best practices

5. expert-react-frontend-engineer (⭐ 75% match)
   React architecture, state management

? Generate AGENTS.md with these recommendations? [Y/n]
```

### Flow 2: Quick Search

```
$ uv run agent-discover search "playwright testing e2e"

Found 4 matching agents:

1. playwright-tester.agent.md (⭐ 92%)
   E2E testing with Playwright

2. quality-engineer.prompt.md (⭐ 78%)
   Test strategy and quality assurance

3. playwright-typescript.instructions.md (⭐ 75%)
   Playwright best practices for TypeScript
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Create project structure
- [ ] Implement AgentCollector
- [ ] Extend AgentIngester for discovery metadata
- [ ] Ingest all 300+ agents/prompts/instructions

### Phase 2: Discovery Engine (Week 2)
- [ ] Implement CodebaseProfile analyzer
- [ ] Build QuestionGenerator with YAML-driven questions
- [ ] Create DiscoveryEngine with semantic search

### Phase 3: CLI & Output (Week 3)
- [ ] Build Click CLI interface
- [ ] Create OutputGenerator with Jinja2 templates
- [ ] Add interactive prompts with `rich` or `questionary`

### Phase 4: Polish & Testing (Week 4)
- [ ] Add unit tests
- [ ] Create user documentation
- [ ] Add CI/CD for ingestion updates
- [ ] Performance optimization

---

## Dependencies

```toml
[project]
dependencies = [
    "chroma-ingestion",  # Local package from ../chroma
    "chromadb>=0.5.0",
    "click>=8.1.0",
    "pyyaml>=6.0",
    "pydantic>=2.0",
    "jinja2>=3.1.0",
    "rich>=13.0",        # Pretty console output
    "questionary>=2.0",  # Interactive prompts
]
```

---

## Integration with CUSTOM_AGENTS_GUIDE.md

The system will use templates derived from CUSTOM_AGENTS_GUIDE.md:

1. **Agent Structure**: Follow the frontmatter + sections format
2. **Naming Conventions**: Enforce kebab-case naming
3. **Categories**: Use consistent category taxonomy
4. **Quality Standards**: Validate against guide requirements

---

## Next Steps

1. **Create project scaffolding** with pyproject.toml
2. **Implement AgentCollector** to scan all sources
3. **Run initial ingestion** to populate Chroma
4. **Build MVP CLI** with basic search functionality
5. **Iterate** based on user feedback

---

## Open Questions

- [ ] Should we support VS Code extension integration?
- [ ] How to handle agent versioning/updates?
- [ ] Should questions be fully dynamic or semi-static?
- [ ] How to handle duplicate/similar agents?

---
type: reference
---

# Python Project Scaffolding

Generate complete, production-ready Python applications with modern tooling (uv, FastAPI, Django), type hints, testing setup, and configuration following current best practices.

## Context

The user needs automated Python project scaffolding that creates consistent, type-safe applications with proper structure, dependency management, testing, and tooling. Focus on modern Python patterns and scalable architecture.

## Requirements

- [user-defined]

## Instructions

### 1. Analyze Project Type

Determine the project type from user requirements:
- **FastAPI**: REST APIs, microservices, async applications ([source: python-development/commands/python-scaffold.md])
- **Django**: Full-stack web applications, admin panels, ORM-heavy projects ([source: python-development/commands/python-scaffold.md])
- **Library**: Reusable packages, utilities, tools ([source: python-development/commands/python-scaffold.md])
- **CLI**: Command-line tools, automation scripts ([source: python-development/commands/python-scaffold.md])
- **Generic**: Standard Python applications ([source: python-development/commands/python-scaffold.md])

### 2. Initialize Project with uv

```bash
# Create new project with uv
uv init <project-name>
cd <project-name>

# Initialize git repository
git init
echo ".venv/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "__pycache__/" >> .gitignore
echo ".pytest_cache/" >> .gitignore
echo ".ruff_cache/" >> .gitignore

# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Generate FastAPI Project Structure

[...] (The rest of the instructions are provided as in the original document)

## Output Format / Reports
1. **Project Structure**: Complete directory tree with all necessary files
2. **Configuration**: pyproject.toml with dependencies and tool settings
3. **Entry Point**: Main application file (main.py, cli.py, etc.)
4. **Tests**: Test structure with pytest configuration
5. **Documentation**: README with setup and usage instructions
6. **Development Tools**: Makefile, .env.example, .gitignore

Focus on creating production-ready Python projects with modern tooling, type safety, and comprehensive testing setup.
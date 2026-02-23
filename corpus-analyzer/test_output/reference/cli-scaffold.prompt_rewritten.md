---
title: CLI Project Scaffold Prompt
source: prompts/cli-scaffold.prompt.md
---

## Classification Insights
- Primary Category: reference (confidence: 0.95)
- Key Features: code_examples (1.0), function_signatures (1.0), parameter_descriptions (1.0), return_values_and_exceptions (1.0), usage_examples (1.0)

---
type: reference
---

# CLI Project Scaffold Prompt

Generate a complete, production-ready Python CLI project structure.

## Input Requirements

Provide the following details for your CLI tool:

- **CLI Name**: The name of your CLI tool (e.g., `mytool`, `data-sync`)
- **Description**: Brief description of what the tool does
- **Framework**: Choose between `click` or `typer` (default: `typer`)
- **Commands**: List of main commands/subcommands needed
- **Features**: Optional features to include

## Example Input

```
CLI Name: file-organizer
Description: Organize files in directories by type, date, or custom rules
Framework: typer
Commands:
  - organize: Main command to organize files
  - preview: Show what would be organized (dry-run)
  - config: Manage configuration settings
  - undo: Revert last organization operation
Features:
  - Configuration file support
  - Progress bars
  - Verbose/quiet modes
  - JSON output option
```

## Output Structure

The scaffold will generate the following files and directories:

1. `pyproject.toml`
2. `src/{package_name}` (containing multiple subdirectories)
3. `tests` directory
4. `README.md`
5. `.gitignore`

### 1. `pyproject.toml`
```toml
[project]
name = "{cli-name}"
version = "0.1.0"
description = "{description}"
requires-python = ">=3.9"
dependencies = [
    "typer>=0.9.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
]

[project.scripts]
{cli-name} = "{package_name}.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### 2. `src/{package_name}` (containing multiple subdirectories)

#### 2.1. `__init__.py`
```python
"""{{description}}"""

__version__ = "0.1.0"
```

#### 2.2. `cli.py`
```python
"""Command-line interface for {cli-name}."""

import typer
from rich.console import Console

from . import __version__

app = typer.Typer(
    name="{cli-name}",
    help="{description}",
    add_completion=False,
)
console = Console()

def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold]{cli-name}[/bold] version {__version__}")
        raise typer.Exit()

@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """{{description}}"""
    pass

@app.command()
def {command_name}(
    # Add appropriate arguments and options
) -> None:
    """Command description."""
    pass

if __name__ == "__main__":
    app()
```

#### 2.3. `core.py`
```python
"""Core business logic for {cli-name}."""

# Separate business logic from CLI layer
# This enables easier testing and potential library usage
```

### 3. `tests` directory

#### 3.1. `test_cli.py`
```python
"""Tests for CLI commands."""

from typer.testing import CliRunner

from {package_name}.cli import app

runner = CliRunner()

def test_version():
    """Test version flag."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "{cli-name}" in result.stdout

def test_help():
    """Test help output."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
```

### 4. `README.md`
```markdown
# {cli-name}

{description}

## Installation

```bash
pip install {cli-name}
```

## Usage

```bash
{cli-name} --help
```

## Commands

- `{command}`: Description

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```
```

### 5. `.gitignore`
```
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
.eggs/
.pytest_cache/
.coverage
htmlcov/
.env
.venv/
venv/
```

## Framework-Specific Variations

### Click Framework
If `click` is specified, adjust cli.py:

```python
"""Command-line interface for {cli-name}."""

import click
from rich.console import Console

from . import __version__

console = Console()

@click.group()
@click.version_option(__version__, "-V", "--version")
def cli():
    """{{description}}"""
    pass

@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
def {command_name}(path: str, verbose: bool) -> None:
    """Command description."""
    pass

if __name__ == "__main__":
    cli()
```

## Additional Features

### Configuration File Support
Add `src/{package_name}/config.py`:
```python
"""Configuration management."""

from pathlib import Path
from typing import Any

import tomllib

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "{cli-name}" / "config.toml"

def load_config(path: str = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    with open(path, 'r') as f:
        return tomllib.load(f)

def save_config(data: dict[str, Any], path: str = DEFAULT_CONFIG_PATH):
    with open(path, 'w') as f:
        tomllib.dump(data, f)
```

### Progress Bars
```python
from tqdm import tqdm

def process_items(items):
    return tqdm(items, total=len(items))
```

### JSON Output Option
```python
import json

@app.command()
def list_items(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all items."""
    items = get_items()
    if json_output:
        print(json.dumps(items, indent=2))
    else:
        for item in items:
            console.print(f"• {item}")
```

## Checklist

After generation, verify:
- [ ] `pyproject.toml` has correct entry point
- [ ] Package name is valid Python identifier (no hyphens)
- [ ] All commands have docstrings
- [ ] Tests cover basic functionality
- [ ] README has installation and usage instructions

[source: prompts/cli-scaffold.prompt.md]
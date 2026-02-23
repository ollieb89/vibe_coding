---
type: reference
---

# Python CLI Development Best Practices

Guidelines for building professional, user-friendly command-line applications in Python using Click, Typer, and Rich.

## Configuration Options
- `--framework`: The CLI framework to use (Click or Typer) [default: Click]

## Project Structure
### Recommended Layout

```
my-cli/
├── pyproject.toml
├── src/
│   └── my_cli/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       └── commands/
│           ├── __init__.py
│           └── subcommand.py
└── tests/
    └── test_cli.py
```

### Entry Point Configuration

```toml
# pyproject.toml
[project.scripts]
my-cli = "my_cli.cli:cli"
```

## Command Design

### Argument vs Option

```python
# ❌ BAD: Everything as options
@click.command()
@click.option("--input-file", required=True)
def process(input_file):
    pass

# ✅ GOOD: Required as argument, optional as option
@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", default="-", help="Output file [default: stdout]")
def process(input_file, output):
    pass
```

### Option Naming

```python
# ❌ BAD: Inconsistent, unclear
@click.option("--v")
@click.option("--outputDir")
@click.option("-verbose")

# ✅ GOOD: Consistent short/long, clear names
@click.option("--verbose", "-v", is_flag=True)
@click.option("--output-dir", "-o", help="Output directory")
@click.option("--dry-run", "-n", is_flag=True, help="Show what would be done")
```

### Boolean Flags

```python
# ❌ BAD: Requires value
@click.option("--verbose", type=bool, default=False)

# ✅ GOOD: Simple flag
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")

# ✅ GOOD: Flag with negation
@click.option("--color/--no-color", default=True, help="Enable/disable colored output")
```

## Help Text

### Command Help

```python
# ❌ BAD: No help, unclear purpose
@click.command()
def sync():
    pass

# ✅ GOOD: Clear and concise help
@click.command()
@click.pass_context
def sync(ctx):
    ctx.invoke(sync.help)
```

### Option Help

```python
@click.option("--verbose", is_flag=True, help="Enable verbose output.")
```

## Error Handling

### User-Friendly Errors

```python
def load_config(path):
    try:
        with open(path) as f:
            return json.load(f)  # JSONDecodeError if invalid
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Config file not found: {path}")
        raise SystemExit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error:[/red] Invalid JSON in {path}")
        console.print(f"[dim]  Line {e.lineno}: {e.msg}[/dim]")
        raise SystemExit(1)
```

## Testing

### Basic CLI Test

```python
from click.testing import CliRunner
from my_cli.cli import cli

def test_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "1.0.0" in result.output
```

### Command Test with Arguments

```python
def test_create_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["create", "myproject", "--template", "basic"])
        assert result.exit_code == 0
        assert Path("myproject").exists()
```

### Test Error Handling

```python
def test_missing_file_error():
    runner = CliRunner()
    result = runner.invoke(cli, ["process", "nonexistent.txt"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()
```

## Common Pitfalls

| Problem | Cause | Solution |
|---------|-------|----------|
| Help text not showing | Missing docstring | Add docstring to command function |
| Options not working | Wrong decorator order | `@click.command()` must be last (top) |
| Context not available | Not using `@click.pass_context` | Add decorator and ctx parameter |
| Subcommands not found | Not registered with group | Use `@group.command()` or `group.add_command()` |
| Progress bar flickering | Printing during progress | Use `progress.console.print()` instead |
| Colors not showing | Windows terminal | Install `colorama` or use `--force-terminal` |

## Packaging Checklist

- [ ] pyproject.toml with `[project.scripts]` entry point
- [ ] `__version__` in `__init__.py`
- [ ] `__main__.py` for `python -m` support
- [ ] `--version` flag on main command
- [ ] `--help` automatically provided by Click/Typer
- [ ] README with installation and usage examples
- [ ] Tests with CliRunner covering main paths

[source: instructions/python-cli-tooling.instructions.md]
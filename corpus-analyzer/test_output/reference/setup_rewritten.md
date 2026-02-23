---
type: reference
---

# Setup.py for SuperClaude Framework

This is a minimal setup.py that defers to `pyproject.toml` for configuration. Modern Python packaging uses `pyproject.toml` as the primary configuration file. [source: setup.py]

## Configuration Options
- `setup()`: This function is called to initialize the setup process. It takes no arguments in this case, as all configuration is handled by the `pyproject.toml` file.

## Usage Example
```markdown
from setuptools import setup

# All configuration is now in pyproject.toml
setup()
```
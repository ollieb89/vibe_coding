---
type: reference
---

## SuperClaude Doctor Command [source: src/superclaude/cli/doctor.py]

Health check for SuperClaude installation.

### Configuration Options
- `verbose` (optional, default: False): Include detailed diagnostic information

### Run Health Checks
```python
run_doctor(verbose)
```

#### Parameters
- `verbose`: A boolean value that determines whether to include detailed diagnostic information. Default is set to False.

#### Returns
A dictionary containing check results, including the list of checks and a flag indicating if all checks passed.

### Check Pytest Plugin Loaded
```python
_check_pytest_plugin()
```

#### Description
Checks if the pytest plugin is loaded and SuperClaude plugin is active.

#### Return Value
A dictionary containing details about the check result, including whether the SuperClaude pytest plugin is active or not.

### Check Skills Installed
```python
_check_skills_installed()
```

#### Description
Checks if any skills are installed in the specified directory.

#### Return Value
A dictionary containing details about the check result, including the number of installed skills and their names.

### Check Configuration
```python
_check_configuration()
```

#### Description
Checks SuperClaude configuration by attempting to import the superclaude package.

#### Return Value
A dictionary containing details about the check result, including whether SuperClaude was imported correctly or not.

### Usage Example
To run health checks for SuperClaude:
```python
from src.superclaude.cli.doctor import run_doctor

result = run_doctor(verbose=True)
print(result)
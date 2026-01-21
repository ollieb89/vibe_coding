# Phase 3.1.1 - Real Executor Quick Reference

## Basic Usage

```python
from agent_discovery import RealExecutor

# Create executor
executor = RealExecutor(default_timeout_seconds=30)

# Execute code
result = executor.execute(
    code="print('Hello, World!')",
    timeout_seconds=10
)

# Check result
if result.success:
    print(f"Output: {result.stdout}")
else:
    print(f"Error ({result.error_category}): {result.stderr}")
```

## Error Categories

| Category | Detection | Example |
|----------|-----------|---------|
| **timeout** | TimeoutExpired | Script runs > timeout |
| **permission** | OSError, "Permission denied" | Script not executable |
| **dependency** | ImportError, ModuleNotFoundError | Missing package |
| **syntax** | SyntaxError, IndentationError | Invalid Python code |
| **runtime** | Other exceptions | Division by zero |

## Advanced Usage

```python
# Custom timeout per execution
result = executor.execute(
    code="time.sleep(2); print('Done')",
    timeout_seconds=5,
    working_directory="/tmp"
)

# Access all result fields
print(f"Success: {result.success}")
print(f"Stdout: {result.stdout}")
print(f"Stderr: {result.stderr}")
print(f"Time: {result.execution_time_seconds}s")
print(f"Error Type: {result.error_category}")
```

## Integration with Agent Discovery

```python
# Within agent execution pipeline
from agent_discovery import RealExecutor, AgentValidator

executor = RealExecutor()
validator = AgentValidator()

# Validate agent code
is_valid, issues = validator.validate(code)

# Execute validated code
if is_valid:
    result = executor.execute(code)
    # Analyze result for Phase 4
```

## Files

- **Implementation**: `src/agent_discovery/real_executor.py`
- **Tests**: `tests/test_executor_edge_cases.py`
- **Documentation**: `PHASE_3_1_1_COMPLETE.md`
- **Type Hints**: Full coverage, Python 3.11+

## Testing

```bash
# Run all tests
python -m pytest tests/test_executor_edge_cases.py -v

# Run specific test
python -m pytest tests/test_executor_edge_cases.py::test_timeout_handling -v

# Check linting
ruff check src/agent_discovery/real_executor.py
```

## Next Phase: 3.2 (LLM Integration)

The RealExecutor is production-ready and exported from:

```python
from agent_discovery import RealExecutor
```

Ready for integration with LLM-driven execution orchestration.

---

## Phase 3.1.1 Complete ✅

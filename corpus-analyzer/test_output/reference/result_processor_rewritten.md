---
type: reference
---

# Result processor for enhancing and categorizing orchestrated execution results

This module provides intelligent post-processing of execution results from the orchestrator. It categorizes results into success/partial/failure states, extracts metadata, and prepares results for downstream processing (caching, optimization, profiling).

## Configuration Options
- `execution_mode`: Execution mode used (mock_only, real_only, both) [source: src/agent_discovery/result_processor.py]

## Classes and Enums
### ResultCategory
Result categorization based on execution outcome.

```python
class ResultCategory(Enum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"
```

### ErrorType
Classification of error types for analysis.

```python
class ErrorType(Enum):
    TIMEOUT = "timeout"
    PERMISSION = "permission"
    DEPENDENCY = "dependency"
    SYNTAX = "syntax"
    RUNTIME = "runtime"
    MEMORY = "memory"
    IO = "io"
    UNKNOWN = "unknown"
```

### ResultMetadata
Metadata extracted from execution result.

```python
@dataclass
class ResultMetadata:
    execution_time_ms: float
    output_size_bytes: int
    stdout_length: int
    stderr_length: int
    exit_code: int
    error_type: ErrorType | None = None
    has_stderr: bool = False
    is_timeout: bool = False
    is_real_execution: bool = True
    confidence_score: float = 0.5
    execution_mode: str = "real_only"
    extra_metadata: dict[str, Any] = field(default_factory=dict)
```

### EnhancedResult
Enhanced execution result with categorization and metadata.

```python
@dataclass
class EnhancedResult:
    ...
```

## Functions
- `_classify_error(output: str, exit_code: int) -> ErrorType | None`
Classify error type from output and exit code.

- `_categorize_result(result: OrchestratedResult, metadata: ResultMetadata) -> ResultCategory`
Categorize execution result.

- `_is_cacheable(result: OrchestratedResult, category: ResultCategory) -> bool`
Determine if result is safe to cache.

- `_extract_output(result: OrchestratedResult) -> str | None`
Extract primary output from result.

- `_generate_summary(result: OrchestratedResult) -> str`
Generate a summary of the execution result.

[source: src/agent_discovery/result_processor.py]
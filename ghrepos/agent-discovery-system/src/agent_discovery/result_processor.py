"""Result processor for enhancing and categorizing orchestrated execution results.

This module provides intelligent post-processing of execution results from the
orchestrator. It categorizes results into success/partial/failure states,
extracts metadata, and prepares results for downstream processing (caching,
optimization, profiling).

Features:
- Intelligent result categorization based on exit codes and output
- Metadata extraction (error types, output characteristics)
- Result enrichment with analysis data
- Preparation for caching and optimization
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from agent_discovery.orchestrator import OrchestratedResult
from agent_discovery.real_executor import ExecutionResult


class ResultCategory(Enum):
    """Result categorization based on execution outcome."""

    SUCCESS = "success"
    """Execution completed successfully with exit code 0."""

    PARTIAL_SUCCESS = "partial_success"
    """Execution completed with non-zero exit code but produced output."""

    FAILURE = "failure"
    """Execution failed with error output."""

    TIMEOUT = "timeout"
    """Execution timed out."""

    ERROR = "error"
    """Execution encountered fatal error."""


class ErrorType(Enum):
    """Classification of error types for analysis."""

    TIMEOUT = "timeout"
    """Execution exceeded timeout limit."""

    PERMISSION = "permission"
    """Permission denied error."""

    DEPENDENCY = "dependency"
    """Missing dependency or import error."""

    SYNTAX = "syntax"
    """Syntax error in code."""

    RUNTIME = "runtime"
    """Runtime error during execution."""

    MEMORY = "memory"
    """Out of memory error."""

    IO = "io"
    """Input/output error."""

    UNKNOWN = "unknown"
    """Unknown error type."""


@dataclass
class ResultMetadata:
    """Metadata extracted from execution result."""

    execution_time_ms: float
    """Total execution time in milliseconds."""

    output_size_bytes: int
    """Total output size in bytes."""

    stdout_length: int
    """Length of stdout in characters."""

    stderr_length: int
    """Length of stderr in characters."""

    exit_code: int
    """Exit code from execution."""

    error_type: ErrorType | None = None
    """Classified error type if applicable."""

    has_stderr: bool = False
    """Whether execution produced stderr output."""

    is_timeout: bool = False
    """Whether execution timed out."""

    is_real_execution: bool = True
    """Whether result is from real (vs mock) execution."""

    confidence_score: float = 0.5
    """Code quality confidence score from orchestrator."""

    execution_mode: str = "real_only"
    """Execution mode used (mock_only, real_only, both)."""

    extra_metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata from orchestrator."""


@dataclass
class EnhancedResult:
    """Enhanced execution result with categorization and metadata.

    This class wraps an OrchestratedResult and adds intelligent categorization,
    extracted metadata, and enriched analysis data for downstream processing.
    """

    orchestrated_result: OrchestratedResult
    """Original orchestrated execution result."""

    category: ResultCategory
    """Categorized result status."""

    metadata: ResultMetadata
    """Extracted metadata from execution."""

    is_cacheable: bool
    """Whether result can be safely cached."""

    summary: str
    """Human-readable summary of execution result."""

    primary_output: str | None = None
    """Primary output from execution."""

    is_successful: bool = field(default=False, init=False)
    """Whether execution was successful."""

    def __post_init__(self) -> None:
        """Post-initialization setup."""
        self.is_successful = self.category == ResultCategory.SUCCESS


class ResultProcessor:
    """Process and enhance orchestrated execution results.

    The ResultProcessor takes OrchestratedResult objects and enriches them with
    intelligent categorization, metadata extraction, and analysis data.
    This prepares results for caching, optimization, and profiling.
    """

    def __init__(self) -> None:
        """Initialize result processor."""
        self.timeout_keywords = [
            "timeout",
            "timed out",
            "deadline exceeded",
            "killed",
        ]
        self.permission_keywords = [
            "permission denied",
            "access denied",
            "unauthorized",
        ]
        self.dependency_keywords = [
            "importerror",
            "modulenotfounderror",
            "no module",
            "cannot import",
        ]
        self.syntax_keywords = ["syntaxerror", "invalid syntax", "unexpected"]
        self.memory_keywords = ["memoryerror", "out of memory", "heap space"]

    def process(self, result: OrchestratedResult) -> EnhancedResult:
        """Process and enhance an orchestrated result.

        Args:
            result: OrchestratedResult to process

        Returns:
            EnhancedResult with categorization and metadata
        """
        # Extract metadata from result
        metadata = self._extract_metadata(result)

        # Categorize the result
        category = self._categorize_result(result, metadata)

        # Determine if result is cacheable
        is_cacheable = self._is_cacheable(result, category)

        # Extract primary output
        primary_output = self._extract_output(result)

        # Generate summary
        summary = self._generate_summary(category, metadata, result)

        return EnhancedResult(
            orchestrated_result=result,
            category=category,
            metadata=metadata,
            is_cacheable=is_cacheable,
            summary=summary,
            primary_output=primary_output,
        )

    def process_batch(self, results: list[OrchestratedResult]) -> list[EnhancedResult]:
        """Process multiple orchestrated results.

        Args:
            results: List of OrchestratedResult objects

        Returns:
            List of EnhancedResult objects
        """
        return [self.process(result) for result in results]

    def _extract_metadata(self, result: OrchestratedResult) -> ResultMetadata:
        """Extract metadata from orchestrated result.

        Args:
            result: OrchestratedResult to extract from

        Returns:
            ResultMetadata with extracted information
        """
        primary = result.primary_result

        # Handle both ExecutionResult and MockExecutionResult
        if isinstance(primary, ExecutionResult):
            execution_time_ms = primary.execution_time_ms
            output_size = primary.output_size
            stdout_length = len(primary.stdout)
            stderr_length = len(primary.stderr)
            exit_code = primary.exit_code
            has_stderr = len(primary.stderr) > 0
            error_type = self._classify_error(primary.stderr, exit_code)
        else:  # MockExecutionResult
            execution_time_ms = primary.execution_time_ms
            output_size = len(primary.stdout) + len(primary.stderr)
            stdout_length = len(primary.stdout)
            stderr_length = len(primary.stderr)
            exit_code = primary.exit_code
            has_stderr = len(primary.stderr) > 0
            error_output = primary.stderr if primary.stderr else primary.stdout
            error_type = self._classify_error(error_output, exit_code)

        is_timeout = error_type == ErrorType.TIMEOUT

        return ResultMetadata(
            execution_time_ms=execution_time_ms,
            output_size_bytes=output_size,
            stdout_length=stdout_length,
            stderr_length=stderr_length,
            exit_code=exit_code,
            error_type=error_type,
            has_stderr=has_stderr,
            is_timeout=is_timeout,
            is_real_execution=result.is_real_result(),
            confidence_score=result.confidence_score,
            execution_mode=result.execution_mode.value,
            extra_metadata=result.comparison_metadata,
        )

    def _classify_error(self, output: str, exit_code: int) -> ErrorType | None:
        """Classify error type from output and exit code.

        Args:
            output: Error output text
            exit_code: Process exit code

        Returns:
            ErrorType classification or None
        """
        if exit_code == 0:
            return None

        output_lower = output.lower()

        # Check for timeout
        for keyword in self.timeout_keywords:
            if keyword in output_lower:
                return ErrorType.TIMEOUT

        # Check for permission errors
        for keyword in self.permission_keywords:
            if keyword in output_lower:
                return ErrorType.PERMISSION

        # Check for dependency errors
        for keyword in self.dependency_keywords:
            if keyword in output_lower:
                return ErrorType.DEPENDENCY

        # Check for syntax errors
        for keyword in self.syntax_keywords:
            if keyword in output_lower:
                return ErrorType.SYNTAX

        # Check for memory errors
        for keyword in self.memory_keywords:
            if keyword in output_lower:
                return ErrorType.MEMORY

        # Check for IO errors
        if "io" in output_lower or "file" in output_lower:
            if "error" in output_lower:
                return ErrorType.IO

        # Default to runtime error
        return ErrorType.RUNTIME

    def _categorize_result(
        self, result: OrchestratedResult, metadata: ResultMetadata
    ) -> ResultCategory:
        """Categorize execution result.

        Args:
            result: OrchestratedResult to categorize
            metadata: Extracted metadata

        Returns:
            ResultCategory for the result
        """
        # Check for timeout
        if metadata.is_timeout:
            return ResultCategory.TIMEOUT

        # Success: exit code 0
        if metadata.exit_code == 0:
            return ResultCategory.SUCCESS

        # Has output but failed: partial success
        if metadata.stdout_length > 0 or metadata.stderr_length > 0:
            return ResultCategory.PARTIAL_SUCCESS

        # No output and failed: error
        if metadata.error_type in (
            ErrorType.SYNTAX,
            ErrorType.MEMORY,
            ErrorType.DEPENDENCY,
        ):
            return ResultCategory.ERROR

        # Default: failure
        return ResultCategory.FAILURE

    def _is_cacheable(self, result: OrchestratedResult, category: ResultCategory) -> bool:
        """Determine if result is safe to cache.

        Results are cacheable if:
        - Success: Always cacheable
        - Partial success: Cacheable (useful for analysis)
        - Timeout/Error/Failure: Not cacheable (may change on retry)

        Args:
            result: OrchestratedResult to evaluate
            category: Result category

        Returns:
            Whether result can be cached
        """
        if category in (ResultCategory.SUCCESS, ResultCategory.PARTIAL_SUCCESS):
            return True

        # Don't cache transient failures
        if category in (ResultCategory.TIMEOUT, ResultCategory.ERROR):
            return False

        return False

    def _extract_output(self, result: OrchestratedResult) -> str | None:
        """Extract primary output from result.

        Args:
            result: OrchestratedResult to extract from

        Returns:
            Primary output string or None
        """
        primary = result.primary_result

        if isinstance(primary, ExecutionResult):
            # Prefer stdout, fall back to stderr
            return primary.stdout if primary.stdout else primary.stderr
        else:  # MockExecutionResult
            return primary.stdout if primary.stdout else primary.stderr

    def _generate_summary(
        self,
        category: ResultCategory,
        metadata: ResultMetadata,
        result: OrchestratedResult,
    ) -> str:
        """Generate human-readable summary.

        Args:
            category: Result category
            metadata: Extracted metadata
            result: Orchestrated result

        Returns:
            Summary string
        """
        parts = []

        # Category summary
        parts.append(f"Status: {category.value.replace('_', ' ').title()}")

        # Exit code
        if metadata.exit_code != 0:
            parts.append(f"Exit code: {metadata.exit_code}")

        # Error type
        if metadata.error_type:
            parts.append(f"Error: {metadata.error_type.value}")

        # Execution time
        parts.append(f"Time: {metadata.execution_time_ms:.0f}ms")

        # Output size
        parts.append(f"Output: {metadata.output_size_bytes} bytes")

        # Execution mode
        parts.append(f"Mode: {metadata.execution_mode}")

        # Agreement if both modes were used
        if result.secondary_result is not None:
            agreement = result.results_agree()
            parts.append(f"Agreement: {agreement}")

        return " | ".join(parts)

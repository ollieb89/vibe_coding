"""Real agent execution with subprocess isolation and comprehensive metrics.

This module provides utilities for safely executing actual agent code with
process isolation, timeout enforcement, and detailed metrics collection.

Features:
- Subprocess-based execution for safety
- Configurable timeout with forceful termination
- Comprehensive metrics: execution time, memory, exit code, stdout/stderr
- Error categorization for analysis
- Support for Python and Shell agents
"""

import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExecutionResult:
    """Result of real agent execution."""

    success: bool
    """Whether execution completed successfully (exit code 0)."""

    exit_code: int
    """Process exit code (0 = success, non-zero = failure)."""

    stdout: str
    """Standard output from process."""

    stderr: str
    """Standard error output."""

    execution_time_ms: float
    """Total wall-clock execution time in milliseconds."""

    error_category: str | None = None
    """Error classification: timeout, permission, dependency, syntax, etc."""

    output_size: int = 0
    """Total size of stdout + stderr in bytes."""

    def __post_init__(self) -> None:
        """Calculate output size."""
        self.output_size = len(self.stdout) + len(self.stderr)


class RealExecutor:
    """Execute agent code safely with process isolation."""

    # Maximum output to capture (10 MB)
    MAX_OUTPUT_SIZE = 10 * 1024 * 1024

    # Supported agent extensions and their interpreters
    INTERPRETERS = {
        ".py": [sys.executable],  # Python agent
        ".sh": ["/bin/bash"],  # Shell agent
    }

    def __init__(self, timeout_seconds: int = 30, max_retries: int = 1):
        """Initialize real executor.

        Args:
            timeout_seconds: Maximum execution time (default 30s)
            max_retries: Number of retries on failure (default 1)
        """
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def execute_python(self, code: str) -> ExecutionResult:
        """Execute Python code.

        Args:
            code: Python code to execute

        Returns:
            ExecutionResult with metrics
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            return self._run_subprocess(
                [sys.executable, temp_file],
                timeout_seconds=self.timeout_seconds,
                cwd=None,
            )
        finally:
            try:
                os.unlink(temp_file)
            except OSError:
                pass  # File cleanup failure is non-critical

    def execute_shell(self, script: str) -> ExecutionResult:
        """Execute shell script.

        Args:
            script: Shell script to execute

        Returns:
            ExecutionResult with metrics
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sh", delete=False, encoding="utf-8"
        ) as f:
            f.write(script)
            temp_file = f.name

        try:
            return self._run_subprocess(
                ["/bin/bash", temp_file],
                timeout_seconds=self.timeout_seconds,
                cwd=None,
            )
        finally:
            try:
                os.unlink(temp_file)
            except OSError:
                pass

    def execute_file(self, file_path: str) -> ExecutionResult:
        """Execute agent code from file.

        Args:
            file_path: Path to agent file

        Returns:
            ExecutionResult with metrics
        """
        path = Path(file_path)

        if not path.exists():
            return ExecutionResult(
                success=False,
                exit_code=127,
                stdout="",
                stderr=f"File not found: {file_path}",
                execution_time_ms=0,
                error_category="file_not_found",
            )

        suffix = path.suffix.lower()

        if suffix == ".py":
            return self.execute_python(path.read_text(encoding="utf-8"))
        elif suffix == ".sh":
            return self.execute_shell(path.read_text(encoding="utf-8"))
        else:
            return ExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr=f"Unsupported file type: {suffix}",
                execution_time_ms=0,
                error_category="unsupported_type",
            )

    def _run_subprocess(
        self, cmd: list[str], timeout_seconds: int, cwd: str | None = None
    ) -> ExecutionResult:
        """Run command in subprocess with timeout.

        Args:
            cmd: Command and arguments
            timeout_seconds: Timeout in seconds
            cwd: Working directory (None = current)

        Returns:
            ExecutionResult with output and metrics
        """
        start_time = time.time()

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            try:
                stdout, stderr = process.communicate(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                # Process exceeded timeout - terminate forcefully
                process.kill()
                try:
                    stdout, stderr = process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    # Still not dead after 5s, it's a zombie
                    stdout, stderr = "", f"Process killed after timeout of {timeout_seconds}s"

                execution_time_ms = (time.time() - start_time) * 1000

                return ExecutionResult(
                    success=False,
                    exit_code=-1,
                    stdout=stdout[: self.MAX_OUTPUT_SIZE],
                    stderr=stderr[: self.MAX_OUTPUT_SIZE],
                    execution_time_ms=execution_time_ms,
                    error_category="timeout",
                )

            execution_time_ms = (time.time() - start_time) * 1000

            # Check for success
            success = process.returncode == 0

            return ExecutionResult(
                success=success,
                exit_code=process.returncode,
                stdout=stdout[: self.MAX_OUTPUT_SIZE],
                stderr=stderr[: self.MAX_OUTPUT_SIZE],
                execution_time_ms=execution_time_ms,
                error_category=None if success else _categorize_error(stderr),
            )

        except PermissionError as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr=str(e),
                execution_time_ms=execution_time_ms,
                error_category="permission_denied",
            )

        except FileNotFoundError as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                success=False,
                exit_code=127,
                stdout="",
                stderr=str(e),
                execution_time_ms=execution_time_ms,
                error_category="file_not_found",
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr=str(e),
                execution_time_ms=execution_time_ms,
                error_category="unknown_error",
            )


def _categorize_error(stderr: str) -> str | None:
    """Categorize error from stderr output.

    Args:
        stderr: Standard error output

    Returns:
        Error category string or None if no error detected
    """
    stderr_lower = stderr.lower()

    if "modulenotfounderror" in stderr_lower or "importerror" in stderr_lower:
        return "missing_dependency"
    elif "syntaxerror" in stderr_lower:
        return "syntax_error"
    elif "typeerror" in stderr_lower or "attributeerror" in stderr_lower:
        return "runtime_error"
    elif "permission denied" in stderr_lower:
        return "permission_denied"
    elif "not found" in stderr_lower or "command not found" in stderr_lower:
        return "file_not_found"
    elif stderr_lower.startswith("env:") or "no such file" in stderr_lower:
        return "environment_error"
    else:
        return "execution_error"

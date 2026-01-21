"""Structured logging and metrics collection for execution orchestration."""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class LogLevel(Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """Individual log entry with context."""

    timestamp: str
    level: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)
    source: str = "ExecutionOrchestrator"
    duration_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class ExecutionStats:
    """Aggregated execution statistics."""

    total_executions: int = 0
    successful: int = 0
    failed: int = 0
    mock_only: int = 0
    real_only: int = 0
    both_executors: int = 0
    agreements: int = 0
    disagreements: int = 0
    avg_confidence: float = 0.0
    avg_duration_ms: float = 0.0
    error_categories: dict[str, int] = field(default_factory=dict)

    def update_confidence(self, new_confidence: float, total_count: int) -> None:
        """Update running average confidence."""
        if total_count > 0:
            self.avg_confidence = (
                self.avg_confidence * (total_count - 1) + new_confidence
            ) / total_count

    def update_duration(self, duration_ms: float, total_count: int) -> None:
        """Update running average duration."""
        if total_count > 0:
            self.avg_duration_ms = (
                self.avg_duration_ms * (total_count - 1) + duration_ms
            ) / total_count


class ExecutionLogger:
    """Structured logging with context tracking for execution orchestration."""

    def __init__(
        self,
        name: str = "ExecutionOrchestrator",
        log_file: Path | None = None,
        verbose: bool = False,
    ) -> None:
        """Initialize logger.

        Args:
            name: Logger name/source identifier
            log_file: Optional file path for persistent logging
            verbose: If True, print all logs to stdout
        """
        self.name = name
        self.log_file = log_file
        self.verbose = verbose
        self.logs: list[LogEntry] = []
        self._context_stack: list[dict[str, Any]] = []

    def push_context(self, context: dict[str, Any]) -> None:
        """Push context onto stack for nested operations.

        Args:
            context: Context dictionary to push
        """
        self._context_stack.append(context)

    def pop_context(self) -> dict[str, Any] | None:
        """Pop context from stack.

        Returns:
            Popped context or None if stack empty
        """
        return self._context_stack.pop() if self._context_stack else None

    def _get_current_context(self) -> dict[str, Any]:
        """Get merged context from all stack levels.

        Returns:
            Merged context dictionary
        """
        merged = {}
        for ctx in self._context_stack:
            merged.update(ctx)
        return merged

    def _log(
        self,
        level: LogLevel,
        message: str,
        context: dict[str, Any] | None = None,
        duration_ms: float | None = None,
    ) -> None:
        """Internal logging method.

        Args:
            level: Log level
            message: Log message
            context: Additional context
            duration_ms: Optional duration in milliseconds
        """
        merged_context = self._get_current_context()
        if context:
            merged_context.update(context)

        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level.value,
            message=message,
            context=merged_context,
            source=self.name,
            duration_ms=duration_ms,
        )

        self.logs.append(entry)

        if self.verbose:
            ctx_str = f" | {json.dumps(merged_context)}" if merged_context else ""
            duration_str = f" ({duration_ms:.2f}ms)" if duration_ms is not None else ""
            print(f"[{entry.timestamp}] {level.value} | {message}{ctx_str}{duration_str}")

        if self.log_file:
            self._write_to_file(entry)

    def debug(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, context)

    def info(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log info message."""
        self._log(LogLevel.INFO, message, context)

    def warning(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log warning message."""
        self._log(LogLevel.WARNING, message, context)

    def error(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log error message."""
        self._log(LogLevel.ERROR, message, context)

    def critical(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message, context)

    def log_execution(
        self,
        code_snippet: str,
        result: Any,
        duration_ms: float,
        executor_type: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Log execution result.

        Args:
            code_snippet: The code that was executed
            result: Execution result
            duration_ms: Execution duration
            executor_type: Type of executor used (mock, real, orchestrated)
            context: Additional context
        """
        exec_context = {
            "executor_type": executor_type,
            "code_length": len(code_snippet),
            "result_type": type(result).__name__,
        }
        if context:
            exec_context.update(context)

        self._log(
            LogLevel.INFO,
            f"Execution completed via {executor_type}",
            exec_context,
            duration_ms,
        )

    def log_routing_decision(
        self,
        confidence: float,
        decision: str,
        reason: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Log routing decision.

        Args:
            confidence: Confidence score
            decision: Decision made (mock_only, real_only, both)
            reason: Reasoning for decision
            context: Additional context
        """
        routing_context = {
            "confidence": confidence,
            "decision": decision,
            "reason": reason,
        }
        if context:
            routing_context.update(context)

        self.info("Routing decision made", routing_context)

    def log_validation(
        self,
        is_valid: bool,
        confidence: float,
        issues: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Log validation result.

        Args:
            is_valid: Whether validation passed
            confidence: Confidence score
            issues: List of validation issues if any
            context: Additional context
        """
        validation_context = {
            "is_valid": is_valid,
            "confidence": confidence,
            "issue_count": len(issues) if issues else 0,
        }
        if context:
            validation_context.update(context)

        level = LogLevel.INFO if is_valid else LogLevel.WARNING
        self._log(level, "Code validation completed", validation_context)

    def _write_to_file(self, entry: LogEntry) -> None:
        """Write log entry to file.

        Args:
            entry: Log entry to write
        """
        if not self.log_file:
            return
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, "a") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")
        except OSError as e:
            print(f"Warning: Failed to write log to file: {e}")

    def get_logs(self, level: LogLevel | None = None) -> list[LogEntry]:
        """Get logs filtered by level.

        Args:
            level: Optional level to filter by

        Returns:
            Filtered list of log entries
        """
        if level is None:
            return self.logs.copy()
        return [log for log in self.logs if log.level == level.value]

    def export_logs(self, format_type: str = "json") -> str:
        """Export logs in specified format.

        Args:
            format_type: 'json' or 'text'

        Returns:
            Formatted log output
        """
        if format_type == "json":
            return json.dumps([log.to_dict() for log in self.logs], indent=2)
        else:  # text
            lines = []
            for log in self.logs:
                ctx_str = f" | {json.dumps(log.context)}" if log.context else ""
                duration_str = f" ({log.duration_ms:.2f}ms)" if log.duration_ms else ""
                lines.append(
                    f"[{log.timestamp}] {log.level} | {log.message}{ctx_str}{duration_str}"
                )
            return "\n".join(lines)

    def clear(self) -> None:
        """Clear all logs."""
        self.logs.clear()
        self._context_stack.clear()


class MetricsCollector:
    """Collects and aggregates metrics from execution orchestration."""

    def __init__(self, logger: ExecutionLogger | None = None) -> None:
        """Initialize metrics collector.

        Args:
            logger: Optional ExecutionLogger for recording metric events
        """
        self.logger = logger
        self.stats = ExecutionStats()
        self._timings: dict[str, list[float]] = {}
        self._execution_history: list[dict[str, Any]] = []

    def record_execution(
        self,
        executor_type: str,
        success: bool,
        duration_ms: float,
        error_category: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record execution metrics.

        Args:
            executor_type: Type of executor (mock, real, orchestrated)
            success: Whether execution succeeded
            duration_ms: Duration in milliseconds
            error_category: Optional error category
            metadata: Optional additional metadata
        """
        self.stats.total_executions += 1

        if success:
            self.stats.successful += 1
        else:
            self.stats.failed += 1
            if error_category:
                self.stats.error_categories[error_category] = (
                    self.stats.error_categories.get(error_category, 0) + 1
                )

        if executor_type == "mock":
            self.stats.mock_only += 1
        elif executor_type == "real":
            self.stats.real_only += 1
        elif executor_type == "both":
            self.stats.both_executors += 1

        self._record_timing(executor_type, duration_ms)
        self.stats.update_duration(duration_ms, self.stats.total_executions)

        record = {
            "timestamp": datetime.now().isoformat(),
            "executor_type": executor_type,
            "success": success,
            "duration_ms": duration_ms,
            "error_category": error_category,
        }
        if metadata:
            record.update(metadata)
        self._execution_history.append(record)

        if self.logger:
            self.logger.debug(
                f"Metrics recorded for {executor_type} execution",
                {"success": success, "duration_ms": duration_ms},
            )

    def record_routing_decision(
        self, confidence: float, decision: str, agreement: bool | None = None
    ) -> None:
        """Record routing decision metrics.

        Args:
            confidence: Confidence score
            decision: Routing decision
            agreement: Optional boolean indicating if results agreed
        """
        self.stats.update_confidence(confidence, self.stats.total_executions)

        if agreement is True:
            self.stats.agreements += 1
        elif agreement is False:
            self.stats.disagreements += 1

        if self.logger:
            self.logger.debug(
                "Routing decision recorded",
                {"confidence": confidence, "decision": decision},
            )

    def record_validation(self, confidence: float) -> None:
        """Record validation metrics.

        Args:
            confidence: Validation confidence score
        """
        self.stats.update_confidence(confidence, self.stats.total_executions)

        if self.logger:
            self.logger.debug("Validation recorded", {"confidence": confidence})

    def _record_timing(self, executor_type: str, duration_ms: float) -> None:
        """Record timing for executor type.

        Args:
            executor_type: Type of executor
            duration_ms: Duration in milliseconds
        """
        if executor_type not in self._timings:
            self._timings[executor_type] = []
        self._timings[executor_type].append(duration_ms)

    def get_timing_stats(self, executor_type: str) -> dict[str, float]:
        """Get timing statistics for executor type.

        Args:
            executor_type: Type of executor

        Returns:
            Dictionary with min, max, avg, total statistics
        """
        if executor_type not in self._timings or not self._timings[executor_type]:
            return {"min": 0, "max": 0, "avg": 0, "total": 0, "count": 0}

        timings = self._timings[executor_type]
        return {
            "min": min(timings),
            "max": max(timings),
            "avg": sum(timings) / len(timings),
            "total": sum(timings),
            "count": len(timings),
        }

    def get_stats_summary(self) -> dict[str, Any]:
        """Get summary of all statistics.

        Returns:
            Dictionary with current statistics
        """
        return {
            "total_executions": self.stats.total_executions,
            "successful": self.stats.successful,
            "failed": self.stats.failed,
            "success_rate": (
                self.stats.successful / self.stats.total_executions
                if self.stats.total_executions > 0
                else 0.0
            ),
            "routing_distribution": {
                "mock_only": self.stats.mock_only,
                "real_only": self.stats.real_only,
                "both_executors": self.stats.both_executors,
            },
            "agreement_metrics": {
                "agreements": self.stats.agreements,
                "disagreements": self.stats.disagreements,
                "agreement_rate": (
                    self.stats.agreements / (self.stats.agreements + self.stats.disagreements)
                    if (self.stats.agreements + self.stats.disagreements) > 0
                    else 0.0
                ),
            },
            "performance": {
                "avg_confidence": self.stats.avg_confidence,
                "avg_duration_ms": self.stats.avg_duration_ms,
                "mock_timings": self.get_timing_stats("mock"),
                "real_timings": self.get_timing_stats("real"),
            },
            "errors": {
                "categories": self.stats.error_categories,
                "total_errors": self.stats.failed,
            },
        }

    def export_metrics(self, format_type: str = "json") -> str:
        """Export metrics in specified format.

        Args:
            format_type: 'json' or 'text'

        Returns:
            Formatted metrics output
        """
        summary = self.get_stats_summary()

        if format_type == "json":
            return json.dumps(summary, indent=2)
        else:  # text
            lines = [
                "=== Execution Metrics Summary ===",
                f"Total Executions: {summary['total_executions']}",
                f"Successful: {summary['successful']}",
                f"Failed: {summary['failed']}",
                f"Success Rate: {summary['success_rate']:.2%}",
                "",
                "=== Routing Distribution ===",
                f"Mock Only: {summary['routing_distribution']['mock_only']}",
                f"Real Only: {summary['routing_distribution']['real_only']}",
                f"Both Executors: {summary['routing_distribution']['both_executors']}",
                "",
                "=== Agreement Metrics ===",
                f"Agreements: {summary['agreement_metrics']['agreements']}",
                f"Disagreements: {summary['agreement_metrics']['disagreements']}",
                f"Agreement Rate: {summary['agreement_metrics']['agreement_rate']:.2%}",
                "",
                "=== Performance ===",
                f"Avg Confidence: {summary['performance']['avg_confidence']:.4f}",
                f"Avg Duration: {summary['performance']['avg_duration_ms']:.2f}ms",
                "",
                "=== Error Categories ===",
            ]

            for category, count in summary["errors"]["categories"].items():
                lines.append(f"{category}: {count}")

            return "\n".join(lines)

    def get_execution_history(self) -> list[dict[str, Any]]:
        """Get complete execution history.

        Returns:
            List of execution records
        """
        return self._execution_history.copy()

    def clear(self) -> None:
        """Clear all metrics and history."""
        self.stats = ExecutionStats()
        self._timings.clear()
        self._execution_history.clear()

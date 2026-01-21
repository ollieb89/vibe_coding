"""Execution analyzer for metrics extraction and pattern analysis.

This module provides the ExecutionAnalyzer class for analyzing execution
results, extracting metrics, and identifying patterns across multiple
executions.

Features:
- Single result analysis
- Batch analysis and aggregation
- Error pattern detection
- Performance metrics
- Confidence correlation
"""

from dataclasses import dataclass, field
from typing import Any

from agent_discovery.mock_executor import MockExecutionResult
from agent_discovery.real_executor import ExecutionResult


@dataclass
class ExecutionMetrics:
    """Metrics from execution analysis."""

    total_executions: int
    """Total number of executions analyzed."""

    successful_executions: int
    """Number of successful executions."""

    failed_executions: int
    """Number of failed executions."""

    success_rate: float
    """Success rate (0-1)."""

    average_execution_time_ms: float
    """Average execution time in milliseconds."""

    min_execution_time_ms: float
    """Minimum execution time."""

    max_execution_time_ms: float
    """Maximum execution time."""

    error_categories: dict[str, int] = field(default_factory=dict)
    """Count of errors by category."""

    average_output_size: int = 0
    """Average output size in bytes."""

    confidence_distribution: dict[str, int] = field(default_factory=dict)
    """Distribution of confidence scores."""


@dataclass
class AnalysisReport:
    """Report from execution analysis."""

    metrics: ExecutionMetrics
    """Calculated metrics."""

    patterns: dict[str, Any] = field(default_factory=dict)
    """Detected patterns."""

    insights: list[str] = field(default_factory=list)
    """Key insights from analysis."""

    recommendations: list[str] = field(default_factory=list)
    """Recommendations based on analysis."""


class ExecutionAnalyzer:
    """Analyzes execution results and extracts metrics.

    The ExecutionAnalyzer processes individual and batched execution results
    to extract metrics, identify patterns, and generate insights for system
    optimization and Phase 4 integration.

    Example:
        >>> analyzer = ExecutionAnalyzer()
        >>> report = analyzer.analyze_batch(results)
        >>> print(f"Success rate: {report.metrics.success_rate:.1%}")
    """

    def __init__(self) -> None:
        """Initialize analyzer."""
        pass

    def analyze_result(self, result: ExecutionResult | MockExecutionResult) -> dict[str, Any]:
        """Analyze single execution result.

        Args:
            result: Execution result to analyze

        Returns:
            Dictionary with analysis data
        """
        is_mock = isinstance(result, MockExecutionResult)

        return {
            "is_mock": is_mock,
            "success": result.success,
            "exit_code": getattr(result, "exit_code", None),
            "execution_time_ms": (
                result.execution_time_ms if hasattr(result, "execution_time_ms") else None
            ),
            "error_category": result.error_category,
            "output_size": len(result.stdout) + len(result.stderr),
            "stderr_length": len(result.stderr),
            "stdout_length": len(result.stdout),
            "has_error": bool(result.stderr),
        }

    def analyze_batch(
        self,
        results: list[ExecutionResult | MockExecutionResult],
        confidence_scores: list[float] | None = None,
    ) -> AnalysisReport:
        """Analyze batch of execution results.

        Args:
            results: List of execution results
            confidence_scores: Optional confidence scores for each result

        Returns:
            AnalysisReport with metrics and insights
        """
        if not results:
            return AnalysisReport(
                metrics=ExecutionMetrics(
                    total_executions=0,
                    successful_executions=0,
                    failed_executions=0,
                    success_rate=0.0,
                    average_execution_time_ms=0.0,
                    min_execution_time_ms=0.0,
                    max_execution_time_ms=0.0,
                ),
                insights=["No executions to analyze"],
            )

        # Analyze individual results
        analyses = [self.analyze_result(r) for r in results]

        # Calculate metrics
        successful = sum(1 for a in analyses if a["success"])
        failed = len(analyses) - successful

        execution_times = [
            a["execution_time_ms"] for a in analyses if a["execution_time_ms"] is not None
        ]
        avg_time = sum(execution_times) / len(execution_times) if execution_times else 0.0
        min_time = min(execution_times) if execution_times else 0.0
        max_time = max(execution_times) if execution_times else 0.0

        error_categories = {}
        for analysis in analyses:
            if analysis["error_category"]:
                error_categories[analysis["error_category"]] = (
                    error_categories.get(analysis["error_category"], 0) + 1
                )

        avg_output_size = sum(a["output_size"] for a in analyses) // len(analyses)

        # Distribution of confidence (if provided)
        confidence_dist = {}
        if confidence_scores:
            for score in confidence_scores:
                bucket = int(score * 10) / 10  # 0.0-0.1, 0.1-0.2, etc.
                key = f"{bucket:.1f}"
                confidence_dist[key] = confidence_dist.get(key, 0) + 1

        metrics = ExecutionMetrics(
            total_executions=len(analyses),
            successful_executions=successful,
            failed_executions=failed,
            success_rate=successful / len(analyses),
            average_execution_time_ms=avg_time,
            min_execution_time_ms=min_time,
            max_execution_time_ms=max_time,
            error_categories=error_categories,
            average_output_size=avg_output_size,
            confidence_distribution=confidence_dist,
        )

        # Generate patterns
        patterns = self._detect_patterns(analyses, metrics)

        # Generate insights
        insights = self._generate_insights(metrics, patterns)

        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, patterns)

        return AnalysisReport(
            metrics=metrics,
            patterns=patterns,
            insights=insights,
            recommendations=recommendations,
        )

    def _detect_patterns(
        self, analyses: list[dict[str, Any]], metrics: ExecutionMetrics
    ) -> dict[str, Any]:
        """Detect patterns in execution results.

        Args:
            analyses: List of analyzed results
            metrics: Calculated metrics

        Returns:
            Dictionary of detected patterns
        """
        mock_count = sum(1 for a in analyses if a["is_mock"])
        real_count = len(analyses) - mock_count

        return {
            "mock_ratio": mock_count / len(analyses) if analyses else 0.0,
            "real_ratio": real_count / len(analyses) if analyses else 0.0,
            "has_errors": metrics.failed_executions > 0,
            "dominant_error": (
                max(
                    metrics.error_categories.items(),
                    key=lambda x: x[1],
                )[0]
                if metrics.error_categories
                else None
            ),
            "execution_time_stable": (
                (metrics.max_execution_time_ms - metrics.min_execution_time_ms)
                < metrics.average_execution_time_ms * 0.5
            ),
        }

    def _generate_insights(self, metrics: ExecutionMetrics, patterns: dict[str, Any]) -> list[str]:
        """Generate insights from metrics.

        Args:
            metrics: Execution metrics
            patterns: Detected patterns

        Returns:
            List of insight strings
        """
        insights = []

        if metrics.success_rate > 0.9:
            insights.append("Excellent success rate (>90%)")
        elif metrics.success_rate > 0.7:
            insights.append("Good success rate (>70%)")
        elif metrics.success_rate < 0.5:
            insights.append("Low success rate (<50%) - investigate issues")

        if patterns["execution_time_stable"]:
            insights.append("Execution time is stable and predictable")
        else:
            insights.append("Execution time shows high variability")

        if patterns["dominant_error"]:
            insights.append(f"Most common error: {patterns['dominant_error']}")

        if patterns["mock_ratio"] > 0.7:
            insights.append("Mostly mock executions - consider higher confidence")
        elif patterns["real_ratio"] > 0.7:
            insights.append("Mostly real executions - good confidence levels")

        return insights

    def _generate_recommendations(
        self, metrics: ExecutionMetrics, patterns: dict[str, Any]
    ) -> list[str]:
        """Generate recommendations.

        Args:
            metrics: Execution metrics
            patterns: Detected patterns

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if metrics.success_rate < 0.5:
            recommendations.append("Reduce confidence thresholds or improve code validation")

        if patterns["dominant_error"]:
            recommendations.append(f"Address {patterns['dominant_error']} errors")

        if metrics.average_execution_time_ms > 5000:
            recommendations.append("Consider increasing timeout thresholds")

        if len(metrics.error_categories) > 3:
            recommendations.append("Multiple error types detected - improve error handling")

        return recommendations

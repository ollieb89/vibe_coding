"""Optimization engine for analyzing patterns and generating recommendations.

This module provides intelligent analysis of execution metrics and patterns,
generating actionable optimization recommendations for improving code execution
performance and reducing overhead.

Features:
- Pattern analysis from historical metrics
- Timing trend detection
- Error pattern identification
- Confidence-based recommendations
- Routing adjustment suggestions
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from agent_discovery.analyzer import AnalysisReport
from agent_discovery.logging import MetricsCollector


class OptimizationStrategy(Enum):
    """Types of optimization strategies."""

    CACHE_AGGRESSIVE = "cache_aggressive"
    """Use aggressive caching for frequently executed patterns."""

    CACHE_CONSERVATIVE = "cache_conservative"
    """Use conservative caching only for high-confidence results."""

    ROUTING_REAL_ONLY = "routing_real_only"
    """Skip mock execution for high-confidence code."""

    ROUTING_BOTH = "routing_both"
    """Always use both executors for validation."""

    SPLIT_EXECUTION = "split_execution"
    """Split execution into smaller, more manageable chunks."""

    PROFILE_HEAVY = "profile_heavy"
    """Profile heavily to identify performance bottlenecks."""

    RETRY_AGGRESSIVE = "retry_aggressive"
    """Retry failed executions more aggressively."""


@dataclass
class PatternAnalysis:
    """Analysis of execution patterns from metrics."""

    success_rate: float
    """Percentage of successful executions (0-1)."""

    average_execution_time_ms: float
    """Average execution time in milliseconds."""

    min_execution_time_ms: float
    """Minimum observed execution time."""

    max_execution_time_ms: float
    """Maximum observed execution time."""

    timeout_rate: float
    """Percentage of timeouts (0-1)."""

    error_rate: float
    """Percentage of errors (0-1)."""

    agreement_rate: float | None = None
    """Rate at which mock and real results agree (if applicable)."""

    most_common_error: str | None = None
    """Most frequently occurring error type."""

    execution_count: int = 0
    """Number of executions analyzed."""

    timing_trend: str = "stable"
    """Trend: 'improving', 'degrading', or 'stable'."""

    volatility: float = 0.0
    """Coefficient of variation for execution time."""


@dataclass
class OptimizationRecommendation:
    """Recommended optimization action."""

    strategy: OptimizationStrategy
    """Type of optimization strategy."""

    description: str
    """Human-readable description of recommendation."""

    expected_benefit: str
    """Expected benefit (e.g., '20% faster', '40% fewer timeouts')."""

    confidence: float
    """Confidence in recommendation (0-1)."""

    reason: str
    """Detailed reason for recommendation."""

    parameters: dict[str, Any] = field(default_factory=dict)
    """Optional parameters for strategy implementation."""

    priority: int = 5
    """Priority level (1=highest, 10=lowest)."""

    def __lt__(self, other: "OptimizationRecommendation") -> bool:
        """Enable sorting by priority."""
        return self.priority < other.priority


class OptimizationEngine:
    """Generate optimization recommendations based on execution patterns.

    The OptimizationEngine analyzes historical metrics and patterns to
    generate intelligent recommendations for optimizing code execution,
    reducing overhead, and improving reliability.
    """

    def __init__(self) -> None:
        """Initialize optimization engine."""
        self.min_samples_for_pattern = 5
        self.timeout_threshold = 5000  # milliseconds
        self.volatility_threshold = 0.3

    def analyze_patterns(self, collector: MetricsCollector) -> PatternAnalysis | None:
        """Analyze execution patterns from metrics collector.

        Args:
            collector: MetricsCollector with historical metrics

        Returns:
            PatternAnalysis or None if insufficient data
        """
        summary = collector.get_stats_summary()

        execution_count = summary.get("total_executions", 0)
        if execution_count < self.min_samples_for_pattern:
            return None

        # Extract basic statistics
        success_rate = summary.get("success_rate", 0.0)
        error_rate = 1.0 - success_rate

        # Get timing statistics
        perf_data = summary.get("performance", {})
        real_timings = perf_data.get("real_timings", {})

        avg_time = real_timings.get("avg", 0.0)
        min_time = real_timings.get("min", 0.0)
        max_time = real_timings.get("max", 0.0)

        # Get timing history for volatility calculation
        timings_list = collector._timings.get("real", [])
        if timings_list and len(timings_list) > 0:
            variance = sum((t - avg_time) ** 2 for t in timings_list) / len(timings_list)
            std_dev = variance**0.5
            volatility = std_dev / avg_time if avg_time > 0 else 0.0
        else:
            volatility = 0.0

        # Calculate timeout rate
        timeout_count = sum(1 for t in timings_list if t > self.timeout_threshold)
        timeout_rate = timeout_count / len(timings_list) if timings_list else 0.0

        # Detect timing trend
        if len(timings_list) >= 3:
            early = sum(timings_list[:2]) / 2
            late = sum(timings_list[-2:]) / 2
            if late < early * 0.9:
                timing_trend = "improving"
            elif late > early * 1.1:
                timing_trend = "degrading"
            else:
                timing_trend = "stable"
        else:
            timing_trend = "stable"

        # Get agreement rate if available
        agreement_metrics = summary.get("agreement_metrics", {})
        agreement_rate = agreement_metrics.get("agreement_rate", None)

        # Get most common error
        error_data = summary.get("errors", {})
        error_categories = error_data.get("categories", {})
        most_common_error = (
            max(error_categories, key=error_categories.get) if error_categories else None
        )

        return PatternAnalysis(
            success_rate=success_rate,
            average_execution_time_ms=avg_time,
            min_execution_time_ms=min_time,
            max_execution_time_ms=max_time,
            timeout_rate=timeout_rate,
            error_rate=error_rate,
            agreement_rate=agreement_rate,
            most_common_error=most_common_error,
            execution_count=execution_count,
            timing_trend=timing_trend,
            volatility=volatility,
        )

    def generate_recommendations(
        self,
        pattern: PatternAnalysis,
        analysis: AnalysisReport | None = None,
    ) -> list[OptimizationRecommendation]:
        """Generate optimization recommendations based on patterns.

        Args:
            pattern: PatternAnalysis to analyze
            analysis: Optional AnalysisReport for additional context

        Returns:
            List of OptimizationRecommendation sorted by priority
        """
        recommendations: list[OptimizationRecommendation] = []

        # High timeout rate: aggressive caching
        if pattern.timeout_rate > 0.3:
            timeout_reason = (
                f"Timeout rate is {pattern.timeout_rate:.1%}, "
                "indicating patterns suitable for caching"
            )
            recommendations.append(
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.CACHE_AGGRESSIVE,
                    description="Enable aggressive caching for timed-out operations",
                    expected_benefit=f"Reduce timeouts by {int(pattern.timeout_rate * 100)}%",
                    confidence=0.85,
                    reason=timeout_reason,
                    parameters={"ttl_seconds": 3600, "max_size": 1000},
                    priority=1,
                )
            )

        # High success rate: skip mock validation
        if pattern.success_rate > 0.9 and pattern.agreement_rate and pattern.agreement_rate > 0.95:
            success_reason = (
                f"Success rate is {pattern.success_rate:.1%} with "
                f"{pattern.agreement_rate:.1%} agreement"
            )
            recommendations.append(
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.ROUTING_REAL_ONLY,
                    description="Skip mock validation for highly reliable patterns",
                    expected_benefit="50% reduction in execution overhead",
                    confidence=0.9,
                    reason=success_reason,
                    parameters={"confidence_threshold": 0.85},
                    priority=2,
                )
            )

        # High volatility: profile execution
        if pattern.volatility > self.volatility_threshold:
            volatility_reason = (
                f"Execution time volatility is {pattern.volatility:.2f}, "
                "indicating inconsistent performance"
            )
            recommendations.append(
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.PROFILE_HEAVY,
                    description="Enable heavy profiling to identify bottlenecks",
                    expected_benefit="Identify and fix 40-60% of performance issues",
                    confidence=0.75,
                    reason=volatility_reason,
                    parameters={"sample_rate": 0.5, "trace_enabled": True},
                    priority=3,
                )
            )

        # Degrading performance: split execution
        if pattern.timing_trend == "degrading":
            recommendations.append(
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.SPLIT_EXECUTION,
                    description="Split complex operations into smaller tasks",
                    expected_benefit="30-50% performance improvement",
                    confidence=0.7,
                    reason="Execution times are degrading, suggesting accumulating overhead",
                    parameters={"max_chunk_size": 1000, "parallel_enabled": False},
                    priority=4,
                )
            )

        # High error rate: retry strategy
        if pattern.error_rate > 0.2 and pattern.error_rate < 0.5:
            recovery_pct = int(pattern.error_rate * 100 * 0.4)
            error_reason = (
                f"Error rate is {pattern.error_rate:.1%}, " "suggesting transient failures"
            )
            recommendations.append(
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.RETRY_AGGRESSIVE,
                    description="Implement more aggressive retry logic",
                    expected_benefit=f"Recover {recovery_pct}% of failed executions",
                    confidence=0.65,
                    reason=error_reason,
                    parameters={"max_retries": 3, "backoff_factor": 2.0},
                    priority=5,
                )
            )

        # Always recommend: conservative caching
        cache_reason = "Conservative caching beneficial for all " "workloads with >90% success rate"
        recommendations.append(
            OptimizationRecommendation(
                strategy=OptimizationStrategy.CACHE_CONSERVATIVE,
                description="Enable conservative caching for successful operations",
                expected_benefit="20-30% reduction in redundant executions",
                confidence=0.95,
                reason=cache_reason,
                parameters={"ttl_seconds": 1800, "max_size": 500},
                priority=10,
            )
        )

        # Sort by priority and return
        return sorted(recommendations)

    def recommend_for_analysis(self, analysis: AnalysisReport) -> list[OptimizationRecommendation]:
        """Generate recommendations based on analysis report.

        Args:
            analysis: AnalysisReport from execution analysis

        Returns:
            List of OptimizationRecommendation
        """
        recommendations: list[OptimizationRecommendation] = []

        # Recommend profiling for slow operations
        avg_time = analysis.metrics.average_execution_time_ms
        if avg_time > 5000:
            time_str = f"{avg_time:.0f}ms"
            recommendations.append(
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.PROFILE_HEAVY,
                    description="Profile slow operations for optimizations",
                    expected_benefit="Identify performance bottlenecks",
                    confidence=0.8,
                    reason=f"Average execution time is {time_str}",
                    priority=3,
                )
            )

        return recommendations

    def get_best_recommendation(
        self, recommendations: list[OptimizationRecommendation]
    ) -> OptimizationRecommendation | None:
        """Get highest-priority recommendation.

        Args:
            recommendations: List of recommendations

        Returns:
            Highest-priority recommendation or None
        """
        return recommendations[0] if recommendations else None

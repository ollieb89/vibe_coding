"""Recommendation engine for generating code improvement suggestions.

This module synthesizes insights from performance profiling, pattern analysis,
and execution results to generate actionable code improvement recommendations
with confidence scoring and priority ranking.

Features:
- Multi-source recommendation synthesis (timing, patterns, results)
- Confidence-based scoring for each recommendation type
- Priority-based ranking (1-5 scale)
- Human-readable report generation
- Confidence threshold filtering
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RecommendationType(Enum):
    """Types of code improvement recommendations."""

    CACHE = "cache"
    """Recommendation to cache code execution results."""

    SPLIT = "split"
    """Recommendation to split code into parallel operations."""

    PROFILE = "profile"
    """Recommendation to profile code for performance analysis."""

    OPTIMIZE = "optimize"
    """Recommendation to optimize code based on patterns."""

    RETRY = "retry"
    """Recommendation to add retry logic for fault tolerance."""

    REDUCE = "reduce"
    """Recommendation to reduce/simplify code."""


@dataclass
class CodeRecommendation:
    """A single code improvement recommendation."""

    recommendation_type: RecommendationType
    """Type of recommendation (CACHE, SPLIT, PROFILE, etc)."""

    description: str
    """Human-readable description of the recommendation."""

    expected_savings_ms: float
    """Estimated execution time savings in milliseconds."""

    confidence: float
    """Confidence score (0.0-1.0) based on evidence strength."""

    priority: int
    """Priority rank (1-5, where 5 is highest priority)."""

    target_code: str | None = None
    """Code snippet targeted for optimization."""

    estimated_effort: str = "MEDIUM"
    """Effort to implement: LOW, MEDIUM, HIGH."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata: source, reasoning, alternatives."""

    def __post_init__(self) -> None:
        """Validate recommendation after initialization."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")
        if not 1 <= self.priority <= 5:
            raise ValueError(f"Priority must be 1-5, got {self.priority}")
        if self.expected_savings_ms < 0:
            raise ValueError(f"Expected savings cannot be negative: {self.expected_savings_ms}")


class RecommendationEngine:
    """Generate code improvement recommendations from multiple sources."""

    def __init__(self) -> None:
        """Initialize the recommendation engine."""
        self._recommendations: list[CodeRecommendation] = []

    def synthesize_recommendations(
        self,
        prediction: Any,  # PerformancePrediction
        optimization: Any,  # OptimizationRecommendation
        result: Any,  # EnhancedResult
    ) -> list[CodeRecommendation]:
        """Synthesize recommendations from multiple input sources.

        Combines performance predictions, optimization patterns, and execution
        results into a prioritized list of actionable recommendations.

        Args:
            prediction: PerformancePrediction with timing estimates and confidence.
            optimization: OptimizationRecommendation with pattern analysis.
            result: EnhancedResult with execution categorization.

        Returns:
            List of CodeRecommendation objects, sorted by priority (highest first).

        Example:
            >>> engine = RecommendationEngine()
            >>> recs = engine.synthesize_recommendations(pred, opt, result)
            >>> high_confidence = [r for r in recs if r.confidence > 0.8]
        """
        self._recommendations = []

        # Evaluate each recommendation type
        if cache_rec := self._evaluate_caching_potential(result, optimization):
            self._recommendations.append(cache_rec)

        if split_rec := self._evaluate_splitting_potential(prediction, result):
            self._recommendations.append(split_rec)

        if profile_rec := self._evaluate_profiling_need(prediction):
            self._recommendations.append(profile_rec)

        if optimize_rec := self._evaluate_optimization_potential(optimization):
            self._recommendations.append(optimize_rec)

        if retry_rec := self._evaluate_retry_potential(result):
            self._recommendations.append(retry_rec)

        # Sort by priority (highest first), then by confidence
        return sorted(
            self._recommendations,
            key=lambda r: (-r.priority, -r.confidence),
        )

    def _evaluate_caching_potential(
        self,
        result: Any,  # EnhancedResult
        optimization: Any,  # OptimizationRecommendation
    ) -> CodeRecommendation | None:
        """Evaluate if code is suitable for memoization.

        Args:
            result: EnhancedResult from ResultProcessor.
            optimization: OptimizationRecommendation from OptimizationEngine.

        Returns:
            CodeRecommendation if caching is recommended, None otherwise.
        """
        # Extract success rate from result
        is_successful = getattr(result, "category", None) == "success"
        base_confidence = 0.6 if is_successful else 0.3

        # Check if optimization suggests caching
        opt_type = getattr(optimization, "recommendation_type", None)
        has_optimization_signal = str(opt_type).lower() == "cache" if opt_type else False
        if has_optimization_signal:
            base_confidence += 0.2

        # Get complexity from prediction (if available)
        complexity = getattr(optimization, "complexity_level", None)
        if complexity and str(complexity).lower() != "complex":
            base_confidence += 0.1

        # Cap confidence at 0.95
        final_confidence = min(0.95, base_confidence)

        # Only recommend if confidence is reasonable
        if final_confidence < 0.5:
            return None

        return CodeRecommendation(
            recommendation_type=RecommendationType.CACHE,
            description=(
                "Code is suitable for memoization due to high success rate "
                "and repeatability pattern"
            ),
            expected_savings_ms=50.0,  # Typical cache lookup overhead
            confidence=final_confidence,
            priority=4,
            estimated_effort="LOW",
            metadata={
                "source": "caching_analysis",
                "reason": "Repeated execution pattern detected",
                "assumption": "Code is deterministic and side-effect free",
            },
        )

    def _evaluate_splitting_potential(
        self,
        prediction: Any,  # PerformancePrediction
        result: Any,  # EnhancedResult
    ) -> CodeRecommendation | None:
        """Evaluate if code can be parallelized.

        Args:
            prediction: PerformancePrediction with timing estimates.
            result: EnhancedResult with execution categorization.

        Returns:
            CodeRecommendation if splitting is recommended, None otherwise.
        """
        # Check if code is slow enough to justify splitting
        predicted_time = getattr(prediction, "predicted_time_ms", 0)
        if predicted_time < 100:
            return None  # Too fast to parallelize effectively

        # Check if code is stable (not failing frequently)
        is_successful = getattr(result, "category", None) == "success"
        base_confidence = 0.65 if is_successful else 0.3

        # Estimate savings: parallel execution with 4 workers
        workers = 4
        estimated_savings = min(predicted_time * 0.6, predicted_time / workers)
        estimated_savings = max(estimated_savings, 50.0)  # Minimum 50ms savings

        # Only recommend if confidence is reasonable
        if base_confidence < 0.5:
            return None

        return CodeRecommendation(
            recommendation_type=RecommendationType.SPLIT,
            description="Code execution can be optimized through parallelization",
            expected_savings_ms=estimated_savings,
            confidence=base_confidence,
            priority=3,
            estimated_effort="MEDIUM",
            metadata={
                "source": "parallelization_analysis",
                "predicted_time_ms": predicted_time,
                "workers": workers,
                "reason": "Independent operations detected",
            },
        )

    def _evaluate_profiling_need(
        self,
        prediction: Any,  # PerformancePrediction
    ) -> CodeRecommendation | None:
        """Evaluate if code needs deeper performance analysis.

        Args:
            prediction: PerformancePrediction with confidence and variance.

        Returns:
            CodeRecommendation if profiling is recommended, None otherwise.
        """
        # Get confidence from prediction
        confidence_score = getattr(prediction, "confidence", 0.5)

        # Low confidence indicates high variance
        if confidence_score > 0.8:
            return None  # Prediction is already confident

        # Get percentile information if available
        percentile_used = getattr(prediction, "percentile_used", 50)
        min_time = getattr(prediction, "min_time_ms", 0)
        max_time = getattr(prediction, "max_time_ms", 0)

        # Calculate variance
        timing_variance = max_time - min_time if max_time > 0 else 0

        # High variance suggests profiling would help
        if timing_variance < 100:
            return None  # Variance is too small to investigate

        profiling_confidence = max(0.6, min(0.85, 1.0 - confidence_score))

        return CodeRecommendation(
            recommendation_type=RecommendationType.PROFILE,
            description="Code has unpredictable execution time; profiling recommended",
            expected_savings_ms=0.0,  # Profiling doesn't save time directly
            confidence=profiling_confidence,
            priority=2,
            estimated_effort="LOW",
            metadata={
                "source": "variance_analysis",
                "prediction_confidence": confidence_score,
                "timing_variance_ms": timing_variance,
                "percentile_used": percentile_used,
                "reason": "High variance in execution time detected",
            },
        )

    def _evaluate_optimization_potential(
        self,
        optimization: Any,  # OptimizationRecommendation
    ) -> CodeRecommendation | None:
        """Evaluate optimization recommendations from patterns.

        Args:
            optimization: OptimizationRecommendation from OptimizationEngine.

        Returns:
            CodeRecommendation if optimization is recommended, None otherwise.
        """
        # Check if optimization recommendation exists and is meaningful
        opt_type = getattr(optimization, "recommendation_type", None)
        opt_confidence = getattr(optimization, "confidence", 0.0)
        expected_impact = getattr(optimization, "expected_impact", 0.0)

        # Skip if confidence is too low
        if opt_confidence < 0.5:
            return None

        # Map optimization type to priority
        priority_map = {
            "cache_aggressive": 5,
            "cache_conservative": 4,
            "route_adjustment": 3,
            "retry_strategy": 2,
        }
        priority = priority_map.get(str(opt_type).lower(), 2)

        description = getattr(
            optimization,
            "description",
            "Code pattern suggests optimization opportunity",
        )

        return CodeRecommendation(
            recommendation_type=RecommendationType.OPTIMIZE,
            description=description,
            expected_savings_ms=expected_impact,
            confidence=opt_confidence,
            priority=priority,
            estimated_effort="MEDIUM",
            metadata={
                "source": "pattern_analysis",
                "optimization_type": str(opt_type),
                "reason": "Recurring pattern detected",
            },
        )

    def _evaluate_retry_potential(
        self,
        result: Any,  # EnhancedResult
    ) -> CodeRecommendation | None:
        """Evaluate if code needs retry/fault-tolerance logic.

        Args:
            result: EnhancedResult from ResultProcessor.

        Returns:
            CodeRecommendation if retry is recommended, None otherwise.
        """
        # Check if result indicates transient failures
        category = getattr(result, "category", None)
        is_timeout = category == "timeout"
        is_failure = category == "failure"

        # Get error metadata
        metadata = getattr(result, "metadata", {})
        error_type = metadata.get("error_type", None)

        # Only recommend retry for transient errors
        transient_errors = {"timeout", "connection_error", "resource_unavailable"}
        is_transient = error_type in transient_errors

        if not (is_timeout or (is_failure and is_transient)):
            return None

        return CodeRecommendation(
            recommendation_type=RecommendationType.RETRY,
            description="Code has transient failures; retry logic recommended",
            expected_savings_ms=500.0,  # Approximate retry overhead
            confidence=0.7,
            priority=3,
            estimated_effort="LOW",
            metadata={
                "source": "failure_analysis",
                "error_type": error_type,
                "reason": "Transient failure detected",
                "suggested_max_retries": 3,
            },
        )

    def generate_report(
        self,
        recommendations: list[CodeRecommendation],
    ) -> str:
        """Generate a human-readable report of recommendations.

        Args:
            recommendations: List of CodeRecommendation objects.

        Returns:
            Formatted text report with all recommendations.

        Example:
            >>> engine = RecommendationEngine()
            >>> recs = engine.synthesize_recommendations(pred, opt, result)
            >>> report = engine.generate_report(recs)
            >>> print(report)
        """
        if not recommendations:
            return "No recommendations generated."

        lines = [
            "Code Improvement Recommendations",
            "=" * 40,
            "",
        ]

        for i, rec in enumerate(recommendations, 1):
            effort_str = f"Effort: {rec.estimated_effort}"
            savings_str = (
                f"Savings: {rec.expected_savings_ms:.1f}ms"
                if rec.expected_savings_ms > 0
                else "Savings: Analysis benefit"
            )
            lines.extend(
                [
                    f"{i}. [{rec.recommendation_type.value.upper()}] "
                    f"(Priority: {rec.priority}/5, Confidence: {rec.confidence:.1%})",
                    f"   {rec.description}",
                    f"   {effort_str} | {savings_str}",
                    "",
                ]
            )

        return "\n".join(lines)

    def filter_by_confidence(
        self,
        recommendations: list[CodeRecommendation],
        min_confidence: float = 0.6,
    ) -> list[CodeRecommendation]:
        """Filter recommendations by minimum confidence threshold.

        Args:
            recommendations: List of CodeRecommendation objects.
            min_confidence: Minimum confidence threshold (0.0-1.0).

        Returns:
            Filtered list of recommendations above threshold.

        Raises:
            ValueError: If min_confidence is outside 0.0-1.0 range.

        Example:
            >>> high_confidence = engine.filter_by_confidence(recs, 0.75)
        """
        if not 0.0 <= min_confidence <= 1.0:
            raise ValueError(f"min_confidence must be 0.0-1.0, got {min_confidence}")

        return [r for r in recommendations if r.confidence >= min_confidence]

    def get_top_recommendations(
        self,
        recommendations: list[CodeRecommendation],
        limit: int = 3,
    ) -> list[CodeRecommendation]:
        """Get top N recommendations by priority and confidence.

        Args:
            recommendations: List of CodeRecommendation objects.
            limit: Maximum number of recommendations to return.

        Returns:
            Top N recommendations (already sorted by priority/confidence).

        Example:
            >>> top_3 = engine.get_top_recommendations(recs, limit=3)
        """
        return recommendations[:limit]

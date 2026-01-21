"""Performance profiler for execution timing analysis and predictions.

This module provides execution profiling capabilities to analyze historical
execution times, build performance profiles, and predict future execution
times based on patterns.

Features:
- Per-complexity-level execution profiles
- Statistical analysis (min, max, avg, percentiles)
- Execution time prediction with confidence scoring
- Incremental profile updates
- Batch forecasting
"""

import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ComplexityLevel(Enum):
    """Code complexity classification for profiling."""

    SIMPLE = "simple"
    """Simple code: <500 tokens, fast execution."""

    MODERATE = "moderate"
    """Moderate code: 500-2000 tokens, normal execution."""

    COMPLEX = "complex"
    """Complex code: >2000 tokens, slow execution."""

    UNKNOWN = "unknown"
    """Complexity not determined."""


@dataclass
class ExecutionProfile:
    """Statistical profile of execution times for a complexity level."""

    complexity_level: ComplexityLevel
    """Code complexity level this profile represents."""

    min_ms: float
    """Minimum observed execution time in milliseconds."""

    max_ms: float
    """Maximum observed execution time in milliseconds."""

    avg_ms: float
    """Average execution time in milliseconds."""

    p50_ms: float
    """50th percentile (median) execution time."""

    p95_ms: float
    """95th percentile execution time (95% complete within this time)."""

    p99_ms: float
    """99th percentile execution time (99% complete within this time)."""

    sample_count: int
    """Number of samples used to build this profile."""

    std_dev_ms: float = 0.0
    """Standard deviation of execution times."""

    last_updated: str = ""
    """Timestamp of last profile update."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional profile metadata."""

    def get_estimated_time(self, percentile: int = 95) -> float:
        """Get estimated execution time for percentile.

        Args:
            percentile: Percentile to use (50, 95, 99, default 95)

        Returns:
            Estimated execution time in milliseconds
        """
        if percentile == 50:
            return self.p50_ms
        elif percentile == 99:
            return self.p99_ms
        else:  # Default to 95
            return self.p95_ms

    def is_valid(self) -> bool:
        """Check if profile is valid for predictions.

        Returns:
            True if profile has sufficient data
        """
        return self.sample_count >= 3


@dataclass
class PerformancePrediction:
    """Predicted execution time with confidence."""

    predicted_time_ms: float
    """Predicted execution time in milliseconds."""

    confidence: float
    """Confidence in prediction (0-1)."""

    reason: str
    """Explanation for the prediction."""

    complexity_level: ComplexityLevel = ComplexityLevel.UNKNOWN
    """Detected complexity level."""

    percentile_used: int = 95
    """Percentile used for prediction (50, 95, 99)."""

    min_time_ms: float = 0.0
    """Conservative estimate (minimum time)."""

    max_time_ms: float = 0.0
    """Optimistic estimate (maximum time)."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional prediction metadata."""


class PerformanceProfiler:
    """Builds and maintains execution performance profiles.

    The PerformanceProfiler analyzes historical execution times to build
    performance profiles for different code complexity levels. It provides
    prediction capabilities with confidence scoring for execution time
    estimation.
    """

    def __init__(self) -> None:
        """Initialize performance profiler."""
        self._profiles: dict[ComplexityLevel, ExecutionProfile] = {}
        self._timings_history: dict[ComplexityLevel, list[float]] = {
            level: [] for level in ComplexityLevel
        }
        self.min_samples_for_profile = 3

    def build_profile(
        self,
        timings: list[float],
        complexity_level: ComplexityLevel = ComplexityLevel.MODERATE,
    ) -> ExecutionProfile | None:
        """Build execution profile from timing samples.

        Args:
            timings: List of execution times in milliseconds
            complexity_level: Complexity level for this profile

        Returns:
            ExecutionProfile or None if insufficient data
        """
        if len(timings) < self.min_samples_for_profile:
            return None

        try:
            min_time = min(timings)
            max_time = max(timings)
            avg_time = statistics.mean(timings)

            # Calculate percentiles
            p50 = statistics.median(timings)
            p95 = self._percentile(timings, 95)
            p99 = self._percentile(timings, 99)

            # Standard deviation
            std_dev = statistics.stdev(timings) if len(timings) > 1 else 0.0

            profile = ExecutionProfile(
                complexity_level=complexity_level,
                min_ms=min_time,
                max_ms=max_time,
                avg_ms=avg_time,
                p50_ms=p50,
                p95_ms=p95,
                p99_ms=p99,
                sample_count=len(timings),
                std_dev_ms=std_dev,
            )

            # Store profile and history
            self._profiles[complexity_level] = profile
            self._timings_history[complexity_level] = timings.copy()

            return profile

        except (ValueError, statistics.StatisticsError):
            return None

    def predict(
        self,
        complexity_level: ComplexityLevel = ComplexityLevel.MODERATE,
        percentile: int = 95,
    ) -> PerformancePrediction:
        """Predict execution time for given complexity level.

        Args:
            complexity_level: Code complexity level
            percentile: Percentile to use (50, 95, 99)

        Returns:
            PerformancePrediction with estimated time and confidence
        """
        profile = self._profiles.get(complexity_level)

        if not profile or not profile.is_valid():
            # No profile available
            return PerformancePrediction(
                predicted_time_ms=1000.0,  # Default estimate
                confidence=0.1,
                reason=f"No profile available for {complexity_level.value}",
                complexity_level=complexity_level,
                percentile_used=percentile,
            )

        # Get estimated time for percentile
        estimated_time = profile.get_estimated_time(percentile)

        # Calculate confidence based on sample size and variability
        sample_confidence = min(1.0, profile.sample_count / 100)
        variability = profile.std_dev_ms / profile.avg_ms if profile.avg_ms > 0 else 0.0
        variability_confidence = 1.0 / (1.0 + variability)
        confidence = (sample_confidence + variability_confidence) / 2

        return PerformancePrediction(
            predicted_time_ms=estimated_time,
            confidence=confidence,
            reason=(
                f"Prediction based on {profile.sample_count} samples, " f"{percentile}th percentile"
            ),
            complexity_level=complexity_level,
            percentile_used=percentile,
            min_time_ms=profile.p50_ms,
            max_time_ms=profile.p99_ms,
            metadata={
                "avg_ms": profile.avg_ms,
                "std_dev_ms": profile.std_dev_ms,
                "sample_count": profile.sample_count,
            },
        )

    def update_profile(
        self,
        actual_time_ms: float,
        complexity_level: ComplexityLevel = ComplexityLevel.MODERATE,
    ) -> ExecutionProfile | None:
        """Update profile with new execution time.

        Args:
            actual_time_ms: Actual execution time in milliseconds
            complexity_level: Complexity level of code

        Returns:
            Updated ExecutionProfile or None
        """
        # Add to history
        self._timings_history[complexity_level].append(actual_time_ms)

        # Rebuild profile if history is large enough
        history = self._timings_history[complexity_level]
        if len(history) >= self.min_samples_for_profile:
            return self.build_profile(history, complexity_level)

        return self._profiles.get(complexity_level)

    def get_profile_stats(
        self,
        complexity_level: ComplexityLevel = ComplexityLevel.MODERATE,
    ) -> ExecutionProfile | None:
        """Get execution profile for complexity level.

        Args:
            complexity_level: Complexity level to query

        Returns:
            ExecutionProfile or None if not available
        """
        return self._profiles.get(complexity_level)

    def forecast_batch(
        self,
        complexity_levels: list[ComplexityLevel],
        percentile: int = 95,
    ) -> list[PerformancePrediction]:
        """Forecast execution times for multiple complexity levels.

        Args:
            complexity_levels: List of complexity levels to predict
            percentile: Percentile to use (50, 95, 99)

        Returns:
            List of PerformancePrediction objects
        """
        return [self.predict(level, percentile) for level in complexity_levels]

    def detect_complexity(
        self,
        code: str,
    ) -> ComplexityLevel:
        """Detect code complexity level.

        Simple heuristic based on code length in tokens.

        Args:
            code: Code to analyze

        Returns:
            ComplexityLevel estimate
        """
        # Rough token estimate: ~4 characters per token
        token_estimate = len(code) // 4

        if token_estimate < 500:
            return ComplexityLevel.SIMPLE
        elif token_estimate < 2000:
            return ComplexityLevel.MODERATE
        else:
            return ComplexityLevel.COMPLEX

    def get_all_profiles(
        self,
    ) -> dict[ComplexityLevel, ExecutionProfile]:
        """Get all available profiles.

        Returns:
            Dictionary of complexity level -> ExecutionProfile
        """
        return self._profiles.copy()

    def clear_profiles(self) -> None:
        """Clear all profiles and history."""
        self._profiles.clear()
        self._timings_history = {level: [] for level in ComplexityLevel}

    def export_profiles(self) -> dict[str, Any]:
        """Export profiles in JSON-serializable format.

        Returns:
            Dictionary with profile data
        """
        export_data = {
            "profiles": {},
            "metadata": {
                "profile_count": len(self._profiles),
                "levels_with_data": [level.value for level in self._profiles.keys()],
            },
        }

        for level, profile in self._profiles.items():
            export_data["profiles"][level.value] = {
                "min_ms": profile.min_ms,
                "max_ms": profile.max_ms,
                "avg_ms": profile.avg_ms,
                "p50_ms": profile.p50_ms,
                "p95_ms": profile.p95_ms,
                "p99_ms": profile.p99_ms,
                "sample_count": profile.sample_count,
                "std_dev_ms": profile.std_dev_ms,
            }

        return export_data

    @staticmethod
    def _percentile(
        data: list[float],
        percentile: int,
    ) -> float:
        """Calculate percentile value.

        Args:
            data: List of values
            percentile: Percentile to calculate (0-100)

        Returns:
            Percentile value
        """
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = (percentile / 100.0) * (len(sorted_data) - 1)
        lower_index = int(index)
        upper_index = min(lower_index + 1, len(sorted_data) - 1)

        if lower_index == upper_index:
            return sorted_data[lower_index]

        # Linear interpolation
        lower_value = sorted_data[lower_index]
        upper_value = sorted_data[upper_index]
        fraction = index - lower_index

        return lower_value + (upper_value - lower_value) * fraction

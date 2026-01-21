"""Execution orchestrator for intelligent routing between mock and real executors.

This module provides the ExecutionOrchestrator class that makes intelligent
decisions about whether to use MockExecutor (for validation) or RealExecutor
(for production execution) based on code quality confidence scores.

The orchestrator implements a flexible routing strategy:
- High confidence (>0.8): Use RealExecutor only
- Medium confidence (0.5-0.8): Use both, compare results
- Low confidence (<0.5): Use MockExecutor only for validation
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from agent_discovery.mock_executor import MockExecutionResult, MockExecutor
from agent_discovery.real_executor import ExecutionResult, RealExecutor


class ExecutionMode(Enum):
    """Execution routing mode."""

    MOCK_ONLY = "mock_only"  # Use MockExecutor only
    REAL_ONLY = "real_only"  # Use RealExecutor only
    BOTH = "both"  # Use both and compare


@dataclass
class RoutingDecision:
    """Decision made by orchestrator."""

    mode: ExecutionMode
    """Chosen execution mode."""

    confidence: float
    """Code quality confidence (0-1)."""

    reason: str
    """Human-readable reason for decision."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata about the decision."""


@dataclass
class OrchestratedResult:
    """Result from orchestrated execution."""

    success: bool
    """Overall execution success."""

    primary_result: ExecutionResult | MockExecutionResult
    """Primary execution result (mock or real)."""

    secondary_result: ExecutionResult | MockExecutionResult | None = None
    """Secondary result if running both modes."""

    routing_decision: RoutingDecision | None = None
    """Routing decision made."""

    execution_mode: ExecutionMode = ExecutionMode.REAL_ONLY
    """Which mode was used."""

    confidence_score: float = 0.5
    """Confidence score used for routing."""

    comparison_metadata: dict[str, Any] = field(default_factory=dict)
    """Comparison data if both modes were used."""

    def is_mock_result(self) -> bool:
        """Check if primary result is from mock execution."""
        return isinstance(self.primary_result, MockExecutionResult)

    def is_real_result(self) -> bool:
        """Check if primary result is from real execution."""
        return isinstance(self.primary_result, ExecutionResult)

    def results_agree(self) -> bool | None:
        """Check if mock and real results agree (when both available)."""
        if self.secondary_result is None:
            return None
        return self.primary_result.success == self.secondary_result.success


class ExecutionOrchestrator:
    """Routes execution between MockExecutor and RealExecutor intelligently.

    The orchestrator makes routing decisions based on code quality confidence:
    - High confidence (>0.8): Use RealExecutor only (production)
    - Medium confidence (0.5-0.8): Use both, compare results
    - Low confidence (<0.5): Use MockExecutor only (validation)

    Example:
        >>> orchestrator = ExecutionOrchestrator()
        >>> result = orchestrator.execute(code, confidence=0.85)
        >>> assert result.execution_mode == ExecutionMode.REAL_ONLY
    """

    def __init__(
        self,
        real_executor: RealExecutor | None = None,
        mock_executor: MockExecutor | None = None,
        high_confidence_threshold: float = 0.8,
        low_confidence_threshold: float = 0.5,
    ) -> None:
        """Initialize orchestrator.

        Args:
            real_executor: RealExecutor instance (default: create new)
            mock_executor: MockExecutor instance (default: create new)
            high_confidence_threshold: Threshold for real-only execution
            low_confidence_threshold: Threshold for mock-only execution
        """
        self.real_executor = real_executor or RealExecutor()
        self.mock_executor = mock_executor or MockExecutor()
        self.high_confidence_threshold = high_confidence_threshold
        self.low_confidence_threshold = low_confidence_threshold

        # Statistics tracking
        self.stats = {
            "total_executions": 0,
            "mock_only": 0,
            "real_only": 0,
            "both": 0,
            "agreements": 0,
            "disagreements": 0,
        }

    def execute(
        self,
        code: str,
        confidence: float = 0.5,
        timeout_seconds: int | None = None,
    ) -> OrchestratedResult:
        """Execute code with intelligent routing.

        Args:
            code: Code to execute
            confidence: Confidence score (0-1) for code quality
            timeout_seconds: Timeout for execution

        Returns:
            OrchestratedResult with execution outcome and routing info
        """
        # Ensure confidence is in valid range
        confidence = max(0.0, min(1.0, confidence))

        # Make routing decision
        decision = self._make_routing_decision(code, confidence)

        self.stats["total_executions"] += 1

        # Execute based on decision
        if decision.mode == ExecutionMode.REAL_ONLY:
            self.stats["real_only"] += 1
            result = self.real_executor.execute_python(code)
            return OrchestratedResult(
                success=result.success,
                primary_result=result,
                secondary_result=None,
                routing_decision=decision,
                execution_mode=ExecutionMode.REAL_ONLY,
                confidence_score=confidence,
            )

        elif decision.mode == ExecutionMode.MOCK_ONLY:
            self.stats["mock_only"] += 1
            result = self.mock_executor.execute(code, timeout_seconds)
            return OrchestratedResult(
                success=result.success,
                primary_result=result,
                secondary_result=None,
                routing_decision=decision,
                execution_mode=ExecutionMode.MOCK_ONLY,
                confidence_score=confidence,
            )

        else:  # BOTH
            self.stats["both"] += 1
            mock_result = self.mock_executor.execute(code, timeout_seconds)
            real_result = self.real_executor.execute_python(code)

            # Track agreement
            if mock_result.success == real_result.success:
                self.stats["agreements"] += 1
            else:
                self.stats["disagreements"] += 1

            # Use real result as primary when both available
            return OrchestratedResult(
                success=real_result.success,
                primary_result=real_result,
                secondary_result=mock_result,
                routing_decision=decision,
                execution_mode=ExecutionMode.BOTH,
                confidence_score=confidence,
                comparison_metadata={
                    "agreement": mock_result.success == real_result.success,
                    "mock_success": mock_result.success,
                    "real_success": real_result.success,
                },
            )

    def _make_routing_decision(self, code: str, confidence: float) -> RoutingDecision:
        """Make routing decision based on confidence.

        Args:
            code: Code to analyze
            confidence: Confidence score (0-1)

        Returns:
            RoutingDecision with mode and reasoning
        """
        if confidence > self.high_confidence_threshold:
            mode = ExecutionMode.REAL_ONLY
            reason = f"High confidence ({confidence:.2f}) - " "use RealExecutor for production"

        elif confidence < self.low_confidence_threshold:
            mode = ExecutionMode.MOCK_ONLY
            reason = f"Low confidence ({confidence:.2f}) - " "use MockExecutor for validation only"

        else:  # Medium confidence
            mode = ExecutionMode.BOTH
            reason = (
                f"Medium confidence ({confidence:.2f}) - " "use both executors to compare results"
            )

        return RoutingDecision(
            mode=mode,
            confidence=confidence,
            reason=reason,
            metadata={
                "code_length": len(code),
                "code_lines": code.count("\n"),
            },
        )

    def get_stats(self) -> dict[str, Any]:
        """Get execution statistics.

        Returns:
            Dictionary with execution statistics
        """
        return {
            **self.stats,
            "agreement_rate": (
                self.stats["agreements"]
                / max(1, self.stats["agreements"] + self.stats["disagreements"])
            ),
        }

    def reset_stats(self) -> None:
        """Reset execution statistics."""
        self.stats = {
            "total_executions": 0,
            "mock_only": 0,
            "real_only": 0,
            "both": 0,
            "agreements": 0,
            "disagreements": 0,
        }

    def set_thresholds(
        self,
        high_confidence_threshold: float | None = None,
        low_confidence_threshold: float | None = None,
    ) -> None:
        """Adjust routing thresholds.

        Args:
            high_confidence_threshold: New high threshold (optional)
            low_confidence_threshold: New low threshold (optional)
        """
        if high_confidence_threshold is not None:
            self.high_confidence_threshold = high_confidence_threshold
        if low_confidence_threshold is not None:
            self.low_confidence_threshold = low_confidence_threshold

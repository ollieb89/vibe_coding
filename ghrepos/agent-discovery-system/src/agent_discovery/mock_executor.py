"""Mock agent executor for validation and testing.

This module provides a MockExecutor that simulates agent execution without
actually running code. Useful for:
- Fast validation before real execution
- Testing execution flow without external dependencies
- Confidence-based decision making in orchestration
- Development and debugging
"""

import random
from dataclasses import dataclass
from enum import Enum


class SimulationType(Enum):
    """Type of simulation behavior."""

    SUCCESS = "success"  # Always succeeds
    FAILURE = "failure"  # Always fails
    RANDOM = "random"  # Random success/failure
    DETERMINISTIC = "deterministic"  # Based on code content


@dataclass
class MockExecutionResult:
    """Result of mock agent execution."""

    success: bool
    """Whether execution was simulated as successful."""

    stdout: str
    """Simulated standard output."""

    stderr: str
    """Simulated standard error."""

    execution_time_ms: float
    """Simulated execution time in milliseconds."""

    exit_code: int
    """Simulated exit code (0 = success)."""

    error_category: str | None = None
    """Error classification if failed."""

    is_mock: bool = True
    """Flag indicating this is a mock result."""

    simulation_type: SimulationType = SimulationType.DETERMINISTIC
    """Type of simulation used."""


class MockExecutor:
    """Simulates agent execution for validation and testing.

    The MockExecutor provides a lightweight execution simulation that can be
    used to validate agent code before running it with the RealExecutor.

    Features:
    - Multiple simulation modes (success, failure, random, deterministic)
    - Fast execution (no subprocess overhead)
    - Confidence-based result generation
    - Ideal for testing orchestration logic

    Example:
        >>> executor = MockExecutor(simulation_type=SimulationType.DETERMINISTIC)
        >>> result = executor.execute(code="print('test')")
        >>> assert result.is_mock
    """

    def __init__(
        self,
        simulation_type: SimulationType = SimulationType.DETERMINISTIC,
        seed: int | None = None,
    ) -> None:
        """Initialize mock executor.

        Args:
            simulation_type: Type of simulation behavior
            seed: Random seed for reproducible results
        """
        self.simulation_type = simulation_type
        if seed is not None:
            random.seed(seed)

    def execute(self, code: str, timeout_seconds: int | None = None) -> MockExecutionResult:
        """Execute code in mock mode.

        Args:
            code: Code to simulate executing
            timeout_seconds: Timeout (ignored in mock mode)

        Returns:
            MockExecutionResult with simulated execution outcome
        """
        match self.simulation_type:
            case SimulationType.SUCCESS:
                return self._simulate_success(code)
            case SimulationType.FAILURE:
                return self._simulate_failure(code)
            case SimulationType.RANDOM:
                return self._simulate_random(code)
            case SimulationType.DETERMINISTIC:
                return self._simulate_deterministic(code)
            case _:
                return self._simulate_deterministic(code)

    def _simulate_success(self, code: str) -> MockExecutionResult:
        """Simulate successful execution."""
        return MockExecutionResult(
            success=True,
            stdout=f"[MOCK] Simulated execution of {len(code)} char code",
            stderr="",
            execution_time_ms=random.uniform(10, 50),
            exit_code=0,
            error_category=None,
            simulation_type=SimulationType.SUCCESS,
        )

    def _simulate_failure(self, code: str) -> MockExecutionResult:
        """Simulate failed execution."""
        errors = [
            ("SyntaxError", "syntax"),
            ("RuntimeError", "runtime"),
            ("ImportError", "dependency"),
            ("PermissionError", "permission"),
        ]
        error_msg, category = random.choice(errors)
        return MockExecutionResult(
            success=False,
            stdout="",
            stderr=f"[MOCK] {error_msg}: Simulated execution failed",
            execution_time_ms=random.uniform(5, 20),
            exit_code=1,
            error_category=category,
            simulation_type=SimulationType.FAILURE,
        )

    def _simulate_random(self, code: str) -> MockExecutionResult:
        """Simulate random success or failure."""
        if random.random() > 0.5:
            return self._simulate_success(code)
        else:
            return self._simulate_failure(code)

    def _simulate_deterministic(self, code: str) -> MockExecutionResult:
        """Simulate based on code content analysis.

        Heuristics:
        - Code with 'import' → likely success (has dependencies)
        - Code with 'print' → success
        - Code with 'raise' → failure
        - Short code → success
        - Long complex code → possible failure
        """
        # Simple heuristics for deterministic behavior
        code_lower = code.lower()

        # Check for obvious failure patterns
        if "raise" in code_lower or "error" in code_lower:
            return self._simulate_failure(code)

        # Check for success indicators
        if "print" in code_lower or "return" in code_lower or len(code) < 100:
            return self._simulate_success(code)

        # Complex code → slightly more likely to fail
        if len(code) > 500:
            return self._simulate_random(code)

        # Default to success for normal code
        return self._simulate_success(code)

    def set_simulation_type(self, simulation_type: SimulationType) -> None:
        """Change simulation type.

        Args:
            simulation_type: New simulation type
        """
        self.simulation_type = simulation_type

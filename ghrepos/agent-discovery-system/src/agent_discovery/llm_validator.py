"""LLM-based code validator for confidence scoring.

This module provides the LLMValidator interface and implementations for
validating agent code and assessing execution confidence scores.

The validator checks for common issues, security concerns, and code quality,
then produces a confidence score (0-1) that guides execution routing in
the ExecutionOrchestrator.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationResult:
    """Result of code validation."""

    is_valid: bool
    """Whether code passed validation."""

    confidence: float
    """Confidence score (0-1) for execution."""

    issues: list[str] | None = None
    """List of issues found (if any)."""

    suggestions: list[str] | None = None
    """Suggestions for improvement."""

    metrics: dict[str, Any] | None = None
    """Code quality metrics."""

    def __post_init__(self) -> None:
        """Initialize default values."""
        if self.issues is None:
            self.issues = []
        if self.suggestions is None:
            self.suggestions = []
        if self.metrics is None:
            self.metrics = {}


class LLMValidator:
    """Validates code and assesses execution confidence.

    This class provides code validation and confidence assessment, designed
    as an interface for LLM integration. Currently implements deterministic
    heuristic-based validation; can be extended with LLM-based validation.

    Features:
    - Static code analysis (syntax, imports, security)
    - Confidence scoring (0-1)
    - Issue and suggestion generation
    - Code quality metrics

    Example:
        >>> validator = LLMValidator()
        >>> result = validator.validate("print('hello')")
        >>> assert result.confidence > 0.8
    """

    def __init__(self, strict_mode: bool = False) -> None:
        """Initialize validator.

        Args:
            strict_mode: If True, validate more strictly
        """
        self.strict_mode = strict_mode

        # Define validation rules
        self.security_keywords = [
            "eval",
            "exec",
            "compile",
            "__import__",
            "globals",
            "locals",
            "vars",
        ]
        self.dangerous_imports = [
            "subprocess",
            "os",
            "sys",
            "shutil",
        ]

    def validate(self, code: str) -> ValidationResult:
        """Validate code and assess confidence.

        Args:
            code: Code to validate

        Returns:
            ValidationResult with confidence score and issues
        """
        issues = []
        suggestions = []
        metrics = {
            "length": len(code),
            "lines": code.count("\n") + 1,
            "imports": 0,
            "functions": 0,
            "classes": 0,
        }

        # Check for empty code
        if not code.strip():
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                issues=["Code is empty"],
                suggestions=["Provide non-empty code"],
                metrics=metrics,
            )

        # Count code elements
        metrics["imports"] = code.count("import ")
        metrics["functions"] = code.count("def ")
        metrics["classes"] = code.count("class ")

        # Check for security issues
        for keyword in self.security_keywords:
            if keyword in code:
                issues.append(f"Security risk: {keyword} detected")
                suggestions.append(f"Avoid using {keyword} for safety")

        # Check for dangerous imports
        for import_name in self.dangerous_imports:
            if f"import {import_name}" in code:
                issues.append(f"Dangerous import detected: {import_name}")
                suggestions.append(f"Avoid importing {import_name} for safety")

        # Check for infinite loops (simple heuristic)
        if "while True" in code:
            if self.strict_mode:
                issues.append("Infinite loop detected")
                suggestions.append("Use bounded loops with exit conditions")

        # Check syntax (simple heuristic)
        if code.count("(") != code.count(")"):
            issues.append("Mismatched parentheses")
        if code.count("[") != code.count("]"):
            issues.append("Mismatched brackets")
        if code.count("{") != code.count("}"):
            issues.append("Mismatched braces")

        # Calculate confidence
        confidence = self._calculate_confidence(code, issues, metrics)

        is_valid = len(issues) == 0 or (not self.strict_mode and confidence > 0.5)

        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            issues=issues,
            suggestions=suggestions,
            metrics=metrics,
        )

    def _calculate_confidence(self, code: str, issues: list[str], metrics: dict[str, Any]) -> float:
        """Calculate confidence score.

        Args:
            code: Code being validated
            issues: Issues found
            metrics: Code metrics

        Returns:
            Confidence score (0-1)
        """
        confidence = 1.0

        # Deduct for each issue
        confidence -= len(issues) * 0.15

        # Code length factor
        code_len = metrics["length"]
        if code_len < 10:
            confidence -= 0.1  # Too short
        elif code_len > 10000:
            confidence -= 0.1  # Too long

        # Complexity factor
        complexity = metrics["functions"] + metrics["classes"] + metrics["imports"]
        if complexity > 20:
            confidence -= 0.1  # Too complex
        elif complexity == 0:
            confidence -= 0.05  # Very simple

        # Has imports (good sign)
        if metrics["imports"] > 0:
            confidence += 0.05

        # Has structure (good sign)
        if metrics["functions"] > 0 or metrics["classes"] > 0:
            confidence += 0.05

        # Ensure valid range
        return max(0.0, min(1.0, confidence))

    def assess_code_type(self, code: str) -> str:
        """Assess type of code.

        Args:
            code: Code to assess

        Returns:
            Code type: 'simple', 'function', 'class', 'complex', 'script'
        """
        has_functions = "def " in code
        has_classes = "class " in code
        has_imports = "import " in code
        lines = code.count("\n") + 1

        if has_classes:
            return "class"
        elif has_functions:
            return "function"
        elif has_imports and lines > 20:
            return "script"
        elif lines > 50:
            return "complex"
        else:
            return "simple"

    def suggest_execution_mode(self, code: str) -> tuple[str, float, str]:
        """Suggest execution mode based on code analysis.

        Args:
            code: Code to analyze

        Returns:
            Tuple of (suggested_mode, confidence, reason)
        """
        result = self.validate(code)
        confidence = result.confidence

        if confidence > 0.8:
            mode = "real_only"
            reason = "High confidence - use RealExecutor"
        elif confidence > 0.5:
            mode = "both"
            reason = "Medium confidence - compare results"
        else:
            mode = "mock_only"
            reason = "Low confidence - validation only"

        return mode, confidence, reason

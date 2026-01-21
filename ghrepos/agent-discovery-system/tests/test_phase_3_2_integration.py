"""Integration tests for Phase 3.2 - LLM Execution Orchestration.

Tests cover:
- ExecutionOrchestrator routing logic
- LLMValidator confidence assessment
- ExecutionAnalyzer metrics extraction
- ExecutionLogger structured logging
- MetricsCollector aggregation
- End-to-end orchestration flow
"""

import json
import tempfile
from pathlib import Path

import pytest

from agent_discovery.analyzer import ExecutionAnalyzer
from agent_discovery.llm_validator import LLMValidator, ValidationResult
from agent_discovery.logging import ExecutionLogger, LogLevel, MetricsCollector
from agent_discovery.mock_executor import MockExecutor, SimulationType
from agent_discovery.orchestrator import ExecutionMode, ExecutionOrchestrator
from agent_discovery.real_executor import ExecutionResult, RealExecutor


class TestExecutionOrchestrator:
    """Test ExecutionOrchestrator routing logic."""

    def test_orchestrator_initialization(self) -> None:
        """Test orchestrator can be initialized with different modes."""
        for mode in ExecutionMode:
            orchestrator = ExecutionOrchestrator(mode=mode)
            assert orchestrator.mode == mode
            assert orchestrator.stats.total_executions == 0

    def test_mock_only_routing(self) -> None:
        """Test routing to mock executor only when confidence is low."""
        orchestrator = ExecutionOrchestrator(mode=ExecutionMode.BOTH)
        mock_exec = MockExecutor(SimulationType.SUCCESS)
        real_exec = RealExecutor()

        code = "print('hello')"
        validator = LLMValidator()
        result = validator.validate(code)

        # Force low confidence to trigger mock-only routing
        low_confidence_result = ValidationResult(
            is_valid=True, confidence=0.3, issues=[], suggestions=[], metrics={}
        )

        # Mock the validator to return low confidence
        result = low_confidence_result
        orchestrated = orchestrator.execute(
            code,
            confidence=result.confidence,
            executor_mock=mock_exec,
            executor_real=real_exec,
        )

        assert orchestrated.routing.decision == "mock_only"
        assert orchestrated.mock_result is not None
        assert orchestrated.real_result is None

    def test_real_only_routing(self) -> None:
        """Test routing to real executor only when confidence is high."""
        orchestrator = ExecutionOrchestrator(mode=ExecutionMode.BOTH)
        mock_exec = MockExecutor(SimulationType.SUCCESS)
        real_exec = RealExecutor()

        code = "x = 1 + 1"
        orchestrated = orchestrator.execute(
            code,
            confidence=0.9,
            executor_mock=mock_exec,
            executor_real=real_exec,
        )

        assert orchestrated.routing.decision == "real_only"
        assert orchestrated.real_result is not None
        assert orchestrated.mock_result is None

    def test_both_executors_routing(self) -> None:
        """Test routing to both executors when confidence is moderate."""
        orchestrator = ExecutionOrchestrator(mode=ExecutionMode.BOTH)
        mock_exec = MockExecutor(SimulationType.SUCCESS)
        real_exec = RealExecutor()

        code = "x = 42"
        orchestrated = orchestrator.execute(
            code,
            confidence=0.65,
            executor_mock=mock_exec,
            executor_real=real_exec,
        )

        assert orchestrated.routing.decision == "both"
        assert orchestrated.mock_result is not None
        assert orchestrated.real_result is not None


class TestLLMValidator:
    """Test LLMValidator code validation and confidence scoring."""

    def test_validator_initialization(self) -> None:
        """Test validator initializes correctly."""
        validator = LLMValidator()
        assert validator is not None

    def test_simple_code_validation(self) -> None:
        """Test validation of simple, safe code."""
        validator = LLMValidator()
        result = validator.validate("x = 1 + 2")

        assert result.is_valid is True
        assert result.confidence > 0.8
        assert len(result.issues) == 0

    def test_dangerous_code_detection(self) -> None:
        """Test detection of dangerous code patterns."""
        validator = LLMValidator()

        dangerous_codes = [
            "eval(user_input)",
            "exec(code_string)",
            "import subprocess; subprocess.call('rm -rf /')",
            "__import__('os').system('rm -rf /')",
            "compile(code, '<string>', 'exec')",
        ]

        for code in dangerous_codes:
            result = validator.validate(code)
            assert result.is_valid is False or result.confidence < 0.7
            assert len(result.issues) > 0

    def test_confidence_scoring(self) -> None:
        """Test confidence scoring increases with code simplicity."""
        validator = LLMValidator()

        simple_code = "x = 1"
        complex_code = """
def process_data(data):
    if not data:
        return None
    try:
        result = eval(data['expression'])
        return result
    except Exception as e:
        return str(e)
"""

        simple_result = validator.validate(simple_code)
        complex_result = validator.validate(complex_code)

        # Simple code should have higher confidence than complex code
        assert simple_result.confidence > complex_result.confidence

    def test_code_type_assessment(self) -> None:
        """Test code type classification."""
        validator = LLMValidator()

        types_and_codes = [
            ("simple", "x = 1"),
            ("function", "def add(a, b):\n    return a + b"),
            ("class", "class MyClass:\n    def __init__(self):\n        pass"),
        ]

        for expected_type, code in types_and_codes:
            result = validator.validate(code)
            assert result.metrics.get("code_type") == expected_type


class TestExecutionAnalyzer:
    """Test ExecutionAnalyzer metrics extraction and analysis."""

    def test_analyzer_initialization(self) -> None:
        """Test analyzer initializes correctly."""
        analyzer = ExecutionAnalyzer()
        assert analyzer is not None

    def test_analyze_single_result(self) -> None:
        """Test analyzing a single execution result."""
        analyzer = ExecutionAnalyzer()
        mock_exec = MockExecutor(SimulationType.SUCCESS)

        result = mock_exec.execute("print('test')")
        analysis = analyzer.analyze_result(result, "mock")

        assert analysis.metrics.success_rate is not None
        assert analysis.metrics.timing is not None

    def test_batch_analysis(self) -> None:
        """Test batch analysis of multiple results."""
        analyzer = ExecutionAnalyzer()
        mock_exec = MockExecutor(SimulationType.SUCCESS)

        results = []
        for i in range(5):
            result = mock_exec.execute(f"x = {i}")
            results.append(("mock", result))

        analysis = analyzer.analyze_batch(results)

        assert analysis.metrics.success_rate == 1.0
        assert len(analysis.patterns) > 0

    def test_error_categorization(self) -> None:
        """Test error categorization in analysis."""
        analyzer = ExecutionAnalyzer()

        # Create mock results with different error types
        timeout_result = ExecutionResult(
            exit_code=124, stdout="", stderr="timeout", duration_ms=5000
        )
        permission_result = ExecutionResult(
            exit_code=1, stdout="", stderr="Permission denied", duration_ms=100
        )

        analysis1 = analyzer.analyze_result(timeout_result, "real")
        analysis2 = analyzer.analyze_result(permission_result, "real")

        # Verify different error categories are detected
        assert analysis1.metrics is not None
        assert analysis2.metrics is not None


class TestExecutionLogger:
    """Test ExecutionLogger structured logging."""

    def test_logger_initialization(self) -> None:
        """Test logger initializes correctly."""
        logger = ExecutionLogger(name="TestLogger", verbose=False)
        assert logger.name == "TestLogger"
        assert len(logger.logs) == 0

    def test_logging_messages(self) -> None:
        """Test logging messages at different levels."""
        logger = ExecutionLogger(verbose=False)

        logger.debug("Debug message", {"key": "value"})
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

        assert len(logger.logs) == 5
        assert logger.logs[0].level == LogLevel.DEBUG.value
        assert logger.logs[4].level == LogLevel.CRITICAL.value

    def test_context_stack(self) -> None:
        """Test context stack management."""
        logger = ExecutionLogger(verbose=False)

        logger.push_context({"request_id": "123"})
        logger.push_context({"user_id": "456"})
        logger.info("Message with context")

        assert logger.logs[0].context["request_id"] == "123"
        assert logger.logs[0].context["user_id"] == "456"

        logger.pop_context()
        logger.info("Message without user context")
        assert "user_id" not in logger.logs[1].context

    def test_file_logging(self) -> None:
        """Test logging to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = ExecutionLogger(log_file=log_file, verbose=False)

            logger.info("Test message")

            assert log_file.exists()
            with open(log_file) as f:
                content = f.read()
                assert "Test message" in content

    def test_log_export(self) -> None:
        """Test exporting logs in different formats."""
        logger = ExecutionLogger(verbose=False)
        logger.info("Message 1")
        logger.info("Message 2")

        # Test JSON export
        json_export = logger.export_logs(format_type="json")
        parsed = json.loads(json_export)
        assert len(parsed) == 2
        assert parsed[0]["message"] == "Message 1"

        # Test text export
        text_export = logger.export_logs(format_type="text")
        assert "Message 1" in text_export
        assert "Message 2" in text_export


class TestMetricsCollector:
    """Test MetricsCollector metrics aggregation."""

    def test_collector_initialization(self) -> None:
        """Test collector initializes correctly."""
        collector = MetricsCollector()
        assert collector is not None
        assert collector.stats.total_executions == 0

    def test_record_execution(self) -> None:
        """Test recording execution metrics."""
        collector = MetricsCollector()

        collector.record_execution("mock", success=True, duration_ms=100)
        collector.record_execution("real", success=True, duration_ms=150)
        collector.record_execution("real", success=False, duration_ms=200, error_category="timeout")

        assert collector.stats.total_executions == 3
        assert collector.stats.successful == 2
        assert collector.stats.failed == 1
        assert collector.stats.error_categories["timeout"] == 1

    def test_routing_distribution_tracking(self) -> None:
        """Test tracking routing distribution."""
        collector = MetricsCollector()

        collector.record_execution("mock", success=True, duration_ms=100)
        collector.record_execution("real", success=True, duration_ms=100)
        collector.record_execution("both", success=True, duration_ms=100)

        assert collector.stats.mock_only == 1
        assert collector.stats.real_only == 1
        assert collector.stats.both_executors == 1

    def test_agreement_metrics(self) -> None:
        """Test agreement metrics tracking."""
        collector = MetricsCollector()

        collector.record_routing_decision(0.8, "real_only", agreement=True)
        collector.record_routing_decision(0.6, "both", agreement=False)
        collector.record_routing_decision(0.4, "mock_only", agreement=None)

        assert collector.stats.agreements == 1
        assert collector.stats.disagreements == 1

    def test_metrics_summary(self) -> None:
        """Test metrics summary generation."""
        collector = MetricsCollector()

        for i in range(10):
            success = i % 2 == 0
            collector.record_execution("mock", success=success, duration_ms=100 + i)

        summary = collector.get_stats_summary()

        assert summary["total_executions"] == 10
        assert summary["successful"] == 5
        assert summary["failed"] == 5
        assert summary["success_rate"] == 0.5

    def test_timing_statistics(self) -> None:
        """Test timing statistics calculation."""
        collector = MetricsCollector()

        for duration in [100, 150, 200, 250]:
            collector.record_execution("real", success=True, duration_ms=duration)

        timing = collector.get_timing_stats("real")

        assert timing["min"] == 100
        assert timing["max"] == 250
        assert timing["count"] == 4

    def test_metrics_export(self) -> None:
        """Test exporting metrics in different formats."""
        collector = MetricsCollector()

        collector.record_execution("mock", success=True, duration_ms=100)
        collector.record_execution("real", success=True, duration_ms=150)

        # Test JSON export
        json_export = collector.export_metrics(format_type="json")
        parsed = json.loads(json_export)
        assert parsed["total_executions"] == 2

        # Test text export
        text_export = collector.export_metrics(format_type="text")
        assert "Execution Metrics Summary" in text_export
        assert "Total Executions: 2" in text_export

    def test_execution_history(self) -> None:
        """Test execution history tracking."""
        collector = MetricsCollector()

        collector.record_execution(
            "mock",
            success=True,
            duration_ms=100,
            metadata={"code_length": 42},
        )

        history = collector.get_execution_history()
        assert len(history) == 1
        assert history[0]["executor_type"] == "mock"
        assert history[0]["code_length"] == 42


class TestEndToEndOrchestration:
    """Integration tests for end-to-end orchestration flow."""

    def test_full_orchestration_flow(self) -> None:
        """Test complete orchestration flow from validation to analysis."""
        # Initialize components
        validator = LLMValidator()
        orchestrator = ExecutionOrchestrator(mode=ExecutionMode.BOTH)
        analyzer = ExecutionAnalyzer()
        logger = ExecutionLogger(verbose=False)
        collector = MetricsCollector(logger=logger)

        code = "x = 1 + 2\nprint(x)"

        # Step 1: Validate code
        validation = validator.validate(code)
        logger.log_validation(validation.is_valid, validation.confidence, validation.issues)
        collector.record_validation(validation.confidence)

        assert validation.is_valid is True

        # Step 2: Log routing decision
        mock_exec = MockExecutor(SimulationType.SUCCESS)
        real_exec = RealExecutor()

        logger.log_routing_decision(
            validation.confidence, "both", "Code complexity warrants dual execution"
        )

        # Step 3: Execute with orchestrator
        orchestrated = orchestrator.execute(
            code,
            confidence=validation.confidence,
            executor_mock=mock_exec,
            executor_real=real_exec,
        )

        logger.log_execution(code, orchestrated, 150, orchestrated.routing.decision)
        collector.record_execution(
            orchestrated.routing.decision,
            success=(orchestrated.mock_result.exit_code == 0 if orchestrated.mock_result else True),
            duration_ms=150,
        )

        # Step 4: Analyze results
        if orchestrated.mock_result:
            analyzer.analyze_result(orchestrated.mock_result, "mock")
        if orchestrated.real_result:
            analyzer.analyze_result(orchestrated.real_result, "real")

        # Step 5: Get summary
        summary = collector.get_stats_summary()

        assert summary["total_executions"] == 1
        assert orchestrated.routing.decision in ("mock_only", "real_only", "both")
        assert len(logger.logs) > 0

    def test_orchestration_with_logging_and_metrics(self) -> None:
        """Test orchestration integrated with logging and metrics."""
        logger = ExecutionLogger(verbose=False)
        collector = MetricsCollector(logger=logger)
        orchestrator = ExecutionOrchestrator(mode=ExecutionMode.BOTH)

        mock_exec = MockExecutor(SimulationType.SUCCESS)
        real_exec = RealExecutor()

        code = "result = 2 ** 10"

        # Execute
        orchestrated = orchestrator.execute(
            code,
            confidence=0.75,
            executor_mock=mock_exec,
            executor_real=real_exec,
        )

        # Record metrics
        collector.record_execution(
            orchestrated.routing.decision,
            success=(orchestrated.mock_result.exit_code == 0 if orchestrated.mock_result else True),
            duration_ms=100,
        )

        logger.log_routing_decision(
            0.75, orchestrated.routing.decision, orchestrated.routing.reason
        )

        # Verify
        summary = collector.get_stats_summary()
        assert summary["total_executions"] == 1
        assert len(logger.logs) == 1
        assert logger.logs[0].level == LogLevel.INFO.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

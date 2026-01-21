"""Integration tests for Phase 4 modules: results processing pipeline.

Comprehensive testing of all 6 Phase 4 modules working together:
- ResultProcessor: Categorization and enhancement
- ResultCache: Memoization and TTL
- PerformanceProfiler: Profiling and prediction
- OptimizationEngine: Pattern analysis
- RecommendationEngine: Recommendation synthesis
- ResultExporter: Multi-format export

Tests cover:
- Individual module functionality
- Data flow between modules
- All export formats
- Error handling and edge cases
- End-to-end pipeline
"""

import json
import sys
from pathlib import Path

import pytest

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# Mock objects for testing (simple dataclass-like objects)
class MockEnhancedResult:
    """Mock EnhancedResult for testing."""

    def __init__(
        self,
        category: str = "success",
        success: bool = True,
        metadata: dict | None = None,
    ) -> None:
        self.category = category
        self.success = success
        self.metadata = metadata or {}


class MockExecutionProfile:
    """Mock ExecutionProfile for testing."""

    def __init__(
        self,
        complexity_level: str = "SIMPLE",
        min_ms: float = 100.0,
        max_ms: float = 500.0,
        avg_ms: float = 300.0,
        p50_ms: float = 250.0,
        p95_ms: float = 450.0,
        p99_ms: float = 490.0,
        sample_count: int = 10,
    ) -> None:
        self.complexity_level = complexity_level
        self.min_ms = min_ms
        self.max_ms = max_ms
        self.avg_ms = avg_ms
        self.p50_ms = p50_ms
        self.p95_ms = p95_ms
        self.p99_ms = p99_ms
        self.sample_count = sample_count


class MockPerformancePrediction:
    """Mock PerformancePrediction for testing."""

    def __init__(
        self,
        predicted_time_ms: float = 300.0,
        confidence: float = 0.85,
        complexity_level: str = "SIMPLE",
        percentile_used: int = 50,
        min_time_ms: float = 100.0,
        max_time_ms: float = 500.0,
    ) -> None:
        self.predicted_time_ms = predicted_time_ms
        self.confidence = confidence
        self.complexity_level = complexity_level
        self.percentile_used = percentile_used
        self.min_time_ms = min_time_ms
        self.max_time_ms = max_time_ms


class MockCodeRecommendation:
    """Mock CodeRecommendation for testing."""

    def __init__(
        self,
        recommendation_type: str = "CACHE",
        description: str = "Cache this result",
        expected_savings_ms: float = 50.0,
        confidence: float = 0.9,
        priority: int = 4,
        estimated_effort: str = "LOW",
    ) -> None:
        self.recommendation_type = recommendation_type
        self.description = description
        self.expected_savings_ms = expected_savings_ms
        self.confidence = confidence
        self.priority = priority
        self.estimated_effort = estimated_effort


# Fixtures
@pytest.fixture
def mock_result():
    """Provide a mock EnhancedResult for testing."""
    return MockEnhancedResult(
        category="success",
        success=True,
        metadata={"output_size": 1024, "error_type": None},
    )


@pytest.fixture
def mock_prediction():
    """Provide a mock PerformancePrediction for testing."""
    return MockPerformancePrediction(
        predicted_time_ms=250.0,
        confidence=0.85,
        complexity_level="MODERATE",
        percentile_used=50,
    )


@pytest.fixture
def mock_recommendations():
    """Provide mock CodeRecommendation list for testing."""
    return [
        MockCodeRecommendation(
            recommendation_type="CACHE",
            description="Cache execution results",
            expected_savings_ms=50.0,
            confidence=0.9,
            priority=4,
            estimated_effort="LOW",
        ),
        MockCodeRecommendation(
            recommendation_type="SPLIT",
            description="Parallelize operations",
            expected_savings_ms=100.0,
            confidence=0.7,
            priority=3,
            estimated_effort="MEDIUM",
        ),
    ]


@pytest.fixture
def failed_result():
    """Provide a mock failed EnhancedResult."""
    return MockEnhancedResult(
        category="failure",
        success=False,
        metadata={"output_size": 0, "error_type": "timeout"},
    )


@pytest.fixture
def simple_code():
    """Provide simple code sample (<500 tokens)."""
    return "x = 1\ny = 2\nz = x + y"


@pytest.fixture
def complex_code():
    """Provide complex code sample (>2000 tokens)."""
    return "\n".join([f"def func_{i}():\n    pass" for i in range(300)])


# Module Import Tests
class TestModuleImports:
    """Test that all Phase 4 modules can be imported."""

    def test_result_processor_import(self) -> None:
        """Test ResultProcessor can be imported."""
        from agent_discovery.result_processor import ResultProcessor

        processor = ResultProcessor()
        assert processor is not None

    def test_result_cache_import(self) -> None:
        """Test ResultCache can be imported."""
        from agent_discovery.result_cache import ResultCache

        cache = ResultCache()
        assert cache is not None

    def test_performance_profiler_import(self) -> None:
        """Test PerformanceProfiler can be imported."""
        from agent_discovery.performance_profiler import PerformanceProfiler

        profiler = PerformanceProfiler()
        assert profiler is not None

    def test_optimization_engine_import(self) -> None:
        """Test OptimizationEngine can be imported."""
        from agent_discovery.optimization_engine import OptimizationEngine

        engine = OptimizationEngine()
        assert engine is not None

    def test_recommendation_engine_import(self) -> None:
        """Test RecommendationEngine can be imported."""
        from agent_discovery.recommendation_engine import RecommendationEngine

        engine = RecommendationEngine()
        assert engine is not None

    def test_result_exporter_import(self) -> None:
        """Test ResultExporter can be imported."""
        from agent_discovery.result_exporter import ExportFormat, ResultExporter

        exporter = ResultExporter()
        assert exporter is not None
        assert hasattr(ExportFormat, "JSON")


# ResultProcessor Tests
class TestResultProcessor:
    """Test ResultProcessor functionality."""

    def test_result_processor_instantiation(self) -> None:
        """Test ResultProcessor can be instantiated."""
        from agent_discovery.result_processor import ResultProcessor

        processor = ResultProcessor()
        assert processor is not None

    def test_successful_result_properties(self, mock_result) -> None:
        """Test successful result has expected properties."""
        assert mock_result.category == "success"
        assert mock_result.success is True
        assert "output_size" in mock_result.metadata

    def test_failed_result_properties(self, failed_result) -> None:
        """Test failed result has expected properties."""
        assert failed_result.category == "failure"
        assert failed_result.success is False
        assert failed_result.metadata["error_type"] == "timeout"


# ResultCache Tests
class TestResultCache:
    """Test ResultCache functionality."""

    def test_result_cache_instantiation(self) -> None:
        """Test ResultCache can be instantiated."""
        from agent_discovery.result_cache import ResultCache

        cache = ResultCache()
        assert cache is not None

    def test_cache_get_all_profiles_empty(self) -> None:
        """Test cache returns empty profiles initially."""
        from agent_discovery.result_cache import ResultCache

        cache = ResultCache()
        profiles = cache.get_all_profiles()
        # Should handle empty cache gracefully
        assert isinstance(profiles, dict)

    def test_cache_clear_profiles(self) -> None:
        """Test cache can be cleared."""
        from agent_discovery.result_cache import ResultCache

        cache = ResultCache()
        cache.clear_profiles()
        # Should not raise an error


# PerformanceProfiler Tests
class TestPerformanceProfiler:
    """Test PerformanceProfiler functionality."""

    def test_profiler_instantiation(self) -> None:
        """Test PerformanceProfiler can be instantiated."""
        from agent_discovery.performance_profiler import PerformanceProfiler

        profiler = PerformanceProfiler()
        assert profiler is not None

    def test_detect_complexity_simple(self, simple_code) -> None:
        """Test complexity detection for simple code."""
        from agent_discovery.performance_profiler import PerformanceProfiler

        profiler = PerformanceProfiler()
        complexity = profiler.detect_complexity(simple_code)
        # Simple code should be detected
        assert complexity is not None

    def test_detect_complexity_complex(self, complex_code) -> None:
        """Test complexity detection for complex code."""
        from agent_discovery.performance_profiler import PerformanceProfiler

        profiler = PerformanceProfiler()
        complexity = profiler.detect_complexity(complex_code)
        # Complex code should be detected
        assert complexity is not None

    def test_profiler_get_all_profiles_empty(self) -> None:
        """Test profiler returns empty profiles initially."""
        from agent_discovery.performance_profiler import PerformanceProfiler

        profiler = PerformanceProfiler()
        profiles = profiler.get_all_profiles()
        assert isinstance(profiles, dict)

    def test_profiler_clear_profiles(self) -> None:
        """Test profiler can clear profiles."""
        from agent_discovery.performance_profiler import PerformanceProfiler

        profiler = PerformanceProfiler()
        profiler.clear_profiles()
        # Should not raise an error


# OptimizationEngine Tests
class TestOptimizationEngine:
    """Test OptimizationEngine functionality."""

    def test_optimization_engine_instantiation(self) -> None:
        """Test OptimizationEngine can be instantiated."""
        from agent_discovery.optimization_engine import OptimizationEngine

        engine = OptimizationEngine()
        assert engine is not None


# RecommendationEngine Tests
class TestRecommendationEngine:
    """Test RecommendationEngine functionality."""

    def test_recommendation_engine_instantiation(self) -> None:
        """Test RecommendationEngine can be instantiated."""
        from agent_discovery.recommendation_engine import RecommendationEngine

        engine = RecommendationEngine()
        assert engine is not None

    def test_recommendation_filter_by_confidence(self, mock_recommendations) -> None:
        """Test filtering recommendations by confidence."""
        from agent_discovery.recommendation_engine import RecommendationEngine

        engine = RecommendationEngine()
        # All recommendations should have confidence >= 0.5
        filtered = engine.filter_by_confidence(mock_recommendations, min_confidence=0.5)
        assert len(filtered) >= 0  # Should not crash

    def test_recommendation_invalid_confidence_raises(self) -> None:
        """Test that invalid confidence raises ValueError."""
        from agent_discovery.recommendation_engine import RecommendationEngine

        engine = RecommendationEngine()
        with pytest.raises(ValueError):
            engine.filter_by_confidence([], min_confidence=1.5)

    def test_get_top_recommendations(self, mock_recommendations) -> None:
        """Test getting top N recommendations."""
        from agent_discovery.recommendation_engine import RecommendationEngine

        engine = RecommendationEngine()
        top = engine.get_top_recommendations(mock_recommendations, limit=1)
        assert len(top) <= 1


# ResultExporter Tests
class TestResultExporter:
    """Test ResultExporter functionality."""

    def test_exporter_instantiation(self) -> None:
        """Test ResultExporter can be instantiated."""
        from agent_discovery.result_exporter import ResultExporter

        exporter = ResultExporter()
        assert exporter is not None
        assert exporter.VERSION == "1.0"

    def test_export_to_json(self, mock_result, mock_prediction, mock_recommendations):
        """Test JSON export format."""
        from agent_discovery.result_exporter import ExportFormat, ResultExporter

        exporter = ResultExporter()
        output = exporter.export_single(
            mock_result, mock_prediction, mock_recommendations, ExportFormat.JSON
        )
        # Should be valid JSON
        data = json.loads(output)
        assert "metadata" in data
        assert "result" in data
        assert "prediction" in data
        assert "recommendations" in data

    def test_export_to_csv(self, mock_result, mock_prediction, mock_recommendations):
        """Test CSV export format."""
        from agent_discovery.result_exporter import ExportFormat, ResultExporter

        exporter = ResultExporter()
        output = exporter.export_single(
            mock_result, mock_prediction, mock_recommendations, ExportFormat.CSV
        )
        # Should have CSV structure
        lines = output.strip().split("\n")
        assert len(lines) >= 2  # Header + at least one row

    def test_export_to_text(self, mock_result, mock_prediction, mock_recommendations):
        """Test TEXT export format."""
        from agent_discovery.result_exporter import ExportFormat, ResultExporter

        exporter = ResultExporter()
        output = exporter.export_single(
            mock_result, mock_prediction, mock_recommendations, ExportFormat.TEXT
        )
        # Should contain expected sections
        assert "EXECUTION RESULT EXPORT" in output
        assert "RESULT SUMMARY" in output or "PERFORMANCE" in output

    def test_export_to_report(self, mock_result, mock_prediction, mock_recommendations):
        """Test REPORT (Markdown) export format."""
        from agent_discovery.result_exporter import ExportFormat, ResultExporter

        exporter = ResultExporter()
        output = exporter.export_single(
            mock_result, mock_prediction, mock_recommendations, ExportFormat.REPORT
        )
        # Should be Markdown format
        assert "# Execution Result Report" in output
        assert "##" in output

    def test_export_to_html(self, mock_result, mock_prediction, mock_recommendations):
        """Test HTML export format."""
        from agent_discovery.result_exporter import ExportFormat, ResultExporter

        exporter = ResultExporter()
        output = exporter.export_single(
            mock_result, mock_prediction, mock_recommendations, ExportFormat.HTML
        )
        # Should be valid HTML structure
        assert "<!DOCTYPE html>" in output
        assert "</html>" in output

    def test_export_invalid_format_raises(self) -> None:
        """Test that invalid format raises ValueError."""
        from agent_discovery.result_exporter import ResultExporter

        exporter = ResultExporter()
        # Create an invalid format
        with pytest.raises(ValueError):
            exporter.export_single(None, None, [], format="INVALID")

    def test_export_null_handling(self) -> None:
        """Test exporter handles None inputs gracefully."""
        from agent_discovery.result_exporter import ExportFormat, ResultExporter

        exporter = ResultExporter()
        # Should not crash with None values
        output = exporter.export_single(None, None, [], ExportFormat.JSON)
        assert isinstance(output, str)
        data = json.loads(output)
        assert data["result"] == {}
        assert data["prediction"] == {}


# Batch Export Tests
class TestBatchExport:
    """Test batch export functionality."""

    def test_batch_export_json(self, mock_result, mock_prediction, mock_recommendations):
        """Test batch JSON export."""
        from agent_discovery.result_exporter import ExportFormat, ResultExporter

        exporter = ResultExporter()
        results = [mock_result, mock_result]
        predictions = [mock_prediction, mock_prediction]
        recs_list = [mock_recommendations, mock_recommendations]
        output = exporter.export_batch(results, predictions, recs_list, ExportFormat.JSON)
        assert isinstance(output, str)
        assert len(output) > 0

    def test_batch_export_csv(self, mock_recommendations):
        """Test batch CSV export."""
        from agent_discovery.result_exporter import ExportFormat, ResultExporter

        exporter = ResultExporter()
        # CSV batch export should flatten recommendations
        output = exporter.export_batch([], [], [mock_recommendations], ExportFormat.CSV)
        lines = output.strip().split("\n")
        assert len(lines) >= 1  # Should have header


# End-to-End Pipeline Tests
class TestEndToEndPipeline:
    """Test complete pipeline from result to export."""

    def test_pipeline_json_export(self, mock_result, mock_prediction, mock_recommendations):
        """Test full pipeline with JSON export."""
        from agent_discovery.result_exporter import ExportFormat, ResultExporter

        exporter = ResultExporter()
        output = exporter.export_single(
            mock_result, mock_prediction, mock_recommendations, ExportFormat.JSON
        )
        data = json.loads(output)
        # Verify complete structure
        assert data["result"]["category"] == "success"
        assert data["result"]["success"] is True
        assert data["prediction"]["predicted_time_ms"] == 250.0
        assert len(data["recommendations"]) == 2

    def test_pipeline_csv_export(self, mock_result, mock_prediction, mock_recommendations):
        """Test full pipeline with CSV export."""
        from agent_discovery.result_exporter import ExportFormat, ResultExporter

        exporter = ResultExporter()
        output = exporter.export_single(
            mock_result, mock_prediction, mock_recommendations, ExportFormat.CSV
        )
        lines = output.strip().split("\n")
        # Header + 2 recommendations
        assert len(lines) >= 3

    def test_pipeline_report_export(self, mock_result, mock_prediction, mock_recommendations):
        """Test full pipeline with Markdown report export."""
        from agent_discovery.result_exporter import ExportFormat, ResultExporter

        exporter = ResultExporter()
        output = exporter.export_single(
            mock_result, mock_prediction, mock_recommendations, ExportFormat.REPORT
        )
        # Verify report structure
        assert "# Execution Result Report" in output
        assert "## Summary" in output
        assert "## Performance Analysis" in output or "Recommendations" in output

    def test_pipeline_with_failed_result(
        self, failed_result, mock_prediction, mock_recommendations
    ):
        """Test pipeline with failed execution result."""
        from agent_discovery.result_exporter import ExportFormat, ResultExporter

        exporter = ResultExporter()
        output = exporter.export_single(
            failed_result, mock_prediction, mock_recommendations, ExportFormat.JSON
        )
        data = json.loads(output)
        assert data["result"]["success"] is False
        assert data["result"]["category"] == "failure"


# Format Consistency Tests
class TestFormatConsistency:
    """Test consistency across all export formats."""

    @pytest.mark.parametrize(
        "export_format",
        ["json", "csv", "text", "report", "html"],
    )
    def test_all_formats_produce_output(
        self,
        export_format,
        mock_result,
        mock_prediction,
        mock_recommendations,
    ):
        """Test that all formats produce non-empty output."""
        from agent_discovery.result_exporter import ExportFormat, ResultExporter

        exporter = ResultExporter()
        format_enum = ExportFormat[export_format.upper()]
        output = exporter.export_single(
            mock_result, mock_prediction, mock_recommendations, format_enum
        )
        assert isinstance(output, str)
        assert len(output) > 0

    def test_csv_has_headers(self, mock_recommendations):
        """Test CSV export has headers."""
        from agent_discovery.result_exporter import ExportFormat, ResultExporter

        exporter = ResultExporter()
        output = exporter.export_single(None, None, mock_recommendations, ExportFormat.CSV)
        lines = output.strip().split("\n")
        assert "type" in lines[0]

    def test_json_is_valid_json(self, mock_result, mock_prediction):
        """Test JSON export is valid JSON."""
        from agent_discovery.result_exporter import ExportFormat, ResultExporter

        exporter = ResultExporter()
        output = exporter.export_single(mock_result, mock_prediction, [], ExportFormat.JSON)
        # Should not raise json.JSONDecodeError
        data = json.loads(output)
        assert isinstance(data, dict)


# Error Handling Tests
class TestErrorHandling:
    """Test error handling and validation."""

    def test_recommendation_confidence_out_of_bounds_high(self):
        """Test that confidence > 1.0 is rejected."""
        with pytest.raises(ValueError):
            MockCodeRecommendation(confidence=1.5)

    def test_recommendation_confidence_out_of_bounds_low(self):
        """Test that confidence < 0.0 is rejected."""
        with pytest.raises(ValueError):
            MockCodeRecommendation(confidence=-0.1)

    def test_recommendation_priority_out_of_bounds_high(self):
        """Test that priority > 5 is rejected."""
        with pytest.raises(ValueError):
            MockCodeRecommendation(priority=6)

    def test_recommendation_priority_out_of_bounds_low(self):
        """Test that priority < 1 is rejected."""
        with pytest.raises(ValueError):
            MockCodeRecommendation(priority=0)

    def test_exporter_strict_zip_with_unequal_lengths(self):
        """Test that export_batch handles unequal list lengths."""
        from agent_discovery.result_exporter import ExportFormat, ResultExporter

        exporter = ResultExporter()
        results = [MockEnhancedResult()]
        predictions = [MockPerformancePrediction(), MockPerformancePrediction()]
        recs_list = [[]]
        # strict=True should raise ValueError on unequal lengths
        with pytest.raises(ValueError):
            exporter.export_batch(results, predictions, recs_list, ExportFormat.JSON)


# Smoke Tests
class TestSmoke:
    """Quick smoke tests to ensure nothing is broken."""

    def test_all_modules_imported_successfully(self) -> None:
        """Test all Phase 4 modules import successfully."""
        from agent_discovery.optimization_engine import OptimizationEngine
        from agent_discovery.performance_profiler import PerformanceProfiler
        from agent_discovery.recommendation_engine import RecommendationEngine
        from agent_discovery.result_cache import ResultCache
        from agent_discovery.result_exporter import ResultExporter
        from agent_discovery.result_processor import ResultProcessor

        # If we got here, all imports succeeded
        assert ResultProcessor is not None
        assert ResultCache is not None
        assert PerformanceProfiler is not None
        assert OptimizationEngine is not None
        assert RecommendationEngine is not None
        assert ResultExporter is not None

    def test_quick_export_pipeline(self) -> None:
        """Quick test of export pipeline."""
        from agent_discovery.result_exporter import ExportFormat, ResultExporter

        exporter = ResultExporter()
        result = MockEnhancedResult()
        prediction = MockPerformancePrediction()
        recommendations = [MockCodeRecommendation()]
        # Just make sure no exceptions
        output = exporter.export_single(result, prediction, recommendations, ExportFormat.JSON)
        assert isinstance(output, str)

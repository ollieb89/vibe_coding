"""Agent Discovery System - Intelligent agent recommendation for GitHub Copilot.

This package provides tools to discover, search, and recommend GitHub Copilot agents,
prompts, instructions, and chatmodes based on codebase analysis and user needs.
"""

from agent_discovery.analyzer import AnalysisReport, ExecutionAnalyzer, ExecutionMetrics
from agent_discovery.llm_validator import LLMValidator, ValidationResult
from agent_discovery.logging import ExecutionLogger, LogEntry, LogLevel, MetricsCollector
from agent_discovery.mock_executor import MockExecutionResult, MockExecutor, SimulationType
from agent_discovery.models import Agent, AgentMatch, AgentType, CodebaseProfile
from agent_discovery.optimization_engine import (
    OptimizationEngine,
    OptimizationRecommendation,
    OptimizationStrategy,
    PatternAnalysis,
)
from agent_discovery.orchestrator import (
    ExecutionMode,
    ExecutionOrchestrator,
    OrchestratedResult,
    RoutingDecision,
)
from agent_discovery.performance_profiler import (
    ComplexityLevel,
    ExecutionProfile,
    PerformancePrediction,
    PerformanceProfiler,
)
from agent_discovery.real_executor import ExecutionResult, RealExecutor
from agent_discovery.recommendation_engine import (
    CodeRecommendation,
    RecommendationEngine,
    RecommendationType,
)
from agent_discovery.result_cache import CacheEntry, CacheStatistics, ResultCache
from agent_discovery.result_exporter import (
    ExportFormat,
    ExportMetadata,
    ResultExporter,
)

# Phase 4 - Results Optimization Pipeline
from agent_discovery.result_processor import (
    EnhancedResult,
    ErrorType,
    ResultCategory,
    ResultProcessor,
)

__all__ = [
    # Phase 3.1.1 - RealExecutor
    "RealExecutor",
    "ExecutionResult",
    # Phase 3.2.1 - MockExecutor
    "MockExecutor",
    "MockExecutionResult",
    "SimulationType",
    # Phase 3.2.2 - ExecutionOrchestrator
    "ExecutionOrchestrator",
    "ExecutionMode",
    "OrchestratedResult",
    "RoutingDecision",
    # Phase 3.2.3 - LLMValidator
    "LLMValidator",
    "ValidationResult",
    # Phase 3.2.4 - Analyzer
    "ExecutionAnalyzer",
    "ExecutionMetrics",
    "AnalysisReport",
    # Phase 3.2.5 - Logging
    "ExecutionLogger",
    "MetricsCollector",
    "LogEntry",
    "LogLevel",
    # Phase 4.1 - ResultProcessor
    "ResultProcessor",
    "ResultCategory",
    "ErrorType",
    "EnhancedResult",
    # Phase 4.2 - OptimizationEngine
    "OptimizationEngine",
    "OptimizationStrategy",
    "PatternAnalysis",
    "OptimizationRecommendation",
    # Phase 4.3 - ResultCache
    "ResultCache",
    "CacheEntry",
    "CacheStatistics",
    # Phase 4.4 - PerformanceProfiler
    "PerformanceProfiler",
    "ComplexityLevel",
    "ExecutionProfile",
    "PerformancePrediction",
    # Phase 4.5 - RecommendationEngine
    "RecommendationEngine",
    "RecommendationType",
    "CodeRecommendation",
    # Phase 4.6 - ResultExporter
    "ResultExporter",
    "ExportFormat",
    "ExportMetadata",
    # Original exports
    "Agent",
    "AgentMatch",
    "AgentType",
    "CodebaseProfile",
]

__version__ = "0.1.0"

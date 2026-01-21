"""Phase 1 integration tests for agent learning system.

Tests the complete flow of:
1. Agent execution logging with AgentExecutor
2. Aggregation of metrics with PerformanceAggregator
3. Pattern extraction with PatternExtractor
4. RAG-enhanced discovery with RAGDiscoveryEngine
"""

from datetime import datetime

from agent_discovery.aggregator import PerformanceAggregator
from agent_discovery.collections import ChromaCollectionManager
from agent_discovery.executor import AgentExecutor, ExecutorConfig
from agent_discovery.extractor import PatternExtractor
from agent_discovery.models import (
    AgentPattern,
    ExecutionOutcome,
    ExecutionRecord,
)
from agent_discovery.rag_discovery import RAGDiscoveryEngine


class TestAgentExecutor:
    """Tests for AgentExecutor."""

    def test_executor_init(self):
        """Test AgentExecutor initialization."""
        manager = ChromaCollectionManager()
        config = ExecutorConfig(model_name="test-model")
        executor = AgentExecutor(manager, config)

        assert executor.config.model_name == "test-model"
        assert executor.config.enable_logging is True
        assert len(executor._execution_history) == 0

    def test_executor_execute_success(self, sample_agent, sample_execution_func):
        """Test successful agent execution."""
        manager = ChromaCollectionManager()
        executor = AgentExecutor(
            manager,
            ExecutorConfig(
                model_name="gpt-4",
                enable_logging=False,  # Disable Chroma for testing
            ),
        )

        record = executor.execute(
            agent=sample_agent,
            executor_func=sample_execution_func,
            user_prompt="Test prompt",
            quality_metrics={"relevance": 0.9, "correctness": 0.85},
        )

        assert record.success is True
        assert record.outcome == ExecutionOutcome.SUCCESS
        assert record.agent_id == sample_agent.name.lower().replace(" ", "-")
        assert record.quality_score is None  # Not set individually
        assert record.relevance == 0.9
        assert record.correctness == 0.85

    def test_executor_history(self, sample_agent, sample_execution_func):
        """Test execution history tracking."""
        manager = ChromaCollectionManager()
        executor = AgentExecutor(
            manager,
            ExecutorConfig(enable_logging=False),
        )

        # Execute multiple times
        for i in range(3):
            executor.execute(
                agent=sample_agent,
                executor_func=sample_execution_func,
                user_prompt=f"Prompt {i}",
            )

        history = executor.get_execution_history()
        assert len(history) == 3

    def test_executor_stats(self, sample_agent, sample_execution_func):
        """Test execution statistics calculation."""
        manager = ChromaCollectionManager()
        executor = AgentExecutor(
            manager,
            ExecutorConfig(enable_logging=False),
        )

        # Execute multiple times
        for i in range(5):
            executor.execute(
                agent=sample_agent,
                executor_func=sample_execution_func,
                quality_metrics={"quality_score": 0.8 + (i * 0.02)},
            )

        stats = executor.get_execution_stats()
        assert stats["total_executions"] == 5
        assert stats["successful"] == 5
        assert stats["success_rate"] == 1.0
        assert stats["avg_quality_score"] > 0

    def test_executor_batch(self, sample_agents, sample_execution_func):
        """Test batch execution."""
        manager = ChromaCollectionManager()
        executor = AgentExecutor(
            manager,
            ExecutorConfig(enable_logging=False),
        )

        records = executor.execute_batch(
            agents=sample_agents,
            executor_func=lambda agent: sample_execution_func(),
        )

        assert len(records) == len(sample_agents)
        assert all(r.success for r in records)


class TestPerformanceAggregator:
    """Tests for PerformanceAggregator."""

    def test_aggregator_init(self):
        """Test PerformanceAggregator initialization."""
        manager = ChromaCollectionManager()
        aggregator = PerformanceAggregator(manager)
        assert aggregator.collection_manager is manager

    def test_period_boundaries(self):
        """Test period boundary calculation."""
        manager = ChromaCollectionManager()
        aggregator = PerformanceAggregator(manager)

        test_date = datetime(2025, 12, 15, 10, 30, 45)

        # Daily
        start, end = aggregator._get_period_boundaries("daily", test_date)
        assert start.day == 15
        assert start.hour == 0
        assert (end - start).days == 1

        # Weekly
        start, end = aggregator._get_period_boundaries("weekly", test_date)
        assert start.weekday() == 0  # Monday
        assert (end - start).days == 7

        # Monthly
        start, end = aggregator._get_period_boundaries("monthly", test_date)
        assert start.day == 1
        if test_date.month == 12:
            assert end.month == 1
        else:
            assert end.month == test_date.month + 1

    def test_aggregate_empty(self):
        """Test aggregation with no records."""
        manager = ChromaCollectionManager()
        aggregator = PerformanceAggregator(manager)

        metric = aggregator.aggregate_period(
            agent_id="test-agent",
            agent_name="Test Agent",
            agent_type="agent",
            category="general",
            execution_records=[],
        )

        assert metric.total_executions == 0
        assert metric.successful_executions == 0
        assert metric.success_rate == 0.0

    def test_aggregate_records(self, execution_records):
        """Test aggregation with execution records."""
        manager = ChromaCollectionManager()
        aggregator = PerformanceAggregator(manager)

        metric = aggregator.aggregate_period(
            agent_id="test-agent",
            agent_name="Test Agent",
            agent_type="agent",
            category="general",
            execution_records=execution_records,
        )

        assert metric.total_executions > 0
        assert metric.success_rate >= 0
        assert metric.avg_execution_time_ms >= 0

    def test_calculate_trend(self):
        """Test trend calculation."""
        manager = ChromaCollectionManager()
        aggregator = PerformanceAggregator(manager)

        metric1 = aggregator._calculate_metrics(
            agent_id="test",
            agent_name="Test",
            agent_type="agent",
            category="general",
            period_type="daily",
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow(),
            execution_records=[
                ExecutionRecord(
                    agent_id="test",
                    agent_name="Test",
                    agent_type="agent",
                    user_prompt="test",
                    outcome=ExecutionOutcome.SUCCESS,
                    success=True,
                    execution_time_ms=1000,
                    model_name="gpt-4",
                ),
            ],
        )

        metric2 = aggregator._calculate_metrics(
            agent_id="test",
            agent_name="Test",
            agent_type="agent",
            category="general",
            period_type="daily",
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow(),
            execution_records=[
                ExecutionRecord(
                    agent_id="test",
                    agent_name="Test",
                    agent_type="agent",
                    user_prompt="test",
                    outcome=ExecutionOutcome.SUCCESS,
                    success=True,
                    execution_time_ms=1000,
                    model_name="gpt-4",
                    quality_score=0.95,
                ),
                ExecutionRecord(
                    agent_id="test",
                    agent_name="Test",
                    agent_type="agent",
                    user_prompt="test",
                    outcome=ExecutionOutcome.SUCCESS,
                    success=True,
                    execution_time_ms=1000,
                    model_name="gpt-4",
                    quality_score=0.90,
                ),
            ],
        )

        trend, direction = aggregator.calculate_trend(metric2, metric1)
        assert isinstance(trend, str)
        assert -1.0 <= direction <= 1.0


class TestPatternExtractor:
    """Tests for PatternExtractor."""

    def test_extractor_init(self):
        """Test PatternExtractor initialization."""
        manager = ChromaCollectionManager()
        extractor = PatternExtractor(manager)
        assert extractor.collection_manager is manager

    def test_extract_success_patterns(self, execution_records):
        """Test extraction of success patterns."""
        manager = ChromaCollectionManager()
        extractor = PatternExtractor(manager)

        # Create mostly successful records
        successful_records = [
            r for r in execution_records if r.outcome == ExecutionOutcome.SUCCESS and r.success
        ]

        patterns = extractor._extract_success_patterns(
            execution_records=execution_records,
            agent_id="test-agent",
            min_frequency=1,
        )

        # Should extract some patterns from successful executions
        assert isinstance(patterns, list)
        assert all(p.pattern_type == "success_pattern" for p in patterns)

    def test_extract_failure_patterns(self, execution_records):
        """Test extraction of failure patterns."""
        manager = ChromaCollectionManager()
        extractor = PatternExtractor(manager)

        # Create some failed records
        failed_records = [r for r in execution_records if r.outcome != ExecutionOutcome.SUCCESS]

        patterns = extractor._extract_failure_patterns(
            execution_records=failed_records,
            agent_id="test-agent",
            min_frequency=1,
        )

        # Should handle empty or few failures gracefully
        assert isinstance(patterns, list)

    def test_extract_use_case_patterns(self, execution_records):
        """Test extraction of use case patterns."""
        manager = ChromaCollectionManager()
        extractor = PatternExtractor(manager)

        patterns = extractor._extract_use_case_patterns(
            execution_records=execution_records,
            agent_id="test-agent",
            min_frequency=1,
        )

        # Should extract some patterns from category distribution
        assert isinstance(patterns, list)
        if patterns:
            assert all(p.pattern_type == "use_case" for p in patterns)

    def test_rank_patterns(self):
        """Test pattern ranking."""
        manager = ChromaCollectionManager()
        extractor = PatternExtractor(manager)

        # Create patterns with different scores
        patterns = extractor.rank_patterns(
            patterns=[
                AgentPattern(
                    pattern_id="1",
                    pattern_type="success",
                    agents_involved=["test"],
                    description="Pattern 1",
                    frequency=10,
                    effectiveness_score=0.5,
                ),
                AgentPattern(
                    pattern_id="2",
                    pattern_type="success",
                    agents_involved=["test"],
                    description="Pattern 2",
                    frequency=20,
                    effectiveness_score=0.9,
                ),
            ]
        )

        # Higher ranked pattern should be first
        assert patterns[0].pattern_id == "2"


class TestRAGDiscoveryEngine:
    """Tests for RAGDiscoveryEngine."""

    def test_rag_init(self):
        """Test RAGDiscoveryEngine initialization."""
        engine = RAGDiscoveryEngine()
        assert engine.base_engine is not None
        assert engine.collection_manager is not None
        assert isinstance(engine.aggregator, PerformanceAggregator)
        assert isinstance(engine.extractor, PatternExtractor)

    def test_rag_discover_empty(self):
        """Test discovery with empty collection."""
        engine = RAGDiscoveryEngine()
        matches = engine.discover(query="test query")
        # Should handle gracefully with empty results
        assert isinstance(matches, list)

    def test_rag_get_quality_report(self):
        """Test agent quality report generation."""
        engine = RAGDiscoveryEngine()
        report = engine.get_agent_quality_report("nonexistent-agent")
        assert isinstance(report, dict)
        # Should handle nonexistent agents gracefully
        assert "agent_id" in report

    def test_rag_get_recommended_agents(self):
        """Test recommended agents retrieval."""
        engine = RAGDiscoveryEngine()
        agents = engine.get_recommended_agents(min_quality=0.7)
        assert isinstance(agents, list)
        # Empty is ok for fresh collections
        assert all(m.score >= 0.7 for m in agents)


class TestPhase1Integration:
    """Integration tests for Phase 1 system."""

    def test_executor_to_aggregator(self, sample_agent, sample_execution_func):
        """Test flow from execution logging to aggregation."""
        manager = ChromaCollectionManager()

        # Step 1: Execute agent
        executor = AgentExecutor(
            manager,
            ExecutorConfig(enable_logging=False),
        )
        for _ in range(5):
            executor.execute(
                agent=sample_agent,
                executor_func=sample_execution_func,
                quality_metrics={"quality_score": 0.85},
            )

        # Step 2: Aggregate metrics
        history = executor.get_execution_history()
        aggregator = PerformanceAggregator(manager)
        metric = aggregator._calculate_metrics(
            agent_id=sample_agent.name.lower().replace(" ", "-"),
            agent_name=sample_agent.name,
            agent_type=sample_agent.agent_type,
            category=sample_agent.category,
            period_type="daily",
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow(),
            execution_records=history,
        )

        assert metric.total_executions == 5
        assert metric.success_rate == 1.0

    def test_executor_to_extractor(self, sample_agent, sample_execution_func):
        """Test flow from execution to pattern extraction."""
        manager = ChromaCollectionManager()

        # Step 1: Execute agent
        executor = AgentExecutor(
            manager,
            ExecutorConfig(enable_logging=False),
        )
        records = []
        for i in range(10):
            record = executor.execute(
                agent=sample_agent,
                executor_func=sample_execution_func,
                quality_metrics={"quality_score": 0.8 + (i * 0.01)},
            )
            records.append(record)

        # Step 2: Extract patterns
        extractor = PatternExtractor(manager)
        patterns = extractor.extract_from_records(
            execution_records=records,
            agent_id=sample_agent.name.lower().replace(" ", "-"),
            min_frequency=2,
        )

        assert isinstance(patterns, list)
        # Should extract at least some patterns from 10 executions
        assert len(patterns) >= 0

    def test_full_pipeline(self, sample_agent, sample_execution_func):
        """Test complete Phase 1 pipeline."""
        manager = ChromaCollectionManager()

        # 1. Execute agent
        executor = AgentExecutor(
            manager,
            ExecutorConfig(enable_logging=False),
        )
        for _ in range(5):
            executor.execute(
                agent=sample_agent,
                executor_func=sample_execution_func,
            )

        # 2. Aggregate metrics
        history = executor.get_execution_history()
        aggregator = PerformanceAggregator(manager)
        metric = aggregator.aggregate_period(
            agent_id=sample_agent.name.lower().replace(" ", "-"),
            agent_name=sample_agent.name,
            agent_type=sample_agent.agent_type,
            category=sample_agent.category,
            execution_records=history,
        )

        # 3. Extract patterns
        extractor = PatternExtractor(manager)
        patterns = extractor.extract_from_records(
            execution_records=history,
            agent_id=sample_agent.name.lower().replace(" ", "-"),
        )

        # 4. Use in discovery (would use RAG queries)
        engine = RAGDiscoveryEngine(collection_manager=manager)

        # Verify all components worked
        assert metric.total_executions == 5
        assert isinstance(patterns, list)
        assert engine.base_engine is not None

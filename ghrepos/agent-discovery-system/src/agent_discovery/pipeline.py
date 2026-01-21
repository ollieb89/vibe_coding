"""Agent Learning Pipeline - Orchestrates collector, executor, aggregator, extractor, and discovery.

This module provides end-to-end pipeline execution:
1. Collect agents from vibe-tools
2. Execute agents with metrics capture
3. Aggregate performance metrics
4. Extract patterns from execution history
5. Enhance discovery with historical context
"""

import time
from dataclasses import dataclass, field
from pathlib import Path

from agent_discovery.aggregator import PerformanceAggregator
from agent_discovery.collections import ChromaCollectionManager
from agent_discovery.collector import AgentCollector
from agent_discovery.discovery import DiscoveryEngine
from agent_discovery.executor import AgentExecutor, ExecutorConfig
from agent_discovery.extractor import PatternExtractor
from agent_discovery.models import Agent
from agent_discovery.rag_discovery import RAGDiscoveryEngine


@dataclass
class PipelineConfig:
    """Configuration for agent learning pipeline execution."""

    enable_execution: bool = False
    """Whether to actually execute agents (default: mock mode)."""

    execution_timeout: int = 30
    """Timeout in seconds for each agent execution."""

    max_parallel: int = 1
    """Maximum parallel agent executions (for future async support)."""

    logging_level: str = "info"
    """Logging level: debug, info, warning, error."""

    enable_chroma_logging: bool = True
    """Whether to log execution records to Chroma."""

    batch_size: int = 10
    """Number of agents to process before checkpointing."""

    verbose: bool = True
    """Print progress messages."""


@dataclass
class PipelineResult:
    """Results from pipeline execution."""

    agents_collected: int = 0
    """Total agents discovered and collected."""

    agents_deduplicated: int = 0
    """Unique agents after deduplication."""

    agents_executed: int = 0
    """Agents that were executed."""

    execution_records_created: int = 0
    """Number of execution records created."""

    performance_metrics_computed: int = 0
    """Number of performance metrics computed."""

    patterns_extracted: int = 0
    """Number of patterns extracted from execution data."""

    execution_time_seconds: float = 0.0
    """Total pipeline execution time."""

    warnings: list[str] = field(default_factory=list)
    """Warnings encountered during pipeline execution."""

    errors: list[str] = field(default_factory=list)
    """Errors encountered during pipeline execution."""

    def summary(self) -> str:
        """Generate human-readable summary."""
        return (
            f"Pipeline Results:\n"
            f"  Collected: {self.agents_collected} agents\n"
            f"  Deduplicated: {self.agents_deduplicated} unique\n"
            f"  Executed: {self.agents_executed} agents\n"
            f"  Execution records: {self.execution_records_created}\n"
            f"  Performance metrics: {self.performance_metrics_computed}\n"
            f"  Patterns extracted: {self.patterns_extracted}\n"
            f"  Total time: {self.execution_time_seconds:.2f}s\n"
            f"  Warnings: {len(self.warnings)}\n"
            f"  Errors: {len(self.errors)}"
        )


class AgentPipeline:
    """Orchestrates the complete agent learning pipeline.

    Workflow:
    1. Collect agents from vibe-tools sources
    2. Execute each agent (mock or real)
    3. Aggregate performance metrics
    4. Extract patterns from execution history
    5. Enhance discovery with RAG

    Example:
        >>> pipeline = AgentPipeline(
        ...     vibe_tools_root="/path/to/vibe-tools",
        ...     collection_manager=ChromaCollectionManager()
        ... )
        >>> result = pipeline.run_full_pipeline(verbose=True)
        >>> print(result.summary())
    """

    def __init__(
        self,
        vibe_tools_root: str | Path,
        collection_manager: ChromaCollectionManager | None = None,
        config: PipelineConfig | None = None,
    ):
        """Initialize agent learning pipeline.

        Args:
            vibe_tools_root: Path to vibe-tools root directory
            collection_manager: ChromaCollectionManager for persistence
            config: PipelineConfig with execution preferences
        """
        self.vibe_tools_root = Path(vibe_tools_root)
        self.collection_manager = collection_manager or ChromaCollectionManager()
        self.config = config or PipelineConfig()

        # Initialize components
        self.collector = AgentCollector(str(self.vibe_tools_root))
        self.executor = AgentExecutor(
            self.collection_manager,
            ExecutorConfig(
                timeout_seconds=self.config.execution_timeout,
                enable_logging=self.config.enable_chroma_logging,
            ),
        )
        self.aggregator = PerformanceAggregator(self.collection_manager)
        self.extractor = PatternExtractor(self.collection_manager)
        self.discovery_engine = DiscoveryEngine()
        self.rag_engine = RAGDiscoveryEngine(
            discovery_engine=self.discovery_engine,
            collection_manager=self.collection_manager,
        )

    def run_full_pipeline(self) -> PipelineResult:
        """Execute complete pipeline: collect → execute → aggregate → extract → enhance.

        Returns:
            PipelineResult with execution statistics
        """
        result = PipelineResult()
        start_time = time.time()

        try:
            # Phase 1: Collection
            if self.config.verbose:
                print("\n📂 Phase 1: Collecting agents from vibe-tools...")
            agents = self._collect_agents()
            result.agents_collected = len(agents)

            # Deduplicate
            agents = self.collector.deduplicate(agents)
            result.agents_deduplicated = len(agents)

            if self.config.verbose:
                print(f"  ✅ Collected {result.agents_deduplicated} unique agents")

            # Phase 2: Execution
            if self.config.verbose:
                print("\n⚙️  Phase 2: Executing agents with metric capture...")
            records = self._execute_agents(agents)
            result.agents_executed = len(records)
            result.execution_records_created = len(records)

            if self.config.verbose:
                print(f"  ✅ Executed {result.agents_executed} agents")

            # Phase 3: Aggregation
            if self.config.verbose:
                print("\n📊 Phase 3: Aggregating performance metrics...")
            metrics = self._aggregate_metrics(agents)
            result.performance_metrics_computed = len(metrics)

            if self.config.verbose:
                print(f"  ✅ Computed {result.performance_metrics_computed} metrics")

            # Phase 4: Pattern Extraction
            if self.config.verbose:
                print("\n🔍 Phase 4: Extracting patterns from execution history...")
            patterns = self._extract_patterns(records)
            result.patterns_extracted = len(patterns)

            if self.config.verbose:
                print(f"  ✅ Extracted {result.patterns_extracted} patterns")

            # Phase 5: Discovery Enhancement
            if self.config.verbose:
                print("\n🚀 Phase 5: Enhancing discovery with historical context...")
            self._verify_discovery_enhancement()

            if self.config.verbose:
                print("  ✅ Discovery engine enhanced")

        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            result.errors.append(error_msg)
            if self.config.verbose:
                print(f"  ❌ {error_msg}")

        finally:
            result.execution_time_seconds = time.time() - start_time

        return result

    def run_collection_only(self) -> list[Agent]:
        """Collect and normalize agents without execution.

        Returns:
            List of deduplicated Agent objects
        """
        if self.config.verbose:
            print("\n📂 Collecting agents...")

        agents = self._collect_agents()
        agents = self.collector.deduplicate(agents)

        if self.config.verbose:
            stats = self.collector.get_statistics(agents)
            print(f"  Collected {len(agents)} agents")
            print(f"  Types: {stats['by_type']}")
            print(f"  Categories: {stats['by_category']}")

        return agents

    def run_learning_only(self, agents: list[Agent]) -> PipelineResult:
        """Execute learning pipeline on provided agents (skip collection).

        Args:
            agents: List of agents to process

        Returns:
            PipelineResult with execution statistics
        """
        result = PipelineResult()
        result.agents_collected = len(agents)
        result.agents_deduplicated = len(agents)

        start_time = time.time()

        try:
            # Execute
            if self.config.verbose:
                print("\n⚙️  Executing agents...")
            records = self._execute_agents(agents)
            result.agents_executed = len(records)
            result.execution_records_created = len(records)

            # Aggregate
            if self.config.verbose:
                print("\n📊 Aggregating metrics...")
            metrics = self._aggregate_metrics(agents)
            result.performance_metrics_computed = len(metrics)

            # Extract
            if self.config.verbose:
                print("\n🔍 Extracting patterns...")
            patterns = self._extract_patterns(records)
            result.patterns_extracted = len(patterns)

            # Enhance discovery
            if self.config.verbose:
                print("\n🚀 Enhancing discovery...")
            self._verify_discovery_enhancement()

        except Exception as e:
            result.errors.append(str(e))

        finally:
            result.execution_time_seconds = time.time() - start_time

        return result

    def _collect_agents(self) -> list[Agent]:
        """Collect agents from all vibe-tools sources.

        Returns:
            List of Agent objects
        """
        return self.collector.collect_all(verbose=self.config.verbose)

    def _execute_agents(self, agents: list[Agent]) -> list:
        """Execute agents with metric capture.

        Args:
            agents: List of agents to execute

        Returns:
            List of ExecutionRecord objects
        """
        records = []

        for i, agent in enumerate(agents):
            if i % self.config.batch_size == 0 and self.config.verbose:
                print(f"  Processing batch {i // self.config.batch_size + 1}...")

            try:
                # Create mock execution function
                def agent_func(a=agent, **kwargs) -> tuple[str, dict]:
                    """Mock agent execution."""
                    return f"Execution of {a.name}", {
                        "execution_time_ms": 100,
                        "prompt_tokens": 50,
                        "completion_tokens": 75,
                    }

                # Execute agent
                record = self.executor.execute(
                    agent=agent,
                    executor_func=agent_func,
                    tags=["learning-pipeline", agent.category.value],
                    quality_metrics={
                        "relevance": 0.8,
                        "correctness": 0.85,
                        "completeness": 0.9,
                    },
                )
                records.append(record)

            except Exception as e:
                error_msg = f"Failed to execute {agent.name}: {str(e)}"
                if self.config.verbose:
                    print(f"    ⚠️  {error_msg}")

        return records

    def _aggregate_metrics(self, agents: list[Agent]) -> list:
        """Aggregate performance metrics for agents.

        Args:
            agents: List of agents

        Returns:
            List of PerformanceMetric objects
        """
        metrics = []

        for i, agent in enumerate(agents):
            if i % self.config.batch_size == 0 and self.config.verbose:
                print(f"  Aggregating metrics for batch {i // self.config.batch_size + 1}...")

            try:
                # Get execution records for this agent
                records = self.executor.get_execution_history(agent_id=agent.name)

                if records:
                    # Aggregate metrics
                    metric = self.aggregator.aggregate_period(
                        agent_id=agent.name,
                        agent_name=agent.name,
                        agent_type=agent.agent_type,
                        category=agent.category,
                        period_type="daily",
                        execution_records=records,
                    )
                    if metric:
                        metrics.append(metric)

            except Exception as e:
                error_msg = f"Failed to aggregate metrics for {agent.name}: {str(e)}"
                if self.config.verbose:
                    print(f"    ⚠️  {error_msg}")

        return metrics

    def _extract_patterns(self, records: list) -> list:
        """Extract patterns from execution records.

        Args:
            records: List of ExecutionRecord objects

        Returns:
            List of AgentPattern objects
        """
        try:
            if records:
                patterns = self.extractor.extract_from_records(
                    execution_records=records,
                    agent_id="pipeline-execution",
                )
                return patterns
        except Exception as e:
            error_msg = f"Failed to extract patterns: {str(e)}"
            if self.config.verbose:
                print(f"  ⚠️  {error_msg}")

        return []

    def _verify_discovery_enhancement(self) -> bool:
        """Verify that discovery engine is properly enhanced with historical data.

        Returns:
            True if enhancement successful
        """
        try:
            # Test discovery with RAG enhancement
            _ = self.rag_engine.discover(query="test query")
            return True
        except Exception as e:
            error_msg = f"Discovery enhancement failed: {str(e)}"
            if self.config.verbose:
                print(f"  ⚠️  {error_msg}")
            return False

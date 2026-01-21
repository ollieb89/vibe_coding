"""Pytest fixtures for Agent Enhancement System testing.

Provides sample data generators and mock Chroma collections for testing.
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from agent_discovery.models import (
    Agent,
    AgentType,
    CapabilityVector,
    Category,
    CollaborationPattern,
    Complexity,
    ExecutionOutcome,
    ExecutionRecord,
    PerformanceMetric,
)


class SampleDataGenerator:
    """Generates sample data for testing."""

    @staticmethod
    def create_execution_record(
        agent_id: str = "test-agent",
        agent_name: str = "Test Agent",
        agent_type: AgentType = AgentType.AGENT,
        success: bool = True,
        outcome: ExecutionOutcome = ExecutionOutcome.SUCCESS,
        category: Category = Category.GENERAL,
        execution_time_ms: float = 1500.0,
        quality_score: float | None = 0.9,
    ) -> ExecutionRecord:
        """Create a sample execution record."""
        return ExecutionRecord(
            record_id=str(uuid4()),
            agent_id=agent_id,
            agent_name=agent_name,
            agent_type=agent_type,
            timestamp=datetime.utcnow(),
            user_prompt="What is the best way to design a REST API?",
            prompt_anonymized="What is the best way to design a [DOMAIN] API?",
            outcome=outcome,
            success=success,
            error_message=None if success else "Agent failed to respond",
            execution_time_ms=execution_time_ms,
            prompt_tokens=450,
            completion_tokens=1200,
            total_tokens=1650,
            model_name="gpt-4",
            model_version="2025-01",
            quality_score=quality_score,
            relevance=0.95 if success else 0.3,
            correctness=0.92 if success else 0.2,
            completeness=0.88 if success else 0.1,
            category=category,
            tags=["api-design", "architecture"],
            custom_metadata={"session_id": str(uuid4())},
        )

    @staticmethod
    def create_performance_metric(
        agent_id: str = "test-agent",
        agent_name: str = "Test Agent",
        agent_type: AgentType = AgentType.AGENT,
        category: Category = Category.GENERAL,
        total_executions: int = 100,
        successful_executions: int = 85,
        success_rate: float = 0.85,
    ) -> PerformanceMetric:
        """Create a sample performance metric."""
        now = datetime.utcnow()
        return PerformanceMetric(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_type=agent_type,
            category=category,
            period_start=now - timedelta(days=1),
            period_end=now,
            period_type="daily",
            total_executions=total_executions,
            successful_executions=successful_executions,
            partial_executions=10,
            failed_executions=4,
            error_executions=1,
            success_rate=success_rate,
            partial_rate=0.10,
            failure_rate=0.04,
            avg_execution_time_ms=1250.5,
            min_execution_time_ms=500.0,
            max_execution_time_ms=3500.0,
            avg_prompt_tokens=450.5,
            avg_completion_tokens=1200.3,
            avg_total_tokens=1650.8,
            total_tokens_used=165080,
            avg_quality_score=0.88,
            avg_relevance=0.91,
            avg_correctness=0.87,
            avg_completeness=0.85,
            cost_per_execution=0.025,
            total_cost=2.50,
            trend="improving",
            trend_direction=0.05,
            models_used=["gpt-4", "gpt-3.5-turbo"],
        )

    @staticmethod
    def create_collaboration_pattern(
        primary_agent: str = "architect-agent",
        collaborating_agents: list[str] | None = None,
    ) -> CollaborationPattern:
        """Create a sample collaboration pattern."""
        if collaborating_agents is None:
            collaborating_agents = ["backend-specialist", "security-expert"]

        return CollaborationPattern(
            pattern_id=str(uuid4()),
            primary_agent=primary_agent,
            collaborating_agents=collaborating_agents,
            pattern_name="API Architecture with Security Review",
            description=(
                "The architecture agent designs the API structure, "
                "then collaborates with the backend specialist for implementation "
                "details and the security expert for threat modeling."
            ),
            success_rate=0.92,
            frequency=45,
            use_cases=[
                "Designing secure REST APIs",
                "Planning microservices architecture",
                "Creating API security policies",
            ],
            discovered_date=datetime.utcnow() - timedelta(days=7),
            last_used=datetime.utcnow() - timedelta(hours=2),
            effectiveness_score=0.92,
        )

    @staticmethod
    def create_capability_vector(
        agent_id: str = "test-agent",
        capability_name: str = "API Design",
    ) -> CapabilityVector:
        """Create a sample capability vector."""
        return CapabilityVector(
            capability_id=str(uuid4()),
            agent_id=agent_id,
            capability_name=capability_name,
            capability_description="Expertise in designing scalable REST and GraphQL APIs",
            confidence_score=0.95,
            source="description",
            embedding=[0.1] * 1536,  # Mock embedding
            extracted_date=datetime.utcnow(),
            usage_count=150,
            last_used=datetime.utcnow() - timedelta(hours=1),
            related_capabilities=["API Security", "Performance Optimization"],
            related_agents=["backend-specialist", "security-expert"],
        )

    @staticmethod
    def create_sample_agent(
        name: str = "API Design Agent",
        agent_id: str = "api-designer",
    ) -> Agent:
        """Create a sample agent definition."""
        return Agent(
            name=name,
            agent_type=AgentType.AGENT,
            description="Expert in REST and GraphQL API design",
            category=Category.BACKEND,
            tech_stack=[
                "rest",
                "graphql",
                "openapi",
                "json-schema",
            ],
            languages=["typescript", "python", "java"],
            frameworks=["express", "fastapi", "spring"],
            use_cases=[
                "API endpoint design",
                "Schema validation",
                "Error handling",
            ],
            complexity=Complexity.INTERMEDIATE,
            subjects=["backend", "api-design"],
            source_path="/vibe-tools/ghc_tools/agents/api-designer.agent.md",
            source_collection="ghc_agents",
            content="# API Design Agent\n\nExpert in REST and GraphQL API design...",
            content_hash="abc123def456",
            frontmatter={"version": "1.0.0", "category": "backend"},
        )


@pytest.fixture
def execution_record() -> ExecutionRecord:
    """Provide a sample execution record."""
    return SampleDataGenerator.create_execution_record()


@pytest.fixture
def execution_records() -> list[ExecutionRecord]:
    """Provide multiple sample execution records."""
    return [
        SampleDataGenerator.create_execution_record(
            agent_id="architect-agent",
            agent_name="System Architect",
            success=True,
        ),
        SampleDataGenerator.create_execution_record(
            agent_id="backend-specialist",
            agent_name="Backend Specialist",
            success=True,
        ),
        SampleDataGenerator.create_execution_record(
            agent_id="frontend-expert",
            agent_name="Frontend Expert",
            success=False,
            outcome=ExecutionOutcome.FAILURE,
            quality_score=0.3,
        ),
        SampleDataGenerator.create_execution_record(
            agent_id="testing-expert",
            agent_name="Testing Expert",
            success=True,
            outcome=ExecutionOutcome.PARTIAL,
        ),
    ]


@pytest.fixture
def performance_metric() -> PerformanceMetric:
    """Provide a sample performance metric."""
    return SampleDataGenerator.create_performance_metric()


@pytest.fixture
def performance_metrics() -> list[PerformanceMetric]:
    """Provide multiple sample performance metrics."""
    return [
        SampleDataGenerator.create_performance_metric(
            agent_id="architect-agent",
            agent_name="System Architect",
            success_rate=0.92,
        ),
        SampleDataGenerator.create_performance_metric(
            agent_id="backend-specialist",
            agent_name="Backend Specialist",
            success_rate=0.88,
        ),
        SampleDataGenerator.create_performance_metric(
            agent_id="frontend-expert",
            agent_name="Frontend Expert",
            success_rate=0.75,
        ),
    ]


@pytest.fixture
def collaboration_pattern() -> CollaborationPattern:
    """Provide a sample collaboration pattern."""
    return SampleDataGenerator.create_collaboration_pattern()


@pytest.fixture
def collaboration_patterns() -> list[CollaborationPattern]:
    """Provide multiple sample collaboration patterns."""
    return [
        SampleDataGenerator.create_collaboration_pattern(
            primary_agent="architect-agent",
            collaborating_agents=["backend-specialist", "security-expert"],
        ),
        SampleDataGenerator.create_collaboration_pattern(
            primary_agent="backend-specialist",
            collaborating_agents=["database-expert", "performance-tuner"],
        ),
        SampleDataGenerator.create_collaboration_pattern(
            primary_agent="frontend-expert",
            collaborating_agents=["ux-designer", "accessibility-expert"],
        ),
    ]


@pytest.fixture
def capability_vector() -> CapabilityVector:
    """Provide a sample capability vector."""
    return SampleDataGenerator.create_capability_vector()


@pytest.fixture
def sample_agent() -> Agent:
    """Provide a sample agent definition."""
    return SampleDataGenerator.create_sample_agent()


@pytest.fixture
def sample_agents():
    """Provide multiple sample agents."""
    return [
        SampleDataGenerator.create_sample_agent(
            name="System Architect",
            agent_id="architect-agent",
        ),
        SampleDataGenerator.create_sample_agent(
            name="Backend Specialist",
            agent_id="backend-specialist",
        ),
        SampleDataGenerator.create_sample_agent(
            name="Frontend Expert",
            agent_id="frontend-expert",
        ),
    ]


@pytest.fixture
def sample_execution_func():
    """Provide a sample execution function for testing AgentExecutor."""

    def executor_func(**kwargs) -> tuple[str, dict[str, Any]]:
        """Mock agent execution function that accepts any kwargs."""
        agent = kwargs.get("agent")
        agent_name = agent.name if agent else "Unknown Agent"
        result = f"Execution result from {agent_name}"

        return result, {
            "execution_time_ms": 100,
            "prompt_tokens": 50,
            "completion_tokens": 75,
        }

    return executor_func

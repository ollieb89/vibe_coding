---
type: reference
---

# Pytest Fixtures for Agent Enhancement System Testing [source: tests/conftest.py]

Provides sample data generators and mock Chroma collections for testing the Agent Enhancement System.

## Configuration Options
- `None`: This document does not have any configuration options as it is focused on function signatures, parameter descriptions, return values, exceptions, and usage examples.

## Sample Data Generator

### Class: SampleDataGenerator

#### Overview

This class generates sample data for testing the Agent Enhancement System. It includes methods to create execution records, performance metrics, collaboration patterns, capability vectors, and sample agents.

#### Methods

1. `create_execution_record(agent_id: str = "test-agent", agent_name: str = "Test Agent", agent_type: AgentType = AgentType.AGENT, success: bool = True, outcome: ExecutionOutcome = ExecutionOutcome.SUCCESS, category: Category = Category.GENERAL, execution_time_ms: float = 1500.0, quality_score: float | None = 0.9) -> ExecutionRecord`

    Creates a sample execution record with the provided parameters or default values.

2. `create_performance_metric(agent_id: str = "test-agent", agent_name: str = "Test Agent", agent_type: AgentType = AgentType.AGENT, category: Category = Category.GENERAL, total_executions: int = 100, successful_executions: int = 85, success_rate: float = 0.85) -> PerformanceMetric`

    Creates a sample performance metric with the provided parameters or default values.

3. `create_collaboration_pattern() -> CollaborationPattern`

    Creates a sample collaboration pattern.

4. `create_capability_vector() -> CapabilityVector`

    Creates a sample capability vector.

5. `create_sample_agent(name: str = "API Design Agent", agent_id: str = "api-designer") -> Agent`

    Creates a sample agent definition with the provided parameters or default values.

## Fixtures

The following fixtures provide predefined instances of the generated data for testing purposes:

1. `execution_record() -> ExecutionRecord`
2. `execution_records() -> list[ExecutionRecord]`
3. `performance_metric() -> PerformanceMetric`
4. `performance_metrics() -> list[PerformanceMetric]`
5. `collaboration_pattern() -> CollaborationPattern`
6. `collaboration_patterns() -> list[CollaborationPattern]`
7. `capability_vector() -> CapabilityVector`
8. `sample_agent() -> Agent`
9. `sample_agents() -> list[Agent]`
10. `sample_execution_func() -> callable`

    Provides a mock agent execution function for testing the AgentExecutor.
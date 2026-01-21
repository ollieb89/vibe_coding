"""Agent executor with execution logging and metrics collection.

This module provides the AgentExecutor class that wraps agent invocation,
captures execution context and metrics, and logs everything to Chroma
for pattern extraction and performance analysis.
"""

import time
from collections.abc import Callable
from typing import Any

from agent_discovery.collections import ChromaCollectionManager
from agent_discovery.models import Agent, ExecutionOutcome, ExecutionRecord


class ExecutorConfig:
    """Configuration for agent execution logging."""

    def __init__(
        self,
        enable_logging: bool = True,
        enable_chroma_ingestion: bool = True,
        model_name: str = "gpt-4",
        model_version: str | None = None,
        max_retries: int = 3,
        timeout_seconds: int | None = None,
    ):
        """Initialize executor configuration.

        Args:
            enable_logging: Whether to log executions
            enable_chroma_ingestion: Whether to ingest to Chroma
            model_name: Name of model being used
            model_version: Version of model (optional)
            max_retries: Max retry attempts on failure
            timeout_seconds: Execution timeout (None = unlimited)
        """
        self.enable_logging = enable_logging
        self.enable_chroma_ingestion = enable_chroma_ingestion
        self.model_name = model_name
        self.model_version = model_version
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds


class AgentExecutor:
    """Wraps agent execution with logging and metrics collection.

    This class provides a standardized interface for executing agents while
    automatically capturing:
    - Execution outcome (success/partial/failure/error)
    - Performance metrics (time, tokens, quality)
    - Execution context (model used, tags, metadata)

    The executor can optionally log all executions to Chroma for later
    analysis and pattern extraction.

    Example:
        >>> executor = AgentExecutor(
        ...     collection_manager=ChromaCollectionManager(),
        ...     config=ExecutorConfig(model_name="gpt-4")
        ... )
        >>>
        >>> record = executor.execute(
        ...     agent=my_agent,
        ...     user_prompt="Design a system",
        ...     executor_func=agent_invocation_function,
        ...     quality_metrics={"relevance": 0.95, "correctness": 0.92}
        ... )
    """

    def __init__(
        self,
        collection_manager: ChromaCollectionManager,
        config: ExecutorConfig | None = None,
    ):
        """Initialize agent executor.

        Args:
            collection_manager: ChromaCollectionManager for logging executions
            config: ExecutorConfig with logging preferences (defaults to standard config)
        """
        self.collection_manager = collection_manager
        self.config = config or ExecutorConfig()
        self._execution_history: list[ExecutionRecord] = []

    def execute(
        self,
        agent: Agent,
        executor_func: Callable[..., tuple[str, dict[str, Any]]],
        user_prompt: str | None = None,
        prompt_anonymized: str | None = None,
        tags: list[str] | None = None,
        quality_metrics: dict[str, float] | None = None,
        custom_metadata: dict[str, Any] | None = None,
        **executor_kwargs: Any,
    ) -> ExecutionRecord:
        """Execute an agent with logging and metrics collection.

        Args:
            agent: The Agent to execute
            executor_func: Callable that executes the agent.
                          Must return tuple of (output_text, metrics_dict)
                          where metrics_dict can include:
                          - prompt_tokens: int
                          - completion_tokens: int
                          - total_tokens: int
                          - execution_time_ms: float (optional, will be calculated if missing)
            user_prompt: Original user input (for audit trail)
            prompt_anonymized: Anonymized version of prompt (for privacy)
            tags: Custom tags for this execution (e.g., ["real-time", "critical"])
            quality_metrics: Dict with optional keys:
                            - relevance: float (0-1)
                            - correctness: float (0-1)
                            - completeness: float (0-1)
                            - quality_score: float (0-1) [overall score]
            custom_metadata: Additional context (agent version, user ID, etc.)
            **executor_kwargs: Arguments to pass to executor_func

        Returns:
            ExecutionRecord with complete execution data

        Raises:
            TimeoutError: If execution exceeds configured timeout
            RuntimeError: If all retries exhausted
        """
        # Initialize tracking
        start_time = time.time()
        execution_metrics: dict[str, Any] = {}
        error_message: str | None = None
        outcome = ExecutionOutcome.SUCCESS
        success = False

        # Attempt execution with retries
        attempt = 0
        output_text = ""
        executor_result_metrics: dict[str, Any] = {}

        while attempt < self.config.max_retries:
            try:
                # Check timeout
                elapsed = time.time() - start_time
                if self.config.timeout_seconds and elapsed > self.config.timeout_seconds:
                    raise TimeoutError(
                        f"Execution exceeded timeout ({self.config.timeout_seconds}s)"
                    )

                # Execute the agent
                output_text, executor_result_metrics = executor_func(**executor_kwargs)

                # If we got here, execution succeeded
                success = True
                outcome = ExecutionOutcome.SUCCESS
                break

            except TimeoutError as e:
                error_message = str(e)
                outcome = ExecutionOutcome.ERROR
                attempt += 1
                if attempt >= self.config.max_retries:
                    raise

            except Exception as e:
                error_message = str(e)
                outcome = ExecutionOutcome.FAILURE
                attempt += 1
                if attempt >= self.config.max_retries:
                    raise RuntimeError(
                        f"Agent execution failed after {self.config.max_retries} attempts: {e}"
                    ) from e

        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000

        # Merge metrics from executor_func with calculated time
        execution_metrics.update(executor_result_metrics)
        if "execution_time_ms" not in execution_metrics:
            execution_metrics["execution_time_ms"] = execution_time_ms

        # Extract token counts
        prompt_tokens = execution_metrics.get("prompt_tokens", 0)
        completion_tokens = execution_metrics.get("completion_tokens", 0)
        total_tokens = execution_metrics.get("total_tokens", prompt_tokens + completion_tokens)

        # Extract quality metrics
        quality_metrics = quality_metrics or {}
        relevance = quality_metrics.get("relevance")
        correctness = quality_metrics.get("correctness")
        completeness = quality_metrics.get("completeness")
        quality_score = quality_metrics.get("quality_score")

        # Create execution record
        record = ExecutionRecord(
            agent_id=agent.name.lower().replace(" ", "-"),
            agent_name=agent.name,
            agent_type=agent.agent_type,
            user_prompt=user_prompt,
            prompt_anonymized=prompt_anonymized or user_prompt,
            outcome=outcome,
            success=success,
            error_message=error_message,
            execution_time_ms=execution_metrics.get("execution_time_ms", execution_time_ms),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model_name=self.config.model_name,
            model_version=self.config.model_version,
            quality_score=quality_score,
            relevance=relevance,
            correctness=correctness,
            completeness=completeness,
            category=agent.category,
            tags=tags or [],
            custom_metadata=custom_metadata or {},
        )

        # Log execution to Chroma
        if self.config.enable_logging and self.config.enable_chroma_ingestion:
            try:
                self.collection_manager.ingest_execution_record(record)
            except Exception as e:
                # Don't fail the overall execution if logging fails
                print(f"⚠️  Warning: Failed to log execution to Chroma: {e}")

        # Track in memory for retrieval
        self._execution_history.append(record)

        return record

    def execute_batch(
        self,
        agents: list[Agent],
        executor_func: Callable[[Agent], tuple[str, dict[str, Any]]],
        user_prompt: str | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> list[ExecutionRecord]:
        """Execute multiple agents sequentially.

        Args:
            agents: List of agents to execute
            executor_func: Function that takes agent and returns (output, metrics)
            user_prompt: User input for all executions
            tags: Tags to apply to all executions
            **kwargs: Additional arguments

        Returns:
            List of ExecutionRecords
        """
        records: list[ExecutionRecord] = []

        for agent in agents:
            try:
                record = self.execute(
                    agent=agent,
                    executor_func=lambda a=agent: executor_func(a),
                    user_prompt=user_prompt,
                    tags=tags or [],
                    **kwargs,
                )
                records.append(record)
            except Exception as e:
                print(f"⚠️  Batch execution failed for {agent.name}: {e}")
                # Continue with next agent

        return records

    def get_execution_history(
        self,
        agent_id: str | None = None,
        limit: int = 10,
        success_only: bool = False,
    ) -> list[ExecutionRecord]:
        """Get recent execution history.

        Args:
            agent_id: Filter by agent ID (optional)
            limit: Max records to return
            success_only: Only return successful executions

        Returns:
            List of ExecutionRecords
        """
        history = self._execution_history

        # Filter by agent
        if agent_id:
            history = [r for r in history if r.agent_id == agent_id]

        # Filter by success
        if success_only:
            history = [r for r in history if r.success]

        # Return most recent
        return sorted(
            history,
            key=lambda r: r.timestamp,
            reverse=True,
        )[:limit]

    def get_execution_stats(self, agent_id: str | None = None) -> dict[str, Any]:
        """Get statistics for executions.

        Args:
            agent_id: Filter by agent ID (optional)

        Returns:
            Dictionary with execution statistics
        """
        history = self._execution_history

        if agent_id:
            history = [r for r in history if r.agent_id == agent_id]

        if not history:
            return {
                "total_executions": 0,
                "successful": 0,
                "failed": 0,
                "partial": 0,
                "errors": 0,
            }

        successful = sum(1 for r in history if r.success)
        failed = sum(1 for r in history if r.outcome == ExecutionOutcome.FAILURE)
        partial = sum(1 for r in history if r.outcome == ExecutionOutcome.PARTIAL)
        errors = sum(1 for r in history if r.outcome == ExecutionOutcome.ERROR)

        avg_time = sum(r.execution_time_ms for r in history) / len(history)
        avg_tokens = sum(r.total_tokens for r in history if r.total_tokens > 0) / max(
            1, len([r for r in history if r.total_tokens > 0])
        )

        quality_scores = [r.quality_score for r in history if r.quality_score is not None]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        return {
            "total_executions": len(history),
            "successful": successful,
            "failed": failed,
            "partial": partial,
            "errors": errors,
            "success_rate": successful / len(history) if history else 0,
            "avg_execution_time_ms": avg_time,
            "avg_tokens_used": avg_tokens,
            "avg_quality_score": avg_quality,
        }

    def clear_history(self) -> None:
        """Clear in-memory execution history."""
        self._execution_history.clear()

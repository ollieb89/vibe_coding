"""Performance metrics aggregation for agent execution data.

This module provides the PerformanceAggregator class that calculates
performance metrics from ExecutionRecords stored in Chroma, computing
success rates, execution times, token usage, and trends.
"""

from datetime import datetime, timedelta
from typing import Any

from agent_discovery.collections import ChromaCollectionManager
from agent_discovery.models import (
    AgentType,
    Category,
    ExecutionOutcome,
    ExecutionRecord,
    PerformanceMetric,
)


class PerformanceAggregator:
    """Aggregates execution data into performance metrics.

    This class analyzes ExecutionRecords (stored in Chroma or provided directly)
    and computes aggregated PerformanceMetric objects for different time periods
    (daily, weekly, monthly) and agent/category combinations.

    Example:
        >>> aggregator = PerformanceAggregator(collection_manager)
        >>>
        >>> daily_metrics = aggregator.aggregate_period(
        ...     agent_id="system-architect",
        ...     period_type="daily",
        ...     period_date=datetime.now()
        ... )
        >>>
        >>> # Save to Chroma
        >>> collection_manager.ingest_performance_metric(daily_metrics)
    """

    def __init__(self, collection_manager: ChromaCollectionManager):
        """Initialize performance aggregator.

        Args:
            collection_manager: ChromaCollectionManager for querying execution data
        """
        self.collection_manager = collection_manager

    def aggregate_period(
        self,
        agent_id: str,
        agent_name: str,
        agent_type: AgentType,
        category: Category,
        period_type: str = "daily",
        period_date: datetime | None = None,
        execution_records: list[ExecutionRecord] | None = None,
    ) -> PerformanceMetric:
        """Aggregate metrics for an agent over a time period.

        Args:
            agent_id: Agent identifier
            agent_name: Agent display name
            agent_type: Type of agent
            category: Agent category
            period_type: "daily" | "weekly" | "monthly"
            period_date: Reference date (defaults to today)
            execution_records: Explicit records to aggregate (if None, queries Chroma)

        Returns:
            PerformanceMetric with aggregated data
        """
        if period_date is None:
            period_date = datetime.utcnow()

        # Determine period boundaries
        period_start, period_end = self._get_period_boundaries(period_type, period_date)

        # Get execution records for this period
        if execution_records is None:
            execution_records = self._query_period_records(agent_id, period_start, period_end)

        # Calculate metrics
        metrics = self._calculate_metrics(
            agent_id,
            agent_name,
            agent_type,
            category,
            period_type,
            period_start,
            period_end,
            execution_records,
        )

        return metrics

    def aggregate_all_agents(
        self,
        period_type: str = "daily",
        period_date: datetime | None = None,
    ) -> list[PerformanceMetric]:
        """Aggregate metrics for all agents in the system.

        Args:
            period_type: "daily" | "weekly" | "monthly"
            period_date: Reference date (defaults to today)

        Returns:
            List of PerformanceMetric for all agents
        """
        # This would require querying unique agent IDs from Chroma
        # For now, return empty - would need to enhance ChromaCollectionManager
        # to support agent discovery queries
        return []

    def _get_period_boundaries(
        self, period_type: str, reference_date: datetime
    ) -> tuple[datetime, datetime]:
        """Get start and end datetime for a period.

        Args:
            period_type: "daily" | "weekly" | "monthly"
            reference_date: Date within the period

        Returns:
            Tuple of (period_start, period_end)
        """
        if period_type == "daily":
            # Start of day UTC
            start = reference_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif period_type == "weekly":
            # Start of week (Monday) UTC
            days_since_monday = reference_date.weekday()
            start = (reference_date - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end = start + timedelta(weeks=1)
        elif period_type == "monthly":
            # Start of month UTC
            start = reference_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if reference_date.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)
        else:
            raise ValueError(f"Unknown period type: {period_type}")

        return start, end

    def _query_period_records(
        self,
        agent_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> list[ExecutionRecord]:
        """Query execution records from Chroma for a period.

        Args:
            agent_id: Agent to query
            period_start: Start of period
            period_end: End of period

        Returns:
            List of ExecutionRecords
        """
        # Would need to enhance ChromaCollectionManager to support
        # date range queries. For now, return empty.
        # This is a limitation of the current Chroma interface.
        return []

    def _calculate_metrics(
        self,
        agent_id: str,
        agent_name: str,
        agent_type: AgentType,
        category: Category,
        period_type: str,
        period_start: datetime,
        period_end: datetime,
        execution_records: list[ExecutionRecord],
    ) -> PerformanceMetric:
        """Calculate aggregated metrics from execution records.

        Args:
            agent_id: Agent ID
            agent_name: Agent name
            agent_type: Agent type
            category: Agent category
            period_type: Type of period
            period_start: Start datetime
            period_end: End datetime
            execution_records: Records to aggregate

        Returns:
            PerformanceMetric with calculations
        """
        if not execution_records:
            # Return zero-valued metric for empty period
            return PerformanceMetric(
                agent_id=agent_id,
                agent_name=agent_name,
                agent_type=agent_type,
                category=category,
                period_start=period_start,
                period_end=period_end,
                period_type=period_type,
                total_executions=0,
                successful_executions=0,
                partial_executions=0,
                failed_executions=0,
                error_executions=0,
            )

        # Count execution outcomes
        successful = sum(1 for r in execution_records if r.outcome == ExecutionOutcome.SUCCESS)
        partial = sum(1 for r in execution_records if r.outcome == ExecutionOutcome.PARTIAL)
        failed = sum(1 for r in execution_records if r.outcome == ExecutionOutcome.FAILURE)
        errors = sum(1 for r in execution_records if r.outcome == ExecutionOutcome.ERROR)

        total = len(execution_records)

        # Calculate success rates
        success_rate = successful / total if total > 0 else 0.0
        partial_rate = partial / total if total > 0 else 0.0
        failure_rate = (failed + errors) / total if total > 0 else 0.0

        # Calculate execution time statistics
        times = [r.execution_time_ms for r in execution_records if r.execution_time_ms > 0]
        avg_time = sum(times) / len(times) if times else 0.0
        min_time = min(times) if times else 0.0
        max_time = max(times) if times else 0.0

        # Calculate token statistics
        prompt_tokens = [r.prompt_tokens for r in execution_records if r.prompt_tokens > 0]
        completion_tokens = [
            r.completion_tokens for r in execution_records if r.completion_tokens > 0
        ]
        total_tokens = [r.total_tokens for r in execution_records if r.total_tokens > 0]

        avg_prompt = sum(prompt_tokens) / len(prompt_tokens) if prompt_tokens else 0.0
        avg_completion = (
            sum(completion_tokens) / len(completion_tokens) if completion_tokens else 0.0
        )
        avg_total = sum(total_tokens) / len(total_tokens) if total_tokens else 0.0
        total_tokens_used = sum(total_tokens) if total_tokens else 0

        # Calculate quality metrics
        quality_scores = [r.quality_score for r in execution_records if r.quality_score is not None]
        relevance_scores = [r.relevance for r in execution_records if r.relevance is not None]
        correctness_scores = [r.correctness for r in execution_records if r.correctness is not None]
        completeness_scores = [
            r.completeness for r in execution_records if r.completeness is not None
        ]

        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
        avg_correctness = (
            sum(correctness_scores) / len(correctness_scores) if correctness_scores else 0.0
        )
        avg_completeness = (
            sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0.0
        )

        # Calculate trend (comparing to previous period would require historical data)
        trend = "stable"  # Default to stable, would enhance with historical comparison
        trend_direction = 0.0

        # Collect models used
        models_used = list({r.model_name for r in execution_records})

        # Create metric
        metric = PerformanceMetric(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_type=agent_type,
            category=category,
            period_start=period_start,
            period_end=period_end,
            period_type=period_type,
            total_executions=total,
            successful_executions=successful,
            partial_executions=partial,
            failed_executions=failed,
            error_executions=errors,
            success_rate=success_rate,
            partial_rate=partial_rate,
            failure_rate=failure_rate,
            avg_execution_time_ms=avg_time,
            min_execution_time_ms=min_time,
            max_execution_time_ms=max_time,
            avg_prompt_tokens=avg_prompt,
            avg_completion_tokens=avg_completion,
            avg_total_tokens=avg_total,
            total_tokens_used=total_tokens_used,
            avg_quality_score=avg_quality,
            avg_relevance=avg_relevance,
            avg_correctness=avg_correctness,
            avg_completeness=avg_completeness,
            cost_per_execution=0.0,  # Would need pricing model
            total_cost=0.0,  # Would need pricing model
            trend=trend,
            trend_direction=trend_direction,
            models_used=models_used,
        )

        return metric

    def calculate_trend(
        self,
        current_metric: PerformanceMetric,
        previous_metric: PerformanceMetric | None = None,
    ) -> tuple[str, float]:
        """Calculate trend by comparing current and previous metrics.

        Args:
            current_metric: Current period metric
            previous_metric: Previous period metric (optional)

        Returns:
            Tuple of (trend_description, trend_direction_float)
        """
        if previous_metric is None:
            return "unknown", 0.0

        # Compare success rates
        success_change = current_metric.success_rate - previous_metric.success_rate

        # Determine trend
        if success_change > 0.05:  # 5% improvement
            trend = "improving"
            trend_direction = min(1.0, success_change / 0.1)  # Max 1.0 at 10% improvement
        elif success_change < -0.05:  # 5% decline
            trend = "degrading"
            trend_direction = max(-1.0, success_change / 0.1)  # Min -1.0 at 10% decline
        else:
            trend = "stable"
            trend_direction = 0.0

        return trend, trend_direction

    def get_agent_summary(
        self,
        agent_id: str,
        days_back: int = 30,
    ) -> dict[str, Any]:
        """Get summary of agent performance over recent period.

        Args:
            agent_id: Agent ID
            days_back: Number of days to analyze

        Returns:
            Summary dictionary with trends and statistics
        """
        # Would aggregate daily metrics over the period
        # Returns something like:
        # {
        #     "agent_id": "...",
        #     "period": "last 30 days",
        #     "total_executions": 150,
        #     "success_rate": 0.92,
        #     "trend": "improving",
        #     "avg_quality": 0.88,
        #     "models_used": ["gpt-4", "gpt-3.5"]
        # }
        return {}

    def export_metrics(
        self,
        metrics: list[PerformanceMetric],
        format_type: str = "json",
    ) -> str:
        """Export metrics in specified format.

        Args:
            metrics: List of metrics to export
            format_type: "json" | "csv"

        Returns:
            Formatted metrics string
        """
        if format_type == "json":
            return "[" + ", ".join(m.model_dump_json() for m in metrics) + "]"
        elif format_type == "csv":
            # Would generate CSV with headers and rows
            return ""
        else:
            raise ValueError(f"Unknown format: {format_type}")

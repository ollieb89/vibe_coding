"""Pattern extraction from agent execution data.

This module provides the PatternExtractor class that analyzes execution
records to identify success patterns, failure patterns, and use cases,
then stores them in Chroma for discovery and recommendation.
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from agent_discovery.collections import ChromaCollectionManager
from agent_discovery.models import (
    AgentPattern,
    ExecutionOutcome,
    ExecutionRecord,
)


class PatternExtractor:
    """Extracts patterns from execution data.

    This class analyzes collections of ExecutionRecords to identify:
    - Success patterns: Common characteristics of successful executions
    - Failure patterns: Common issues leading to failures
    - Use cases: Typical scenarios and query types
    - Collaboration patterns: Multi-agent workflows

    Extracted patterns are stored in Chroma for RAG-based discovery enhancement.

    Example:
        >>> extractor = PatternExtractor(collection_manager)
        >>>
        >>> patterns = extractor.extract_from_records(
        ...     execution_records=records,
        ...     agent_id="system-architect"
        ... )
        >>>
        >>> for pattern in patterns:
        ...     collection_manager.ingest_pattern(pattern)
    """

    def __init__(self, collection_manager: ChromaCollectionManager):
        """Initialize pattern extractor.

        Args:
            collection_manager: ChromaCollectionManager for data access
        """
        self.collection_manager = collection_manager

    def extract_from_records(
        self,
        execution_records: list[ExecutionRecord],
        agent_id: str,
        min_frequency: int = 3,
    ) -> list[AgentPattern]:
        """Extract patterns from execution records.

        Args:
            execution_records: Records to analyze
            agent_id: Agent ID these records belong to
            min_frequency: Minimum occurrences to consider a pattern

        Returns:
            List of extracted AgentPattern objects
        """
        if not execution_records:
            return []

        patterns: list[AgentPattern] = []

        # Extract success patterns
        success_patterns = self._extract_success_patterns(
            execution_records, agent_id, min_frequency
        )
        patterns.extend(success_patterns)

        # Extract failure patterns
        failure_patterns = self._extract_failure_patterns(
            execution_records, agent_id, min_frequency
        )
        patterns.extend(failure_patterns)

        # Extract use case patterns
        use_case_patterns = self._extract_use_case_patterns(
            execution_records, agent_id, min_frequency
        )
        patterns.extend(use_case_patterns)

        return patterns

    def _extract_success_patterns(
        self,
        execution_records: list[ExecutionRecord],
        agent_id: str,
        min_frequency: int,
    ) -> list[AgentPattern]:
        """Extract success patterns from execution records.

        Args:
            execution_records: Records to analyze
            agent_id: Agent ID
            min_frequency: Minimum occurrences

        Returns:
            List of success pattern AgentPatterns
        """
        patterns: list[AgentPattern] = []

        # Filter successful executions
        successful = [
            r for r in execution_records if r.outcome == ExecutionOutcome.SUCCESS and r.success
        ]

        if len(successful) < min_frequency:
            return patterns

        # Group by common characteristics
        # 1. High quality scores pattern
        high_quality = [r for r in successful if r.quality_score and r.quality_score >= 0.8]
        if len(high_quality) >= min_frequency:
            patterns.append(
                self._create_pattern(
                    agent_id=agent_id,
                    pattern_type="success_pattern",
                    description=(
                        "High quality responses: Agent produces responses "
                        "scoring 0.8+ on quality metrics"
                    ),
                    frequency=len(high_quality),
                    total_executions=len(successful),
                    avg_quality=sum(r.quality_score for r in high_quality if r.quality_score)
                    / len(high_quality),
                    examples=[
                        {
                            "prompt": r.user_prompt[:100] if r.user_prompt else "",
                            "quality_score": r.quality_score,
                            "execution_time_ms": r.execution_time_ms,
                        }
                        for r in high_quality[:3]
                    ],
                )
            )

        # 2. Fast execution pattern
        fast_executions = [
            r for r in successful if r.execution_time_ms and r.execution_time_ms < 500
        ]
        if len(fast_executions) >= min_frequency:
            avg_time = sum(
                r.execution_time_ms for r in fast_executions if r.execution_time_ms
            ) / len(fast_executions)
            patterns.append(
                self._create_pattern(
                    agent_id=agent_id,
                    pattern_type="success_pattern",
                    description=(
                        f"Fast execution: Agent completes tasks in <500ms "
                        f"(average: {avg_time:.0f}ms)"
                    ),
                    frequency=len(fast_executions),
                    total_executions=len(successful),
                    avg_quality=sum(r.quality_score for r in fast_executions if r.quality_score)
                    / len(fast_executions),
                    examples=[
                        {
                            "prompt": r.user_prompt[:100] if r.user_prompt else "",
                            "execution_time_ms": r.execution_time_ms,
                        }
                        for r in fast_executions[:3]
                    ],
                )
            )

        # 3. Low token usage pattern
        low_token = [r for r in successful if r.total_tokens and r.total_tokens < 500]
        if len(low_token) >= min_frequency:
            patterns.append(
                self._create_pattern(
                    agent_id=agent_id,
                    pattern_type="success_pattern",
                    description=("Token efficient: Agent produces results with <500 tokens"),
                    frequency=len(low_token),
                    total_executions=len(successful),
                    avg_quality=sum(r.quality_score for r in low_token if r.quality_score)
                    / len(low_token),
                    examples=[
                        {
                            "prompt": r.user_prompt[:100] if r.user_prompt else "",
                            "total_tokens": r.total_tokens,
                        }
                        for r in low_token[:3]
                    ],
                )
            )

        return patterns

    def _extract_failure_patterns(
        self,
        execution_records: list[ExecutionRecord],
        agent_id: str,
        min_frequency: int,
    ) -> list[AgentPattern]:
        """Extract failure patterns from execution records.

        Args:
            execution_records: Records to analyze
            agent_id: Agent ID
            min_frequency: Minimum occurrences

        Returns:
            List of failure pattern AgentPatterns
        """
        patterns: list[AgentPattern] = []

        # Filter failed executions
        failed = [
            r
            for r in execution_records
            if r.outcome in (ExecutionOutcome.FAILURE, ExecutionOutcome.ERROR)
        ]

        if len(failed) < min_frequency:
            return patterns

        # 1. Timeout failures
        timeouts = [r for r in failed if "timeout" in (r.error_message or "").lower()]
        if len(timeouts) >= min_frequency:
            patterns.append(
                self._create_pattern(
                    agent_id=agent_id,
                    pattern_type="failure_pattern",
                    description=(
                        f"Timeout failures: {len(timeouts)} executions " "exceeded time limits"
                    ),
                    frequency=len(timeouts),
                    total_executions=len(failed),
                    avg_quality=0.0,
                    examples=[
                        {
                            "prompt": r.user_prompt[:100] if r.user_prompt else "",
                            "error": r.error_message[:100] if r.error_message else "",
                        }
                        for r in timeouts[:3]
                    ],
                )
            )

        # 2. Low quality failures
        low_quality_fails = [r for r in failed if r.quality_score and r.quality_score < 0.5]
        if len(low_quality_fails) >= min_frequency:
            patterns.append(
                self._create_pattern(
                    agent_id=agent_id,
                    pattern_type="failure_pattern",
                    description=(
                        "Low quality results: Agent produces incomplete or " "incorrect responses"
                    ),
                    frequency=len(low_quality_fails),
                    total_executions=len(failed),
                    avg_quality=sum(r.quality_score for r in low_quality_fails if r.quality_score)
                    / len(low_quality_fails),
                    examples=[
                        {
                            "prompt": r.user_prompt[:100] if r.user_prompt else "",
                            "quality_score": r.quality_score,
                        }
                        for r in low_quality_fails[:3]
                    ],
                )
            )

        return patterns

    def _extract_use_case_patterns(
        self,
        execution_records: list[ExecutionRecord],
        agent_id: str,
        min_frequency: int,
    ) -> list[AgentPattern]:
        """Extract use case patterns from execution records.

        Args:
            execution_records: Records to analyze
            agent_id: Agent ID
            min_frequency: Minimum occurrences

        Returns:
            List of use case pattern AgentPatterns
        """
        patterns: list[AgentPattern] = []

        # Group by category/tags
        category_executions: dict[str, list[ExecutionRecord]] = {}
        for record in execution_records:
            category = record.category.value if record.category else "general"
            if category not in category_executions:
                category_executions[category] = []
            category_executions[category].append(record)

        # Create pattern for each category with enough executions
        for category, records in category_executions.items():
            if len(records) >= min_frequency:
                successful = sum(1 for r in records if r.outcome == ExecutionOutcome.SUCCESS)
                success_rate = successful / len(records) if records else 0

                patterns.append(
                    self._create_pattern(
                        agent_id=agent_id,
                        pattern_type="use_case",
                        description=(
                            f"Use case: {category} - Agent handles "
                            f"{category}-related queries with "
                            f"{success_rate:.1%} success rate"
                        ),
                        frequency=len(records),
                        total_executions=len(execution_records),
                        avg_quality=sum(r.quality_score for r in records if r.quality_score)
                        / len(records),
                        examples=[
                            {
                                "category": category,
                                "prompt": r.user_prompt[:100] if r.user_prompt else "",
                                "outcome": r.outcome.value,
                            }
                            for r in records[:3]
                        ],
                    )
                )

        return patterns

    def _create_pattern(
        self,
        agent_id: str,
        pattern_type: str,
        description: str,
        frequency: int,
        total_executions: int,
        avg_quality: float,
        examples: list[dict[str, Any]],
    ) -> AgentPattern:
        """Create an AgentPattern object.

        Args:
            agent_id: Agent ID
            pattern_type: Pattern type
            description: Human-readable description
            frequency: Number of times pattern occurred
            total_executions: Total executions analyzed
            avg_quality: Average quality score
            examples: Example executions

        Returns:
            AgentPattern object
        """
        frequency_percent = (frequency / total_executions * 100) if total_executions > 0 else 0

        return AgentPattern(
            pattern_id=str(uuid4()),
            pattern_type=pattern_type,
            agents_involved=[agent_id],
            description=description,
            frequency=frequency,
            frequency_percent=frequency_percent,
            effectiveness_score=min(1.0, avg_quality),
            examples=examples,
            discovered_date=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            tags=[pattern_type, agent_id],
        )

    def merge_patterns(
        self,
        existing_patterns: list[AgentPattern],
        new_patterns: list[AgentPattern],
    ) -> list[AgentPattern]:
        """Merge existing and new patterns, deduplicating and updating.

        Args:
            existing_patterns: Previously extracted patterns
            new_patterns: Newly extracted patterns

        Returns:
            Merged list of patterns
        """
        # For now, return new patterns (would enhance to match descriptions)
        # and update frequency/last_seen for existing patterns
        return new_patterns

    def rank_patterns(
        self,
        patterns: list[AgentPattern],
    ) -> list[AgentPattern]:
        """Rank patterns by effectiveness and frequency.

        Args:
            patterns: Patterns to rank

        Returns:
            Sorted list (highest impact first)
        """
        return sorted(
            patterns,
            key=lambda p: (
                p.effectiveness_score * (p.frequency / max(1, p.frequency)),
                p.frequency_percent,
            ),
            reverse=True,
        )

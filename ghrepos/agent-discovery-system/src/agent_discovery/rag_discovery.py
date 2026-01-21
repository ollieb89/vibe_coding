"""Enhanced discovery engine with RAG (Retrieval-Augmented Generation).

This module extends the basic DiscoveryEngine with RAG capabilities that
use historical execution data and extracted patterns to improve recommendations.
"""

from typing import Any

from agent_discovery.aggregator import PerformanceAggregator
from agent_discovery.collections import ChromaCollectionManager
from agent_discovery.discovery import DiscoveryEngine
from agent_discovery.extractor import PatternExtractor
from agent_discovery.models import AgentMatch, SearchCriteria


class RAGDiscoveryEngine:
    """Discovery engine enhanced with historical performance and pattern data.

    This engine augments basic semantic search with:
    - Success rates from execution history
    - Failure warnings when agents have high failure rates
    - Use case patterns for better matching
    - Collaborative agent suggestions

    Example:
        >>> engine = RAGDiscoveryEngine(
        ...     discovery_engine=base_engine,
        ...     collection_manager=manager
        ... )
        >>>
        >>> matches = engine.discover(
        ...     query="authentication system",
        ...     boost_successful=True
        ... )
    """

    def __init__(
        self,
        discovery_engine: DiscoveryEngine | None = None,
        collection_manager: ChromaCollectionManager | None = None,
    ):
        """Initialize RAG-enhanced discovery engine.

        Args:
            discovery_engine: Base DiscoveryEngine (creates if None)
            collection_manager: ChromaCollectionManager (creates if None)
        """
        self.base_engine = discovery_engine or DiscoveryEngine()
        self.collection_manager = collection_manager or ChromaCollectionManager()
        self.aggregator = PerformanceAggregator(self.collection_manager)
        self.extractor = PatternExtractor(self.collection_manager)

    def discover(
        self,
        query: str,
        criteria: SearchCriteria | None = None,
        boost_successful: bool = True,
        include_warnings: bool = True,
        max_results: int = 10,
    ) -> list[AgentMatch]:
        """Discover agents using semantic search + historical performance.

        Args:
            query: Natural language query
            criteria: Search criteria (optional)
            boost_successful: Boost high success rate agents
            include_warnings: Include failure warnings in results
            max_results: Maximum results to return

        Returns:
            List of AgentMatch sorted by relevance and performance
        """
        # Get baseline semantic matches
        criteria_obj = criteria or SearchCriteria(query_text=query)
        base_matches = self.base_engine.discover(
            criteria=criteria_obj,
            n_results=max_results * 2,  # Get more to filter by performance
        )

        if not base_matches:
            return []

        # Enhance with performance data
        enhanced_matches = []
        for match in base_matches:
            enhanced_match = self._enhance_match(
                match,
                boost_successful=boost_successful,
                include_warnings=include_warnings,
            )
            enhanced_matches.append(enhanced_match)

        # Sort by enhanced score
        enhanced_matches.sort(
            key=lambda m: m.score,
            reverse=True,
        )

        return enhanced_matches[:max_results]

    def discover_by_use_case(
        self,
        use_case: str,
        max_results: int = 5,
    ) -> list[AgentMatch]:
        """Discover agents based on historical use case patterns.

        Args:
            use_case: Use case description
            max_results: Maximum results

        Returns:
            Agents suited for this use case
        """
        # Query patterns collection for matching use cases
        pattern_results = self.collection_manager.query_execution_patterns(
            query_text=use_case,
            n_results=max_results * 3,
        )

        if not pattern_results:
            return []

        # Extract agent IDs from patterns
        agent_ids = set()
        for result in pattern_results:
            metadata = result.get("metadata", {})
            agent_id = metadata.get("agent_id")
            if agent_id:
                agent_ids.add(agent_id)

        # Create minimal matches for discovered agents
        matches = []
        for agent_id in agent_ids:
            # Create a minimal Agent from ID
            from agent_discovery.models import Agent, AgentType, Category

            agent = Agent(
                name=agent_id,
                agent_type=AgentType.AGENT,
                source_path=f"pattern:{agent_id}",
                category=Category.GENERAL,
            )
            match = AgentMatch(
                agent=agent,
                score=0.8,  # Would compute from pattern relevance
                distance=0.2,
                match_reasons=[
                    f"Matches use case pattern: {use_case}",
                ],
            )
            matches.append(match)

        return matches[:max_results]

    def suggest_collaborators(
        self,
        agent_id: str,
        max_suggestions: int = 5,
    ) -> list[str]:
        """Suggest agents to collaborate with based on patterns.

        Args:
            agent_id: Primary agent ID
            max_suggestions: Maximum suggestions

        Returns:
            List of agent IDs that work well with this agent
        """
        # Would query collaboration_patterns collection for this agent
        # and return other agents it has worked well with
        return []

    def _enhance_match(
        self,
        match: AgentMatch,
        boost_successful: bool = True,
        include_warnings: bool = True,
    ) -> AgentMatch:
        """Enhance a match with performance data.

        Args:
            match: Original AgentMatch
            boost_successful: Boost high success agents
            include_warnings: Add warnings for problematic agents

        Returns:
            Enhanced AgentMatch with adjusted score
        """
        if not match.agent:
            return match

        agent_id = match.agent.name.lower().replace(" ", "-")

        # Query performance data for this agent
        perf_results = self.collection_manager.query_performance_metrics(
            query_text=agent_id,
            n_results=1,
        )

        if not perf_results:
            return match

        # Extract performance metadata
        perf_data = perf_results[0].get("metadata", {})
        success_rate = float(perf_data.get("success_rate", 0))
        failure_count = int(perf_data.get("failed_executions", 0))

        # Boost score based on success rate
        original_score = match.score
        if boost_successful and success_rate > 0:
            score_boost = success_rate * 0.2  # Up to 20% boost
            match.score = min(1.0, original_score + score_boost)

        # Add warnings for low success rates
        if include_warnings and failure_count > 5 and success_rate < 0.7:
            match.match_reasons.append(
                f"⚠️  WARNING: Recent success rate only {success_rate:.1%} "
                f"({failure_count} recent failures)"
            )

        return match

    def get_agent_quality_report(
        self,
        agent_id: str,
    ) -> dict[str, Any]:
        """Get detailed quality report for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Dictionary with quality metrics and insights
        """
        # Query performance metrics for agent
        perf_results = self.collection_manager.query_performance_metrics(
            query_text=agent_id,
            n_results=1,
        )

        if not perf_results:
            return {
                "agent_id": agent_id,
                "status": "No performance data available",
            }

        perf_data = perf_results[0].get("metadata", {})

        # Query patterns to understand strengths/weaknesses
        pattern_results = self.collection_manager.query_execution_patterns(
            query_text=agent_id,
            n_results=5,
        )

        success_patterns = [
            p for p in pattern_results if "success" in p.get("metadata", {}).get("pattern_type", "")
        ]
        failure_patterns = [
            p for p in pattern_results if "failure" in p.get("metadata", {}).get("pattern_type", "")
        ]

        return {
            "agent_id": agent_id,
            "performance": perf_data,
            "strengths": [p.get("document", "") for p in success_patterns[:3]],
            "weaknesses": [p.get("document", "") for p in failure_patterns[:3]],
            "success_rate": float(perf_data.get("success_rate", 0)),
            "avg_quality_score": float(perf_data.get("avg_quality_score", 0)),
            "total_executions": int(perf_data.get("total_executions", 0)),
        }

    def get_recommended_agents(
        self,
        for_category: str | None = None,
        min_quality: float = 0.7,
        max_results: int = 10,
    ) -> list[AgentMatch]:
        """Get recommended agents based on overall performance.

        Args:
            for_category: Filter by category (optional)
            min_quality: Minimum quality score threshold
            max_results: Maximum results

        Returns:
            List of high-performing agents
        """
        # Query performance metrics collection for all agents
        query = f"agents with quality score above {min_quality}"
        if for_category:
            query += f" in {for_category}"

        results = self.collection_manager.query_performance_metrics(
            query_text=query,
            n_results=max_results,
        )

        matches = []
        for result in results:
            metadata = result.get("metadata", {})
            score = float(metadata.get("avg_quality_score", 0))
            agent_id = metadata.get("agent_id", "unknown")

            if score >= min_quality:
                # Create a minimal Agent from metadata
                from agent_discovery.models import Agent, AgentType, Category

                agent = Agent(
                    name=agent_id,
                    agent_type=AgentType.AGENT,
                    source_path=f"metric:{agent_id}",
                    category=Category.GENERAL,
                )
                match = AgentMatch(
                    agent=agent,
                    score=score,
                    distance=1.0 - score,  # Inverse relationship
                    match_reasons=[
                        f"High quality agent (score: {score:.2f})",
                        f"Success rate: {metadata.get('success_rate', 0):.1%}",
                    ],
                )
                matches.append(match)

        return matches[:max_results]

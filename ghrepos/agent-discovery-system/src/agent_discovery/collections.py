"""Chroma collection management for Agent Enhancement System.

Provides utilities for initializing, managing, and querying Chroma collections
for agent execution patterns, performance metrics, and collaboration patterns.
"""

import json
from datetime import datetime
from typing import Any

from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

from agent_discovery.models import (
    CollaborationPattern,
    ExecutionRecord,
    PerformanceMetric,
)


class ChromaCollectionManager:
    """Manages Chroma collections for agent execution data."""

    # Collection names
    EXECUTION_PATTERNS_COLLECTION = "agent_execution_patterns"
    PERFORMANCE_METRICS_COLLECTION = "agent_performance_metrics"
    COLLABORATION_PATTERNS_COLLECTION = "agent_collaboration_patterns"
    CAPABILITY_VECTORS_COLLECTION = "agent_capability_vectors"

    # Collection configurations
    COLLECTION_CONFIGS = {
        EXECUTION_PATTERNS_COLLECTION: {
            "description": "Execution records with outcomes and performance metrics",
            "metadata_fields": [
                "agent_id",
                "agent_type",
                "category",
                "outcome",
                "timestamp",
                "success",
            ],
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "distance_threshold": 0.4,
        },
        PERFORMANCE_METRICS_COLLECTION: {
            "description": "Aggregated performance metrics per agent and time period",
            "metadata_fields": [
                "agent_id",
                "agent_type",
                "category",
                "period_type",
                "period_start",
            ],
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "distance_threshold": 0.5,
        },
        COLLABORATION_PATTERNS_COLLECTION: {
            "description": "Patterns of agents working together",
            "metadata_fields": [
                "primary_agent",
                "collaborating_agents",
                "effectiveness_score",
            ],
            "chunk_size": 800,
            "chunk_overlap": 150,
            "distance_threshold": 0.4,
        },
        CAPABILITY_VECTORS_COLLECTION: {
            "description": "Semantic capability vectors for agents",
            "metadata_fields": [
                "agent_id",
                "capability_name",
                "confidence_score",
                "source",
            ],
            "chunk_size": 500,
            "chunk_overlap": 100,
            "distance_threshold": 0.3,
        },
    }

    def __init__(self, chroma_client=None):
        """Initialize collection manager with optional Chroma client.

        Args:
            chroma_client: Optional Chroma client instance. If None, will use
                          singleton from chroma_ingestion.clients.chroma
        """
        self.client = chroma_client
        self._chunkers = {}
        self._collections = {}

    def _get_client(self):
        """Get or initialize Chroma client (lazy loading)."""
        if self.client is None:
            # Use singleton pattern from chroma_ingestion
            try:
                from chroma_ingestion.clients.chroma import get_chroma_client

                self.client = get_chroma_client()
            except ImportError as e:
                raise ImportError(
                    "chroma_ingestion not available. Install with: " "cd ../chroma && uv sync"
                ) from e
        return self.client

    def _get_chunker(self, collection_name: str):
        """Get or create text splitter for collection."""
        if collection_name not in self._chunkers:
            config = self.COLLECTION_CONFIGS[collection_name]
            self._chunkers[collection_name] = RecursiveCharacterTextSplitter.from_language(
                language=Language.MARKDOWN,
                chunk_size=config["chunk_size"],
                chunk_overlap=config["chunk_overlap"],
            )
        return self._chunkers[collection_name]

    def initialize_collection(self, collection_name: str, reset: bool = False) -> Any:
        """Initialize a Chroma collection.

        Args:
            collection_name: Name of collection to initialize
            reset: If True, delete and recreate the collection

        Returns:
            Chroma collection instance
        """
        client = self._get_client()
        config = self.COLLECTION_CONFIGS[collection_name]

        # Delete existing if reset requested
        if reset:
            try:
                client.delete_collection(name=collection_name)
            except Exception:
                pass  # Collection doesn't exist yet

        # Create or get collection
        collection = client.get_or_create_collection(
            name=collection_name,
            metadata={
                "description": config["description"],
                "chunk_size": config["chunk_size"],
                "chunk_overlap": config["chunk_overlap"],
                "distance_threshold": config["distance_threshold"],
                "created_at": datetime.utcnow().isoformat(),
            },
        )

        self._collections[collection_name] = collection
        return collection

    def initialize_all_collections(self, reset: bool = False) -> dict[str, Any]:
        """Initialize all required collections.

        Args:
            reset: If True, delete and recreate all collections

        Returns:
            Dictionary mapping collection names to collection instances
        """
        collections = {}
        for collection_name in self.COLLECTION_CONFIGS:
            collections[collection_name] = self.initialize_collection(collection_name, reset=reset)
        return collections

    def ingest_execution_record(self, record: ExecutionRecord, batch_size: int = 100) -> bool:
        """Ingest an execution record into Chroma.

        Args:
            record: ExecutionRecord instance
            batch_size: Batch size for upsert operation

        Returns:
            True if successful
        """
        collection = self.initialize_collection(self.EXECUTION_PATTERNS_COLLECTION)
        chunker = self._get_chunker(self.EXECUTION_PATTERNS_COLLECTION)

        # Prepare document content
        content = self._prepare_execution_document(record)

        # Chunk the content
        chunks = chunker.split_text(content)
        if not chunks:
            chunks = [content]  # Keep original if chunking produces nothing

        # Prepare metadata for each chunk
        base_metadata = {
            "agent_id": record.agent_id,
            "agent_name": record.agent_name,
            "agent_type": record.agent_type.value,
            "category": record.category.value,
            "outcome": record.outcome.value,
            "success": str(record.success),
            "timestamp": record.timestamp.isoformat(),
            "record_id": record.record_id,
            "execution_time_ms": str(record.execution_time_ms),
            "total_tokens": str(record.total_tokens),
        }

        # Add optional quality metrics if present
        if record.quality_score is not None:
            base_metadata["quality_score"] = str(record.quality_score)
        if record.relevance is not None:
            base_metadata["relevance"] = str(record.relevance)

        # Upsert chunks to collection
        ids = [f"{record.record_id}_{i}" for i in range(len(chunks))]
        metadatas = [base_metadata for _ in chunks]

        try:
            collection.upsert(
                documents=chunks,
                ids=ids,
                metadatas=metadatas,
            )
            return True
        except Exception as e:
            print(f"Error ingesting execution record: {e}")
            return False

    def ingest_performance_metric(self, metric: PerformanceMetric) -> bool:
        """Ingest a performance metric into Chroma.

        Args:
            metric: PerformanceMetric instance

        Returns:
            True if successful
        """
        collection = self.initialize_collection(self.PERFORMANCE_METRICS_COLLECTION)
        chunker = self._get_chunker(self.PERFORMANCE_METRICS_COLLECTION)

        # Prepare document content
        content = self._prepare_performance_document(metric)

        # Chunk the content
        chunks = chunker.split_text(content)
        if not chunks:
            chunks = [content]

        # Prepare metadata
        base_metadata = {
            "agent_id": metric.agent_id,
            "agent_type": metric.agent_type.value,
            "category": metric.category.value,
            "period_type": metric.period_type,
            "period_start": metric.period_start.isoformat(),
            "success_rate": str(metric.success_rate),
            "total_executions": str(metric.total_executions),
            "avg_execution_time_ms": str(metric.avg_execution_time_ms),
            "trend": metric.trend,
        }

        # Upsert chunks
        metric_id = f"{metric.agent_id}_{metric.period_start.isoformat()}"
        ids = [f"{metric_id}_{i}" for i in range(len(chunks))]
        metadatas = [base_metadata for _ in chunks]

        try:
            collection.upsert(
                documents=chunks,
                ids=ids,
                metadatas=metadatas,
            )
            return True
        except Exception as e:
            print(f"Error ingesting performance metric: {e}")
            return False

    def ingest_collaboration_pattern(self, pattern: CollaborationPattern) -> bool:
        """Ingest a collaboration pattern into Chroma.

        Args:
            pattern: CollaborationPattern instance

        Returns:
            True if successful
        """
        collection = self.initialize_collection(self.COLLABORATION_PATTERNS_COLLECTION)
        chunker = self._get_chunker(self.COLLABORATION_PATTERNS_COLLECTION)

        # Prepare document content
        content = self._prepare_collaboration_document(pattern)

        # Chunk the content
        chunks = chunker.split_text(content)
        if not chunks:
            chunks = [content]

        # Prepare metadata
        base_metadata = {
            "pattern_id": pattern.pattern_id,
            "primary_agent": pattern.primary_agent,
            "collaborating_agents": json.dumps(pattern.collaborating_agents),
            "success_rate": str(pattern.success_rate),
            "effectiveness_score": str(pattern.effectiveness_score),
            "frequency": str(pattern.frequency),
        }

        # Upsert chunks
        ids = [f"{pattern.pattern_id}_{i}" for i in range(len(chunks))]
        metadatas = [base_metadata for _ in chunks]

        try:
            collection.upsert(
                documents=chunks,
                ids=ids,
                metadatas=metadatas,
            )
            return True
        except Exception as e:
            print(f"Error ingesting collaboration pattern: {e}")
            return False

    def query_execution_patterns(
        self,
        query_text: str,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Query execution patterns from Chroma.

        Args:
            query_text: Natural language query
            n_results: Number of results to return
            where: Chroma where filter for metadata

        Returns:
            List of matching execution patterns with metadata
        """
        collection = self.initialize_collection(self.EXECUTION_PATTERNS_COLLECTION)
        config = self.COLLECTION_CONFIGS[self.EXECUTION_PATTERNS_COLLECTION]

        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"],
            )

            # Process results
            output = []
            if results["documents"] and len(results["documents"]) > 0:
                for i, doc in enumerate(results["documents"][0]):
                    distance = results["distances"][0][i] if results["distances"] else 0

                    # Filter by distance threshold
                    if distance > config["distance_threshold"]:
                        continue

                    output.append(
                        {
                            "document": doc,
                            "metadata": results["metadatas"][0][i],
                            "distance": distance,
                            "relevance": 1 - distance,  # Convert to relevance score
                        }
                    )

            return output
        except Exception as e:
            print(f"Error querying execution patterns: {e}")
            return []

    def query_performance_metrics(
        self,
        query_text: str,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Query performance metrics from Chroma.

        Args:
            query_text: Natural language query
            n_results: Number of results to return
            where: Chroma where filter

        Returns:
            List of matching performance metrics
        """
        collection = self.initialize_collection(self.PERFORMANCE_METRICS_COLLECTION)
        config = self.COLLECTION_CONFIGS[self.PERFORMANCE_METRICS_COLLECTION]

        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"],
            )

            # Process results
            output = []
            if results["documents"] and len(results["documents"]) > 0:
                for i, doc in enumerate(results["documents"][0]):
                    distance = results["distances"][0][i] if results["distances"] else 0

                    if distance > config["distance_threshold"]:
                        continue

                    output.append(
                        {
                            "document": doc,
                            "metadata": results["metadatas"][0][i],
                            "distance": distance,
                            "relevance": 1 - distance,
                        }
                    )

            return output
        except Exception as e:
            print(f"Error querying performance metrics: {e}")
            return []

    def get_collection_info(self, collection_name: str) -> dict[str, Any]:
        """Get information about a collection.

        Args:
            collection_name: Name of collection

        Returns:
            Dictionary with collection statistics and metadata
        """
        collection = self.initialize_collection(collection_name)
        config = self.COLLECTION_CONFIGS[collection_name]

        try:
            count = collection.count()
            metadata = collection.metadata if hasattr(collection, "metadata") else {}

            return {
                "name": collection_name,
                "description": config["description"],
                "document_count": count,
                "chunk_size": config["chunk_size"],
                "chunk_overlap": config["chunk_overlap"],
                "distance_threshold": config["distance_threshold"],
                "metadata": metadata,
            }
        except Exception as e:
            return {
                "name": collection_name,
                "error": str(e),
            }

    def get_all_collection_info(self) -> dict[str, dict[str, Any]]:
        """Get information about all collections.

        Returns:
            Dictionary mapping collection names to their info
        """
        info = {}
        for collection_name in self.COLLECTION_CONFIGS:
            info[collection_name] = self.get_collection_info(collection_name)
        return info

    @staticmethod
    def _prepare_execution_document(record: ExecutionRecord) -> str:
        """Prepare execution record as document for chunking."""
        content = f"""# Agent Execution Record

**Agent**: {record.agent_name} ({record.agent_id})
**Type**: {record.agent_type.value}
**Category**: {record.category.value}

## Execution Details

**Timestamp**: {record.timestamp.isoformat()}
**Outcome**: {record.outcome.value}
**Success**: {record.success}

## Performance

- **Execution Time**: {record.execution_time_ms}ms
- **Prompt Tokens**: {record.prompt_tokens}
- **Completion Tokens**: {record.completion_tokens}
- **Total Tokens**: {record.total_tokens}

## Model

**Model**: {record.model_name}
**Version**: {record.model_version or 'N/A'}

## Quality

- **Quality Score**: {record.quality_score or 'N/A'}
- **Relevance**: {record.relevance or 'N/A'}
- **Correctness**: {record.correctness or 'N/A'}
- **Completeness**: {record.completeness or 'N/A'}

## Context

**Tags**: {', '.join(record.tags) if record.tags else 'None'}

{f'**Error**: {record.error_message}' if record.error_message else ''}
"""
        return content.strip()

    @staticmethod
    def _prepare_performance_document(metric: PerformanceMetric) -> str:
        """Prepare performance metric as document for chunking."""
        content = f"""# Performance Metrics Summary

**Agent**: {metric.agent_name} ({metric.agent_id})
**Type**: {metric.agent_type.value}
**Category**: {metric.category.value}

## Time Period

**Period**: {metric.period_start.isoformat()} to {metric.period_end.isoformat()}
**Type**: {metric.period_type}

## Execution Summary

- **Total Executions**: {metric.total_executions}
- **Successful**: {metric.successful_executions} ({metric.success_rate * 100:.1f}%)
- **Partial**: {metric.partial_executions} ({metric.partial_rate * 100:.1f}%)
- **Failed**: {metric.failed_executions} ({metric.failure_rate * 100:.1f}%)
- **Errors**: {metric.error_executions}

## Performance Metrics

**Execution Time**:
- Average: {metric.avg_execution_time_ms:.1f}ms
- Min: {metric.min_execution_time_ms:.1f}ms
- Max: {metric.max_execution_time_ms:.1f}ms

**Token Usage**:
- Avg Prompt Tokens: {metric.avg_prompt_tokens:.0f}
- Avg Completion Tokens: {metric.avg_completion_tokens:.0f}
- Total Tokens Used: {metric.total_tokens_used}

## Quality Metrics

- **Quality Score**: {metric.avg_quality_score:.2f}/1.0
- **Relevance**: {metric.avg_relevance:.2f}/1.0
- **Correctness**: {metric.avg_correctness:.2f}/1.0
- **Completeness**: {metric.avg_completeness:.2f}/1.0

## Cost Analysis

- **Cost Per Execution**: ${metric.cost_per_execution:.4f}
- **Total Cost**: ${metric.total_cost:.2f}

## Trend

**Trend**: {metric.trend}
**Direction**: {metric.trend_direction:.2f}

**Models Used**: {', '.join(metric.models_used) if metric.models_used else 'N/A'}
"""
        return content.strip()

    @staticmethod
    def _prepare_collaboration_document(pattern: CollaborationPattern) -> str:
        """Prepare collaboration pattern as document for chunking."""
        content = f"""# Agent Collaboration Pattern

**Pattern Name**: {pattern.pattern_name}
**Pattern ID**: {pattern.pattern_id}

## Agents Involved

**Primary Agent**: {pattern.primary_agent}
**Collaborating Agents**: {', '.join(pattern.collaborating_agents)}

## Pattern Description

{pattern.description}

## Performance

- **Success Rate**: {pattern.success_rate * 100:.1f}%
- **Frequency**: {pattern.frequency} occurrences
- **Effectiveness**: {pattern.effectiveness_score * 100:.1f}%

## Use Cases

{chr(10).join(f'- {uc}' for uc in pattern.use_cases) if pattern.use_cases else 'None documented'}

## History

- **Discovered**: {pattern.discovered_date.isoformat()}
- **Last Used**: {pattern.last_used.isoformat() if pattern.last_used else 'N/A'}
"""
        return content.strip()

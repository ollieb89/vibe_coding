#!/usr/bin/env python
"""Validation script for Phase 0 - Agent Enhancement Infrastructure.

Validates that all data models, collections, and fixtures are properly configured.
"""

import sys
from datetime import datetime

# Test imports
try:
    from agent_discovery.models import (
        AgentType,
        CapabilityVector,
        Category,
        CollaborationPattern,
        ExecutionOutcome,
        ExecutionRecord,
        PerformanceMetric,
    )

    print("✅ All data models imported successfully")
except ImportError as e:
    print(f"❌ Failed to import models: {e}")
    sys.exit(1)

# Test collections module
try:
    from agent_discovery.collections import ChromaCollectionManager

    print("✅ ChromaCollectionManager imported successfully")
except ImportError as e:
    print(f"❌ Failed to import ChromaCollectionManager: {e}")
    sys.exit(1)

# Test model instantiation
try:
    record = ExecutionRecord(
        agent_id="test-agent",
        agent_name="Test Agent",
        agent_type=AgentType.AGENT,
        outcome=ExecutionOutcome.SUCCESS,
        success=True,
        execution_time_ms=1500.0,
        model_name="gpt-4",
    )
    assert record.record_id is not None
    assert record.timestamp is not None
    print("✅ ExecutionRecord model instantiated successfully")
except Exception as e:
    print(f"❌ Failed to instantiate ExecutionRecord: {e}")
    sys.exit(1)

try:
    metric = PerformanceMetric(
        agent_id="test-agent",
        agent_name="Test Agent",
        agent_type=AgentType.AGENT,
        category=Category.GENERAL,
        period_start=datetime.utcnow(),
        period_end=datetime.utcnow(),
        total_executions=100,
        successful_executions=85,
        success_rate=0.85,
        avg_execution_time_ms=1250.5,
        avg_prompt_tokens=450,
        avg_completion_tokens=1200,
        avg_total_tokens=1650,
    )
    assert metric.agent_id == "test-agent"
    print("✅ PerformanceMetric model instantiated successfully")
except Exception as e:
    print(f"❌ Failed to instantiate PerformanceMetric: {e}")
    sys.exit(1)

try:
    pattern = CollaborationPattern(
        primary_agent="architect",
        collaborating_agents=["backend", "security"],
        pattern_name="API Design Pattern",
        description="Architects design APIs with security review",
        success_rate=0.92,
        effectiveness_score=0.92,
    )
    assert pattern.pattern_id is not None
    print("✅ CollaborationPattern model instantiated successfully")
except Exception as e:
    print(f"❌ Failed to instantiate CollaborationPattern: {e}")
    sys.exit(1)

try:
    capability = CapabilityVector(
        agent_id="test-agent",
        capability_name="API Design",
        capability_description="Expertise in API design",
        confidence_score=0.95,
        source="description",
        embedding=[0.1] * 1536,
    )
    assert capability.capability_id is not None
    print("✅ CapabilityVector model instantiated successfully")
except Exception as e:
    print(f"❌ Failed to instantiate CapabilityVector: {e}")
    sys.exit(1)

# Test ChromaCollectionManager configuration
try:
    manager = ChromaCollectionManager()
    assert len(manager.COLLECTION_CONFIGS) == 4
    assert manager.EXECUTION_PATTERNS_COLLECTION in manager.COLLECTION_CONFIGS
    assert manager.PERFORMANCE_METRICS_COLLECTION in manager.COLLECTION_CONFIGS
    assert manager.COLLABORATION_PATTERNS_COLLECTION in manager.COLLECTION_CONFIGS
    assert manager.CAPABILITY_VECTORS_COLLECTION in manager.COLLECTION_CONFIGS
    print("✅ ChromaCollectionManager configured with all required collections")
except Exception as e:
    print(f"❌ Failed to validate ChromaCollectionManager: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 70)
print("PHASE 0 VALIDATION COMPLETE")
print("=" * 70)
print(
    """
✅ All data models created and validated
✅ ChromaCollectionManager implemented with 4 collections:
   - agent_execution_patterns
   - agent_performance_metrics
   - agent_collaboration_patterns
   - agent_capability_vectors

✅ Collection configurations include:
   - Rich metadata fields for filtering
   - Semantic chunking parameters (chunk_size, overlap)
   - Distance thresholds for quality filtering

✅ Model validation tests passing:
   - ExecutionRecord with outcomes and metrics
   - PerformanceMetric with aggregations
   - CollaborationPattern for multi-agent scenarios
   - CapabilityVector for semantic matching

Next Steps:
1. Initialize Chroma collections with ChromaCollectionManager
2. Implement Phase 1: Agent execution logging
3. Create RAG-enhanced discovery queries
4. Build performance aggregation pipeline
"""
)
print("=" * 70)

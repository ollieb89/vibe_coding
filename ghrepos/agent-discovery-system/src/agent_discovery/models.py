"""Data models for the Agent Discovery System."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Types of agent definitions."""

    AGENT = "agent"
    PROMPT = "prompt"
    INSTRUCTION = "instruction"
    CHATMODE = "chatmode"


class Category(str, Enum):
    """Agent category classification."""

    FRONTEND = "frontend"
    BACKEND = "backend"
    FULLSTACK = "fullstack"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    AI_ML = "ai_ml"
    DEVOPS = "devops"
    SECURITY = "security"
    QUALITY = "quality"
    DATABASE = "database"
    PLANNING = "planning"
    DOCUMENTATION = "documentation"
    GENERAL = "general"


class Complexity(str, Enum):
    """Agent complexity level."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Agent(BaseModel):
    """Represents a GitHub Copilot agent/prompt/instruction/chatmode."""

    # Core identity
    name: str = Field(..., description="Agent name (from filename or frontmatter)")
    agent_type: AgentType = Field(..., description="Type of agent definition")
    description: str = Field(default="", description="One-line description")

    # Classification
    category: Category = Field(default=Category.GENERAL, description="Primary category")
    tech_stack: list[str] = Field(default_factory=list, description="Technology keywords")
    languages: list[str] = Field(default_factory=list, description="Programming languages")
    frameworks: list[str] = Field(default_factory=list, description="Frameworks supported")

    # Discovery metadata
    use_cases: list[str] = Field(default_factory=list, description="When to activate")
    complexity: Complexity = Field(default=Complexity.INTERMEDIATE, description="Complexity level")

    # Multi-subject tagging (e.g., security, testing, infra)
    subjects: list[str] = Field(default_factory=list, description="Subject tags for leaderboards")

    # Source tracking
    source_path: str = Field(..., description="Original file path")
    source_collection: str = Field(default="unknown", description="Source collection name")
    content: str = Field(default="", description="Full file content")
    content_hash: str = Field(default="", description="Hash for deduplication")

    # Frontmatter data
    frontmatter: dict[str, Any] = Field(default_factory=dict, description="Parsed frontmatter")


class AgentMatch(BaseModel):
    """An agent matched by the discovery engine."""

    agent: Agent
    score: float = Field(..., ge=0.0, le=1.0, description="Match score (0-1, higher is better)")
    distance: float = Field(..., description="Chroma distance (lower is better)")
    match_reasons: list[str] = Field(default_factory=list, description="Why this matched")


class CodebaseProfile(BaseModel):
    """Profile of a codebase for agent discovery."""

    path: str = Field(..., description="Root path of codebase")

    # Detected attributes
    languages: list[str] = Field(default_factory=list, description="Detected programming languages")
    frameworks: list[str] = Field(default_factory=list, description="Detected frameworks")
    patterns: list[str] = Field(default_factory=list, description="Detected patterns/practices")

    # File analysis
    file_count: int = Field(default=0, description="Total files analyzed")
    file_types: dict[str, int] = Field(default_factory=dict, description="File extension counts")

    # Package analysis
    dependencies: list[str] = Field(default_factory=list, description="Detected dependencies")
    dev_dependencies: list[str] = Field(default_factory=list, description="Dev dependencies")

    # Configuration
    has_tests: bool = Field(default=False, description="Whether tests exist")
    has_ci: bool = Field(default=False, description="Whether CI config exists")
    has_docker: bool = Field(default=False, description="Whether Docker config exists")


class Question(BaseModel):
    """Interactive question for discovery flow."""

    id: str = Field(..., description="Unique question identifier")
    text: str = Field(..., description="Question to display to user")
    question_type: str = Field(default="single", description="single | multi | text")
    options: list[dict[str, Any]] = Field(default_factory=list, description="Available options")
    depends_on: dict[str, Any] | None = Field(default=None, description="Conditional display")
    maps_to: list[str] = Field(default_factory=list, description="Chroma filter fields")


class SearchCriteria(BaseModel):
    """Search criteria derived from user answers."""

    # From codebase analysis
    detected_languages: list[str] = Field(default_factory=list)
    detected_frameworks: list[str] = Field(default_factory=list)

    # From user input
    project_type: str | None = Field(default=None)
    primary_language: str | None = Field(default=None)
    needs: list[str] = Field(default_factory=list)
    complexity_preference: Complexity | None = Field(default=None)

    # Free text
    query_text: str = Field(default="", description="Natural language query")

    def to_chroma_filter(self) -> dict[str, Any]:
        """Convert criteria to Chroma where filter."""
        filters: list[dict[str, Any]] = []

        # Add language filter if specified
        if self.primary_language:
            filters.append({"languages": {"$contains": self.primary_language}})

        # Add framework filters
        for framework in self.detected_frameworks[:3]:  # Limit to avoid complex queries
            filters.append({"tech_stack": {"$contains": framework}})

        # Add needs as category filters
        for need in self.needs:
            if need in [c.value for c in Category]:
                filters.append({"category": need})

        if len(filters) == 0:
            return {}
        elif len(filters) == 1:
            return filters[0]
        else:
            return {"$or": filters}


# =============================================================================
# PHASE 1: Execution Tracking & Performance Models
# =============================================================================


class ExecutionOutcome(str, Enum):
    """Outcome of an agent execution."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    ERROR = "error"


class ExecutionRecord(BaseModel):
    """Immutable record of a single agent execution."""

    # Record identity
    record_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique execution record ID"
    )

    # Agent identification
    agent_id: str = Field(..., description="ID of executed agent")
    agent_name: str = Field(..., description="Human-readable agent name")
    agent_type: AgentType = Field(..., description="Type of agent")

    # Execution context
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When execution occurred"
    )
    user_prompt: str | None = Field(
        default=None, description="User input (may be None for privacy)"
    )
    prompt_anonymized: str | None = Field(default=None, description="Anonymized version of prompt")

    # Execution outcome
    outcome: ExecutionOutcome = Field(..., description="success|partial|failure|error")
    success: bool = Field(..., description="Whether execution succeeded")
    error_message: str | None = Field(default=None, description="Error details if failed")

    # Performance metrics
    execution_time_ms: float = Field(..., description="Total execution time in milliseconds")
    prompt_tokens: int = Field(default=0, description="Prompt tokens consumed")
    completion_tokens: int = Field(default=0, description="Completion tokens generated")
    total_tokens: int = Field(default=0, description="Total tokens (prompt + completion)")

    # Model information
    model_name: str = Field(..., description="LLM model used (e.g., 'gpt-4', 'claude-3')")
    model_version: str | None = Field(default=None, description="Model version if applicable")

    # Quality metrics
    quality_score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="User-provided quality rating (0-1)"
    )
    relevance: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Whether response was relevant to query"
    )
    correctness: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Whether response was correct (0-1)"
    )
    completeness: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Degree response answered the question (0-1)"
    )

    # Metadata
    category: Category = Field(default=Category.GENERAL, description="Agent category")
    tags: list[str] = Field(default_factory=list, description="Custom tags for this execution")
    custom_metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context")

    class Config:
        """Model configuration."""

        json_schema_extra = {
            "example": {
                "record_id": "550e8400-e29b-41d4-a716-446655440000",
                "agent_id": "system-architect",
                "agent_name": "System Architect",
                "agent_type": "agent",
                "timestamp": "2025-12-05T10:30:00",
                "user_prompt": "Design a scalable authentication system",
                "outcome": "success",
                "success": True,
                "execution_time_ms": 2500.0,
                "prompt_tokens": 450,
                "completion_tokens": 1200,
                "total_tokens": 1650,
                "model_name": "gpt-4",
                "quality_score": 0.95,
                "category": "architecture",
            }
        }


class PerformanceMetric(BaseModel):
    """Aggregated performance metrics for an agent."""

    # Agent identification
    agent_id: str = Field(..., description="Agent ID")
    agent_name: str = Field(..., description="Agent name")
    agent_type: AgentType = Field(..., description="Agent type")
    category: Category = Field(..., description="Agent category")

    # Time period
    period_start: datetime = Field(..., description="Start of measurement period")
    period_end: datetime = Field(..., description="End of measurement period")
    period_type: str = Field(default="daily", description="daily|weekly|monthly")

    # Execution statistics
    total_executions: int = Field(default=0, description="Total number of executions")
    successful_executions: int = Field(default=0, description="Number of successful executions")
    partial_executions: int = Field(default=0, description="Number of partial successes")
    failed_executions: int = Field(default=0, description="Number of failures")
    error_executions: int = Field(default=0, description="Number of errors")

    # Success rate calculation
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Percentage successful")
    partial_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Percentage partial")
    failure_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Percentage failed")

    # Performance averages
    avg_execution_time_ms: float = Field(default=0.0, description="Average execution time")
    min_execution_time_ms: float = Field(default=0.0, description="Fastest execution")
    max_execution_time_ms: float = Field(default=0.0, description="Slowest execution")

    # Token usage
    avg_prompt_tokens: float = Field(default=0.0, description="Average prompt tokens")
    avg_completion_tokens: float = Field(default=0.0, description="Average completion tokens")
    avg_total_tokens: float = Field(default=0.0, description="Average total tokens")
    total_tokens_used: int = Field(default=0, description="Total tokens across period")

    # Quality metrics
    avg_quality_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Average quality rating"
    )
    avg_relevance: float = Field(default=0.0, ge=0.0, le=1.0, description="Average relevance")
    avg_correctness: float = Field(default=0.0, ge=0.0, le=1.0, description="Average correctness")
    avg_completeness: float = Field(default=0.0, ge=0.0, le=1.0, description="Average completeness")

    # Cost metrics
    cost_per_execution: float = Field(default=0.0, description="Average cost per execution")
    total_cost: float = Field(default=0.0, description="Total cost for period")

    # Trend analysis
    trend: str = Field(default="stable", description="improving|stable|degrading")
    trend_direction: float = Field(default=0.0, description="Rate of change (-1 to 1)")

    # Models used
    models_used: list[str] = Field(default_factory=list, description="List of models used")


class AgentPattern(BaseModel):
    """Extracted pattern from agent execution data."""

    # Pattern identity
    pattern_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique pattern ID")
    pattern_type: str = Field(..., description="success_pattern|failure_pattern|use_case")

    # Agents involved
    agents_involved: list[str] = Field(..., description="Agent IDs involved in pattern")

    # Pattern description
    description: str = Field(..., description="Human-readable pattern description")
    common_query: str | None = Field(default=None, description="Typical query triggering pattern")

    # Pattern frequency
    frequency: int = Field(default=0, description="How many times pattern occurred")
    frequency_percent: float = Field(default=0.0, description="Percentage of all executions")

    # Effectiveness
    effectiveness_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="How effective is this pattern (0-1)"
    )

    # Examples
    examples: list[dict[str, Any]] = Field(default_factory=list, description="Example executions")

    # Metadata
    discovered_date: datetime = Field(
        default_factory=datetime.utcnow, description="When pattern was found"
    )
    last_seen: datetime = Field(default_factory=datetime.utcnow, description="Last occurrence")
    tags: list[str] = Field(default_factory=list, description="Pattern classification tags")


class CapabilityVector(BaseModel):
    """Semantic capability representation of an agent."""

    # Capability identity
    capability_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique capability ID"
    )
    agent_id: str = Field(..., description="Agent ID")

    # Capability information
    capability_name: str = Field(..., description="Name of capability")
    capability_description: str = Field(..., description="What this capability does")

    # Confidence & source
    confidence_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence in this capability (0-1)"
    )
    source: str = Field(..., description="description|execution_log|user_feedback|inferred")

    # Vector embedding
    embedding: list[float] = Field(
        default_factory=list, description="Vector embedding (1536 dimensions)"
    )

    # Metadata
    extracted_date: datetime = Field(default_factory=datetime.utcnow, description="When extracted")
    usage_count: int = Field(default=0, description="Times this capability was used")
    last_used: datetime | None = Field(default=None, description="Last use date")

    # Related information
    related_capabilities: list[str] = Field(
        default_factory=list, description="IDs of related capabilities"
    )
    related_agents: list[str] = Field(
        default_factory=list, description="Other agents with similar capability"
    )


class CollaborationPattern(BaseModel):
    """Pattern of agents working together."""

    # Pattern identity
    pattern_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique pattern ID")

    # Agents involved
    primary_agent: str = Field(..., description="Main agent")
    collaborating_agents: list[str] = Field(..., description="Supporting agents")

    # Pattern information
    pattern_name: str = Field(..., description="Descriptive name for pattern")
    description: str = Field(..., description="How these agents work together")

    # Effectiveness
    success_rate: float = Field(default=0.0, description="Pattern success rate")
    frequency: int = Field(default=0, description="Times this pattern occurred")

    # Use cases
    use_cases: list[str] = Field(default_factory=list, description="Scenarios where useful")

    # Metadata
    discovered_date: datetime = Field(
        default_factory=datetime.utcnow, description="When discovered"
    )
    last_used: datetime | None = Field(default=None, description="Last use date")
    effectiveness_score: float = Field(default=0.0, description="Overall effectiveness (0-1)")

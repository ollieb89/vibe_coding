"""Improved search strategies for ultimate agent generation."""

SUBJECT_KEYWORDS = {
    "testing": [
        "testing",
        "test",
        "playwright",
        "vitest",
        "e2e",
        "unit test",
        "integration test",
        "qa",
        "quality",
        "assertion",
        "mock",
    ],
    "security": [
        "security",
        "owasp",
        "vulnerability",
        "auth",
        "authentication",
        "encryption",
        "threat",
        "compliance",
        "secure",
        "vulnerability assessment",
    ],
    "devops": [
        "devops",
        "ci/cd",
        "deployment",
        "infrastructure",
        "automation",
        "pipeline",
        "container",
        "docker",
        "kubernetes",
        "monitoring",
    ],
    "backend": [
        "backend",
        "api",
        "rest",
        "microservice",
        "database",
        "server",
        "fastapi",
        "django",
        "flask",
        "node",
        "express",
        "architecture",
    ],
    "frontend": [
        "frontend",
        "react",
        "vue",
        "angular",
        "ui",
        "component",
        "nextjs",
        "responsive",
        "css",
        "javascript",
        "typescript",
    ],
    "database": [
        "database",
        "sql",
        "postgres",
        "mongodb",
        "redis",
        "query",
        "optimization",
        "indexing",
        "schema",
        "migration",
        "orm",
    ],
    "data-science": [
        "data science",
        "machine learning",
        "ml",
        "ai",
        "nlp",
        "analytics",
        "data engineering",
        "pandas",
        "tensorflow",
        "pytorch",
        "model",
    ],
    "ai": [
        "ai",
        "llm",
        "language model",
        "gpt",
        "prompt",
        "generation",
        "machine learning",
        "neural network",
        "deep learning",
        "ml",
    ],
    "documentation": [
        "documentation",
        "docs",
        "readme",
        "guide",
        "tutorial",
        "markdown",
        "api doc",
        "javadoc",
        "comment",
        "docstring",
        "wiki",
    ],
    "architecture": [
        "architecture",
        "design",
        "pattern",
        "system design",
        "scalability",
        "performance",
        "reliability",
        "distributed",
        "caching",
        "modeling",
    ],
    "planning": [
        "planning",
        "project management",
        "requirements",
        "prd",
        "specification",
        "task",
        "roadmap",
        "sprint",
        "agile",
        "breakdown",
    ],
}


def enhance_search_query(subject: str) -> str:
    """Create an enhanced search query from subject.

    Args:
        subject: The subject to search for

    Returns:
        Enhanced query string with keywords
    """
    subject_lower = subject.lower().strip()

    # Check if we have keywords for this subject
    if subject_lower in SUBJECT_KEYWORDS:
        keywords = SUBJECT_KEYWORDS[subject_lower]
        # Use top 3 keywords for better relevance
        return " ".join(keywords[:3])

    # Fall back to original subject
    return subject

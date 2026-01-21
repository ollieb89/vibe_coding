"""Domain tag extractor."""

import re

from corpus_analyzer.core.database import CorpusDatabase
from corpus_analyzer.core.models import Document, DomainTag


# Domain detection patterns
DOMAIN_PATTERNS: dict[DomainTag, list[str]] = {
    DomainTag.BACKEND: [
        r"fastapi", r"flask", r"django", r"express", r"server",
        r"endpoint", r"rest\s?api", r"graphql",
    ],
    DomainTag.FRONTEND: [
        r"react", r"vue", r"angular", r"svelte", r"next\.?js",
        r"component", r"css", r"tailwind", r"html",
    ],
    DomainTag.NEXTJS: [
        r"next\.?js", r"from\s*['\"]next", r"next/",
    ],
    DomainTag.REACT: [
        r"react", r"from\s*['\"]react", r"use[A-Z]",
    ],
    DomainTag.GRAPHQL: [
        r"graphql", r"query\s*{", r"mutation\s*{", r"schema",
        r"resolver", r"apollo",
    ],
    DomainTag.TESTING: [
        r"pytest", r"jest", r"vitest", r"unittest", r"test_",
        r"mock", r"fixture", r"assert",
    ],
    DomainTag.TEMPORAL: [
        r"temporal", r"workflow", r"activity", r"signal",
        r"celery", r"task queue",
    ],
    DomainTag.PYTHON: [
        r"\.py\b", r"python", r"pip", r"pyproject", r"venv",
        r"uv\s", r"poetry",
    ],
    DomainTag.UV: [
        r"uv\s+run", r"uv\s+pip", r"uv\b", r"pixi",
    ],
    DomainTag.TYPESCRIPT: [
        r"typescript", r"\.ts\b", r"\.tsx\b", r"tsconfig",
        r"tsc\b", r"type\s*:",
    ],
    DomainTag.DATABASE: [
        r"sql", r"postgres", r"mysql", r"sqlite", r"mongodb",
        r"prisma", r"orm", r"migration", r"table",
    ],
    DomainTag.DEVOPS: [
        r"docker", r"kubernetes", r"k8s", r"ci/?cd", r"github\s?actions",
        r"terraform", r"ansible", r"helm",
    ],
    DomainTag.SECURITY: [
        r"auth", r"oauth", r"jwt", r"token", r"permission",
        r"rbac", r"encrypt", r"secret",
    ],
    DomainTag.AI: [
        r"llm", r"gpt", r"claude", r"ollama", r"openai",
        r"embedding", r"vector", r"rag", r"prompt",
    ],
}


def detect_domain_tags(doc: Document) -> list[DomainTag]:
    """Detect domain tags for a document."""
    # Build searchable text
    text_parts = [doc.title.lower()]
    text_parts.extend(h.text.lower() for h in doc.headings)
    text_parts.extend(doc.imports)

    # Add code block languages
    for cb in doc.code_blocks:
        if cb.language:
            text_parts.append(cb.language.lower())

    searchable_text = " ".join(text_parts)

    detected_tags: set[DomainTag] = set()

    for tag, patterns in DOMAIN_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, searchable_text, re.IGNORECASE):
                detected_tags.add(tag)
                break  # One match per domain is enough

    # Default to OTHER if no tags detected
    if not detected_tags:
        detected_tags.add(DomainTag.OTHER)

    return list(detected_tags)


def tag_documents(db: CorpusDatabase) -> int:
    """Apply domain tags to all documents."""
    count = 0
    for doc in db.get_documents():
        if doc.id is None:
            continue

        tags = detect_domain_tags(doc)
        db.update_document_tags(
            doc_id=doc.id,
            domain_tags=tags,
        )
        count += 1

    return count

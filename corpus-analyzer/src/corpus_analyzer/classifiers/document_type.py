"""Rule-based document type classifier."""

import re
from typing import NamedTuple

from corpus_analyzer.core.database import CorpusDatabase
from corpus_analyzer.core.models import Document, DocumentCategory


class ClassificationResult(NamedTuple):
    """Result of document classification."""

    category: DocumentCategory
    confidence: float
    matched_rules: list[str]


# Classification rules: (category, confidence_boost, heading_patterns, content_patterns)
CLASSIFICATION_RULES: list[tuple[DocumentCategory, float, list[str], list[str]]] = [
    # Persona documents
    (
        DocumentCategory.PERSONA,
        0.9,
        [r"role", r"expertise", r"personality", r"capabilities"],
        [r"you are", r"agent", r"persona", r"behave as"],
    ),
    # How-to guides
    (
        DocumentCategory.HOWTO,
        0.85,
        [r"steps?", r"how to", r"guide", r"instructions?"],
        [r"step \d+", r"first,?\s", r"then,?\s", r"finally,?\s"],
    ),
    # Runbooks
    (
        DocumentCategory.RUNBOOK,
        0.9,
        [r"troubleshoot", r"recovery", r"incident", r"alert", r"monitoring"],
        [r"on-call", r"escalat", r"runbook", r"procedure"],
    ),
    # Architecture docs
    (
        DocumentCategory.ARCHITECTURE,
        0.85,
        [r"component", r"system design", r"integration", r"overview", r"diagram"],
        [r"architecture", r"service", r"layer", r"module"],
    ),
    # Reference docs
    (
        DocumentCategory.REFERENCE,
        0.8,
        [r"api", r"parameters?", r"options?", r"configuration"],
        [r"\|.*\|.*\|", r"default:", r"type:"],  # Tables, config patterns
    ),
    # Tutorials
    (
        DocumentCategory.TUTORIAL,
        0.85,
        [r"prerequisites?", r"learning objectives?", r"lesson", r"exercise"],
        [r"tutorial", r"learn", r"beginner", r"getting started"],
    ),
    # ADRs (Architecture Decision Records)
    (
        DocumentCategory.ADR,
        0.95,
        [r"status", r"context", r"decision", r"consequences"],
        [r"adr", r"decision record", r"accepted", r"proposed", r"deprecated"],
    ),
    # Specifications
    (
        DocumentCategory.SPEC,
        0.9,
        [r"requirements?", r"constraints?", r"scope", r"acceptance criteria"],
        [r"spec", r"rfc", r"must\s", r"shall\s", r"should\s"],
    ),
]


def classify_document(doc: Document) -> ClassificationResult:
    """Classify a single document based on rules."""
    scores: dict[DocumentCategory, tuple[float, list[str]]] = {}

    # Collect heading text
    heading_text = " ".join(h.text.lower() for h in doc.headings)

    # For matching content patterns, we need the actual content
    # For now, use headings + title as proxy
    content_text = f"{doc.title.lower()} {heading_text}"

    for category, base_confidence, heading_patterns, content_patterns in CLASSIFICATION_RULES:
        matched = []
        score = 0.0

        # Check heading patterns
        for pattern in heading_patterns:
            if re.search(pattern, heading_text, re.IGNORECASE):
                matched.append(f"heading:{pattern}")
                score += 0.2

        # Check content patterns
        for pattern in content_patterns:
            if re.search(pattern, content_text, re.IGNORECASE):
                matched.append(f"content:{pattern}")
                score += 0.15

        if matched:
            # Cap score and apply base confidence
            final_score = min(score, 1.0) * base_confidence
            scores[category] = (final_score, matched)

    if not scores:
        return ClassificationResult(
            category=DocumentCategory.UNKNOWN,
            confidence=0.0,
            matched_rules=[],
        )

    # Return highest scoring category
    best_category = max(scores.keys(), key=lambda c: scores[c][0])
    confidence, matched = scores[best_category]

    return ClassificationResult(
        category=best_category,
        confidence=confidence,
        matched_rules=matched,
    )


def classify_documents(db: CorpusDatabase) -> int:
    """Classify all documents in the database."""
    count = 0
    for doc in db.get_documents():
        if doc.id is None:
            continue

        result = classify_document(doc)
        db.update_document_classification(
            doc_id=doc.id,
            category=result.category,
            confidence=result.confidence,
        )
        count += 1

    return count

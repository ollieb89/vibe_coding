"""Enhanced document type classifier with TF-IDF and semantic analysis."""

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

from corpus_analyzer.core.database import CorpusDatabase
from corpus_analyzer.core.models import Document, DocumentCategory


class ClassificationResult(NamedTuple):
    """Result of document classification."""

    category: DocumentCategory
    confidence: float
    matched_rules: list[str]
    secondary_category: DocumentCategory | None = None
    secondary_confidence: float = 0.0
    content_similarity: float = 0.0
    feature_scores: dict[str, float] = field(default_factory=dict)


@dataclass
class DocumentFeatures:
    """Extracted features from document for classification."""
    
    # Text features
    headings_text: str = ""
    full_text: str = ""
    title_text: str = ""
    code_languages: set[str] = field(default_factory=set)
    
    # Structural features
    heading_count: int = 0
    code_block_count: int = 0
    link_count: int = 0
    has_numbered_sections: bool = False
    has_toc: bool = False
    
    # Content indicators
    step_indicators: int = 0
    code_examples: int = 0
    api_patterns: int = 0
    diagram_references: int = 0


def extract_document_features(doc: Document, content: str | None = None) -> DocumentFeatures:
    """Extract comprehensive features from document."""
    features = DocumentFeatures()
    
    # Basic text features
    features.headings_text = " ".join(h.text.lower() for h in doc.headings)
    features.title_text = doc.title.lower()
    features.heading_count = len(doc.headings)
    features.code_block_count = len(doc.code_blocks)
    features.link_count = len(doc.links)
    
    # Code languages
    features.code_languages = {cb.language.lower() for cb in doc.code_blocks if cb.language}
    
    # Full text content (if provided)
    if content:
        features.full_text = content.lower()
    else:
        # Build from available components
        text_parts = [features.title_text, features.headings_text]
        for cb in doc.code_blocks:
            text_parts.append(cb.content.lower())
        features.full_text = " ".join(text_parts)
    
    # Structural analysis
    features.has_numbered_sections = bool(re.search(r'\b(?:step\s+\d+|\d+\.|\d+\))', features.full_text, re.IGNORECASE))
    features.has_toc = bool(re.search(r'table\s+of\s+contents?|contents?:', features.full_text, re.IGNORECASE))
    
    # Content indicators
    features.step_indicators = len(re.findall(r'\b(?:step|first|then|next|finally)\b', features.full_text, re.IGNORECASE))
    features.code_examples = len(re.findall(r'```[\w]*\n|example|code\s+snippet', features.full_text, re.IGNORECASE))
    features.api_patterns = len(re.findall(r'\b(?:api|endpoint|function|method|parameter)\b', features.full_text, re.IGNORECASE))
    features.diagram_references = len(re.findall(r'\b(?:diagram|chart|graph|figure)\b', features.full_text, re.IGNORECASE))
    
    return features


def compute_tfidf_similarity(text: str, category_patterns: dict[DocumentCategory, list[str]]) -> dict[DocumentCategory, float]:
    """Compute TF-IDF similarity between text and category patterns."""
    # Simple TF-IDF implementation
    similarities = {}
    
    # Tokenize text
    tokens = re.findall(r'\b\w+\b', text.lower())
    token_counts = Counter(tokens)
    total_tokens = len(tokens)
    
    for category, patterns in category_patterns.items():
        # Build category vocabulary from patterns
        category_tokens = []
        for pattern in patterns:
            # Extract meaningful words from patterns
            pattern_words = re.findall(r'\b\w+\b', pattern.lower())
            category_tokens.extend(pattern_words)
        
        if not category_tokens:
            similarities[category] = 0.0
            continue
            
        category_counts = Counter(category_tokens)
        
        # Compute cosine similarity
        similarity = 0.0
        for token in set(tokens) & set(category_tokens):
            tf = token_counts[token] / total_tokens
            # Simple IDF approximation
            idf = math.log(len(category_patterns) / sum(1 for p in category_patterns.values() if token in ' '.join(p)))
            similarity += tf * idf
        
        similarities[category] = similarity
    
    return similarities


# Enhanced classification rules with weights and feature requirements
CLASSIFICATION_RULES: list[tuple[DocumentCategory, float, list[str], list[str], dict[str, float]]] = [
    # Persona documents
    (
        DocumentCategory.PERSONA,
        0.9,
        [r"role", r"expertise", r"personality", r"capabilities"],
        [r"you are", r"agent", r"persona", r"behave as"],
        {"step_indicators": -0.5, "code_examples": -0.3, "api_patterns": -0.2}
    ),
    # How-to guides
    (
        DocumentCategory.HOWTO,
        0.85,
        [r"steps?", r"how to", r"guide", r"instructions?"],
        [r"step \d+", r"first,?\s", r"then,?\s", r"finally,?\s"],
        {"step_indicators": 0.4, "code_examples": 0.3, "has_numbered_sections": 0.2}
    ),
    # Runbooks
    (
        DocumentCategory.RUNBOOK,
        0.9,
        [r"troubleshoot", r"recovery", r"incident", r"alert", r"monitoring"],
        [r"on-call", r"escalat", r"runbook", r"procedure"],
        {"step_indicators": 0.3, "code_examples": 0.1, "api_patterns": 0.1}
    ),
    # Architecture docs
    (
        DocumentCategory.ARCHITECTURE,
        0.85,
        [r"component", r"system design", r"integration", r"overview", r"diagram"],
        [r"architecture", r"service", r"layer", r"module"],
        {"diagram_references": 0.4, "code_examples": 0.2, "api_patterns": 0.1}
    ),
    # Reference docs
    (
        DocumentCategory.REFERENCE,
        0.8,
        [r"api", r"parameters?", r"options?", r"configuration"],
        [r"\|.*\|.*\|", r"default:", r"type:"],  # Tables, config patterns
        {"api_patterns": 0.5, "code_examples": 0.3, "step_indicators": -0.2}
    ),
    # Tutorials
    (
        DocumentCategory.TUTORIAL,
        0.85,
        [r"prerequisites?", r"learning objectives?", r"lesson", r"exercise"],
        [r"tutorial", r"learn", r"beginner", r"getting started"],
        {"step_indicators": 0.3, "code_examples": 0.4, "has_toc": 0.2}
    ),
    # ADRs (Architecture Decision Records)
    (
        DocumentCategory.ADR,
        0.95,
        [r"status", r"context", r"decision", r"consequences"],
        [r"adr", r"decision record", r"accepted", r"proposed", r"deprecated"],
        {"step_indicators": -0.3, "code_examples": -0.2, "api_patterns": -0.1}
    ),
    # Specifications
    (
        DocumentCategory.SPEC,
        0.9,
        [r"requirements?", r"constraints?", r"scope", r"acceptance criteria"],
        [r"spec", r"rfc", r"must\s", r"shall\s", r"should\s"],
        {"api_patterns": 0.2, "code_examples": 0.1, "step_indicators": -0.1}
    ),
]


def classify_document(doc: Document, content: str | None = None) -> ClassificationResult:
    """Classify a single document using enhanced analysis."""
    
    # Extract comprehensive features
    features = extract_document_features(doc, content)
    
    # Build category patterns for TF-IDF
    category_patterns: dict[DocumentCategory, list[str]] = {}
    for category, _, heading_patterns, content_patterns, _ in CLASSIFICATION_RULES:
        category_patterns[category] = heading_patterns + content_patterns
    
    # Compute TF-IDF similarity
    similarities = compute_tfidf_similarity(features.full_text, category_patterns)
    
    # Enhanced scoring with features
    scores: dict[DocumentCategory, tuple[float, list[str], dict[str, float]]] = {}
    
    for category, base_confidence, heading_patterns, content_patterns, feature_weights in CLASSIFICATION_RULES:
        matched = []
        feature_scores: dict[str, float] = {}
        score = 0.0

        # Check heading patterns
        for pattern in heading_patterns:
            if re.search(pattern, features.headings_text, re.IGNORECASE):
                matched.append(f"heading:{pattern}")
                score += 0.2

        # Check content patterns
        for pattern in content_patterns:
            if re.search(pattern, features.full_text, re.IGNORECASE):
                matched.append(f"content:{pattern}")
                score += 0.15

        # Apply feature-based scoring
        for feature_name, weight in feature_weights.items():
            feature_value = getattr(features, feature_name, 0)
            if isinstance(feature_value, bool):
                feature_value = 1.0 if feature_value else 0.0
            elif isinstance(feature_value, int) and feature_value > 0:
                # Normalize by typical max values
                if feature_name in ["step_indicators", "code_examples", "api_patterns", "diagram_references"]:
                    feature_value = min(feature_value / 10.0, 1.0)
                elif feature_name in ["heading_count", "code_block_count", "link_count"]:
                    feature_value = min(feature_value / 20.0, 1.0)
            
            feature_score = weight * feature_value
            feature_scores[feature_name] = feature_score
            score += feature_score

        # Add TF-IDF similarity boost
        similarity_boost = similarities.get(category, 0.0) * 0.1
        feature_scores["tfidf_similarity"] = similarity_boost
        score += similarity_boost

        if matched or score > 0:
            # Cap score and apply base confidence
            final_score = min(max(score, 0.0), 1.0) * base_confidence
            scores[category] = (final_score, matched, feature_scores)

    if not scores:
        return ClassificationResult(
            category=DocumentCategory.UNKNOWN,
            confidence=0.0,
            matched_rules=[],
            content_similarity=0.0,
            feature_scores={},
        )

    # Sort categories by score
    sorted_categories = sorted(scores.keys(), key=lambda c: scores[c][0], reverse=True)
    
    # Primary category
    best_category = sorted_categories[0]
    confidence, matched, feature_scores = scores[best_category]
    
    # Secondary category (if close second)
    secondary_category = None
    secondary_confidence = 0.0
    if len(sorted_categories) > 1:
        second_best = sorted_categories[1]
        second_score = scores[second_best][0]
        if second_score > confidence * 0.7:  # Within 70% of primary
            secondary_category = second_best
            secondary_confidence = second_score

    return ClassificationResult(
        category=best_category,
        confidence=confidence,
        matched_rules=matched,
        secondary_category=secondary_category,
        secondary_confidence=secondary_confidence,
        content_similarity=similarities.get(best_category, 0.0),
        feature_scores=feature_scores,
    )


def read_document_content(doc_path: Path) -> str:
    """Read full document content for enhanced analysis."""
    try:
        return doc_path.read_text(encoding="utf-8")
    except Exception:
        return ""


def classify_documents(db: CorpusDatabase, use_full_content: bool = True) -> int:
    """Classify all documents in the database with enhanced analysis."""
    count = 0
    for doc in db.get_documents():
        if doc.id is None:
            continue

        # Read full content if requested and available
        content = None
        if use_full_content:
            try:
                content = read_document_content(doc.path)
            except Exception:
                content = None

        result = classify_document(doc, content)
        
        # Update with enhanced classification data
        db.update_document_classification(
            doc_id=doc.id,
            category=result.category,
            confidence=result.confidence,
        )
        
        # Store secondary category if available
        if result.secondary_category and result.secondary_confidence > 0.5:
            # Note: This would require database schema update
            # For now, we'll store in a simple way
            pass
        
        count += 1

    return count

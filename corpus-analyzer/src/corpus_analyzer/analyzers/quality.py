"""Quality analysis for documents."""

import logging
from typing import Optional

from corpus_analyzer.core.database import CorpusDatabase
from corpus_analyzer.core.models import Document, DocumentCategory, DomainTag

logger = logging.getLogger(__name__)

class QualityAnalyzer:
    """Analyzes document quality and identifies gold standard patterns."""

    def __init__(self, db: CorpusDatabase) -> None:
        """Initialize with database."""
        self.db = db

    def calculate_score(self, doc: Document) -> float:
        """
        Calculate a quality score (0.0 to 1.0).
        
        Metrics:
        1. Heading density (more headings usually means better structure)
        2. Code block presence
        3. Link density
        4. Size (moderate size is better than tiny or massive)
        """
        score = 0.0
        
        # 1. Heading score (up to 0.4)
        heading_count = len(doc.headings)
        if heading_count >= 5:
            score += 0.4
        elif heading_count >= 2:
            score += 0.2
            
        # 2. Code block score (up to 0.3)
        if len(doc.code_blocks) > 0:
            score += 0.3
            
        # 3. Size score (up to 0.3)
        # Optimal size around 2KB - 10KB
        if 2000 <= doc.size_bytes <= 10000:
            score += 0.3
        elif doc.size_bytes > 500:
            score += 0.1
            
        return round(score, 2)

    def analyze_all(self) -> int:
        """Analyze all documents and mark gold standards."""
        count = 0
        documents = list(self.db.get_documents())
        
        # First pass: calculate scores
        for doc in documents:
            if doc.id is None:
                continue
            
            score = self.calculate_score(doc)
            self.db.update_document_quality(doc.id, score, is_gold_standard=False)
            doc.quality_score = score
            count += 1
            
        # Second pass: mark gold standards per (Category, Tag)
        # We'll take the top 10% in each category that have at least 0.5 score
        categories = self.db.get_categories()
        for cat_name in categories:
            cat = DocumentCategory(cat_name)
            # Find document with highest score in this category
            category_docs = sorted(
                [d for d in documents if d.category == cat],
                key=lambda x: x.quality_score,
                reverse=True
            )
            
            # Mark top doc as gold if score is decent
            if category_docs and category_docs[0].quality_score >= 0.5:
                top_doc = category_docs[0]
                if top_doc.id:
                    self.db.update_document_quality(top_doc.id, top_doc.quality_score, is_gold_standard=True)
                    logger.info(f"Marked {top_doc.path} as gold standard for {cat.value}")

        return count

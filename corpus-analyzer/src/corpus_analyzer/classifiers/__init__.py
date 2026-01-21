"""Classifiers package."""

from corpus_analyzer.classifiers.document_type import classify_documents
from corpus_analyzer.classifiers.domain_tags import tag_documents

__all__ = ["classify_documents", "tag_documents"]

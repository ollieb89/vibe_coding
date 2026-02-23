"""Corpus public API re-exports.

Usage:
    from corpus import search, index
    results = search("my query")
"""

from corpus_analyzer.api.public import SearchResult, index, search

__all__ = ["SearchResult", "search", "index"]

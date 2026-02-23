import logging
import sys
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
from unittest.mock import patch
from corpus_analyzer.ingest.indexer import CorpusIndex
from tests.ingest.test_indexer import MockEmbedder

def test():
    embedder = MockEmbedder()
    # mock table
    class MockTable:
        def search(self):
            raise RuntimeError("db error")
            
    index = CorpusIndex(MockTable(), embedder)
    index._get_existing_files("my-source")

test()

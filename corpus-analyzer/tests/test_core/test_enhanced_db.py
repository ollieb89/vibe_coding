import pytest
from pathlib import Path
from datetime import datetime
from corpus_analyzer.core.database import CorpusDatabase
from corpus_analyzer.core.models import Document, DocumentCategory, DomainTag

def test_database_quality_fields(tmp_path):
    db_path = tmp_path / "test.sqlite"
    db = CorpusDatabase(db_path)
    db.initialize()
    
    doc = Document(
        path=Path("gold.md"),
        relative_path="gold.md",
        file_type="md",
        title="Gold Doc",
        mtime=datetime.now(),
        size_bytes=100,
        category=DocumentCategory.HOWTO,
        quality_score=0.9,
        is_gold_standard=True
    )
    
    doc_id = db.insert_document(doc)
    
    # Retrieve and check
    retrieved = db.get_document_by_id(doc_id)
    assert retrieved.quality_score == 0.9
    assert retrieved.is_gold_standard is True
    
    # Update quality
    db.update_document_quality(doc_id, 0.95, False)
    retrieved = db.get_document_by_id(doc_id)
    assert retrieved.quality_score == 0.95
    assert retrieved.is_gold_standard is False

def test_get_gold_standard_documents(tmp_path):
    db_path = tmp_path / "test.sqlite"
    db = CorpusDatabase(db_path)
    db.initialize()
    
    doc1 = Document(
        path=Path("doc1.md"), relative_path="doc1.md", file_type="md", title="D1",
        mtime=datetime.now(), size_bytes=100, category=DocumentCategory.HOWTO,
        domain_tags=[DomainTag.PYTHON], is_gold_standard=True
    )
    doc2 = Document(
        path=Path("doc2.md"), relative_path="doc2.md", file_type="md", title="D2",
        mtime=datetime.now(), size_bytes=100, category=DocumentCategory.HOWTO,
        is_gold_standard=False
    )
    
    db.insert_document(doc1)
    db.insert_document(doc2)
    
    gold_docs = list(db.get_gold_standard_documents())
    assert len(gold_docs) == 1
    assert gold_docs[0].title == "D1"
    
    gold_python = list(db.get_gold_standard_documents(tag=DomainTag.PYTHON))
    assert len(gold_python) == 1

from corpus_analyzer.core.database import CorpusDatabase
from corpus_analyzer.core.models import Document, DocumentCategory
from pathlib import Path
from datetime import datetime

def test_set_gold_standard(tmp_path):
    db_path = tmp_path / "test.db"
    db = CorpusDatabase(db_path)
    db.initialize()

    doc = Document(
        path=Path("test.md"), relative_path="test.md", file_type="md",
        title="Test Doc", mtime=datetime.now(), size_bytes=100
    )
    db.insert_document(doc)
    doc_id = list(db.get_documents())[0].id
    
    # Original state
    retrieved = db.get_document(doc_id)
    assert not retrieved.is_gold_standard

    # Update
    db.set_gold_standard(doc_id, True)
    
    # Verify
    updated = db.get_document(doc_id)
    assert updated.is_gold_standard

    # Toggle back
    db.set_gold_standard(doc_id, False)
    assert not db.get_document(doc_id).is_gold_standard

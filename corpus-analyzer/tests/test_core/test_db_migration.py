import pytest
from pathlib import Path
from datetime import datetime
from corpus_analyzer.core.database import CorpusDatabase
from corpus_analyzer.core.models import Document, DocumentCategory

def test_auto_migration_missing_columns(tmp_path):
    db_path = tmp_path / "test_migration.sqlite"
    db = CorpusDatabase(db_path)
    
    # Manually create table without the new columns
    db.db.executescript("""
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            relative_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            title TEXT NOT NULL,
            mtime TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            headings TEXT,
            links TEXT,
            code_blocks TEXT,
            token_estimate INTEGER DEFAULT 0,
            module_docstring TEXT,
            imports TEXT,
            symbols TEXT,
            is_cli INTEGER DEFAULT 0,
            category TEXT DEFAULT 'unknown',
            category_confidence REAL DEFAULT 0.0,
            domain_tags TEXT
        )
    """)
    
    # 2. Try to retrieve an *existing* document that was in the DB during migration
    # First, let's add one via raw SQL to ensure it has NULLs
    db.db.execute("INSERT INTO documents (path, relative_path, file_type, title, mtime, size_bytes) VALUES (?, ?, ?, ?, ?, ?)", 
                  ["legacy.md", "legacy.md", "md", "Legacy", datetime.now().isoformat(), 100])
    
    # Try to load all documents
    all_docs = list(db.get_documents())
    assert len(all_docs) >= 1
    legacy = next(d for d in all_docs if d.title == "Legacy")
    assert legacy.quality_score == 0.0
    assert legacy.is_gold_standard is False
    
    # 3. Try to insert a document with more fields
    doc = Document(
        path=Path("migration_test.md"),
        relative_path="migration_test.md",
        file_type="md",
        title="Migration Test",
        mtime=datetime.now(),
        size_bytes=100,
        quality_score=0.85,
        is_gold_standard=True
    )
    
    # This should work now because of alter=True
    doc_id = db.insert_document(doc)
    
    # Verify columns were added
    retrieved = db.get_document_by_id(doc_id)
    assert retrieved.quality_score == 0.85
    assert retrieved.is_gold_standard is True

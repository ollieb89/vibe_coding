import pytest
from pathlib import Path
from datetime import datetime
from corpus_analyzer.core.database import CorpusDatabase
from corpus_analyzer.core.models import Document, DocumentCategory, Heading, CodeBlock
from corpus_analyzer.analyzers.quality import QualityAnalyzer

def test_quality_scoring(tmp_path):
    db_path = tmp_path / "test.sqlite"
    db = CorpusDatabase(db_path)
    db.initialize()
    
    analyzer = QualityAnalyzer(db)
    
    # 1. Low quality doc
    doc_low = Document(
        path=Path("low.md"), relative_path="low.md", file_type="md", title="Low",
        mtime=datetime.now(), size_bytes=100
    )
    score_low = analyzer.calculate_score(doc_low)
    assert score_low < 0.3
    
    # 2. High quality doc
    doc_high = Document(
        path=Path("high.md"), relative_path="high.md", file_type="md", title="High Quality Guide",
        mtime=datetime.now(), size_bytes=5000,
        headings=[
            Heading(level=1, text="Title", line_number=1),
            Heading(level=2, text="Steps", line_number=10),
            Heading(level=2, text="Code", line_number=20),
            Heading(level=2, text="Summary", line_number=30),
            Heading(level=2, text="Next Steps", line_number=40)
        ],
        code_blocks=[CodeBlock(content="print('hi')", content_hash="123", line_start=21, line_end=22)]
    )
    score_high = analyzer.calculate_score(doc_high)
    assert score_high >= 0.7

def test_analyze_all_marks_gold(tmp_path):
    db_path = tmp_path / "test.sqlite"
    db = CorpusDatabase(db_path)
    db.initialize()
    
    # Add a good doc
    doc1 = Document(
        path=Path("good.md"), relative_path="good.md", file_type="md", title="Good Guide",
        mtime=datetime.now(), size_bytes=5000, category=DocumentCategory.HOWTO,
        headings=[Heading(level=1, text="H1", line_number=1)] * 5,
        code_blocks=[CodeBlock(content="code", content_hash="1", line_start=1, line_end=2)]
    )
    db.insert_document(doc1)
    
    # Add a poor doc
    doc2 = Document(
        path=Path("poor.md"), relative_path="poor.md", file_type="md", title="Poor",
        mtime=datetime.now(), size_bytes=100, category=DocumentCategory.HOWTO
    )
    db.insert_document(doc2)
    
    analyzer = QualityAnalyzer(db)
    analyzer.analyze_all()
    
    # Check gold standard
    gold_docs = list(db.get_gold_standard_documents(category=DocumentCategory.HOWTO))
    assert len(gold_docs) == 1
    assert gold_docs[0].title == "Good Guide"

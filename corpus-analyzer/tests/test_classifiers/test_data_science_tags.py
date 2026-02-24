from datetime import datetime
from pathlib import Path

from corpus_analyzer.classifiers.domain_tags import detect_domain_tags
from corpus_analyzer.core.models import Document, DomainTag


def test_detect_data_science_tags():
    doc = Document(
        path=Path("analysis.py"),
        relative_path="analysis.py",
        file_type="py",
        title="Data Analysis",
        mtime=datetime.now(),
        size_bytes=100,
        imports=["pandas", "numpy", "scikit-learn"]
    )
    tags = detect_domain_tags(doc)
    # This should fail until we add the tag and logic
    assert hasattr(DomainTag, 'DATA_SCIENCE'), "DATA_SCIENCE tag not present in Enum"
    assert DomainTag.DATA_SCIENCE in tags

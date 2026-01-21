import pytest
from pathlib import Path
from datetime import datetime
from corpus_analyzer.core.models import Document, DomainTag, DocumentCategory
from corpus_analyzer.classifiers.domain_tags import detect_domain_tags

def test_detect_domain_tags_nextjs():
    doc = Document(
        path=Path("test.md"),
        relative_path="test.md",
        file_type="md",
        title="My Next.js App",
        mtime=datetime.now(),
        size_bytes=100,
        imports=["import { useRouter } from 'next/router'"]
    )
    tags = detect_domain_tags(doc)
    assert DomainTag.NEXTJS in tags
    assert DomainTag.FRONTEND in tags

def test_detect_domain_tags_react():
    doc = Document(
        path=Path("test.tsx"),
        relative_path="test.tsx",
        file_type="tsx",
        title="React Component",
        mtime=datetime.now(),
        size_bytes=100,
        imports=["import React, { useState } from 'react'"]
    )
    tags = detect_domain_tags(doc)
    assert DomainTag.REACT in tags
    assert DomainTag.FRONTEND in tags

def test_detect_domain_tags_uv():
    doc = Document(
        path=Path("script.py"),
        relative_path="script.py",
        file_type="py",
        title="UV Script",
        mtime=datetime.now(),
        size_bytes=100,
    )
    # Simulate finding "uv run" in a heading
    from corpus_analyzer.core.models import Heading
    doc.headings = [Heading(level=1, text="How to uv run this", line_number=1)]
    tags = detect_domain_tags(doc)
    assert DomainTag.UV in tags
    assert DomainTag.PYTHON in tags

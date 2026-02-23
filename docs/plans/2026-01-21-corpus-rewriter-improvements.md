# Corpus Rewriter Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve the quality, performance, and usability of the Corpus Analyzer rewriter and classification system.

**Architecture:** 
- **Prompt Tuning**: Refine prompts to enforce quality standards (frontmatter, structure) and relax strict scoring if necessary.
- **Library Detection**: Expand the taxonomy and detection logic for new libraries.
- **Human Evaluation**: Add a CLI flow for manual "Gold Standard" tagging.
- **Performance**: Parallelize LLM calls using a thread pool.
- **Smart Chunking**: Improve document splitting to respect semantic boundaries (headings) more strictly.

**Tech Stack:** Python, Typer (CLI), Regex, ThreadPoolExecutor, Pydantic.

---

### Task 1: Prompt Tuning & Quality Scoring

**Files:**
- Modify: `corpus-analyzer/src/corpus_analyzer/llm/rewriter.py`

**Step 1: Write the failing test (Quality Logic)**
Create a test that currently produces a "Low quality score" warning for a valid output, or asserts on the current strict scoring. Since we are tuning, we might skip a "failing" test and go straight to verification code, but let's try to simulate a borderline case.

```python
# tests/llm/test_rewriter_quality.py
from corpus_analyzer.llm.rewriter import validate_output

def test_quality_score_relaxed():
    # A content that is good but might fail current strict checks (e.g., minor heading skips)
    content = """---
title: Valid Doc
---
# Title
### Skip Level (H3)
Content
"""
    report = validate_output(content)
    # This might fail currently if H1->H3 is strictly penalized
    assert report.score >= 80, f"Score too low: {report.score}"
```

**Step 2: Modify Prompts & Quality Logic**
1. Update `CATEGORY_PROMPTS` in `rewriter.py` to be even more explicit about Frontmatter and Headings.
2. Adjust `QualityReport.score` in `rewriter.py` to be less punitive for minor issues if needed, or fix the prompt to ensure the model complies.
3. Update `validate_output` to be robust.

**Step 3: Verification**
Run the rewrite on a sample doc and verify warnings are reduced.

---

### Task 2: Library Detection Expansion

**Files:**
- Modify: `corpus-analyzer/src/corpus_analyzer/core/models.py`
- Modify: `corpus-analyzer/src/corpus_analyzer/classifiers/domain_tags.py`

**Step 1: Write the failing test**

```python
# tests/classifiers/test_domain_tags.py
from corpus_analyzer.core.models import Document, DomainTag
from corpus_analyzer.classifiers.domain_tags import detect_domain_tags
from pathlib import Path
from datetime import datetime

def test_detect_new_libraries():
    doc = Document(
        path=Path("test.py"), relative_path="test.py", file_type="py",
        title="Data Analysis with Pandas", mtime=datetime.now(), size_bytes=100,
        imports=["pandas", "numpy"]
    )
    tags = detect_domain_tags(doc)
    assert DomainTag.DATA_SCIENCE in tags # New tag
```

**Step 2: Implement Changes**
1. Add `DATA_SCIENCE` (and others like `FASTAPI` if not implicitly covered by Backend) to `DomainTag` in `models.py`.
2. Update `DOMAIN_PATTERNS` in `domain_tags.py` with regex for Pandas, NumPy, Scikit, etc.
3. Add `FASTAPI` specific patterns if needed, or ensure `BACKEND` covers it well (it does currently, but maybe we want specific tags).

**Step 3: Verify**
Run `pytest tests/classifiers/test_domain_tags.py`.

---

### Task 3: Human Evaluation CLI

**Files:**
- Modify: `corpus-analyzer/src/corpus_analyzer/cli.py`
- Modify: `corpus-analyzer/src/corpus_analyzer/core/database.py` (if update method needed)

**Step 1: Write the failing test**
Testing CLI interaction is tricky, but we can test the database update method.

```python
# tests/core/test_database_gold_standard.py
def test_toggle_gold_standard(db):
    doc = create_test_doc(db)
    assert not doc.is_gold_standard
    db.set_gold_standard(doc.id, True)
    updated = db.get_document(doc.id)
    assert updated.is_gold_standard
```

**Step 2: Implement Database Method**
Add `set_gold_standard` to `CorpusDatabase`.

**Step 3: Implement CLI Command**
Add `review` command to `cli.py`:
- Iterate over docs (filter by category/tag optional).
- Show content preview.
- Prompt: "Mark as Gold Standard? [y/N/q]".
- Update DB.

---

### Task 4: Performance (Parallelization)

**Files:**
- Modify: `corpus-analyzer/src/corpus_analyzer/llm/rewriter.py`

**Step 1: Write the failing test (Performance benchmark - optional)**
We can't easily write a failing test for "it's too slow", but we can write a test that ensures parallel execution works.

**Step 2: Implement Parallelization**
Refactor `rewrite_category` to use `concurrent.futures.ThreadPoolExecutor`.
- Extract single-doc processing into a helper function `_process_single_doc`.
- Use `executor.map` or `submit`.
- Collect results and errors safely.

**Step 3: Verification**
Run `rewrite` on a category and check it completes (and potentially faster, though local Ollama might limit speed).

---

### Task 5: Smart Splitting

**Files:**
- Modify: `corpus-analyzer/src/corpus_analyzer/llm/chunked_processor.py`

**Step 1: Write the failing test**

```python
# tests/llm/test_chunking.py
from corpus_analyzer.llm.chunked_processor import split_on_headings

def test_semantic_split():
    # Create content with H1 -> H2 structure
    content = "# H1\n\n" + ("Text\n" * 100) + "\n## H2\n\n" + ("Text\n" * 100)
    # Force split size such that it *could* split in the middle of H1 text, but *should* split at H2
    chunks = split_on_headings(content, max_chunk_size=len(content)//2 + 50)
    
    # Assert headers are preserved at start of chunks
    assert chunks[1].heading == "H2", "Should have split at H2"
```

**Step 2: Implement Improvement**
Modify `split_on_headings`:
- Instead of just appending lines until full, look ahead for "major" headings (H1, H2) to verify if we are near a logical break.
- If a chunk is getting full, try to backtrack to the last H2 or H3 to split there instead of a random line.

**Step 3: Verify**
Run the test.

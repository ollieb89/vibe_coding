from corpus_analyzer.llm.rewriter import validate_output, QualityReport

def test_quality_score_relaxed():
    # A content that is good but might fail current strict checks (e.g., minor heading skips)
    # This document skips from H1 to H3, which currently penalizes the score.
    content = """---
title: Valid Doc
---
# Title
### Skip Level (H3)
Content
"""
    report = validate_output(content)
    # We want this to be acceptable (>= 80) or at least not fail hard if we relax logic
    print(f"Score: {report.score}, Issues: {report.issues}")
    assert report.score >= 80, f"Score too low: {report.score}. Issues: {report.issues}"

def test_truncation_detection():
    content = "Some content\n[truncated]\nMore content"
    report = validate_output(content)
    assert report.is_truncated
    assert report.score < 80

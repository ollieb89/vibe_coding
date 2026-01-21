"""Quality scoring for rewritten documents."""

import re
from dataclasses import dataclass, field
from enum import Enum


class IssueSeverity(Enum):
    """Severity levels for quality issues."""
    
    CRITICAL = "critical"  # Must be fixed
    HIGH = "high"          # Should be fixed
    MEDIUM = "medium"      # Consider fixing
    LOW = "low"            # Minor improvement
    INFO = "info"          # Informational only


@dataclass
class QualityIssue:
    """A specific quality issue found in content."""
    
    severity: IssueSeverity
    category: str
    message: str
    line: int | None = None
    suggestion: str | None = None


@dataclass
class QualityScore:
    """Comprehensive quality assessment."""
    
    raw_score: float = 100.0
    issues: list[QualityIssue] = field(default_factory=list)
    
    # Detailed metrics
    structure_score: float = 100.0
    completeness_score: float = 100.0
    formatting_score: float = 100.0
    citation_score: float = 100.0
    
    @property
    def overall_score(self) -> float:
        """Calculate weighted overall score."""
        weights = {
            'structure': 0.3,
            'completeness': 0.3,
            'formatting': 0.25,
            'citation': 0.15,
        }
        return (
            self.structure_score * weights['structure'] +
            self.completeness_score * weights['completeness'] +
            self.formatting_score * weights['formatting'] +
            self.citation_score * weights['citation']
        )
    
    @property
    def grade(self) -> str:
        """Return letter grade."""
        s = self.overall_score
        if s >= 90:
            return "A"
        elif s >= 80:
            return "B"
        elif s >= 70:
            return "C"
        elif s >= 60:
            return "D"
        return "F"
    
    @property
    def passed(self) -> bool:
        """Check if document passes quality threshold."""
        return self.overall_score >= 60 and not any(
            issue.severity == IssueSeverity.CRITICAL for issue in self.issues
        )


# Patterns for detection
PLACEHOLDER_PATTERN = re.compile(r'\$[A-Z_]+')
UNCLOSED_CODE_BLOCK = re.compile(r'^```', re.MULTILINE)
CITATION_PATTERN = re.compile(r'\[source:\s*[^\]]+\]')
HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

TRUNCATION_INDICATORS = [
    "[truncated]",
    "# ... (",
    "// ... (",
    "/* ... */",
    "... (code block",
    "... (function",
]


def score_document(content: str, source_path: str | None = None) -> QualityScore:
    """Score a rewritten document for quality.
    
    Args:
        content: The rewritten document content
        source_path: Optional path to original source for citation check
        
    Returns:
        QualityScore with detailed metrics and issues
    """
    score = QualityScore()
    
    # Structure analysis
    _check_structure(content, score)
    
    # Completeness analysis
    _check_completeness(content, score)
    
    # Formatting analysis
    _check_formatting(content, score)
    
    # Citation analysis
    _check_citations(content, source_path, score)
    
    return score


def _check_structure(content: str, score: QualityScore) -> None:
    """Check document structure quality."""
    lines = content.split('\n')
    headings = []
    
    for i, line in enumerate(lines, 1):
        match = HEADING_PATTERN.match(line)
        if match:
            level = len(match.group(1))
            headings.append((i, level, match.group(2)))
    
    if not headings:
        score.structure_score -= 30
        score.issues.append(QualityIssue(
            severity=IssueSeverity.HIGH,
            category="structure",
            message="No headings found in document",
            suggestion="Add at least a title heading (# Title)",
        ))
        return
    
    # Check for title (H1)
    if headings[0][1] != 1:
        score.structure_score -= 10
        score.issues.append(QualityIssue(
            severity=IssueSeverity.MEDIUM,
            category="structure",
            message="Document doesn't start with H1 heading",
            line=headings[0][0],
            suggestion="Start with a single # Title",
        ))
    
    # Check heading hierarchy
    prev_level = 0
    for line_num, level, text in headings:
        if level > prev_level + 1 and prev_level > 0:
            score.structure_score -= 5
            score.issues.append(QualityIssue(
                severity=IssueSeverity.LOW,
                category="structure",
                message=f"Heading level skip: H{prev_level} to H{level}",
                line=line_num,
                suggestion=f"Use H{prev_level + 1} instead of H{level}",
            ))
        prev_level = level


def _check_completeness(content: str, score: QualityScore) -> None:
    """Check content completeness."""
    # Check for placeholders
    placeholders = PLACEHOLDER_PATTERN.findall(content)
    if placeholders:
        score.completeness_score -= 20
        score.issues.append(QualityIssue(
            severity=IssueSeverity.HIGH,
            category="completeness",
            message=f"Retained placeholders: {', '.join(set(placeholders))}",
            suggestion="Replace placeholders with actual content",
        ))
    
    # Check for truncation indicators
    for indicator in TRUNCATION_INDICATORS:
        if indicator in content:
            score.completeness_score -= 30
            score.issues.append(QualityIssue(
                severity=IssueSeverity.CRITICAL,
                category="completeness",
                message=f"Content appears truncated: '{indicator}'",
                suggestion="Process document in smaller chunks",
            ))
            break
    
    # Check for summarized code blocks
    if "# ... (" in content or "// ... (" in content:
        score.completeness_score -= 25
        score.issues.append(QualityIssue(
            severity=IssueSeverity.HIGH,
            category="completeness",
            message="Code blocks appear to be summarized instead of preserved",
            suggestion="Instruct LLM to keep code blocks verbatim",
        ))


def _check_formatting(content: str, score: QualityScore) -> None:
    """Check formatting quality."""
    # Check code block closure
    code_block_count = len(UNCLOSED_CODE_BLOCK.findall(content))
    if code_block_count % 2 != 0:
        score.formatting_score -= 25
        score.issues.append(QualityIssue(
            severity=IssueSeverity.HIGH,
            category="formatting",
            message="Unclosed code block detected",
            suggestion="Ensure all ``` have matching closures",
        ))
    
    # Check for very long lines (might indicate formatting issues)
    for i, line in enumerate(content.split('\n'), 1):
        if len(line) > 500 and not line.startswith('```'):
            score.formatting_score -= 5
            score.issues.append(QualityIssue(
                severity=IssueSeverity.LOW,
                category="formatting",
                message=f"Very long line ({len(line)} chars)",
                line=i,
                suggestion="Break long lines for readability",
            ))
            break  # Only report once


def _check_citations(content: str, source_path: str | None, score: QualityScore) -> None:
    """Check citation quality."""
    citations = CITATION_PATTERN.findall(content)
    
    if not citations:
        score.citation_score -= 50
        score.issues.append(QualityIssue(
            severity=IssueSeverity.MEDIUM,
            category="citation",
            message="No source citations found",
            suggestion="Add [source: path/to/file.md] citation",
        ))
    elif source_path and source_path not in ' '.join(citations):
        score.citation_score -= 25
        score.issues.append(QualityIssue(
            severity=IssueSeverity.LOW,
            category="citation",
            message="Citation doesn't reference original source path",
            suggestion=f"Add citation referencing {source_path}",
        ))

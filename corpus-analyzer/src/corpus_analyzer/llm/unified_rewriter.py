"""Unified document rewriter with enhanced categorization integration."""

import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console

from corpus_analyzer.classifiers.document_type import ClassificationResult
from corpus_analyzer.core.database import CorpusDatabase
from corpus_analyzer.core.models import Document, DocumentCategory
from corpus_analyzer.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

# Constants
MAX_CONTENT_LENGTH = 16000
PLACEHOLDER_PATTERN = re.compile(r'\$[A-Z_]+')
TRUNCATION_INDICATORS = [
    "[truncated]",
    "...",
    "# ... (",
    "// ... (",
    "/* ... */",
]


@dataclass
class RewriteResult:
    """Result of rewriting operation."""

    docs_processed: int
    output_files: list[Path]
    errors: list[str]
    warnings: list[str] = field(default_factory=list)
    quality_scores: dict[str, float] = field(default_factory=dict)


@dataclass
class QualityReport:
    """Quality assessment of rewritten content."""

    has_placeholders: bool = False
    is_truncated: bool = False
    has_frontmatter: bool = False
    has_valid_headings: bool = True
    has_unclosed_code_blocks: bool = False
    issues: list[str] = field(default_factory=list)

    @property
    def score(self) -> float:
        """Calculate quality score (0-100)."""
        score = 100.0
        if self.has_placeholders:
            score -= 20
        if self.is_truncated:
            score -= 30
        if not self.has_frontmatter:
            score -= 10
        if not self.has_valid_headings:
            score -= 15
        if self.has_unclosed_code_blocks:
            score -= 25
        return max(0, score)

    @property
    def grade(self) -> str:
        """Return letter grade."""
        s = self.score
        if s >= 90:
            return "A"
        elif s >= 80:
            return "B"
        elif s >= 70:
            return "C"
        elif s >= 60:
            return "D"
        return "F"


class UnifiedRewriter:
    """Unified rewriter that combines template-based and LLM-based approaches."""

    def __init__(
        self,
        model: str | None = None,
        templates_dir: Path | None = None,
        use_templates: bool = True,
        use_llm_fallback: bool = True
    ) -> None:
        """Initialize the unified rewriter."""
        self.client = OllamaClient(model=model)
        self.templates_dir = templates_dir or Path("templates")
        self.use_templates = use_templates
        self.use_llm_fallback = use_llm_fallback

        # Category-specific system prompts
        self.category_prompts = {
            "howto": """You are a technical documentation expert specializing in how-to guides.
Focus on:
1. Clear step-by-step instructions
2. Practical examples with working code
3. Common pitfalls and troubleshooting
4. Prerequisites and requirements upfront
Keep code blocks verbatim. Add citations in [source: path] format.
Start with YAML frontmatter including title, description, and tags.
Ensure logical heading hierarchy (H1 -> H2 -> H3, do not skip levels).
IMPORTANT: OUTPUT RAW MARKDOWN ONLY. DO NOT WRAP WITH ```markdown.""",

            "reference": """You are a technical documentation expert specializing in API references.
Focus on:
1. Accurate function/method signatures
2. Parameter descriptions and types
3. Return values and exceptions
4. Usage examples for each function
Keep code blocks verbatim. Add citations in [source: path] format.
Start with YAML frontmatter including title, description, and tags.
Ensure logical heading hierarchy (H1 -> H2 -> H3, do not skip levels).
IMPORTANT: OUTPUT RAW MARKDOWN ONLY. DO NOT WRAP WITH ```markdown.""",

            "tutorial": """You are a technical documentation expert specializing in tutorials.
Focus on:
1. Learning progression from simple to complex
2. Explanations of concepts before code
3. Complete working examples
4. Exercises and next steps
Keep code blocks verbatim. Add citations in [source: path] format.
Start with YAML frontmatter including title, description, and tags.
Ensure logical heading hierarchy (H1 -> H2 -> H3, do not skip levels).
IMPORTANT: OUTPUT RAW MARKDOWN ONLY. DO NOT WRAP WITH ```markdown.""",
        }

        self.default_prompt = """You are a technical documentation expert. Your task is to consolidate and rewrite documentation while:

1. Maintaining technical accuracy
2. Following the provided template structure
3. Keeping code blocks verbatim unless explicitly asked to modify
4. Adding citations in the format [source: path/to/file.md#section] for all information
5. Starting with YAML frontmatter including title, description, and tags
6. Do NOT wrap the entire output in a markdown code block (output raw text)
7. Do not use conversational filler before or after the content
8. Refrain from conducting a "plan" or "structure" analysis loop - just output the document.
9. Do not end with a trailing code block marker unless it closes a valid block.
10. Ensure logical heading hierarchy (H1 -> H2 -> H3, do not skip levels).

Be concise but comprehensive. Preserve important details. Do not include these instructions in the output."""

    def _load_template(self, category: DocumentCategory) -> str:
        """Load template for a category."""
        if not self.use_templates:
            return ""

        # Try v1 template first
        filename = f"{category.value}.v1.md"
        template_path = self.templates_dir / filename

        if not template_path.exists():
            # Fallback to standard template
            template_path = self.templates_dir / f"{category.value}.md"

        if template_path.exists():
            return template_path.read_text(encoding="utf-8")

        return ""

    def _preprocess_content(self, content: str) -> str:
        """Pre-process content before sending to LLM."""
        # Replace placeholders with descriptive text
        content = PLACEHOLDER_PATTERN.sub("[user-defined]", content)
        return content

    def _clean_model_output(self, content: str) -> str:
        """Remove wrapping markdown code blocks from LLM response."""
        content = content.strip()
        lines = content.splitlines()

        # Check for opening fence in first 5 lines
        start_idx = -1
        for i in range(min(5, len(lines))):
            if lines[i].strip().startswith("```"):
                start_idx = i
                break

        if start_idx != -1:
            # Check for closing fence at the end
            end_idx = len(lines)
            if lines[-1].strip() == "```":
                end_idx = -1

            candidate_lines = lines[start_idx+1 : end_idx] if end_idx == -1 else lines[start_idx+1:]
            candidate = "\n".join(candidate_lines).strip()

            # Validation: does it look like valid doc content?
            if candidate.startswith("---") or candidate.startswith("#"):
                content = candidate

        return content

    def _ensure_frontmatter(self, content: str, title: str, source_path: str) -> str:
        """Ensure content starts with YAML frontmatter."""
        if content.lstrip().startswith("---"):
            return content

        return f"""---
title: {title}
source: {source_path}
---

{content}"""

    def _validate_output(self, content: str) -> QualityReport:
        """Validate LLM output for quality issues."""
        report = QualityReport()

        # Check for retained placeholders
        if PLACEHOLDER_PATTERN.search(content):
            report.has_placeholders = True
            report.issues.append("Retained placeholder variables ($VAR)")

        # Check for frontmatter
        if content.lstrip().startswith("---"):
            report.has_frontmatter = True
        else:
            report.issues.append("Missing YAML frontmatter")

        # Check for truncation indicators
        for indicator in TRUNCATION_INDICATORS:
            if indicator in content:
                report.is_truncated = True
                report.issues.append(f"Possible truncation: found '{indicator}'")
                break

        # Check heading hierarchy
        lines = content.split("\n")
        prev_level = 0
        for line in lines:
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                if level > prev_level + 1 and prev_level > 0:
                    report.has_valid_headings = False
                    report.issues.append(f"Heading skip: H{prev_level} to H{level}")
                prev_level = level

        # Check for unclosed code blocks
        code_block_count = content.count("```")
        if code_block_count % 2 != 0:
            report.has_unclosed_code_blocks = True
            report.issues.append("Unclosed code block detected")

        return report

    def _build_enhanced_prompt(
        self,
        doc: Document,
        classification: ClassificationResult | None = None,
        template: str = ""
    ) -> tuple[str, str]:
        """Build enhanced prompt using classification data."""

        # System prompt based on category and classification
        system_prompt = self.category_prompts.get(doc.category.value, self.default_prompt)

        # Add classification insights if available
        if classification:
            system_prompt += "\n\n## Classification Insights\n"
            system_prompt += f"- Primary Category: {doc.category.value} (confidence: {classification.confidence:.2f})\n"
            if classification.secondary_category:
                system_prompt += f"- Secondary Category: {classification.secondary_category.value} (confidence: {classification.secondary_confidence:.2f})\n"

            # Add feature-based guidance
            if classification.feature_scores:
                significant_features = {k: v for k, v in classification.feature_scores.items() if abs(v) > 0.1}
                if significant_features:
                    system_prompt += f"- Key Features: {', '.join(f'{k} ({v:.2f})' for k, v in significant_features.items())}\n"

        # Add template if available
        user_prompt = f"""Rewrite the following {doc.category.value} document following best practices for this document type.

## Source Document
Path: {doc.relative_path}
Title: {doc.title}
"""

        if template:
            user_prompt += f"""
## Template Structure
```markdown
{template}
```

Please follow this template structure while rewriting the content.
"""

        user_prompt += f"""
### Content
{self._preprocess_content(doc.path.read_text(encoding="utf-8", errors="replace")[:12000])}

## Instructions
1. Improve structure and clarity
2. Keep all code blocks exactly as-is (verbatim, do not summarize)
3. Add a citation [source: {doc.relative_path}] at the end
4. Ensure all headings follow a logical hierarchy (no skipping levels)
5. Expand any placeholder text like [user-defined] into helpful descriptions
6. Start with YAML frontmatter including title, description, and tags
7. Do NOT wrap the output in a markdown code block (output raw text)
8. Do not repeat these instructions in your response.

Output the rewritten document in markdown format."""

        return system_prompt, user_prompt

    def rewrite_document(
        self,
        doc: Document,
        output_dir: Path,
        classification: ClassificationResult | None = None,
        optimized: bool = False
    ) -> tuple[Path | None, QualityReport, list[str]]:
        """Rewrite a single document using unified approach."""
        errors = []
        warnings = []

        try:
            # Load template if enabled
            template = self._load_template(doc.category) if self.use_templates else ""

            # Build enhanced prompts
            system_prompt, user_prompt = self._build_enhanced_prompt(doc, classification, template)

            # Generate rewrite
            if not self.client.is_available():
                errors.append("Ollama is not available")
                return None, QualityReport(), errors

            rewritten = self.client.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.3,
            )

            # Clean and ensure frontmatter
            rewritten = self._clean_model_output(rewritten)
            rewritten = self._ensure_frontmatter(rewritten, doc.title, doc.relative_path)

            # Validate quality
            quality = self._validate_output(rewritten)

            # Save output
            category_dir = output_dir / doc.category.value
            category_dir.mkdir(parents=True, exist_ok=True)

            output_path = category_dir / f"{doc.path.stem}_rewritten.md"
            output_path.write_text(rewritten, encoding="utf-8")

            # Add quality warnings
            if quality.issues:
                for issue in quality.issues:
                    warnings.append(f"{doc.relative_path}: {issue}")

            if quality.score < 60:
                warnings.append(f"{doc.relative_path}: Low quality score ({quality.grade})")

            return output_path, quality, warnings

        except Exception as e:
            errors.append(f"Error processing {doc.relative_path}: {e}")
            return None, QualityReport(), errors

    def rewrite_category(
        self,
        db: CorpusDatabase,
        category: str,
        output_dir: Path,
        optimized: bool = False,
        max_workers: int = 4,
    ) -> RewriteResult:
        """Rewrite all documents in a category."""
        try:
            doc_category = DocumentCategory(category)
        except ValueError:
            return RewriteResult(
                docs_processed=0,
                output_files=[],
                errors=[f"Unknown category: {category}"],
            )

        # Get documents in category
        docs = list(db.get_documents(category=doc_category))
        if not docs:
            return RewriteResult(
                docs_processed=0,
                output_files=[],
                errors=[f"No documents found in category: {category}"],
            )

        output_files: list[Path] = []
        errors: list[str] = []
        warnings: list[str] = []
        quality_scores: dict[str, float] = {}

        # Initialize progress tracking
        console = Console()
        total_docs = len(docs)

        # Simple progress tracking without rich progress bar to avoid conflicts
        console.print(f"[bold blue]Starting rewrite of {total_docs} {category} documents...[/]")
        start_time = time.time()

        # Process documents with simple progress tracking
        for i, doc in enumerate(docs):
            # Show progress every 10 documents or for the last one
            if (i + 1) % 10 == 0 or (i + 1) == total_docs:
                elapsed = time.time() - start_time
                avg_time = elapsed / (i + 1)
                eta = avg_time * (total_docs - i - 1) if i + 1 < total_docs else 0

                console.print(
                    f"[dim]Progress: {i + 1}/{total_docs} documents ({doc.path.name}), "
                    f"Avg: {avg_time:.1f}s/doc, ETA: {eta:.0f}s remaining[/]"
                )

            # Get enhanced classification if available
            classification = None
            try:
                from corpus_analyzer.classifiers.document_type import (
                    classify_document,
                    read_document_content,
                )
                content = read_document_content(doc.path)
                classification = classify_document(doc, content)
            except Exception as e:
                warnings.append(f"Could not get enhanced classification for {doc.relative_path}: {e}")

            # Rewrite document
            output_path, quality, doc_warnings = self.rewrite_document(
                doc, output_dir, classification, optimized
            )

            if output_path:
                output_files.append(output_path)
                quality_scores[doc.relative_path] = quality.score

            errors.extend(doc_warnings)
            warnings.extend(doc_warnings)

        return RewriteResult(
            docs_processed=len(output_files),
            output_files=output_files,
            errors=errors,
            warnings=warnings,
            quality_scores=quality_scores,
        )

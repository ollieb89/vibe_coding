"""LLM-assisted document rewriting and consolidation."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

from corpus_analyzer.core.database import CorpusDatabase
from corpus_analyzer.core.models import DocumentCategory
from corpus_analyzer.llm.ollama_client import OllamaClient


# Constants
MAX_CONTENT_LENGTH = 16000  # Increased for Mistral's 32K context
PLACEHOLDER_PATTERN = re.compile(r'\$[A-Z_]+')
# Pattern to detect echoed instructions at the end of the file
INSTRUCTION_ECHO_PATTERN = re.compile(r'## Instructions.*$', re.DOTALL | re.IGNORECASE)

TRUNCATION_INDICATORS = [
    "[truncated]",
    "...",
    "# ... (",
    "// ... (",
    "/* ... */",
]


class RewriteResult(NamedTuple):
    """Result of rewriting operation."""

    docs_processed: int
    output_files: list[Path]
    errors: list[str]
    warnings: list[str] = []


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


def preprocess_content(content: str) -> str:
    """Pre-process content before sending to LLM."""
    # Replace placeholders with descriptive text
    content = PLACEHOLDER_PATTERN.sub("[user-defined]", content)
    return content


def ensure_frontmatter(content: str, title: str, source_path: str) -> str:
    """Ensure content starts with YAML frontmatter."""
    if content.lstrip().startswith("---"):
        return content
    
    return f"""---
title: {title}
source: {source_path}
---

{content}"""


def clean_model_output(content: str) -> str:
    """Remove wrapping markdown code blocks from LLM response."""
    content = content.strip()
    # Debug prints removed
    
    lines = content.splitlines()
    
    # Check for opening fence in first 5 lines (handling optional preamble)
    start_idx = -1
    for i in range(min(5, len(lines))):
        if lines[i].strip().startswith("```"):
            start_idx = i
            break
            
    if start_idx != -1:
        # We found an opening fence. Check if it looks like a document wrapper.
        
        # Check for closing fence at the end
        end_idx = len(lines)
        if lines[-1].strip() == "```":
            end_idx = -1
            
        candidate_lines = lines[start_idx+1 : end_idx] if end_idx == -1 else lines[start_idx+1:]
        candidate = "\n".join(candidate_lines).strip()
        
        # Validation: does it look like valid doc content?
        if candidate.startswith("---") or candidate.startswith("#"):
            content = candidate

    # Second pass: Check for echoed instructions at the end
    # Mistral sometimes repeats the prompt's instructions at the end of the file
    content = INSTRUCTION_ECHO_PATTERN.sub("", content).strip()
    
    # Check for trailing code block markers that might be left over
    if content.endswith("```"):
        content = content[:-3].strip()

    return content


def validate_output(content: str) -> QualityReport:
    """Post-validate LLM output for quality issues."""
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


# Category-specific system prompts
CATEGORY_PROMPTS = {
    "howto": """You are a technical documentation expert specializing in how-to guides.
Focus on:
1. Clear step-by-step instructions
2. Practical examples with working code
3. Common pitfalls and troubleshooting
4. Prerequisites and requirements upfront
Keep code blocks verbatim. Add citations in [source: path] format.
Start with YAML frontmatter including title, description, and tags.
IMPORTANT: OUTPUT RAW MARKDOWN ONLY. DO NOT WRAP WITH ```markdown.""",

    "reference": """You are a technical documentation expert specializing in API references.
Focus on:
1. Accurate function/method signatures
2. Parameter descriptions and types
3. Return values and exceptions
4. Usage examples for each function
Keep code blocks verbatim. Add citations in [source: path] format.
Start with YAML frontmatter including title, description, and tags.
IMPORTANT: OUTPUT RAW MARKDOWN ONLY. DO NOT WRAP WITH ```markdown.""",

    "tutorial": """You are a technical documentation expert specializing in tutorials.
Focus on:
1. Learning progression from simple to complex
2. Explanations of concepts before code
3. Complete working examples
4. Exercises and next steps
Keep code blocks verbatim. Add citations in [source: path] format.
Start with YAML frontmatter including title, description, and tags.
IMPORTANT: OUTPUT RAW MARKDOWN ONLY. DO NOT WRAP WITH ```markdown.""",
}

DEFAULT_SYSTEM_PROMPT = """You are a technical documentation expert. Your task is to consolidate and rewrite documentation while:

1. Maintaining technical accuracy
2. Following the provided template structure
3. Keeping code blocks verbatim unless explicitly asked to modify
4. Adding citations in the format [source: path/to/file.md#section] for all information
5. Starting with YAML frontmatter including title, description, and tags
6. Do NOT wrap the entire output in a markdown code block (output raw text)
7. Do not use conversational filler before or after the content
8. Refrain from conducting a "plan" or "structure" analysis loop - just output the document.
9. Do not end with a trailing code block marker unless it closes a valid block.

Be concise but comprehensive. Preserve important details. Do not include these instructions in the output.""",


def rewrite_category(
    db: CorpusDatabase,
    category: str,
    model: str,
    output_dir: Path,
    optimized: bool = False,
) -> RewriteResult:
    """Rewrite/consolidate documents in a category using LLM."""
    try:
        doc_category = DocumentCategory(category)
    except ValueError:
        return RewriteResult(
            docs_processed=0,
            output_files=[],
            errors=[f"Unknown category: {category}"],
        )

    client = OllamaClient(model=model)

    if not client.is_available():
        return RewriteResult(
            docs_processed=0,
            output_files=[],
            errors=["Ollama is not available. Make sure it's running."],
        )

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
    
    # Select category-specific prompt
    system_prompt = CATEGORY_PROMPTS.get(category, DEFAULT_SYSTEM_PROMPT)
    # Add negative constraints to system prompt
    system_prompt += "\n\nNEVER use '...' or '[truncated]' to summarize code or text. Write everything out in full."

    # Use AdvancedRewriter if optimized
    from corpus_analyzer.generators.advanced_rewriter import AdvancedRewriter
    adv_rewriter = AdvancedRewriter(model=model)
    # Give the client a db reference so AdvancedRewriter can find gold docs
    adv_rewriter.client.db = db

    for doc in docs:
        try:
            # Read source content
            if doc.path.exists():
                content = doc.path.read_text(encoding="utf-8", errors="replace")
            else:
                errors.append(f"File not found: {doc.path}")
                continue

            # Pre-process: filter placeholders
            content = preprocess_content(content)
            
            # Check if content needs chunking
            if len(content) > MAX_CONTENT_LENGTH:
                from corpus_analyzer.llm.chunked_processor import split_on_headings, merge_chunks
                
                warnings.append(f"Chunking large document: {doc.relative_path} ({len(content)} chars)")
                chunks = split_on_headings(content, max_chunk_size=MAX_CONTENT_LENGTH)
                rewritten_chunks = []
                
                for i, chunk in enumerate(chunks):
                    chunk_prompt = f"""Rewrite this section (Part {i+1}/{len(chunks)}) of the {category} document '{doc.title}'.
Follow best practices and the original structure.

### Section Content
{chunk.content}

## Instructions
1. Improve structure and clarity
2. Keep all code blocks exactly as-is (verbatim)
3. Maintain heading hierarchy (Current section level: {chunk.level})
4. Expand placeholders
"""
                    rewritten_chunk = client.generate(
                        prompt=chunk_prompt,
                        system=system_prompt,
                        temperature=0.3,
                    )
                    rewritten_chunk = clean_model_output(rewritten_chunk)
                    rewritten_chunks.append(rewritten_chunk)
                
                rewritten = merge_chunks(rewritten_chunks)
                # Ensure frontmatter is present after merging
                rewritten = ensure_frontmatter(rewritten, doc.title, doc.relative_path)
                
            else:
                # Standard processing for normal sized docs
                prompt = f"""Rewrite the following {category} document following best practices for this document type.

## Source Document
Path: {doc.relative_path}
Title: {doc.title}

### Content
{content}

## Instructions
1. Improve structure and clarity
2. Keep all code blocks exactly as-is (verbatim, do not summarize)
3. Add a citation [source: {doc.relative_path}] at the end
4. Ensure all headings follow a logical hierarchy (no skipping levels)
5. Expand any placeholder text like [user-defined] into helpful descriptions
6. Start with YAML frontmatter including title, description, and tags
6. Start with YAML frontmatter including title, description, and tags
7. Do NOT wrap the output in a markdown code block (output raw text)
8. Do not repeat these instructions in your response.

Output the rewritten document in markdown format."""

                # Generate rewrite
                if optimized:
                    res = adv_rewriter.rewrite_document(doc, output_dir, optimized=True)
                    if res.success:
                        rewritten = output_dir / f"{doc.path.stem}.rewritten.md" # Placeholder, actual path in res
                        # The AdvancedRewriter already writes the file, so we skip standard save
                        output_files.append(res.output_path)
                        continue
                    else:
                        errors.append(f"Advanced rewrite failed for {doc.path}: {res.error}")
                        continue
                
                rewritten = client.generate(
                    prompt=prompt,
                    system=system_prompt,
                    temperature=0.3,
                )
                
                # Clean and ensure frontmatter
                rewritten = clean_model_output(rewritten)
                rewritten = ensure_frontmatter(rewritten, doc.title, doc.relative_path)

            # Post-validate output
            quality = validate_output(rewritten)
            if quality.issues:
                for issue in quality.issues:
                    warnings.append(f"{doc.relative_path}: {issue}")
            
            if quality.score < 60:
                warnings.append(f"{doc.relative_path}: Low quality score ({quality.grade})")

            # Save output
            output_path = output_dir / f"{doc.path.stem}_rewritten.md"
            output_path.write_text(rewritten)
            output_files.append(output_path)

        except Exception as e:
            errors.append(f"Error processing {doc.relative_path}: {e}")

    return RewriteResult(
        docs_processed=len(output_files),
        output_files=output_files,
        errors=errors,
        warnings=warnings,
    )


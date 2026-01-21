"""Advanced rewriter for Phase 5 pipeline."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from corpus_analyzer.core.models import Document, DocumentCategory
from corpus_analyzer.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

@dataclass
class RewriteResult:
    """Result of a rewrite operation."""
    success: bool
    output_path: Path | None = None
    sources_path: Path | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

class AdvancedRewriter:
    """Rewriter that uses v1 templates and tracks provenance."""

    def __init__(self, model: str | None = None, templates_dir: Path | None = None) -> None:
        """Initialize rewriter."""
        self.client = OllamaClient(model=model)
        self.templates_dir = templates_dir or Path("templates")
        
    def _load_template(self, category: DocumentCategory) -> str:
        """Load the v1 template for a category."""
        # Map category to filename
        # e.g. howto -> howto.v1.md
        filename = f"{category.value}.v1.md"
        template_path = self.templates_dir / filename
        
        if not template_path.exists():
            # Fallback to .md if .v1.md doesn't exist (during transition)
            template_path = self.templates_dir / f"{category.value}.md"
            
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found for category: {category} at {template_path}")
            
        return template_path.read_text(encoding="utf-8")

    def rewrite_document(
        self, 
        doc: Document, 
        output_dir: Path,
        dry_run: bool = False,
        optimized: bool = False
    ) -> RewriteResult:
        """Rewrite a single document using its category template."""
        try:
            # 1. Load Template
            if not doc.category:
                return RewriteResult(success=False, error="Document has no category")
                
            try:
                template_content = self._load_template(doc.category)
            except FileNotFoundError as e:
                return RewriteResult(success=False, error=str(e))

            # 2. Prepare Output Paths
            category_dir = output_dir / doc.category.value
            category_dir.mkdir(parents=True, exist_ok=True)
            
            stem = Path(doc.path).stem
            output_md_path = category_dir / f"{stem}.rewritten.md"
            output_json_path = category_dir / f"{stem}.sources.json"
            
            # 2.5. Fetch Gold Standard Patterns (if optimized)
            exemplary_patterns = ""
            if optimized:
                # Try to find a gold standard doc for the same category and first domain tag
                tag = doc.domain_tags[0] if doc.domain_tags else None
                gold_docs = list(self.client.db.get_gold_standard_documents(category=doc.category, tag=tag)) if hasattr(self.client, 'db') else []
                
                # If no db on client, we might need a different way to get gold docs
                # For now, let's assume AdvancedRewriter might need the db
                if gold_docs:
                    exemplary_patterns = "\n# Exemplary Patterns (Gold Standard)\n"
                    for g_doc in gold_docs[:2]: # Use up to 2 examples
                        exemplary_patterns += f"## Pattern from: {g_doc.path.name}\n"
                        # Extract first 3k chars as pattern
                        exemplary_patterns += g_doc.path.read_text(encoding='utf-8', errors='replace')[:3000]
                        exemplary_patterns += "\n---\n"
            
            # 3. Construct Prompt
            # We want to inject the template and the source content.
            system_prompt = (
                "You are an expert technical writer specializing in creating strict, structured documentation agent instructions. "
                "Your task is to rewrite the provided source content into the exact structure defined by the Template.\n"
                "\n"
                "Constraints:\n"
                "1. STRICTLY follow the Template structure. Do not add sections not in the template.\n"
                "2. Preserve all code blocks exactly as they appear in the source.\n"
                "3. If information for a required section is missing, mark it as [MISSING INFO].\n"
                "4. Identify the source file path in the output metadata.\n"
                "5. Ensure the operational logic (if any) is preserved."
            )
            
            if optimized:
                system_prompt += (
                    "\nOPTIMIZATION MODE ENABLED:\n"
                    "In addition to following the Template, analyze the # Exemplary Patterns provided. "
                    "Extract the best technical writing styles, structure nuances, and clarity patterns "
                    "from the Exemplary Patterns and apply them to the rewritten content. "
                    "The goal is to produce the 'best' possible version of this document."
                )
            
            user_prompt = f"""
# Template to Follow
```markdown
{template_content}
```

# Source Content
(Path: {doc.path})
```markdown
{doc.path.read_text(encoding="utf-8", errors="replace")[:12000]} 
```
(Note: Source content truncated at 12k chars for safety)

{exemplary_patterns}

Please rewrite the Source Content to match the Template.
"""

            # 4. Generate
            if dry_run:
                # In dry run, we skip the expensive/fragile LLM call
                logger.info(f"Dry run enabled for {doc.title} - skipping LLM generation")
                rewritten_content = f"""# [DRY RUN PLACEHOLDER] {doc.title}

*   **Category**: {doc.category.value}
*   **Source Path**: {doc.path}
*   **Template Used**: {doc.category.value}.v1.md

## Mock Content
(This content is a placeholder. In a real run, the LLM would generate text here based on the template.)
"""
            elif not self.client.is_available():
                # Factor in availability check
                return RewriteResult(success=False, error="Ollama not available")
            else:
                rewritten_content = self.client.generate(
                    prompt=user_prompt,
                    system=system_prompt,
                    temperature=0.2 # Low temp for adherence
                )

            # 5. Write Output
            output_md_path.write_text(rewritten_content, encoding="utf-8")

            # 6. Write Provenance
            provenance = {
                "source_document_id": doc.id,
                "source_path": str(doc.path),
                "category": doc.category.value,
                "template_used": str(self.templates_dir / f"{doc.category.value}.v1.md"),
                "llm_model": self.client.model,
                "generated_at": "timestamp_here" # TODO: Add timestamp
            }
            output_json_path.write_text(json.dumps(provenance, indent=2), encoding="utf-8")
            
            return RewriteResult(
                success=True,
                output_path=output_md_path,
                sources_path=output_json_path,
                metadata=provenance
            )

        except Exception as e:
            logger.exception(f"Failed to rewrite document {doc.path}")
            return RewriteResult(success=False, error=str(e))

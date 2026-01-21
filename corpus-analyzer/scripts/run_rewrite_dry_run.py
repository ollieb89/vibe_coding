#!/usr/bin/env python3
"""Run a dry run of the automated rewrite pipeline."""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from corpus_analyzer.config import settings
from corpus_analyzer.core.database import CorpusDatabase
from corpus_analyzer.core.models import DocumentCategory
from corpus_analyzer.generators.advanced_rewriter import AdvancedRewriter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Execute dry run."""
    db_path = Path("corpus.sqlite")
    if not db_path.exists():
        logger.error(f"Database not found at {db_path}")
        sys.exit(1)

    db = CorpusDatabase(str(db_path))
    rewriter = AdvancedRewriter(
        templates_dir=Path("./templates")
    )
    
    # Define output directory
    dry_run_dir = Path("rewrites/dry-run")
    dry_run_dir.mkdir(parents=True, exist_ok=True)
    
    # Categories to test
    categories = [
        DocumentCategory.HOWTO,
        DocumentCategory.RUNBOOK,
        DocumentCategory.PERSONA,
        DocumentCategory.REFERENCE,
        DocumentCategory.TUTORIAL,
        DocumentCategory.SPEC
    ]
    
    total_processed = 0
    total_errors = 0
    
    print(f"Starting Dry Run to {dry_run_dir}...\n")
    
    for category in categories:
        # Get one sample
        # Get documents and slice manually since get_documents doesn't support limit
        all_docs = list(db.get_documents(category=category))
        docs = all_docs[:1] if all_docs else []
        
        if not docs:
            logger.warning(f"No documents found for category: {category}")
            continue
            
        doc = docs[0]
        print(f"Processing Category: {category.value} -> Doc: {doc.title} ({doc.path})")
        
        result = rewriter.rewrite_document(
            doc=doc,
            output_dir=dry_run_dir,
            dry_run=True # Force dry run to verify pipeline mechanics first
        )
        
        if result.success:
            print(f"  ✅ Generated: {result.output_path}")
            print(f"  ✅ Provenance: {result.sources_path}")
            total_processed += 1
        else:
            print(f"  ❌ Error: {result.error}")
            total_errors += 1
            
    print(f"\nDry Run Complete. Processed: {total_processed}, Errors: {total_errors}")

if __name__ == "__main__":
    main()

"""Sample extraction logic."""

import shutil
from pathlib import Path
from typing import Optional

from rich.console import Console

from corpus_analyzer.core.database import CorpusDatabase
from corpus_analyzer.core.models import DocumentCategory

console = Console()

def extract_samples(
    db: CorpusDatabase, 
    output_dir: Path, 
    samples_per_category: int = 2
) -> int:
    """Extract representative samples for each category to output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    categories = db.get_categories()
    
    total_copied = 0
    for cat_str in categories:
        try:
            category = DocumentCategory(cat_str)
        except ValueError:
            continue

        # Get documents for this category
        docs = list(db.get_documents(category=category))
        if not docs:
            continue

        # Sort by confidence
        docs.sort(key=lambda d: d.category_confidence, reverse=True)
        
        # Take samples
        samples = docs[:samples_per_category]
        
        for i, doc in enumerate(samples):
            suffix = f"_{i+1}" if len(samples) > 1 else ""
            dest_name = f"{cat_str}{suffix}{doc.path.suffix}"
            dest_path = output_dir / dest_name
            
            if doc.path.exists():
                shutil.copy2(doc.path, dest_path)
                total_copied += 1
                
    return total_copied

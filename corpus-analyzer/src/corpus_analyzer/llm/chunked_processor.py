"""Chunked processing for large documents."""

import re
from dataclasses import dataclass
from pathlib import Path


# Heading pattern for splitting
HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)


@dataclass
class DocumentChunk:
    """A chunk of document content."""
    
    content: str
    heading: str | None = None
    level: int = 0
    start_line: int = 0
    end_line: int = 0
    
    @property
    def char_count(self) -> int:
        return len(self.content)


def split_on_headings(content: str, max_chunk_size: int = 8000) -> list[DocumentChunk]:
    """Split document into chunks on heading boundaries.
    
    Args:
        content: Full document content
        max_chunk_size: Maximum characters per chunk
        
    Returns:
        List of DocumentChunk objects
    """
    lines = content.split('\n')
    chunks: list[DocumentChunk] = []
    current_chunk_lines: list[str] = []
    current_heading: str | None = None
    current_level: int = 0
    start_line: int = 0
    
    def finalize_chunk():
        nonlocal current_chunk_lines, current_heading, start_line
        if current_chunk_lines:
            chunk_content = '\n'.join(current_chunk_lines)
            chunks.append(DocumentChunk(
                content=chunk_content,
                heading=current_heading,
                level=current_level,
                start_line=start_line,
                end_line=start_line + len(current_chunk_lines) - 1,
            ))
            current_chunk_lines = []
    
    for i, line in enumerate(lines):
        heading_match = HEADING_PATTERN.match(line)
        
        if heading_match:
            # Check if adding this section would exceed max size
            current_size = sum(len(l) for l in current_chunk_lines)
            
            # If current chunk is big enough, finalize it
            if current_size > max_chunk_size // 2:
                finalize_chunk()
                start_line = i
            
            # Start new heading context
            if not current_chunk_lines:
                current_heading = heading_match.group(2)
                current_level = len(heading_match.group(1))
                start_line = i
        
        current_chunk_lines.append(line)
        
        # Force split if chunk gets too large
        current_size = sum(len(l) for l in current_chunk_lines)
        if current_size > max_chunk_size:
            finalize_chunk()
            start_line = i + 1
    
    # Finalize remaining content
    finalize_chunk()
    
    return chunks


def merge_chunks(chunks: list[str], deduplicate_headings: bool = True) -> str:
    """Merge processed chunks back together.
    
    Args:
        chunks: List of processed chunk contents
        deduplicate_headings: Remove duplicate consecutive headings
        
    Returns:
        Merged document content
    """
    if not chunks:
        return ""
    
    merged = chunks[0]
    
    for chunk in chunks[1:]:
        # Add separator if needed
        if not merged.endswith('\n\n'):
            merged += '\n\n'
        
        if deduplicate_headings:
            # Check if chunk starts with same heading as merged ends with
            merged_lines = merged.strip().split('\n')
            chunk_lines = chunk.strip().split('\n')
            
            if merged_lines and chunk_lines:
                last_heading = None
                for line in reversed(merged_lines[-5:]):
                    if line.startswith('#'):
                        last_heading = line
                        break
                
                first_heading = None
                for line in chunk_lines[:3]:
                    if line.startswith('#'):
                        first_heading = line
                        break
                
                if last_heading and first_heading and last_heading == first_heading:
                    # Skip duplicate heading in chunk
                    chunk_lines = chunk_lines[chunk_lines.index(first_heading) + 1:]
                    chunk = '\n'.join(chunk_lines)
        
        merged += chunk
    
    return merged


def estimate_chunks_needed(content: str, max_chunk_size: int = 16000) -> int:
    """Estimate how many chunks will be needed for content.
    
    Args:
        content: Document content
        max_chunk_size: Maximum characters per chunk
        
    Returns:
        Estimated number of chunks
    """
    if len(content) <= max_chunk_size:
        return 1
    
    # Account for some overhead from splitting on headings
    return (len(content) // max_chunk_size) + 1

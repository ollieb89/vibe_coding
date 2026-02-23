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
    """Split document into chunks on logical boundaries (headings, code blocks).
    
    Args:
        content: Full document content
        max_chunk_size: Maximum characters per chunk
        
    Returns:
        List of DocumentChunk objects
    """
    lines = content.split('\n')
    
    # Validation: empty content
    if not content.strip():
        return [DocumentChunk(content="", start_line=0, end_line=0)]

    # Step 1: Group lines into "Atomic Blocks"
    # Atoms: Heading, CodeFence+Content, Paragraph
    @dataclass
    class Atom:
        lines: list[str]
        heading: str | None
        level: int
        is_code: bool
        start_idx: int

    atoms: list[Atom] = []
    current_lines: list[str] = []
    current_heading: str | None = None
    current_level: int = 0
    in_code_block: bool = False
    atom_start_idx: int = 0
    
    def finalize_atom(force_heading=None, force_level=0, is_code_atom=False):
        nonlocal current_lines, current_heading, current_level, atom_start_idx
        if current_lines:
            # Use specific heading for this atom if provided (e.g. the heading line itself)
            # otherwise use the context heading
            h = force_heading if force_heading else current_heading
            l = force_level if force_level else current_level
            
            atoms.append(Atom(
                lines=current_lines,
                heading=h,
                level=l,
                is_code=is_code_atom,
                start_idx=atom_start_idx
            ))
            atom_start_idx += len(current_lines)
            current_lines = []

    for i, line in enumerate(lines):
        # Check for Code Block Toggle
        if line.lstrip().startswith("```"):
            if not in_code_block:
                # Starting a code block. 
                # Finalize previous text as an atom.
                finalize_atom()
                in_code_block = True
                current_lines.append(line)
            else:
                # Ending a code block.
                current_lines.append(line)
                in_code_block = False
                finalize_atom(is_code_atom=True)
            continue
        
        if in_code_block:
            current_lines.append(line)
            continue

        # Check for Heading
        heading_match = HEADING_PATTERN.match(line)
        if heading_match:
            # Finalize previous paragraph
            finalize_atom()
            
            # Update context
            current_heading = heading_match.group(2)
            current_level = len(heading_match.group(1))
            
            # Add heading as its own atom (or start of next)? 
            # Better to keep heading separate so we can split BEFORE it easily.
            current_lines = [line]
            finalize_atom(force_heading=current_heading, force_level=current_level)
            continue
            
        # Normal text
        current_lines.append(line)
        
        # Split paragraph on double newlines? 
        # For now, let's just respect headings and code blocks strictness, 
        # and maybe only split text if we want granular paragraphs.
        # But `current_lines` might get huge.
        # Let's split atoms on blank lines too?
        if not line.strip() and current_lines:
             finalize_atom()

    # Finalize last bits
    finalize_atom(is_code_atom=in_code_block) # If unclosed, treat as code?

    # Step 2: Merge Atoms into Chunks
    chunks: list[DocumentChunk] = []
    current_chunk_atoms: list[Atom] = []
    current_chunk_size = 0
    
    def get_chunk_text(atoms_list):
        return "\n".join(chain_lines(atoms_list))
        
    def chain_lines(atoms_list):
        res = []
        for a in atoms_list:
            res.extend(a.lines)
        return res

    for atom in atoms:
        atom_size = sum(len(l) for l in atom.lines)
        
        # Heuristic: If adding this atom exceeds max size...
        if current_chunk_atoms and (current_chunk_size + atom_size > max_chunk_size):
            # ... and the current chunk is at least non-trivial (say > 10% of max or just > 0)
            # Finalize current chunk
            
             # Create chunk object
            first_atom = current_chunk_atoms[0]
            last_atom = current_chunk_atoms[-1]
            chunk_content = get_chunk_text(current_chunk_atoms)
            
            chunks.append(DocumentChunk(
                content=chunk_content,
                heading=first_atom.heading, # Or header of the chunk context
                level=first_atom.level,
                start_line=first_atom.start_idx,
                end_line=last_atom.start_idx + len(last_atom.lines)
            ))
            
            current_chunk_atoms = []
            current_chunk_size = 0
        
        # If single atom is HUGE (> max_chunk_size), we accept it as an oversized chunk 
        # (to avoid breaking code blocks) OR we force split it.
        # Requirement says "Chunking logic to split semantically". 
        # Breaking code block is bad semantics. So we accept oversized.
        
        current_chunk_atoms.append(atom)
        current_chunk_size += atom_size

    # Finalize last chunk
    if current_chunk_atoms:
        first_atom = current_chunk_atoms[0]
        last_atom = current_chunk_atoms[-1]
        chunks.append(DocumentChunk(
            content=get_chunk_text(current_chunk_atoms),
            heading=first_atom.heading,
            level=first_atom.level,
            start_line=first_atom.start_idx,
            end_line=last_atom.start_idx + len(last_atom.lines)
        ))

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

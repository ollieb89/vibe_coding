"""Document chunking functions for corpus-analyzer.

This module provides functions to split various document types into chunks
with text content and line ranges.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any


def chunk_lines(path: Path, window: int = 50, overlap: int = 10) -> list[dict[str, Any]]:
    """Split a file into overlapping line windows.

    Args:
        path: Path to the file to chunk.
        window: Number of lines per chunk.
        overlap: Number of lines to overlap between chunks.

    Returns:
        List of chunks with "text", "start_line", and "end_line" keys.
    """
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        return []

    # Remove trailing newline from last line for cleaner text
    if lines and lines[-1].endswith("\n"):
        lines[-1] = lines[-1][:-1]

    chunks = []
    step = window - overlap
    total_lines = len(lines)

    start = 0
    while start < total_lines:
        end = min(start + window, total_lines)
        chunk_lines_subset = lines[start:end]
        chunk_text = "".join(chunk_lines_subset).rstrip("\n")

        chunks.append({
            "text": chunk_text,
            "start_line": start + 1,  # 1-indexed
            "end_line": end,  # 1-indexed, inclusive
        })

        if end >= total_lines:
            break
        start += step

    return chunks


def chunk_markdown(path: Path, max_words: int = 512) -> list[dict[str, Any]]:
    """Split a markdown file on ATX headings.

    Args:
        path: Path to the markdown file.
        max_words: Maximum words per chunk. Large sections are sub-split.

    Returns:
        List of chunks with "text", "start_line", and "end_line" keys.
    """
    with open(path, encoding="utf-8") as f:
        content = f.read()
        lines = content.split("\n")

    if not lines:
        return []

    # Find heading lines (ATX headings: ^#{1,6}\s)
    heading_pattern = re.compile(r"^#{1,6}\s")
    heading_indices = []
    for i, line in enumerate(lines):
        if heading_pattern.match(line):
            heading_indices.append(i)

    # If no headings, return single chunk
    if not heading_indices:
        return [{
            "text": content,
            "start_line": 1,
            "end_line": len(lines),
        }]

    # Split into heading sections
    chunks = []

    for i, heading_idx in enumerate(heading_indices):
        # Start from heading line
        start_idx = heading_idx

        # End at line before next heading (or end of file)
        end_idx = heading_indices[i + 1] if i + 1 < len(heading_indices) else len(lines)

        section_lines = lines[start_idx:end_idx]
        section_text = "\n".join(section_lines).strip()

        if not section_text:
            continue

        # For markdown, include blank lines that precede next heading
        # Find the last line that has content OR is a blank line before next section
        actual_end_line = start_idx + len(section_lines)
        # Strip only trailing blank lines at end of file (not between sections)
        if i + 1 < len(heading_indices):
            # Not the last section - include blanks up to next heading
            actual_end_line = heading_indices[i + 1] - 1  # Line before next heading
        else:
            # Last section - strip trailing blanks
            while actual_end_line > start_idx and not lines[actual_end_line - 1].strip():
                actual_end_line -= 1

        word_count = len(section_text.split())

        if word_count > max_words:
            # Sub-split large sections using chunk_lines approach
            section_chunks = _subsplit_section(
                section_lines, start_idx + 1, window=50, overlap=10
            )
            chunks.extend(section_chunks)
        else:
            chunks.append({
                "text": section_text,
                "start_line": start_idx + 1,  # 1-indexed
                "end_line": actual_end_line + 1,  # Convert to 1-indexed
            })

    # Handle content before first heading (preamble)
    if heading_indices[0] > 0:
        preamble_lines = lines[0:heading_indices[0]]
        preamble_text = "\n".join(preamble_lines).strip()
        if preamble_text and chunks:
            chunks.insert(0, {
                "text": preamble_text + "\n\n" + chunks[0]["text"],
                "start_line": 1,
                "end_line": chunks[0]["end_line"],
            })
            # Remove the original first chunk since merged into preamble
            chunks.pop(1)

    return chunks


def _subsplit_section(
    lines: list[str], start_line_offset: int, window: int = 50, overlap: int = 10
) -> list[dict[str, Any]]:
    """Sub-split a large section into overlapping chunks.

    Args:
        lines: Lines of the section to split.
        start_line_offset: Starting line number (1-indexed) in the original file.
        window: Number of lines per chunk.
        overlap: Number of lines to overlap.

    Returns:
        List of sub-chunks.
    """
    chunks = []
    step = window - overlap
    total_lines = len(lines)

    start = 0
    while start < total_lines:
        end = min(start + window, total_lines)
        chunk_lines_subset = lines[start:end]
        chunk_text = "\n".join(chunk_lines_subset).strip()

        if chunk_text:
            chunks.append({
                "text": chunk_text,
                "start_line": start_line_offset + start,
                "end_line": start_line_offset + end - 1,
            })

        if end >= total_lines:
            break
        start += step

    return chunks


def chunk_python(path: Path) -> list[dict[str, Any]]:
    """Split a Python file into chunks by top-level definitions.

    Args:
        path: Path to the Python file.

    Returns:
        List of chunks with "text", "start_line", and "end_line" keys.
        Falls back to chunk_lines if no top-level definitions found.
    """
    with open(path, encoding="utf-8") as f:
        source = f.read()
        lines = source.split("\n")

    if not source.strip():
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Fall back to line-based chunking on parse error
        return chunk_lines(path)

    # Get top-level function/class definitions
    top_level_nodes = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            top_level_nodes.append(node)

    # If no top-level defs, fall back to chunk_lines
    if not top_level_nodes:
        return chunk_lines(path)

    chunks = []
    for i, node in enumerate(top_level_nodes):
        start_line = node.lineno

        # Determine end line (one line before next node starts)
        end_line = (
            top_level_nodes[i + 1].lineno - 1
            if i + 1 < len(top_level_nodes)
            else len(lines)
        )

        # Extract the chunk text
        chunk_lines_subset = lines[start_line - 1:end_line]
        chunk_text = "\n".join(chunk_lines_subset).rstrip()

        # For Python, stop at last non-blank line before next definition
        # Walk back from next_node.lineno to find last content line
        actual_end_line = end_line
        while actual_end_line > start_line and not lines[actual_end_line - 1].strip():
            actual_end_line -= 1

        if chunk_text:
            chunks.append({
                "text": chunk_text,
                "start_line": start_line,
                "end_line": actual_end_line,
            })

    return chunks


def chunk_file(path: Path) -> list[dict[str, Any]]:
    """Dispatch chunking based on file extension.

    Args:
        path: Path to the file to chunk.

    Returns:
        List of chunks with "text", "start_line", and "end_line" keys.

    Raises:
        ValueError: If file extension is not supported.
    """
    ext = path.suffix.lower()

    if ext == ".md":
        return chunk_markdown(path)
    elif ext == ".py":
        return chunk_python(path)
    elif ext in (".ts", ".js", ".json", ".yaml", ".yml", ".txt", ".toml"):
        return chunk_lines(path)
    else:
        # Default to line-based chunking for unknown types
        return chunk_lines(path)

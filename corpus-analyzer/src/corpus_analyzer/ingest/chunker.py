"""Document chunking functions for corpus-analyzer.

This module provides functions to split various document types into chunks
with text content and line ranges.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any


def chunk_lines(path: Path, window: int = 20, overlap: int = 5) -> list[dict[str, Any]]:
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

        chunks.append(
            {
                "text": chunk_text,
                "start_line": start + 1,  # 1-indexed
                "end_line": end,  # 1-indexed, inclusive
            }
        )

        if end >= total_lines:
            break
        start += step

    return chunks


def chunk_markdown(path: Path, max_words: int = 200) -> list[dict[str, Any]]:
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
        return [
            {
                "text": content,
                "start_line": 1,
                "end_line": len(lines),
                "chunk_name": "",
                "chunk_text": content,
            }
        ]

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

        heading_line = lines[start_idx]
        if word_count > max_words:
            # Sub-split large sections using chunk_lines approach
            section_chunks = _subsplit_section(section_lines, start_idx + 1, window=20, overlap=5)
            chunks.extend(section_chunks)
        else:
            chunks.append(
                {
                    "text": section_text,
                    "start_line": start_idx + 1,  # 1-indexed
                    "end_line": actual_end_line,  # Already 1-indexed from calculation above
                    "chunk_name": heading_line,
                    "chunk_text": section_text,
                }
            )

    # Handle content before first heading (preamble)
    if heading_indices[0] > 0:
        preamble_lines = lines[0 : heading_indices[0]]
        preamble_text = "\n".join(preamble_lines).strip()
        if preamble_text and chunks:
            merged_text = preamble_text + "\n\n" + chunks[0]["text"]
            chunks.insert(
                0,
                {
                    "text": merged_text,
                    "start_line": 1,
                    "end_line": chunks[0]["end_line"],
                    "chunk_name": chunks[0].get("chunk_name", ""),
                    "chunk_text": merged_text,
                },
            )
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
            chunks.append(
                {
                    "text": chunk_text,
                    "start_line": start_line_offset + start,
                    "end_line": start_line_offset + end - 1,
                }
            )

        if end >= total_lines:
            break
        start += step

    return chunks


def _chunk_class(node: ast.ClassDef, lines: list[str]) -> list[dict[str, Any]]:
    """Extract the header chunk from a ClassDef AST node.

    The header chunk covers the class contract: decorators, class signature,
    class-level attributes, docstring, and __init__ self-assignments up to the
    first non-assignment statement.

    Args:
        node: The ClassDef AST node.
        lines: All source lines (0-indexed) of the file.

    Returns:
        A list containing a single header chunk dict.
    """
    # Determine start_line (1-indexed): first decorator or class keyword
    start_line = node.decorator_list[0].lineno if node.decorator_list else node.lineno

    # Find method nodes in class body (FunctionDef or AsyncFunctionDef)
    method_nodes = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

    if not method_nodes:
        # No methods: header covers entire class
        header_end_line = node.end_lineno
    else:
        first_method = method_nodes[0]
        if first_method.name == "__init__":
            # __init__ is the first method — include leading self-assignments
            header_end_line = first_method.lineno - 1  # default: end before __init__
            for stmt in first_method.body:
                is_self_assign = False
                if isinstance(stmt, (ast.Assign, ast.AugAssign)):
                    # Check targets for self.x pattern
                    targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
                    is_self_assign = any(
                        isinstance(t, ast.Attribute)
                        and isinstance(t.value, ast.Name)
                        and t.value.id == "self"
                        for t in targets
                    )
                elif isinstance(stmt, ast.AnnAssign):
                    # Annotated assign: self.x: type = value
                    is_self_assign = (
                        isinstance(stmt.target, ast.Attribute)
                        and isinstance(stmt.target.value, ast.Name)
                        and stmt.target.value.id == "self"
                    )
                if is_self_assign:
                    header_end_line = stmt.end_lineno
                else:
                    # First non-self-assignment stops the scan
                    break
        else:
            # First method is not __init__ — header ends before it
            header_end_line = first_method.lineno - 1

    chunk_text = "\n".join(lines[start_line - 1 : header_end_line]).rstrip()
    result: list[dict[str, Any]] = [
        {
            "text": chunk_text,
            "start_line": start_line,
            "end_line": header_end_line,
            "chunk_name": node.name,
            "chunk_text": chunk_text,
        }
    ]

    # Append one chunk per method (FunctionDef / AsyncFunctionDef) in class body.
    # Only iterate node.body directly — nested ClassDef bodies are opaque.
    for method in node.body:
        if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        # Include decorator line(s) if present
        method_start = method.decorator_list[0].lineno if method.decorator_list else method.lineno
        method_end = method.end_lineno

        method_text = "\n".join(lines[method_start - 1 : method_end]).rstrip()

        result.append(
            {
                "text": method_text,
                "start_line": method_start,
                "end_line": method_end,
                "chunk_name": f"{node.name}.{method.name}",
                "chunk_text": method_text,
            }
        )

    return result


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
        if isinstance(node, ast.ClassDef):
            chunks.extend(_chunk_class(node, lines))
            continue

        start_line = node.lineno

        # Determine end line (one line before next node starts)
        end_line = top_level_nodes[i + 1].lineno - 1 if i + 1 < len(top_level_nodes) else len(lines)

        # Extract the chunk text
        chunk_lines_subset = lines[start_line - 1 : end_line]
        chunk_text = "\n".join(chunk_lines_subset).rstrip()

        # For Python, stop at last non-blank line before next definition
        # Walk back from next_node.lineno to find last content line
        actual_end_line = end_line
        while actual_end_line > start_line and not lines[actual_end_line - 1].strip():
            actual_end_line -= 1

        if chunk_text:
            chunks.append(
                {
                    "text": chunk_text,
                    "start_line": start_line,
                    "end_line": actual_end_line,
                    "chunk_name": node.name,
                    "chunk_text": chunk_text,
                }
            )

    return chunks


def _enforce_char_limit(
    chunks: list[dict[str, Any]], max_chars: int = 4000
) -> list[dict[str, Any]]:
    """Enforce maximum character limit on chunks, splitting if necessary.

    Args:
        chunks: List of chunks to process.
        max_chars: Maximum characters allowed per chunk.

    Returns:
        List of chunks with character limit enforced.
    """
    result = []
    for chunk in chunks:
        text = chunk["text"]
        if len(text) <= max_chars:
            result.append(chunk)
            continue

        # Split oversized chunk into smaller pieces
        parent_chunk_name = chunk.get("chunk_name", "")
        parent_chunk_text = chunk.get("chunk_text", "")
        lines = text.split("\n")
        current_lines: list[str] = []
        current_start = chunk["start_line"]
        current_line_num = chunk["start_line"]

        for line in lines:
            # Handle extremely long individual lines
            if len(line) > max_chars:
                # Flush current buffer first
                if current_lines:
                    result.append(
                        {
                            "text": "\n".join(current_lines),
                            "start_line": current_start,
                            "end_line": current_line_num - 1,
                            "chunk_name": parent_chunk_name,
                            "chunk_text": parent_chunk_text,
                        }
                    )
                    current_lines = []
                    current_start = current_line_num

                # Split the long line into chunks
                for i in range(0, len(line), max_chars):
                    sub_text = line[i : i + max_chars]
                    result.append(
                        {
                            "text": sub_text,
                            "start_line": current_line_num,
                            "end_line": current_line_num,
                            "chunk_name": parent_chunk_name,
                            "chunk_text": parent_chunk_text,
                        }
                    )
                current_start = current_line_num + 1
            else:
                # Check if adding this line would exceed limit
                test_text = "\n".join(current_lines + [line])
                if len(test_text) > max_chars and current_lines:
                    # Finalize current chunk
                    result.append(
                        {
                            "text": "\n".join(current_lines),
                            "start_line": current_start,
                            "end_line": current_line_num - 1,
                            "chunk_name": parent_chunk_name,
                            "chunk_text": parent_chunk_text,
                        }
                    )
                    # Start new chunk
                    current_lines = [line]
                    current_start = current_line_num
                else:
                    current_lines.append(line)
            current_line_num += 1

        # Add remaining lines
        if current_lines:
            result.append(
                {
                    "text": "\n".join(current_lines),
                    "start_line": current_start,
                    "end_line": chunk["end_line"],
                    "chunk_name": parent_chunk_name,
                    "chunk_text": parent_chunk_text,
                }
            )

    return result


def chunk_file(path: Path) -> list[dict[str, Any]]:
    """Dispatch chunking based on file extension.

    Args:
        path: Path to the file to chunk.

    Returns:
        List of chunks with "text", "start_line", and "end_line" keys.
        Returns empty list if file can't be read as text.

    Raises:
        ValueError: If file extension is not supported.
    """
    ext = path.suffix.lower()

    # Skip known binary file types
    binary_extensions = {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".ico",
        ".woff",
        ".woff2",
        ".ttf",
        ".otf",
        ".eot",
        ".svg",
        ".pdf",
        ".zip",
        ".tar",
        ".gz",
        ".bz2",
        ".7z",
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".bin",
        ".dat",
        ".db",
        ".sqlite",
        ".sqlite3",
    }
    if ext in binary_extensions:
        return []

    try:
        if ext == ".md":
            chunks = chunk_markdown(path)
        elif ext == ".py":
            chunks = chunk_python(path)
        elif ext in (".ts", ".tsx", ".js", ".jsx"):
            from corpus_analyzer.ingest.ts_chunker import chunk_typescript

            chunks = chunk_typescript(path)
        elif ext in (".json", ".yaml", ".yml", ".txt", ".toml"):
            chunks = chunk_lines(path)
        else:
            # Default to line-based chunking for unknown types
            chunks = chunk_lines(path)

        # Enforce maximum character limit on all chunks
        return _enforce_char_limit(chunks, max_chars=4000)
    except UnicodeDecodeError:
        # Skip files that can't be decoded as UTF-8
        return []
    except Exception:
        # Skip any other problematic files
        return []

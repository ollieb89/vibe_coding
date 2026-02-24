"""TypeScript/JavaScript AST-aware chunker using tree-sitter.

Provides chunk_typescript() which splits .ts, .tsx, .js, and .jsx files
into chunks by top-level named constructs, mirroring chunk_python() in style
and return format.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from tree_sitter import Parser
from tree_sitter_language_pack import get_parser

_DIALECT: dict[str, str] = {
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "tsx",
}

_TARGET_TYPES: frozenset[str] = frozenset({
    "function_declaration",
    "generator_function_declaration",
    "class_declaration",
    "abstract_class_declaration",
    "interface_declaration",
    "type_alias_declaration",
    "lexical_declaration",
    "enum_declaration",
})


@lru_cache(maxsize=8)
def _get_cached_parser(dialect: str) -> Parser:
    """Return a cached tree-sitter Parser for the given grammar dialect.

    Args:
        dialect: One of "typescript", "tsx", or "javascript".

    Returns:
        Configured tree_sitter.Parser instance (loaded once per dialect per process).
    """
    return get_parser(dialect)  # type: ignore[arg-type]


def _extract_name(node: Any, export_node: Any | None) -> str:
    """Extract the human-readable name from a declaration AST node.

    Args:
        node: The declaration node (after export unwrapping).
        export_node: The export_statement node if this was an export, else None.

    Returns:
        Name string for the chunk_name field. Falls back to "<anonymous>".
    """
    # Check for export default — name is always "default"
    if export_node is not None:
        for child in export_node.children:
            if child.type == "default":
                return "default"

    if node.type == "lexical_declaration":
        # No direct name field; first variable_declarator holds the identifier
        for child in node.children:
            if child.type == "variable_declarator":
                name_node = child.child_by_field_name("name")
                if name_node is not None and name_node.text is not None:
                    return str(name_node.text.decode("utf-8"))
        return "<anonymous>"

    # All other target types (function, class, interface, type alias, enum, generator)
    # expose a "name" field directly
    name_node = node.child_by_field_name("name")
    if name_node is not None and name_node.text is not None:
        return str(name_node.text.decode("utf-8"))
    return "<anonymous>"


def chunk_typescript(path: Path) -> list[dict[str, Any]]:
    """Split a TypeScript/JavaScript file into chunks by top-level constructs.

    Handles .ts, .tsx, .js, and .jsx files using the appropriate tree-sitter
    grammar. Falls back to chunk_lines() if parsing fails or no named constructs
    are found. Does NOT fall back on root_node.has_error alone — tree-sitter
    produces useful partial trees.

    JSDoc blocks (/** ... */) immediately preceding a construct (no intervening
    blank lines) are included in the chunk text. Single-line // comments are not.

    Args:
        path: Path to the TypeScript/JavaScript source file.

    Returns:
        List of chunk dicts with "text", "start_line", "end_line", and
        "chunk_name" keys. start_line and end_line are 1-indexed, inclusive.
    """
    from corpus_analyzer.ingest.chunker import chunk_lines  # lazy: avoid circular

    ext = path.suffix.lower()
    dialect = _DIALECT.get(ext)
    if dialect is None:
        return chunk_lines(path)

    try:
        with open(path, encoding="utf-8") as f:
            source = f.read()
    except (UnicodeDecodeError, OSError):
        return chunk_lines(path)

    if not source.strip():
        return []

    try:
        parser = _get_cached_parser(dialect)
        tree = parser.parse(source.encode("utf-8"))
    except Exception:
        return chunk_lines(path)

    root_node = tree.root_node
    lines = source.splitlines()
    chunks: list[dict[str, Any]] = []

    for child in root_node.children:
        export_node: Any | None = None
        node = child

        if child.type == "export_statement":
            inner = child.child_by_field_name("declaration")
            if inner is None:
                # Could be `export default <expression>` (no declaration field).
                # Check for "default" keyword — if present, emit the whole statement
                # as a chunk with chunk_name "default", then move on.
                has_default = any(c.type == "default" for c in child.children)
                if has_default:
                    outer = child
                    chunk_start_row = outer.start_point[0]
                    start_line = chunk_start_row + 1
                    end_line = outer.end_point[0] + 1
                    chunk_text = "\n".join(
                        lines[chunk_start_row : outer.end_point[0] + 1]
                    ).rstrip()
                    if chunk_text:
                        chunks.append({
                            "text": chunk_text,
                            "start_line": start_line,
                            "end_line": end_line,
                            "chunk_name": "default",
                        })
                # Re-export or other export without declaration — skip
                continue
            export_node = child
            node = inner

        if node.type not in _TARGET_TYPES:
            continue

        # outer is the export wrapper (if present) or the declaration itself.
        # Line range for the emitted chunk is always outer's span.
        outer = export_node if export_node is not None else node
        chunk_start_row = outer.start_point[0]  # 0-indexed row

        # JSDoc lookback: include immediately preceding /** ... */ block comment.
        # "Immediately preceding" means the comment ends on the row just before
        # outer starts (at most one row gap, to allow for tree-sitter whitespace nodes).
        prev = outer.prev_sibling
        # prev_sibling may return a whitespace/newline token; skip those
        if prev is not None and prev.type not in ("comment",):
            prev = prev.prev_sibling  # walk one more step past whitespace
        if prev is not None and prev.type == "comment":
            comment_bytes = prev.text
            if comment_bytes is not None:
                comment_text = comment_bytes.decode("utf-8")
                # Adjacency check: comment ends on the row immediately before outer
                if comment_text.startswith("/**") and outer.start_point[0] - prev.end_point[0] <= 1:
                    chunk_start_row = prev.start_point[0]

        start_line = chunk_start_row + 1  # convert 0-indexed row → 1-indexed line
        end_line = outer.end_point[0] + 1  # inclusive, 1-indexed

        chunk_text = "\n".join(lines[chunk_start_row : outer.end_point[0] + 1]).rstrip()
        chunk_name = _extract_name(node, export_node)

        if chunk_text:
            chunks.append({
                "text": chunk_text,
                "start_line": start_line,
                "end_line": end_line,
                "chunk_name": chunk_name,
            })

    if not chunks:
        return chunk_lines(path)

    return chunks

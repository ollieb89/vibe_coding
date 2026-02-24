"""Search result formatting helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.markup import escape


def extract_snippet(text: str, query: str, max_lines: int = 3) -> str:
    """Extract up to max_lines around the most query-relevant line.

    If query is empty, returns the first max_lines lines.
    Truncates snippets longer than 200 chars at a word boundary with an ellipsis.
    """

    lines = text.splitlines()
    if len(lines) <= max_lines:
        snippet = text
    elif not query.strip():
        snippet = "\n".join(lines[:max_lines])
    else:
        query_terms = {term for term in query.lower().split() if term}
        best_line_index = 0
        best_score = -1

        for idx, line in enumerate(lines):
            line_lower = line.lower()
            score = sum(1 for term in query_terms if term in line_lower)
            if score > best_score:
                best_score = score
                best_line_index = idx

        start = max(0, best_line_index - 1)
        end = min(len(lines), start + max_lines)
        snippet = "\n".join(lines[start:end])

    if len(snippet) <= 200:
        return snippet

    truncated = snippet[:200]
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return truncated.rstrip() + "\u2026"


def format_result(result: dict[str, Any], cwd: Path) -> tuple[str, str | None]:
    """Format a search result as a grep-style Rich markup string pair.

    Returns a tuple of (primary_line, preview_line) where preview_line is None
    when chunk_text is empty or falsy.

    The primary line contains the relative (or absolute) file path, optional
    line range, optional construct type in dim brackets, and the relevance score
    in cyan — all suitable for passing to ``Console.print()``.

    The preview line (when present) is the first line of ``chunk_text``,
    indented by 4 spaces and truncated to 200 characters with ``...`` appended
    if the content exceeds that limit.
    """
    file_path: str = result["file_path"]
    start_line: int = result.get("start_line", 0) or 0
    end_line: int = result.get("end_line", 0) or 0
    construct_type: str | None = result.get("construct_type") or None
    score: float = result.get("_relevance_score", 0.0) or 0.0
    chunk_text: str = result.get("chunk_text", "") or ""

    # Build relative path (fall back to absolute on ValueError)
    try:
        rel_path = str(Path(file_path).relative_to(cwd))
    except ValueError:
        rel_path = file_path

    # Build location string: include line range unless BOTH are zero (legacy row)
    if start_line == 0 and end_line == 0:
        location = rel_path
    else:
        location = f"{rel_path}:{start_line}-{end_line}"

    # Construct type part
    construct_part = f" [dim][{escape(construct_type)}][/dim]" if construct_type else ""

    # Score part
    score_part = f" [cyan]score:{score:.3f}[/cyan]"

    # Primary line
    primary = f"[bold]{escape(location)}[/bold]{construct_part}{score_part}"

    # Preview line
    if not chunk_text:
        return (primary, None)

    first_line = chunk_text.split("\n", 1)[0]
    preview = first_line[:200] + "..." if len(first_line) > 200 else first_line

    return (primary, f"    {escape(preview)}")

"""Search result formatting helpers."""

from __future__ import annotations


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
    return truncated.rstrip() + "…"

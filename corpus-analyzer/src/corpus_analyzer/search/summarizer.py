"""Summary generation helpers for indexed files."""

from __future__ import annotations

import ollama

SUMMARY_PROMPT_TEMPLATE = """You are indexing files in an AI agent library.
Write 1-2 sentences describing what this file does and when an agent should use it.
Be specific and agent-actionable. Do not start with "This file".

File: {filename}
Content:
{content}

Summary:"""


def should_summarize(
    source_summarize: bool,
    stored_summary: str | None,
    content_hash_changed: bool,
) -> bool:
    """Return True when summary generation should run for a file."""
    return source_summarize and (content_hash_changed or stored_summary is None)


def generate_summary(filename: str, content: str, model: str, host: str) -> str:
    """Generate a short summary for a file.

    Returns an empty string when summary generation fails.
    """
    prompt = SUMMARY_PROMPT_TEMPLATE.format(filename=filename, content=content[:4000])

    try:
        client = ollama.Client(host=host)
        response = client.generate(model=model, prompt=prompt)
        return str(response.response).strip()
    except Exception:
        return ""

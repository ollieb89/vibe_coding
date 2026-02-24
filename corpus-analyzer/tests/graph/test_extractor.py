# tests/graph/test_extractor.py
"""Tests for ## Related Skills / ## Related Files slug extraction."""
from __future__ import annotations

from corpus_analyzer.graph.extractor import extract_related_slugs


def test_extracts_backtick_slugs() -> None:
    md = "## Related Skills\n\n- `feature-planning`, `dev-spec`\n"
    assert extract_related_slugs(md) == ["feature-planning", "dev-spec"]


def test_extracts_bold_slugs() -> None:
    md = "## Related Skills\n\n- **feature-planning**: for planning\n- **dev-spec**: for specs\n"
    assert extract_related_slugs(md) == ["feature-planning", "dev-spec"]


def test_extracts_plain_list_slugs() -> None:
    md = "## Related Skills\n\n- writing-clearly-and-concisely\n"
    assert extract_related_slugs(md) == ["writing-clearly-and-concisely"]


def test_mixed_formats_in_one_section() -> None:
    md = (
        "## Related Skills\n\n"
        "- `micro-saas-launcher`, `copywriting`\n"
        "- **landing-page-design**: For landing pages\n"
        "- seo\n"
    )
    result = extract_related_slugs(md)
    assert set(result) == {"micro-saas-launcher", "copywriting", "landing-page-design", "seo"}


def test_also_extracts_related_files_section() -> None:
    md = "## Related Files\n\n- `SKILL.md` - Main skill guide\n- `ADVANCED.md`\n"
    # .md extension is stripped: SKILL, ADVANCED
    assert "SKILL" in extract_related_slugs(md) or "SKILL.md" in extract_related_slugs(md)


def test_returns_empty_when_no_related_section() -> None:
    md = "# My Skill\n\nSome content here.\n"
    assert extract_related_slugs(md) == []


def test_stops_at_next_heading() -> None:
    md = (
        "## Related Skills\n\n"
        "- `feature-planning`\n\n"
        "## Usage\n\n"
        "- `something-else`\n"
    )
    assert extract_related_slugs(md) == ["feature-planning"]


def test_deduplicates_slugs() -> None:
    md = "## Related Skills\n\n- `auth`, `auth`\n"
    assert extract_related_slugs(md) == ["auth"]

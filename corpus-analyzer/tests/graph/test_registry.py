# tests/graph/test_registry.py
"""Tests for the slug-to-path component registry."""
from __future__ import annotations

import logging
from pathlib import Path

import pytest

from corpus_analyzer.graph.registry import SlugRegistry


def test_resolves_known_slug(tmp_path: Path) -> None:
    (tmp_path / "skills" / "feature-planning").mkdir(parents=True)
    (tmp_path / "skills" / "feature-planning" / "SKILL.md").write_text("content")
    reg = SlugRegistry.build([tmp_path])
    assert reg.resolve("feature-planning") == tmp_path / "skills" / "feature-planning" / "SKILL.md"


def test_returns_none_for_unknown_slug(tmp_path: Path) -> None:
    reg = SlugRegistry.build([tmp_path])
    assert reg.resolve("no-such-skill") is None


def test_warns_on_ambiguous_slug(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    (tmp_path / "a" / "auth").mkdir(parents=True)
    (tmp_path / "a" / "auth" / "SKILL.md").write_text("a")
    (tmp_path / "b" / "auth").mkdir(parents=True)
    (tmp_path / "b" / "auth" / "SKILL.md").write_text("b")
    with caplog.at_level(logging.WARNING, logger="corpus_analyzer.graph.registry"):
        reg = SlugRegistry.build([tmp_path])
    assert "ambiguous" in caplog.text.lower()
    resolved = reg.resolve("auth")
    assert resolved is not None
    # duplicates property exposes all candidates for caller to surface to user
    assert "auth" in reg.duplicates
    assert len(reg.duplicates["auth"]) == 2


def test_resolve_closest_prefix_wins(tmp_path: Path) -> None:
    """When resolving an ambiguous slug, the candidate closest to context_path wins."""
    (tmp_path / "cct" / "skills" / "auth").mkdir(parents=True)
    (tmp_path / "cct" / "skills" / "auth" / "SKILL.md").write_text("cct auth")
    (tmp_path / "aliskills" / "auth").mkdir(parents=True)
    (tmp_path / "aliskills" / "auth" / "SKILL.md").write_text("ali auth")
    reg = SlugRegistry.build([tmp_path])
    assert "auth" in reg.duplicates

    # A file in cct/skills should resolve auth to cct/skills/auth
    cct_context = tmp_path / "cct" / "skills" / "feature-planning" / "SKILL.md"
    result = reg.resolve("auth", context_path=cct_context)
    assert result is not None
    assert "cct" in str(result)

    # A file in aliskills should resolve auth to aliskills/auth
    ali_context = tmp_path / "aliskills" / "other" / "SKILL.md"
    result = reg.resolve("auth", context_path=ali_context)
    assert result is not None
    assert "aliskills" in str(result)


def test_resolve_no_context_uses_shortest_path_fallback(tmp_path: Path) -> None:
    """Without context_path, shortest-path candidate is used for ambiguous slugs."""
    (tmp_path / "a" / "b" / "c" / "auth").mkdir(parents=True)
    (tmp_path / "a" / "b" / "c" / "auth" / "SKILL.md").write_text("deep")
    (tmp_path / "x" / "auth").mkdir(parents=True)
    (tmp_path / "x" / "auth" / "SKILL.md").write_text("shallow")
    reg = SlugRegistry.build([tmp_path])
    result = reg.resolve("auth")  # no context
    assert result is not None
    assert "x" in str(result)  # shortest path wins


def test_prefers_skill_md_over_readme(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("skill")
    (skill_dir / "README.md").write_text("readme")
    reg = SlugRegistry.build([tmp_path])
    assert reg.resolve("my-skill") is not None
    assert reg.resolve("my-skill").name == "SKILL.md"  # type: ignore[union-attr]


def test_fallback_to_readme_when_no_skill_md(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "README.md").write_text("readme")
    reg = SlugRegistry.build([tmp_path])
    assert reg.resolve("my-skill") is not None
    assert reg.resolve("my-skill").name == "README.md"  # type: ignore[union-attr]

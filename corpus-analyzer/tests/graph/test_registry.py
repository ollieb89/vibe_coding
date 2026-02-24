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

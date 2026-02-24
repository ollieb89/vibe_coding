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


def test_logs_ambiguous_slug_at_debug(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    (tmp_path / "a" / "auth").mkdir(parents=True)
    (tmp_path / "a" / "auth" / "SKILL.md").write_text("a")
    (tmp_path / "b" / "auth").mkdir(parents=True)
    (tmp_path / "b" / "auth" / "SKILL.md").write_text("b")
    with caplog.at_level(logging.DEBUG, logger="corpus_analyzer.graph.registry"):
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


def test_structural_dirs_are_not_registered(tmp_path: Path) -> None:
    """Directories named after common infrastructure patterns must not become slugs."""
    for structural_name in ("docs", "references", "agents", "commands", "templates"):
        d = tmp_path / structural_name
        d.mkdir()
        (d / "README.md").write_text("infra content")
    reg = SlugRegistry.build([tmp_path])
    for structural_name in ("docs", "references", "agents", "commands", "templates"):
        assert reg.resolve(structural_name) is None, (
            f"Structural dir '{structural_name}' should not be registered as a slug"
        )
        assert structural_name not in reg.duplicates


def test_classify_same_root_is_within_source(tmp_path: Path) -> None:
    """Duplicates whose candidates all live under one source root are within-source (warned)."""
    root = tmp_path / "repo"
    (root / "v1" / "auth").mkdir(parents=True)
    (root / "v1" / "auth" / "SKILL.md").write_text("v1")
    (root / "v2" / "auth").mkdir(parents=True)
    (root / "v2" / "auth" / "SKILL.md").write_text("v2")
    reg = SlugRegistry.build([root])
    within_source, cross_source = reg.classify([root])
    assert "auth" in within_source
    assert "auth" not in cross_source


def test_classify_different_roots_is_cross_source(tmp_path: Path) -> None:
    """Duplicates spanning two source roots are cross-source (suppressed)."""
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    (root_a / "auth").mkdir(parents=True)
    (root_a / "auth" / "SKILL.md").write_text("a")
    (root_b / "auth").mkdir(parents=True)
    (root_b / "auth" / "SKILL.md").write_text("b")
    reg = SlugRegistry.build([root_a, root_b])
    within_source, cross_source = reg.classify([root_a, root_b])
    assert "auth" in cross_source
    assert "auth" not in within_source


def test_classify_orphan_path_treated_as_within_source(tmp_path: Path) -> None:
    """A candidate that matches no source root is treated as within-source (never silenced)."""
    root = tmp_path / "repo"
    (root / "auth").mkdir(parents=True)
    (root / "auth" / "SKILL.md").write_text("in root")
    outside = tmp_path / "other" / "auth"
    outside.mkdir(parents=True)
    (outside / "SKILL.md").write_text("outside")
    # Registry built with both, but classify() only knows about root
    reg = SlugRegistry.build([root, tmp_path / "other"])
    within_source, cross_source = reg.classify([root])  # other is not a known source root
    assert "auth" in within_source
    assert "auth" not in cross_source


def test_classify_nested_roots_longest_match_wins(tmp_path: Path) -> None:
    """When roots are nested, each path is assigned to its most specific root.

    With a single outer root in classify(), deep versioned copies are both
    within-source (they share the same configured source root).
    """
    outer = tmp_path / "repo"
    (outer / "v1" / "auth").mkdir(parents=True)
    (outer / "v1" / "auth" / "SKILL.md").write_text("v1")
    (outer / "v2" / "components" / "auth").mkdir(parents=True)
    (outer / "v2" / "components" / "auth" / "SKILL.md").write_text("v2")
    reg = SlugRegistry.build([outer])
    # Both paths live under `outer`; only one source root is known → within-source.
    within_source, cross_source = reg.classify([outer])
    assert "auth" in within_source
    assert "auth" not in cross_source


def test_non_structural_dirs_still_registered(tmp_path: Path) -> None:
    """Excluding structural dirs must not affect real skill directories."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "README.md").write_text("infra")
    skill_dir = tmp_path / "my-real-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("skill content")
    reg = SlugRegistry.build([tmp_path])
    assert reg.resolve("my-real-skill") is not None
    assert reg.resolve("docs") is None

"""Slug-to-path registry built from a directory scan.

A 'slug' is the final directory name of a component folder, e.g.
``feature-planning`` from ``components/skills/productivity/feature-planning/``.

Resolution priority for candidate index files within a slug directory:
1. ``SKILL.md``
2. ``README.md``
3. First ``.md`` file found (alphabetical)

On ambiguous slug (same directory name under different parents), the
canonical path is the one with the fewest path parts; a WARNING is emitted.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_PREFERRED = ("SKILL.md", "README.md")


def _pick_index_file(directory: Path) -> Path | None:
    """Return the preferred representative file for a slug directory.

    Args:
        directory: A directory that may contain a component index file.

    Returns:
        Path to SKILL.md, README.md, or first .md file found; None if no .md files exist.
    """
    for name in _PREFERRED:
        candidate = directory / name
        if candidate.exists():
            return candidate
    md_files = sorted(directory.glob("*.md"))
    return md_files[0] if md_files else None


class SlugRegistry:
    """Immutable map of slug -> canonical Path, built from root directories."""

    def __init__(self, mapping: dict[str, Path]) -> None:
        """Initialise with a pre-built slug->path mapping.

        Args:
            mapping: Dict of slug string to resolved canonical Path.
        """
        self._map = mapping

    @classmethod
    def build(cls, roots: list[Path]) -> SlugRegistry:
        """Scan *roots* recursively and build slug->path registry.

        Each subdirectory that contains at least one .md file is registered
        under its own directory name as a slug.  When the same directory name
        appears under multiple parents, a WARNING is logged and the candidate
        with the fewest path parts is chosen as canonical.

        Args:
            roots: List of root directories to scan (e.g. each source root).

        Returns:
            A new SlugRegistry instance.
        """
        candidates: dict[str, list[Path]] = {}
        for root in roots:
            for directory in root.rglob("*"):
                if not directory.is_dir():
                    continue
                index = _pick_index_file(directory)
                if index is None:
                    continue
                slug = directory.name
                candidates.setdefault(slug, []).append(index)

        mapping: dict[str, Path] = {}
        for slug, paths in candidates.items():
            if len(paths) > 1:
                logger.warning(
                    "ambiguous slug %r: %d candidates %s — using shortest path",
                    slug,
                    len(paths),
                    [str(p) for p in paths],
                )
                paths = sorted(paths, key=lambda p: len(p.parts))
            mapping[slug] = paths[0]

        return cls(mapping)

    def resolve(self, slug: str) -> Path | None:
        """Return the canonical Path for *slug*, or None if unknown.

        Args:
            slug: The directory-name slug to resolve.

        Returns:
            Canonical Path if found, None otherwise.
        """
        return self._map.get(slug)

    def __len__(self) -> int:
        """Return number of known slugs."""
        return len(self._map)

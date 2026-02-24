"""Slug-to-path registry built from a directory scan.

A 'slug' is the final directory name of a component folder, e.g.
``feature-planning`` from ``components/skills/productivity/feature-planning/``.

Resolution priority for candidate index files within a slug directory:
1. ``SKILL.md``
2. ``README.md``
3. First ``.md`` file found (alphabetical)

On ambiguous slug (same directory name under different parents), a WARNING is
logged and the ``duplicates`` property exposes all candidates so callers can
surface the collision to users.  When ``resolve()`` is given a ``context_path``
the candidate that shares the longest common path prefix with the caller wins;
without context the candidate with the fewest path parts is used as a fallback.
"""
from __future__ import annotations

import logging
import os.path
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

    def __init__(
        self,
        mapping: dict[str, Path],
        ambiguous: dict[str, list[Path]] | None = None,
    ) -> None:
        """Initialise with a pre-built slug->path mapping.

        Args:
            mapping: Dict of slug string to resolved canonical Path (shortest-path fallback).
            ambiguous: Dict of slug -> all candidate Paths for slugs that collided.
        """
        self._map = mapping
        self._ambiguous: dict[str, list[Path]] = ambiguous or {}

    @property
    def duplicates(self) -> dict[str, list[Path]]:
        """Slugs that resolved to more than one candidate path, with all candidates."""
        return self._ambiguous

    @classmethod
    def build(cls, roots: list[Path]) -> SlugRegistry:
        """Scan *roots* recursively and build slug->path registry.

        Each subdirectory that contains at least one .md file is registered
        under its own directory name as a slug.  When the same directory name
        appears under multiple parents, a WARNING is logged, the collision is
        stored in ``duplicates``, and the candidate with fewest path parts is
        used as a context-free fallback.

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
        ambiguous: dict[str, list[Path]] = {}
        for slug, paths in candidates.items():
            if len(paths) > 1:
                logger.warning(
                    "ambiguous slug %r: %d candidates %s",
                    slug,
                    len(paths),
                    [str(p) for p in paths],
                )
                sorted_paths = sorted(paths, key=lambda p: len(p.parts))
                ambiguous[slug] = sorted_paths
                mapping[slug] = sorted_paths[0]  # shortest-path fallback
            else:
                mapping[slug] = paths[0]

        return cls(mapping, ambiguous)

    def resolve(self, slug: str, context_path: Path | str | None = None) -> Path | None:
        """Return the best-matching Path for *slug*, or None if unknown.

        For unambiguous slugs the single known path is returned directly.
        For ambiguous slugs (same directory name under different parents) the
        candidate that shares the longest common path prefix with *context_path*
        is preferred; if no context is given the shortest-path fallback is used.

        Args:
            slug: The directory-name slug to resolve.
            context_path: Path of the file doing the referencing.  Used to
                pick the closest neighbour when multiple candidates exist.

        Returns:
            Best-matching Path if found, None otherwise.
        """
        if slug not in self._map:
            return None
        if slug not in self._ambiguous or context_path is None:
            return self._map[slug]

        context = str(context_path)
        candidates = self._ambiguous[slug]

        def common_prefix_parts(p: Path) -> int:
            try:
                return len(os.path.commonpath([str(p), context]).split(os.sep))
            except ValueError:
                return 0

        return max(candidates, key=common_prefix_parts)

    def __len__(self) -> int:
        """Return number of known slugs."""
        return len(self._map)

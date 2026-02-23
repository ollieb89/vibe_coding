"""File scanning and change detection for corpus-analyzer.

This module provides functions for walking source directories,
computing file hashes, and detecting when files need reindexing.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from pathlib import Path


def file_content_hash(path: Path) -> str:
    """Compute SHA256 hash of file content.

    Reads the file in chunks to handle large files efficiently.

    Args:
        path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA256 digest.
    """
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):  # 64KB chunks
            sha256.update(chunk)
    return sha256.hexdigest()


def walk_source(
    base_path: Path,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    extensions: list[str] | None = None,
) -> Iterator[Path]:
    """Walk a source directory and yield matching files.

    Files are yielded if they match any include pattern and do not
    match any exclude pattern. If extensions is provided, only files
    with matching suffixes are yielded.

    Args:
        base_path: Root directory to walk.
        include: Glob patterns for files to include.
        exclude: Glob patterns for files to exclude.
        extensions: List of file extensions to allow (e.g., [".md", ".py"]).
            If None, all extensions are allowed. If empty list, no files are yielded.

    Yields:
        Path objects for matching files.
    """
    if not base_path.exists():
        return

    if include is None:
        include = ["**/*"]
    if exclude is None:
        exclude = []

    for path in base_path.rglob("*"):
        if not path.is_file():
            continue

        rel_path = path.relative_to(base_path)

        # Check excludes first
        if any(_match_glob(str(rel_path), pattern) for pattern in exclude):
            continue

        # Check includes
        if any(_match_glob(str(rel_path), pattern) for pattern in include):
            # Extension filter: applied after include/exclude
            if extensions is not None and path.suffix.lower() not in extensions:
                continue
            yield path


def _match_glob(path: str, pattern: str) -> bool:
    """Check if a path matches a glob pattern.

    Handles simple glob patterns like *.md, **/*, **/node_modules/**
    """
    import fnmatch

    # Handle **/ prefix for recursive matching
    if pattern.startswith("**/"):
        # Match pattern against any suffix of the path
        suffix_pattern = pattern[3:]  # Remove **/
        # Check if any component matches
        parts = path.split("/")
        for i in range(len(parts)):
            suffix = "/".join(parts[i:])
            if fnmatch.fnmatch(suffix, suffix_pattern):
                return True
        return False
    else:
        # Direct match
        return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(
            Path(path).name, pattern
        )

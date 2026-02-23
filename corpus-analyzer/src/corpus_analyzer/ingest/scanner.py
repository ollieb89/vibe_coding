"""File scanning and change detection for corpus-analyzer.

This module provides functions for walking source directories,
computing file hashes, and detecting when files need reindexing.
"""

from __future__ import annotations

import hashlib
import os
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


def needs_reindex(path: Path, stored_mtime: float, stored_hash: str) -> bool:
    """Determine if a file needs to be reindexed.

    Uses a fast path: if mtime is unchanged, returns False immediately.
    If mtime changed, computes the hash and returns True only if the
    hash also differs (content actually changed, not just touched).

    Args:
        path: Path to the file to check.
        stored_mtime: Last known modification time from the index.
        stored_hash: Last known content hash from the index.

    Returns:
        True if the file needs reindexing, False otherwise.
    """
    current_mtime = path.stat().st_mtime

    # Fast path: mtime unchanged
    if current_mtime == stored_mtime:
        return False

    # Mtime changed, check if content actually changed
    current_hash = file_content_hash(path)
    return current_hash != stored_hash


def walk_source(
    source_path: Path, include: list[str], exclude: list[str]
) -> Iterator[Path]:
    """Walk a source directory and yield matching files.

    Files are yielded if they match any include pattern and do not
    match any exclude pattern.

    Args:
        source_path: Root directory to walk.
        include: Glob patterns for files to include.
        exclude: Glob patterns for files to exclude.

    Yields:
        Path objects for matching files.
    """
    if not source_path.exists():
        return

    for root, _dirs, files in os.walk(source_path):
        root_path = Path(root)

        for filename in files:
            file_path = root_path / filename
            rel_path = file_path.relative_to(source_path)
            rel_str = str(rel_path)

            # Check exclude patterns first
            excluded = any(_match_glob(rel_str, pattern) for pattern in exclude)
            if excluded:
                continue

            # Check include patterns
            included = any(_match_glob(rel_str, pattern) for pattern in include)
            if included:
                yield file_path


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

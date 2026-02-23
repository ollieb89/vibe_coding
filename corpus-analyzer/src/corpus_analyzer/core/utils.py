"""Shared file system utilities for corpus-analyzer."""

from __future__ import annotations

import hashlib
from pathlib import Path


def file_content_hash(path: Path) -> str:
    """Compute SHA256 hash of file content.

    Reads the file in 64 KB chunks to handle large files efficiently.

    Args:
        path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA256 digest.
    """
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_file_mtime(path: Path) -> float:
    """Return the file's last-modified timestamp as a Unix float.

    Args:
        path: Path to the file.

    Returns:
        Modification time as a float (seconds since epoch).
    """
    return path.stat().st_mtime

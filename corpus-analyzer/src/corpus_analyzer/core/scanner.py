"""File system scanner for finding documents."""

from pathlib import Path
from typing import Iterator


def scan_directory(
    root: Path,
    extensions: list[str],
    ignore_patterns: list[str] | None = None,
) -> Iterator[Path]:
    """
    Recursively scan a directory for files matching given extensions.

    Args:
        root: Root directory to scan
        extensions: List of file extensions to include (e.g., [".md", ".py"])
        ignore_patterns: Glob patterns to ignore (e.g., ["*.test.py", "__pycache__"])

    Yields:
        Path objects for matching files
    """
    if ignore_patterns is None:
        ignore_patterns = [
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            "node_modules",
            ".pytest_cache",
            ".ruff_cache",
            ".mypy_cache",
            "*.pyc",
            ".DS_Store",
        ]

    def should_ignore(path: Path) -> bool:
        """Check if path matches any ignore pattern."""
        for pattern in ignore_patterns:
            if path.match(pattern):
                return True
            if pattern in path.parts:
                return True
        return False

    if not root.exists():
        return

    for item in root.rglob("*"):
        if item.is_file() and not should_ignore(item):
            if item.suffix.lower() in extensions:
                yield item

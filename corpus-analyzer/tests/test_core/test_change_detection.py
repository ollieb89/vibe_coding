"""Tests for tiered change-detection logic in the extract pipeline."""

from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from corpus_analyzer.cli import app
from corpus_analyzer.core.database import CorpusDatabase
from corpus_analyzer.core.utils import file_content_hash, get_file_mtime

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_md_file(
    directory: Path, name: str = "doc.md", content: str = "# Hello\n\nWorld.\n"
) -> Path:
    """Write a minimal markdown file and return its path."""
    p = directory / name
    p.write_text(content, encoding="utf-8")
    return p


def _run_extract(source: Path, db_path: Path, *, force: bool = False) -> str:
    """Run the extract CLI command and return combined output."""
    args = ["extract", str(source), "--output", str(db_path), "--ext", ".md"]
    if force:
        args.append("--force")
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    return result.output


# ---------------------------------------------------------------------------
# Unit tests: core/utils.py
# ---------------------------------------------------------------------------

def test_file_content_hash_returns_hex_string(tmp_path: Path) -> None:
    """file_content_hash should return a 64-char hex string."""
    f = tmp_path / "sample.txt"
    f.write_bytes(b"hello world")
    h = file_content_hash(f)
    assert isinstance(h, str)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_file_content_hash_changes_with_content(tmp_path: Path) -> None:
    """Hash must differ when file content changes."""
    f = tmp_path / "sample.txt"
    f.write_bytes(b"version 1")
    h1 = file_content_hash(f)
    f.write_bytes(b"version 2")
    h2 = file_content_hash(f)
    assert h1 != h2


def test_get_file_mtime_returns_float(tmp_path: Path) -> None:
    """get_file_mtime should return a positive float."""
    f = tmp_path / "sample.txt"
    f.write_bytes(b"data")
    mtime = get_file_mtime(f)
    assert isinstance(mtime, float)
    assert mtime > 0


# ---------------------------------------------------------------------------
# Unit tests: CorpusDatabase fingerprint methods
# ---------------------------------------------------------------------------

def test_get_file_fingerprint_none_for_unknown_path(tmp_path: Path) -> None:
    """get_file_fingerprint should return None for a path not yet indexed."""
    db = CorpusDatabase(tmp_path / "corpus.sqlite")
    db.initialize()
    assert db.get_file_fingerprint("/nonexistent/file.md") is None


def test_update_file_fingerprint_updates_stored_values(tmp_path: Path) -> None:
    """update_file_fingerprint should update hash and mtime for an existing document."""
    from datetime import datetime

    from corpus_analyzer.core.models import Document

    db_path = tmp_path / "corpus.sqlite"
    db = CorpusDatabase(db_path)
    db.initialize()

    f = tmp_path / "doc.md"
    f.write_text("# Test\n", encoding="utf-8")

    doc = Document(
        path=f,
        relative_path="doc.md",
        file_type="md",
        title="Test",
        mtime=datetime.now(),
        size_bytes=f.stat().st_size,
        content_hash="oldhash",
        last_modified=1000.0,
    )
    db.insert_document(doc)

    db.update_file_fingerprint(str(f), "newhash", 9999.0)

    fp = db.get_file_fingerprint(str(f))
    assert fp == ("newhash", 9999.0)


# ---------------------------------------------------------------------------
# Integration tests: extract CLI command
# ---------------------------------------------------------------------------

def test_extract_new_file_is_indexed(tmp_path: Path) -> None:
    """First extract should index a new file and report it as new."""
    src = tmp_path / "src"
    src.mkdir()
    _make_md_file(src)
    db_path = tmp_path / "corpus.sqlite"

    output = _run_extract(src, db_path)

    assert "New:" in output or "1 extracted" in output
    db = CorpusDatabase(db_path)
    db.initialize()
    docs = list(db.get_documents())
    assert len(docs) == 1


def test_extract_unchanged_file_is_skipped(tmp_path: Path) -> None:
    """Second extract with no changes should skip the file entirely."""
    src = tmp_path / "src"
    src.mkdir()
    _make_md_file(src)
    db_path = tmp_path / "corpus.sqlite"

    _run_extract(src, db_path)  # first run — indexes

    # Ensure mtime is the same (no file modification)
    output2 = _run_extract(src, db_path)  # second run — should skip

    assert "1 unchanged" in output2
    assert "New:" not in output2
    assert "Updated:" not in output2


def test_extract_modified_content_triggers_update(tmp_path: Path) -> None:
    """After changing file content, extract should report the file as updated."""
    src = tmp_path / "src"
    src.mkdir()
    f = _make_md_file(src, content="# Version 1\n\nInitial content.\n")
    db_path = tmp_path / "corpus.sqlite"

    _run_extract(src, db_path)  # first run

    # Modify file content (also bumps mtime)
    f.write_text("# Version 2\n\nCompletely different content.\n", encoding="utf-8")

    output2 = _run_extract(src, db_path)

    assert "Updated:" in output2
    assert "1 unchanged" not in output2


def test_extract_touched_file_hash_check_skips(tmp_path: Path) -> None:
    """If only mtime changes (touch) but content is identical, the file should be skipped."""
    src = tmp_path / "src"
    src.mkdir()
    f = _make_md_file(src)
    db_path = tmp_path / "corpus.sqlite"

    _run_extract(src, db_path)  # first run

    # Touch: update mtime without changing content
    # We need mtime to be strictly different, so advance by 2 seconds.
    current = f.stat().st_mtime
    new_mtime = current + 2.0
    os.utime(f, (new_mtime, new_mtime))

    output2 = _run_extract(src, db_path)

    # Hash check should confirm content is identical → skip
    assert "1 unchanged" in output2
    assert "Updated:" not in output2


def test_extract_force_reindexes_unchanged_file(tmp_path: Path) -> None:
    """--force should re-extract even when content hash is unchanged."""
    src = tmp_path / "src"
    src.mkdir()
    _make_md_file(src)
    db_path = tmp_path / "corpus.sqlite"

    _run_extract(src, db_path)  # first run — indexes

    output2 = _run_extract(src, db_path, force=True)  # forced re-run

    # Should show the file as processed (New or Updated), NOT skipped
    assert "unchanged" not in output2 or "0 unchanged" in output2

---
phase: 05-extension-filtering
verified: 2026-02-23T00:00:00Z
status: passed
score: 4/4 must-haves verified
requirements-completed:
  - CONF-06
  - CONF-07
  - CONF-08
---

# Phase 5: Extension Filtering Verification Report

**Phase Goal:** Users control exactly which file types get indexed per source, and the indexer silently skips non-allowlisted files using a sensible default when no extensions are configured
**Verified:** 2026-02-23
**Status:** passed

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can add `extensions = [".md", ".py"]` to a source block in corpus.toml and only those file types are indexed | ✓ VERIFIED | `SourceConfig.extensions` field (schema.py:78) with Pydantic `field_validator` normalizing values; `walk_source(extensions=source.extensions)` called in indexer.py:172 |
| 2 | corpus index skips `.sh`, `.html`, `.json`, `.lock`, binary files without error or warning | ✓ VERIFIED | `walk_source` filters by suffix match (scanner.py); test `test_indexer_extension_filtering_and_removal` confirms non-allowlisted files are not indexed |
| 3 | A source with no `extensions` key applies default allowlist covering `.md`, `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.yaml`, `.yml`, `.txt` | ✓ VERIFIED | `DEFAULT_EXTENSIONS` constant (schema.py:17-19) used as `SourceConfig.extensions` default (schema.py:78); list matches spec exactly |
| 4 | Default allowlist excludes `.sh`, `.html`, `.json`, `.lock`, binary files | ✓ VERIFIED | `DEFAULT_EXTENSIONS` does not include `.sh`, `.html`, `.json`, `.lock`, or any binary extensions; confirmed in schema.py:17-19 |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/corpus_analyzer/config/schema.py` | `extensions` field on SourceConfig, DEFAULT_EXTENSIONS | ✓ EXISTS + SUBSTANTIVE | `DEFAULT_EXTENSIONS` list at line 17; `extensions` field at line 78 with validator |
| `src/corpus_analyzer/ingest/scanner.py` | `walk_source(extensions=)` parameter | ✓ EXISTS + SUBSTANTIVE | `extensions` param added; case-insensitive suffix filter applied after include/exclude matching |
| `src/corpus_analyzer/ingest/indexer.py` | Passes extensions to walk_source; tracks files_removed | ✓ EXISTS + SUBSTANTIVE | `extensions=source.extensions` at line 172; `files_removed` computed and in `IndexResult` |
| `src/corpus_analyzer/cli.py` | Shows active extensions on first run; warns on file removal | ✓ EXISTS + SUBSTANTIVE | Active extensions shown on first run (line 130); yellow removal warning at line 172-175 |
| `tests/config/test_schema.py` | 6 tests for SourceConfig.extensions | ✓ EXISTS + SUBSTANTIVE | 6 tests covering field defaults, normalization, validator |
| `tests/ingest/test_scanner.py` | 5 tests for walk_source extension filtering | ✓ EXISTS + SUBSTANTIVE | 5 tests covering filtering, case insensitivity, empty list, None |
| `tests/ingest/test_indexer.py` | test_indexer_extension_filtering_and_removal | ✓ EXISTS + SUBSTANTIVE | Covers allowlist indexing and files_removed calculation |

**Artifacts:** 7/7 verified

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| corpus.toml `extensions` | `SourceConfig.extensions` | Pydantic schema load | ✓ WIRED | field_validator normalizes dots and casing |
| `SourceConfig.extensions` | `walk_source()` | indexer.py:172 | ✓ WIRED | `extensions=source.extensions` passed to both indexer and CLI progress counter |
| `walk_source()` | file skip | scanner.py suffix filter | ✓ WIRED | `fp.suffix.lower() not in extensions` check applied |
| `IndexResult.files_removed` | CLI warning | cli.py:172-175 | ✓ WIRED | Yellow warning printed when `files_removed > 0` |

**Wiring:** 4/4 connections verified

## Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| CONF-06: User can specify extensions in corpus.toml per source | ✓ SATISFIED | — |
| CONF-07: corpus index skips files not in allowlist | ✓ SATISFIED | — |
| CONF-08: Default allowlist applies when extensions not configured | ✓ SATISFIED | — |

**Coverage:** 3/3 requirements satisfied

## Anti-Patterns Found

None. No TODOs, stubs, or placeholders found in Phase 5 implementation.

Minor tech debt noted (not phase anti-patterns):
- `cli.py:251` — `_count_stale_files` was calling `walk_source` without `extensions=` (display bug in `status` command). **Fixed during audit.**

## Human Verification Required

### 1. CLI Behavior with corpus.toml extensions
**Test:** Add `extensions = [".md"]` to a source block with mixed file types; run `corpus index`; confirm only `.md` files appear in the index
**Expected:** Only `.md` files indexed; warning shown if previously-indexed non-.md files are removed
**Why human:** Requires a live corpus.toml + mixed-type directory

## Gaps Summary

**No critical gaps found.** Phase goal achieved. Display bug in `corpus status` fixed during audit.

## Verification Metadata

**Verification approach:** Goal-backward (derived from phase goal and ROADMAP.md success criteria)
**Must-haves source:** ROADMAP.md Phase 5 success criteria
**Automated checks:** 179 tests passing at phase completion; 192 passing at audit
**Human checks required:** 1 (live CLI behavior)
**Notes:** Phase 5 SUMMARY files were untracked in git at time of audit — committed as part of gap closure

---
*Verified: 2026-02-23*
*Verifier: Claude (audit)*

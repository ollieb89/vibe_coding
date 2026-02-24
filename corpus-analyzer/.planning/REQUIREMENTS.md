# Requirements: Corpus v1.3

**Defined:** 2026-02-24
**Core Value:** Surface relevant agent files instantly — query an entire local agent library and get ranked, relevant results in under a second

## v1 Requirements

Requirements for v1.3 Code Quality milestone. Each maps to roadmap phases.

### Config

- [x] **CONF-01**: `pyproject.toml` has `per-file-ignores` suppressing E501 for `src/corpus_analyzer/llm/*.py`
- [x] **CONF-02**: `pyproject.toml` has `[[tool.mypy.overrides]]` disabling strict checks for `python-frontmatter` imports
- [x] **CONF-03**: `pyproject.toml` excludes `.windsurf/` and `.planning/` from ruff scope
- [x] **CONF-04**: `pyproject.toml` has `per-file-ignores` for `cli.py` B006 (Typer list default trap)

### Ruff Auto-Fix

- [x] **RUFF-01**: `ruff check --fix` applied, eliminating all auto-fixable violations (W293/W291/I001/F401/UP045/F541/W605)
- [x] **RUFF-02**: All `__init__.py` F401 re-exports verified safe after auto-fix (smoke-test imports pass)

### Ruff Manual

- [ ] **RUFF-03**: All E501 line-length violations in leaf modules fixed (wrapping, not shortening content)
- [x] **RUFF-04**: All B-series violations fixed (B905/B007/B017/B023/B904/B008) — no B006 in cli.py (covered by CONF-04)
- [x] **RUFF-05**: All F841/E741 violations fixed (unused variables, ambiguous names)
- [x] **RUFF-06**: All E402 import ordering violations in `llm/rewriter.py` fixed
- [ ] **RUFF-07**: All E501 violations in `cli.py` fixed (45 lines wrapped)

### Mypy

- [ ] **MYPY-01**: `core/database.py` zero mypy errors — `cast(Table, ...)` pattern applied at all call sites
- [ ] **MYPY-02**: `llm/chunked_processor.py` zero mypy errors — nested functions annotated, `Atom` dataclass promoted to module level
- [ ] **MYPY-03**: `utils/ui.py` zero mypy errors
- [ ] **MYPY-04**: `extractors/markdown.py` and `extractors/__init__.py` zero mypy errors — ABC dict-dispatch annotated
- [ ] **MYPY-05**: `llm/rewriter.py` zero mypy errors — operator bug investigated and fixed; `OllamaClient.db` field added
- [ ] **MYPY-06**: `llm/ollama_client.py`, `ingest/chunker.py`, `analyzers/shape.py` zero mypy errors

### Validation

- [ ] **VALID-01**: `uv run ruff check .` exits 0 with zero violations
- [ ] **VALID-02**: `uv run mypy src/` exits 0 with zero errors
- [ ] **VALID-03**: `uv run pytest -v` — all 281 tests green

## Future Requirements

*(none identified — v1.3 is a contained quality milestone)*

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full refactor of llm/ module | Legacy code; minimal invasive fixes only for v1.3 |
| Row-level TypedDict models for sqlite-utils | High value, high effort — v2 candidate |
| Constructor injection refactor for OllamaClient.db | Design smell; add optional field is sufficient for v1.3 |
| Raising global line limit | Per-file-ignores for llm/ is cleaner than a global change |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CONF-01 | Phase 9 | Complete |
| CONF-02 | Phase 9 | Complete |
| CONF-03 | Phase 9 | Complete |
| CONF-04 | Phase 9 | Complete |
| RUFF-01 | Phase 9 | Complete |
| RUFF-02 | Phase 9 | Complete |
| RUFF-03 | Phase 10 | Pending |
| RUFF-04 | Phase 10 | Complete |
| RUFF-05 | Phase 10 | Complete |
| RUFF-06 | Phase 10 | Complete |
| RUFF-07 | Phase 11 | Pending |
| MYPY-01 | Phase 11 | Pending |
| MYPY-02 | Phase 11 | Pending |
| MYPY-03 | Phase 11 | Pending |
| MYPY-04 | Phase 11 | Pending |
| MYPY-05 | Phase 11 | Pending |
| MYPY-06 | Phase 11 | Pending |
| VALID-01 | Phase 12 | Pending |
| VALID-02 | Phase 12 | Pending |
| VALID-03 | Phase 12 | Pending |

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0

---
*Requirements defined: 2026-02-24*
*Last updated: 2026-02-24 — traceability filled by roadmapper*

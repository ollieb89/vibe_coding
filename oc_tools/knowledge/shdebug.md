# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What Is This

ShDebug is a security-focused QA automation framework for web applications. It has three packages:

- **ui/** — TypeScript + Playwright test harness for browser-based checkout flow testing and data extraction
- **api/** — Python security validation engine with PostgreSQL persistence, evidence capture, and PII redaction
- **server/** — TypeScript control plane API for project management, job scheduling, and scan orchestration

These are independent packages coordinated via the root Makefile. The UI outputs artifacts to `runs/<id>/` which the API consumes. PostgreSQL is the shared data store.

## Build & Test Commands

### Root (Makefile)
```
make run                                    # Full UI + API pipeline
make ui                                     # Playwright e2e tests only
make api                                    # Python harness validation only
make ingest RUN_DIR=... DATABASE_URL=...    # Persist run data to PostgreSQL
make pattern-scan DATABASE_URL=... URLS=... # RAG strategy recommendations
```

### UI (`ui/`)
```
pnpm install                    # Install deps
pnpm test                       # Vitest unit tests (src/**/*.test.ts)
pnpm test:e2e                   # Playwright e2e tests (e2e/)
pnpm exec playwright install    # Install browser binaries
pnpm dev                        # Watch mode for Tailwind CSS
pnpm build                      # Build Tailwind CSS (minified)
```

### API (`api/`)
```
uv venv && source .venv/bin/activate   # Create and activate venv
uv sync                                # Install deps
pytest                                 # Run all tests (tests/test_*.py)
pytest tests/test_money_invariants.py   # Run single test file
ruff check .                           # Lint
mypy .                                 # Type check
```

### Server (`server/`)
```
pnpm install       # Install deps
pnpm test          # Vitest tests (tests/*.test.ts)
pnpm typecheck     # TypeScript type checking
```

### Pre-PR checklist
Run all three test suites: `pnpm test` + `pnpm test:e2e` (in ui/), `pytest` (in api/), `pnpm test` (in server/).

## Architecture

**Data flow:** Browser (Playwright) → `runs/<id>/ui_output.json` → Python harness validates invariants → findings/evidence artifacts → PostgreSQL ingestion

**Key API modules** (`api/src/harness/`):
- `run.py` — Main orchestration
- `normalizer.py` — PostgreSQL data ingestion
- `pattern_rag.py` — Vector embeddings for extraction strategy retrieval
- `safety.py` — Host allowlist enforcement (never bypass)
- `invariants/money.py` — Money parsing and validation
- `evidence/redact.py` — PII/secret redaction (never bypass)

**Database:** PostgreSQL with JSONB columns. Schema in `api/sql/` (5 migration files). Transactional job queue uses `FOR UPDATE SKIP LOCKED`.

## Conventions

- **TypeScript:** ESM modules (ES2022, NodeNext). Strict mode. Logic in `src/`, tests as `*.test.ts`.
- **Python:** PEP 8, snake_case, explicit typing. Keep invariant logic in `invariants/`, evidence code in `evidence/`.
- **Commits:** Imperative mood, format: `type(scope): summary` (e.g. `fix(api): enforce host allowlist`).
- **Safety:** Never skip allowlist, rate limits, or redaction unless explicitly changing safety policy.
- **Config:** Copy `.env.example` to `.env`. Key vars: `BASE_URL`, `ALLOWLIST_HOSTS`, UI selector mappings, `DATABASE_URL`.
- **Package managers:** pnpm for TypeScript packages, uv for Python.

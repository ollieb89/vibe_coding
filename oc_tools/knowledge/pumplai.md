# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered fitness coaching platform with workout generation, form analysis, and trainer/client dashboards.

**Tech Stack:**

- **Frontend:** Next.js 16 (App Router + Turbopack), React 19, Tailwind CSS 4, shadcn/ui
- **Backend:** FastAPI (Python 3.11+), SQLAlchemy 2.0, PostgreSQL
- **Monorepo:** Turborepo + pnpm workspaces
- **Auth:** NextAuth.js v5 ↔ FastAPI JWT
- **Testing:** Playwright (E2E), Vitest (unit), pytest (backend), MSW (mocking)

## Quick Start

```bash
# 1. Start infrastructure (Postgres + Redis)
docker compose -f docker/docker-compose.dev.yml up -d

# 2. Install dependencies
pnpm install
cd apps/api && pixi install && cd ../..

# 3. Run migrations
cd apps/api && pixi run alembic upgrade head && cd ../..

# 4. Start all dev servers
turbo dev
```

**URLs:** Web (3000) | Dashboard (3001) | API (8000) | API Docs (8000/api/docs)

## Development Commands

**Root-level** (from repository root):

```bash
pnpm dev                 # Start all apps
pnpm build               # Build all apps and packages
pnpm lint                # ESLint across all workspaces
pnpm format              # Prettier formatting
pnpm test                # Run all tests (unit + E2E)
pnpm test:unit           # Vitest unit tests
pnpm test:e2e            # Playwright E2E tests
pnpm gen:sdk             # Regenerate TypeScript SDK from API schema
```

**Dashboard** (from `apps/dashboard/`):

```bash
pnpm dev                 # Next.js dev server (port 3001)
pnpm typecheck           # TypeScript checking
pnpm test:unit           # Vitest unit tests
pnpm test:e2e            # Playwright E2E tests
pnpm test:e2e:ui         # Playwright with UI mode
pnpm test:accessibility  # A11y tests
```

**Backend** (from `apps/api/`):

```bash
pixi run dev             # FastAPI dev server (port 8000)
pixi run pytest          # Run all tests
pixi run alembic upgrade head                  # Apply migrations
pixi run alembic revision --autogenerate -m "description"  # Create migration
```

**Never use bare `python` or `pytest`** - always use `pixi run` prefix.

## Adding shadcn/ui Components

**IMPORTANT**: Always add from monorepo root:

```bash
pnpm dlx shadcn@latest add button -c packages/ui
```

This places components in `packages/ui/src/components/` shared across all apps.

**Never run `shadcn add` from within apps/** - always from root with `-c packages/ui`.

## Architecture

### Monorepo Structure

```
pumplai/
├── apps/
│   ├── api/                    # FastAPI Backend (Python)
│   │   ├── src/app/
│   │   │   ├── api/v1/endpoints/  # REST endpoints
│   │   │   ├── models/            # SQLAlchemy models
│   │   │   ├── schemas/           # Pydantic schemas
│   │   │   ├── services/          # Business logic (AI, messaging)
│   │   │   └── core/              # Config, security, caching
│   │   └── migrations/            # Alembic migrations
│   │
│   ├── dashboard/              # Trainer Admin (Next.js 16)
│   │   ├── src/app/            # App Router pages
│   │   ├── src/hooks/          # Custom hooks (use-api)
│   │   ├── src/lib/server/     # Server actions & data fetching
│   │   ├── auth.ts             # NextAuth v5 config
│   │   └── tests/              # Playwright + Vitest
│   │
│   ├── web/                    # Client Portal (Next.js 16)
│   └── storybook/              # UI Component Documentation
│
├── packages/
│   ├── ui/                     # Shared shadcn/ui components
│   │   └── src/components/     # Button, Card, Dialog, etc.
│   ├── sdk/                    # Auto-generated API client
│   ├── types/                  # Shared TypeScript definitions
│   ├── validators/             # Shared Zod schemas
│   ├── eslint-config/          # Shared ESLint configs
│   └── typescript-config/      # Shared TS configs
│
├── docker/                     # Docker infrastructure
├── scripts/                    # Utility & deployment scripts
└── ml-local/                   # ML submodule (model training)
```

### Component Import Pattern

```tsx
// UI components via workspace alias
import { Button } from "@workspace/ui/components/button";
import { cn } from "@workspace/ui/lib/utils";

// App-specific components via @/ alias
import { Providers } from "@/components/providers";
```

### Authentication Flow

**Non-standard:** NextAuth.js calls FastAPI backend for credentials.

```
User → NextAuth (dashboard) → POST /api/v1/auth/login (FastAPI) → JWT tokens
```

Key files:

- `apps/dashboard/auth.ts` - Production auth config
- `apps/dashboard/auth.config.test.ts` - Test mode (no backend)
- `apps/dashboard/src/hooks/use-api.ts` - Authenticated fetch wrapper

**Test mode:** Set `NEXTAUTH_TEST_MODE=true` for E2E tests.

### Dashboard Data Fetching

Dashboard uses `useApi` hook (not TanStack Query):

```tsx
import { useApi } from "@/hooks/use-api";

function Component() {
  const api = useApi();
  const user = await api.get("/api/v1/users/me"); // Auto-injects Bearer token
}
```

**Server Components** use `lib/server/` functions:

```typescript
// app/dashboard/page.tsx
import { getDashboardStats } from '@/lib/server/get-dashboard-stats'

export default async function Page() {
  const stats = await getDashboardStats()
  return <DashboardView stats={stats} />
}
```

**Server Actions** for mutations:

```typescript
// lib/server/workout-actions.ts
"use server";
export async function startWorkoutSession(workoutId: number) { ... }
```

## Testing

```bash
# E2E (Playwright + MSW) - requires test mode
NEXTAUTH_TEST_MODE=true pnpm --filter dashboard test:e2e

# Unit (Vitest)
pnpm --filter dashboard test:unit

# Backend (pytest)
cd apps/api && pixi run pytest

# Performance & Lighthouse
pnpm test:lighthouse
pnpm perf:benchmark
```

MSW handlers: `apps/dashboard/tests/mocks/handlers.ts`

## Package Manager

**pnpm 10.28.1** required (enforced via `packageManager`). Node.js 20+ required.

```bash
pnpm add <package>               # Add to root
pnpm add <package> -w            # Add to workspace root
pnpm add <package> --filter web  # Add to specific app
```

## TypeScript SDK (Optional)

Auto-generated from OpenAPI spec. **Use sparingly** - dashboard already has `useApi` hook.

```bash
pnpm gen:sdk  # Regenerate from API schema (requires API running)
```

## Environment Variables

**Dashboard** (`apps/dashboard/.env.local`):

```bash
AUTH_URL=http://localhost:3001
AUTH_SECRET=<openssl rand -base64 32>
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_TEST_MODE=true  # For E2E tests only
```

**API** (`apps/api/.env`):

```bash
DATABASE_URL=postgresql+asyncpg://...
SECRET_KEY=<min 32 chars>
CORS_ORIGINS=http://localhost:3000,http://localhost:3001  # No spaces!
BNB_SERVER_URL=http://localhost:8000  # ML inference server
```

## ML Local (Submodule)

Git submodule for model training, inference, and evaluation.

```bash
# Initialize submodule
git submodule update --init --recursive

# Start inference server (requires GPU with 8GB+ VRAM)
cd ml-local
conda activate pail310
python -m src.inference.server_bnb_lora --port 8000 --quantization 4bit
```

Model weights (~70GB) stored in `~/pumpl-models/` - never committed.

### Submodule Workflow

```bash
# Work in submodule
cd ml-local
git add . && git commit -m "feat: improve training" && git push

# Update parent repo reference
cd ..
git add ml-local && git commit -m "chore: update ml-local submodule"
```

## Common Pitfalls

| Problem                    | Solution                                       |
| -------------------------- | ---------------------------------------------- |
| Component not found        | Add with `-c packages/ui` from root            |
| Python ModuleNotFoundError | Use `pixi run` prefix                          |
| 401 in E2E tests           | Set `NEXTAUTH_TEST_MODE=true`                  |
| CORS errors                | Check `CORS_ORIGINS` has exact URLs, no spaces |
| Types out of sync          | Run `pnpm install` from root                   |

## Important Notes

- **Always run typecheck** before PRs - build may pass but types might be broken
- **SDK package**: Don't manually edit `packages/sdk/src/` - it's auto-generated
- **Docker**: Use `docker compose -f docker/docker-compose.dev.yml up -d` for local dev
- **Client components**: Mark with `"use client"` only when necessary

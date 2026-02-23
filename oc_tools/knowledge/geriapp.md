# 🏥 GeriApp - Stage-Adaptive Dementia Care Platform

**Comprehensive dementia care platform with AI-powered stage-adaptive UI**

[![codecov](https://codecov.io/gh/ollieb89/geriapp/branch/main/graph/badge.svg)](https://codecov.io/gh/ollieb89/geriapp)

---

## 🚀 Quick Start (Choose One)

### Option 1: Docker (Recommended - Everything in One Command)

```bash
cd ~/Development/Projects/geriapp
./FIX-DOCKER-AND-START.sh
```

**Then visit:** http://localhost:4100

**Time:** ~10 minutes (first build), ~1 minute (subsequent starts)

---

### Option 2: Manual Setup (3 Terminals)

```bash
# Terminal 1: User Service
cd backend/user-service
PORT=8100 pnpm dev

# Terminal 2: Care Service
cd backend/care-service
source venv/bin/activate
PORT=8101 python3 run.py

# Terminal 3: Web Portal
cd web
PORT=4100 pnpm dev
```

**Then visit:** http://localhost:4100

**Time:** ~5 minutes

---

## 🎯 Custom Ports (No Conflicts!)

| Service | Port | URL |
|---------|------|-----|
| **Web Portal** | **4100** | http://localhost:4100 |
| **User Service** | **8100** | http://localhost:8100 |
| **Care Service** | **8101** | http://localhost:8101 |
| PostgreSQL | 5432/5432 | localhost:5432 (Docker) |
| Redis | 6379/6479 | localhost:6479 (Docker) |

**✅ Works alongside your other development applications!**

---

## 🎨 Stage-Adaptive Design System

GeriApp features a unique **cognitive stage-adaptive UI** that adjusts complexity based on user's dementia stage:

### Three Cognitive Stages

**Early Stage** (Mild Forgetfulness)
- Touch targets: 44px
- Font size: 16px
- Full UI complexity
- 3 navigation levels

**Moderate Stage** (Noticeable Memory Loss)
- Touch targets: 58px
- Font size: 18px
- Simplified UI
- 2 navigation levels

**Advanced Stage** (Severe Decline)
- Touch targets: 78px
- Font size: 20px
- Minimal UI
- 1 navigation level

### Interactive Testing

**Visit Dashboard:** http://localhost:4100/dashboard

**Use Stage Switcher (Top-Right Yellow Panel):**
- Change between Early / Moderate / Advanced
- Watch entire UI adapt in real-time
- See touch targets, fonts, and layouts transform

---

## 🏗️ Architecture

### Technology Stack
- **Frontend:** Next.js 16, React 18, Tailwind CSS, shadcn/ui
- **Backend:** Node.js/Express, Python/FastAPI
- **Database:** PostgreSQL 15, Redis 7
- **Package Manager:** pnpm (workspaces)

### Design System Components
- **27 shadcn/ui base components** - Radix UI primitives
- **8 stage-adaptive wrappers** - Cognitive stage adaptation
- **2 medical components** - Emergency & medication features
- **Toast notification system** - Global user feedback

---

## 📑 Working with Contracts
- **Regenerate specs:** `curl http://localhost:8101/openapi.json -o /tmp/care-openapi.json` and `curl http://localhost:8102/openapi.json -o /tmp/ai-openapi.json` (FastAPI defaults).
- **Update clients:** map changes into `web/src/lib/api` and `mobile/src/services` to keep request/response shapes aligned.

---

## 🧩 Shared Libraries & Standards
- **Shared backend utilities:** `backend/shared/` for cross-service helpers and domain logic.
- **Contract conventions:** `docs/api/NAMING_CONVENTIONS.md` for casing and payload shape rules.

---

## 🧪 Contract/Integration Testing
- **Web integration runs:** `cd web && pnpm test:e2e:integrated` (requires backend services).
- **Service-level checks:** `pnpm test:care-service` for FastAPI contract coverage.

---

## 📦 What's Included

### Complete Design System ✅
- Stage-adaptive components (Card, Dialog, Input, Select, Table)
- Medical domain components (Emergency Button, Medication Dialogs)
- Toast notifications for user feedback
- Dev tools (stage switcher for testing)
- WCAG AA accessibility compliance

### Backend Services ✅
- User authentication (JWT)
- Care plan management
- Medication tracking
- Activity scheduling
- Real-time notifications (WebSocket)
- Analytics and reporting

### Documentation ✅
- **DESIGN.md** - Complete design system specification (59KB)
- **QUICKSTART.md** - Manual service startup
- **DOCKER-INSTRUCTIONS.md** - This file
- **IMPLEMENTATION-SUMMARY.md** - Component usage
- **PAGE-MIGRATION-GUIDE.md** - Migration patterns
- **15+ comprehensive guides**

---

## 🧪 Testing

### Access & Register
1. Visit http://localhost:4100/register
2. Create account (any email/password)
3. Auto-redirect to dashboard

### Test Features
- ✅ Stage switcher (top-right) - Change UI complexity
- ✅ Emergency button (bottom-right) - Test SOS flow
- ✅ Touch targets - Inspect with browser dev tools (F12)
- ✅ Typography scaling - See text size changes
- ✅ Layout adaptation - Watch grid columns change

### Automated Testing Strategy

GeriApp uses a **dual testing strategy** combining mock-based and integration testing:

**Mock Testing (No Backend Required)** ⚡ Fast
```bash
cd web
pnpm test:e2e              # All E2E tests with mocks
./scripts/validate-phase1-mocks.sh  # Error scenario validation
```
- Tests frontend error handling (401, 403, 404, 500)
- No backend services needed
- Execution time: ~40 seconds
- Use case: Rapid frontend development, CI/CD

**Integration Testing (Backend Required)** 🔗 Comprehensive
```bash
# Start backend first
./FIX-DOCKER-AND-START.sh  # or pnpm docker:up

# Then run integration tests
cd web
pnpm test:e2e:integrated   # Success path tests
```
- Tests full stack with real backend services
- Validates database interactions
- Use case: Pre-deployment validation, feature completion

**Quick Test Commands**:
```bash
# Frontend only
cd web && pnpm test        # Jest unit tests
cd web && pnpm test:e2e    # Playwright E2E (mocked)

# Backend
cd backend/care-service && pytest  # Python tests
cd backend/user-service && pnpm test  # Node tests
```

**Test Coverage**: 50% overall (299 tests passing)
- Analytics: 85%+ coverage
- Components: 75%+ coverage
- Charts: 90%+ coverage

See `docs/testing-guide-phase-8.md` and validation reports in `claudedocs/` for details.

---

## 🔧 Docker Management

### Daily Usage

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart user-service
```

### Maintenance

```bash
# Rebuild after code changes
docker-compose up -d --build

# Clean rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Clean everything (⚠️ deletes data)
docker-compose down -v
```

---

## 📚 Documentation

**Getting Started:**
- README.md (this file)
- QUICKSTART.md
- DOCKER-INSTRUCTIONS.md
- FIX-DOCKER-AND-START.sh

**Design System:**
- DESIGN.md (complete specification)
- IMPLEMENTATION-SUMMARY.md (component usage)
- PAGE-MIGRATION-GUIDE.md (migration patterns)

**Configuration:**
- PORT-CONFIGURATION.md (port reference)
- DOCKER-SETUP.md (detailed Docker guide)
- BACKEND-SETUP-GUIDE.md (manual setup)

**Help:**
- TROUBLESHOOTING.md (common issues)
- FINAL-INSTRUCTIONS.md (current status)

---

## 🎯 Project Status

### ✅ Completed (Phase 1 & 2)
- Complete design system
- 27 shadcn components installed
- 8 stage-adaptive wrappers
- Dashboard migrated
- Emergency features
- Toast notifications
- Custom port configuration
- Docker setup
- ~2,500 lines of production code
- 15+ documentation guides

### ⏳ In Progress
- Medications page migration
- Care Plans page migration
- Activities page migration
- Component test suite

---

## 🏆 Key Features

### Accessibility First
- WCAG AA compliance (AAA for emergencies)
- 78px maximum touch targets (exceeds 20mm requirement)
- High-contrast focus indicators
- Screen reader support
- Keyboard navigation

### Medical Safety
- Color-coded priority system (red=urgent, amber=high, green=stable)
- Emergency SOS button always visible
- Confirmation flows for critical actions
- Voice guidance for moderate/advanced stages

### Progressive Simplification
- UI adapts to cognitive ability
- Reduces complexity for advanced dementia
- Maintains dignity and independence
- Evidence-based design patterns

---

## 🚀 Start Developing

```bash
# Quick start with Docker
./FIX-DOCKER-AND-START.sh

# Or see QUICKSTART.md for manual mode
```

**Then visit:** http://localhost:4100

**Test your compassionate, accessible, stage-adaptive design system!** 🎉

---

**For detailed setup instructions, see: DOCKER-INSTRUCTIONS.md**

**For design system documentation, see: DESIGN.md**

**For troubleshooting, see: TROUBLESHOOTING.md**

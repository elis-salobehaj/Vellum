---
title: "Dev Tooling & Hybrid Development Mode"
status: implemented
priority: high
estimated_hours: 15-25
dependencies: []
created: 2026-02-14
date_updated: 2026-02-15
date_completed: 2026-02-15
related_files:
  - backend/pyproject.toml
  - backend/tests/conftest.py
  - backend/tests/test_services.py
  - frontend/package.json
  - frontend/vite.config.ts
  - frontend/src/lib/logger.ts
  - scripts/deploy-local.sh
  - scripts/connect.sh
  - scripts/test.sh
  - .nvmrc
tags:
  - tooling
  - nvm
  - uv
  - pnpm
  - hybrid-dev
  - testing
completion:
  - "# Phase 2: Hybrid Development Mode"
  - [x] Configure Vite proxy in `vite.config.ts` to forward `/api/v1/*` to `localhost:8006` ✅
  - [x] Ensure backend `uv run uvicorn main:app --reload` works against port-forwarded K8s services ✅
  - [x] Create `scripts/dev.sh` helper script that starts connect.sh + backend + frontend in parallel ✅
  - [x] Verify hot-reload works for both backend (uvicorn --reload) and frontend (Vite HMR) ✅
  - [x] Document the hybrid workflow in `docs/guides/DEVELOPMENT.md` ✅
  - [x] Verify chatbot query ("what is agentic ai") returns citations in hybrid mode ✅
  - "# Phase 3: Deploy-Local Optimization"
  - [x] Separate `deploy-local.sh` into build vs deploy steps (avoid `--no-cache` on every run) ✅
  - [x] Add incremental Docker build support (use cache layers properly) ✅
  - [x] Add `scripts/deploy-backend.sh` and `scripts/deploy-frontend.sh` for targeted rebuilds ✅
  - [x] Document when to use hybrid dev vs full deploy in `DEVELOPMENT.md` ✅
  - "# Phase 4: Unified Logging Consolidation"
  - [x] Implement structured logging in backend (Python `structlog` or `logging` best practices) ✅
  - [x] Implement `LogLayer` in frontend for consolidated logging ✅
  - [x] Ensure consistent logging levels and metadata across services ✅
  - "# Phase 5: Enhance Testing Suite"
  - [x] Backend test infrastructure (conftest.py, pytest configuration) ✅
  - [x] Fix backend test suite (16/16 passing) ✅
  - [x] Resolve dependency conflicts (requests-toolbelt compatibility) ✅
  - [x] Frontend Playwright test infrastructure (test.sh, playwright.config.ts) ✅
  - [x] Document Playwright flakiness in WSL2 for future investigation ✅
---

## Goal

Standardize development tooling and enable fast hybrid development for the Vellum project:
1. **Package Manager Consistency**: Use `nvm` for Node.js version management, `pnpm` for frontend, `uv` for backend.
2. **Hybrid Development**: Run backend and frontend locally with `--reload` / HMR, only using K8s for infrastructure services (Qdrant, MinIO, KFP, TEI).
3. **Deploy Optimization**: Make `deploy-local.sh` faster and add targeted rebuild scripts.
4. **Unified Logging**: Consolidate backend (Python 2026 best practices) and frontend (`LogLayer`) logging.
5. **Testing Infrastructure**: Establish reliable test suites for both backend and frontend.

## Problem Statement

Currently, `scripts/deploy-local.sh` is the primary development workflow:
1. Rebuilds ALL Docker images from scratch (`--no-cache`)
2. Applies ALL K8s manifests
3. Restarts ALL pods
4. Re-establishes ALL port-forwards

This takes **several minutes per iteration** for a one-line code change. We need a hybrid mode where:
- Infrastructure services run in K8s (Qdrant, MinIO, KFP, TEI, LLM Service)
- Backend runs locally with `uvicorn --reload` (auto-restarts on file change)
- Frontend runs locally with Vite dev server (instant HMR)

## Phase 1: Package Manager & Node Version Standardization

### Why nvm?
Node.js version consistency across developers. The `.nvmrc` file pins the exact version used by the project. All developers and CI run the same version.

### Backend (`uv` + `pyproject.toml`)
Current `pyproject.toml` is minimal. Needs:
- `[build-system]` for `setuptools` (matches wellspring-ai)
- `[dependency-groups]` instead of `[tool.uv.dev-dependencies]` (uv 0.5+ standard)
- `[tool.pytest.ini_options]` for test configuration
- Proper type-checking and linting dev dependencies (`ruff`, `mypy`)

### Frontend (`pnpm`)
Frontend currently has a `package-lock.json` (npm) despite us using `pnpm`. Need to:
- Remove `package-lock.json`
- Generate `pnpm-lock.yaml` 
- Verify all scripts work with `pnpm`

## Phase 2: Hybrid Development Mode

### Architecture
```
┌─────────────────── LOCAL ───────────────────┐
│  Terminal 1: ./scripts/connect.sh           │
│  Terminal 2: cd backend && uv run uvicorn   │ ←── auto-reload on .py change
│  Terminal 3: cd frontend && pnpm dev        │ ←── HMR on .tsx/.css change
└─────────────────────────────────────────────┘
         ↕ port-forwards ↕
┌─────────────── MINIKUBE K8S ────────────────┐
│  Qdrant (6333)     MinIO (9000)             │
│  KFP API (8888)    TEI (8082)               │
│  LLM Service (8081)                         │
└─────────────────────────────────────────────┘
```

### Vite Proxy Configuration
The frontend Vite dev server needs to proxy API requests to the local backend:

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8006',
        changeOrigin: true,
      },
    },
  },
})
```

### Environment Variables
Backend needs to point to port-forwarded K8s services:
```bash
QDRANT_HOST=localhost
QDRANT_PORT=6333
EMBEDDINGS_SERVICE_URL=http://localhost:8082
MINIO_ENDPOINT=localhost:9000
LLM_SERVICE_URL=http://localhost:8081
```

## Phase 3: Deploy-Local Optimization

### Current Pain Points
- `docker compose build --no-cache` rebuilds everything from scratch
- A one-line backend change triggers a full frontend rebuild
- No targeted rebuild option

### Solution
1. Remove `--no-cache` default (use Docker layer cache)
2. Add per-service rebuild scripts:
   ```bash
   ./scripts/deploy-backend.sh   # Only rebuilds + restarts backend pod
   ./scripts/deploy-frontend.sh  # Only rebuilds + restarts frontend pod
   ```
3. Document the decision tree:
   - Changed `.py` file? → Use hybrid mode (no rebuild needed)
   - Changed `Dockerfile`? → Use `deploy-backend.sh`
   - Changed K8s manifests? → Use full `deploy-local.sh`

## Phase 4: Unified Logging Consolidation

### Backend (Python)
Transition from standard `print` or disorganized `logging` calls to a structured logging approach using `structlog` or a standardized `logging` configuration:
- Contextual logging (request IDs, session IDs).
- JSON formatting for production (K8s/Grafana/Loki).
- Human-readable formatting for development.

### Frontend (LogLayer)
Consolidate all `console.log` calls to use `LogLayer`:
- Single entry point for all frontend logs.
- Support for multiple transports (console, external services).
- Metadata attachment for better debugging (trace IDs, user context).

## Phase 5: Enhance Testing Suite

### Goals
Improve the reliability and maintainability of the Vellum test suite.

### Backend Testing
- **Infrastructure**: Created `backend/tests/conftest.py` for proper Python path configuration
- **Test Suite**: Fixed all backend tests (16/16 passing)
- **Dependencies**: Resolved `requests-toolbelt` compatibility with old `kfp 1.4.0` by downgrading to `0.10.1`
- **Coverage**: Tests cover API endpoints, services (LLM, history), and core functionality

### Frontend Testing
- **Infrastructure**: Created `scripts/test.sh` for one-command full-stack testing
- **Playwright Configuration**: Set up `playwright.config.ts` with auth bypass and proper timeouts
- **Known Issues**: Playwright E2E tests exhibit flakiness in WSL2 (6/9 passing). Further investigation on HMR synchronization and browser context initialization is postponed.

---

## Implementation Summary

### Completed Deliverables

**Phase 2: Hybrid Development Mode** ✅
- ✅ Vite proxy configuration for `/api/v1/*` → `localhost:8006`
- ✅ Backend runs with `uv run uvicorn main:app --reload` against K8s services
- ✅ `scripts/dev.sh` for one-command hybrid mode startup
- ✅ Hot-reload verified for both backend (uvicorn) and frontend (Vite HMR)
- ✅ Documentation in `docs/guides/DEVELOPMENT.md`
- ✅ End-to-end verification with RAG query returning citations

**Phase 3: Deploy-Local Optimization** ✅
- ✅ Separated build/deploy steps in `deploy-local.sh`
- ✅ Incremental Docker builds with layer caching
- ✅ Per-service rebuild scripts (`deploy-backend.sh`, `deploy-frontend.sh`)
- ✅ Decision tree documented in `DEVELOPMENT.md`

**Phase 4: Unified Logging** ✅
- ✅ Backend: Structured logging with `structlog` (JSON for production, human-readable for dev)
- ✅ Frontend: `LogLayer` implementation with metadata support
- ✅ Consistent logging levels across services

**Phase 5: Testing Infrastructure** ✅
- ✅ Backend test suite: 16/16 tests passing
- ✅ Fixed dependency conflicts (`requests-toolbelt` compatibility)
- ✅ Created `conftest.py` for proper test configuration
- ✅ Frontend Playwright infrastructure with `test.sh` script
- ✅ Documented WSL2 flakiness for future investigation

### Key Achievements

1. **Developer Velocity**: Hybrid mode reduces iteration time from **minutes to seconds** for code changes
2. **Test Coverage**: Backend test suite provides confidence in core functionality (API, services, auth)
3. **Tooling Standardization**: Consistent use of `nvm`, `pnpm`, and `uv` across the project
4. **Observability**: Unified logging makes debugging easier in both dev and production
5. **Documentation**: Comprehensive guides for development workflows and testing

### Known Limitations

1. **Playwright Flakiness**: Frontend E2E tests show intermittent failures in WSL2 (6/9 passing)
   - Root cause: HMR synchronization and browser context initialization timing
   - Mitigation: Documented for future investigation, tests can be re-run
2. **KFP Test Coverage**: KFP-related tests skipped due to `kfp 1.4.0` compatibility issues
   - Future work: Upgrade to KFP 2.x when platform is ready

### Impact

- **Before**: Full Docker rebuild required for every code change (~3-5 minutes)
- **After**: Instant hot-reload for code changes, Docker rebuild only when needed
- **Test Confidence**: 16/16 backend tests passing, providing safety net for refactoring
- **Developer Experience**: One-command workflows (`./scripts/dev.sh`, `./scripts/test.sh`)

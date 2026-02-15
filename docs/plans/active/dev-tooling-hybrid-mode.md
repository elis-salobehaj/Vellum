---
title: "Dev Tooling & Hybrid Development Mode"
status: active
priority: high
estimated_hours: 15-25
dependencies: []
created: 2026-02-14
date_updated: 2026-02-14
related_files:
  - backend/pyproject.toml
  - frontend/package.json
  - frontend/vite.config.ts
  - scripts/deploy-local.sh
  - scripts/connect.sh
  - .nvmrc
tags:
  - tooling
  - nvm
  - uv
  - pnpm
  - hybrid-dev
completion:
  - "# Phase 1: Package Manager & Node Version Standardization"
  - [ ] Add `.nvmrc` with `24.13.0` to project root (matching wellspring-ai)
  - [ ] Install nvm and configure `nvm use` in project setup
  - [ ] Update `backend/pyproject.toml` with proper `[build-system]`, `[tool.setuptools]`, `[tool.pytest.ini_options]`, and `[dependency-groups]` sections (matching wellspring-ai patterns)
  - [ ] Ensure `uv sync` and `uv run` work for all backend commands
  - [ ] Migrate frontend from `npm` to `pnpm` properly (remove `package-lock.json`, ensure `pnpm-lock.yaml` exists)
  - [ ] Verify `pnpm install` and `pnpm dev` work cleanly
  - [ ] Update all documentation references from `npm` → `pnpm` and `pip` → `uv`
  - "# Phase 2: Hybrid Development Mode"
  - [ ] Configure Vite proxy in `vite.config.ts` to forward `/api/v1/*` to `localhost:8000`
  - [ ] Ensure backend `uv run uvicorn main:app --reload` works against port-forwarded K8s services
  - [ ] Create `scripts/dev.sh` helper script that starts connect.sh + backend + frontend in parallel
  - [ ] Verify hot-reload works for both backend (uvicorn --reload) and frontend (Vite HMR)
  - [ ] Document the hybrid workflow in `docs/guides/DEVELOPMENT.md`
  - "# Phase 3: Deploy-Local Optimization"
  - [ ] Separate `deploy-local.sh` into build vs deploy steps (avoid `--no-cache` on every run)
  - [ ] Add incremental Docker build support (use cache layers properly)
  - [ ] Add `scripts/deploy-backend.sh` and `scripts/deploy-frontend.sh` for targeted rebuilds
  - [ ] Document when to use hybrid dev vs full deploy in `DEVELOPMENT.md`
---

## Goal

Standardize development tooling and enable fast hybrid development for the Vellum project:
1. **Package Manager Consistency**: Use `nvm` for Node.js version management, `pnpm` for frontend, `uv` for backend.
2. **Hybrid Development**: Run backend and frontend locally with `--reload` / HMR, only using K8s for infrastructure services (Qdrant, MinIO, KFP, TEI).
3. **Deploy Optimization**: Make `deploy-local.sh` faster and add targeted rebuild scripts.

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
        target: 'http://localhost:8000',
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

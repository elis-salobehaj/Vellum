# Development Guide

## Running the Stack

### ⚡ Hybrid Development (Recommended)
Run backend and frontend locally against the Kubernetes cluster. This is the fastest iteration mode — no Docker rebuilds needed.

**Option A: Single Command (Automatic)**
```bash
./scripts/dev.sh
```
This script handles `./scripts/connect.sh --hybrid`, `uvicorn --reload`, and `pnpm dev` in a single terminal.

**Option B: Manual Control (Multiple Terminals)**

1. **Terminal 1: Infrastructure**
   ```bash
   ./scripts/connect.sh --hybrid
   ```
2. **Terminal 2: Backend**
   ```bash
   cd backend && uv run uvicorn main:app --reload
   ```
3. **Terminal 3: Frontend**
   ```bash
   cd frontend && pnpm dev
   ```

> **Tip**: Use Vite's dev server (port 5173) for hot-reload during development. The Kubernetes frontend pod (port 9090) is the production Nginx build.

### 🐳 Full Kubernetes Deploy
For testing the full production-like stack in Minikube:

```bash
./scripts/deploy-local.sh
```

This script builds Docker images, applies K8s manifests, and restarts pods. Use this when:
- Testing Kubernetes-specific behavior (Istio routing, namespace isolation)
- Validating Docker images before push
- **Not** for rapid iteration — use hybrid development instead

---

## Critical Commands

### Platform Operations
```bash
# Bootstrap entire platform (Kubeflow + Qdrant + Istio)
./scripts/setup-platform.sh

# Recommended: Start hybrid dev (includes connect.sh --hybrid)
./scripts/dev.sh

# Port-forward all services (including K8s backend/frontend)
./scripts/connect.sh

# Full redeploy (Docker build + K8s apply + pod restart)
./scripts/deploy-local.sh

# Nuclear option: wipe everything
./scripts/nuke-kubeflow.sh
```

### Backend
```bash
# Install dependencies
cd backend && uv sync

# Run dev server
uv run uvicorn main:app --reload

# Run tests
uv run pytest tests/
```

### Frontend
```bash
# Install dependencies
cd frontend && pnpm install

# Run dev server (hot-reload on port 5173)
pnpm dev

# Build for production
pnpm build

# Lint
pnpm lint

# Run Playwright E2E tests
pnpm test
```

### Testing

**Backend Tests**
```bash
cd backend

# Run all tests
uv run pytest -v

# Run specific test file
uv run pytest tests/test_api.py -v

# Run with coverage
uv run pytest --cov=app --cov-report=html
```

**Frontend Tests**
```bash
cd frontend

# Run Playwright E2E tests
pnpm test

# Run tests with UI
pnpm test --ui

# Run specific test file
pnpm test tests/chat.spec.ts
```

**Full Stack Tests** (from project root)
```bash
# Runs backend + frontend E2E tests
./scripts/test.sh --reporter=list
```

> **Note**: Playwright tests may exhibit flakiness in WSL2 environments. If tests fail intermittently, try running them again or use `--retries=2`.

### Ingestion Pipeline
```bash
# Trigger via API
curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"bucket": "documents", "cleanup": true}'

# Or submit directly to KFP
uv run kubeflow/pipelines/ingestion/submit_run.py --chunk_size 256 --chunk_overlap 50

# Verify retrieval quality
uv run scripts/verify_retrieval.py
```

### Kubernetes Debugging
```bash
# Check pod status
kubectl get pods -n kubeflow
kubectl get pods -n kubeflow-vellum
kubectl get pods -n qdrant

# View logs for a specific pod
kubectl logs -n kubeflow-vellum <pod-name> -f

# Restart Vellum pods (picks up new images after deploy-local.sh)
kubectl rollout restart deployment -n kubeflow-vellum

# Restart platform pods (fixes cert issues)
kubectl rollout restart deployment -n kubeflow
```

---

## Port Reference

| Service | Port | URL | Source |
|---------|------|-----|--------|
| **Frontend (dev)** | 5173 | http://localhost:5173 | `pnpm dev` |
| **Frontend (K8s)** | 9090 | http://localhost:9090 | K8s port-forward |
| **Backend API** | 8000 | http://localhost:8000/docs | K8s port-forward |
| **Kubeflow Dashboard** | 8080 | http://localhost:8080 | Istio Ingress |
| **KFP API** | 8888 | http://localhost:8888 | K8s port-forward |
| **MinIO** | 9000 | http://localhost:9000 | K8s port-forward |
| **Qdrant** | 6333 | http://localhost:6333 | K8s port-forward |
| **Embeddings (TEI)** | 8082 | http://localhost:8082 | K8s port-forward |
| **LLM Service** | 8081 | http://localhost:8081 | K8s port-forward |

---

## Authentication

### Dashboard Access
- **URL**: http://localhost:8080
- **Credentials**: `vellum@example.com` / `12341234`

### Bypass Auth for Development
Set in `.env`:
```bash
BYPASS_AUTH=True
VITE_BYPASS_AUTH=true
```

See [Authentication Guide](AUTHENTICATION.md) for full details.

---

## Troubleshooting

### Backend won't start
- **Check cluster**: `minikube status` — is the cluster running?
- **Check port-forwards**: Did you run `./scripts/connect.sh`?
- **Sync dependencies**: `cd backend && uv sync`

### "Connection Refused" errors
- Ensure you ran `./scripts/connect.sh` to establish port-forwards to MinIO, Qdrant, etc.

### Pipeline submission fails
- Verify KFP is running: `kubectl get pods -n kubeflow | grep ml-pipeline`
- Check the KFP API at http://localhost:8888

### "401 Unauthorized" in Kubeflow
- KFP requires `kubeflow-userid` header (handled automatically by the backend)
- For Dashboard access, use credentials: `vellum@example.com` / `12341234`

### Frontend proxy not reaching backend
- Ensure backend is running on port 8000 (`uv run uvicorn main:app --reload`)
- Check `vite.config.ts` for proxy configuration

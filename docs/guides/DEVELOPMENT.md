# Development Guide

## Running the Stack

Completed Phase 1 baseline: use the Kind-hosted slim platform, run backend and frontend locally when possible, and treat `INGESTION_MODE=direct` as the default ingestion contract unless you are specifically debugging Kubeflow.

### Phase 1 Local Topology

```text
┌──────────────────────── Local Machine ────────────────────────┐
│ frontend: pnpm dev (5173)                                    │
│ backend: uvicorn (8006)                                      │
│ kubectl port-forward: dashboard, KFP, Qdrant, TEI, MinIO     │
└──────────────────────────────┬───────────────────────────────┘
                               │
                        ~/.kube/config
                               │
┌──────────────────────────── Kind cluster ─────────────────────┐
│ slim Kubeflow v1.11.0 overlay                                │
│ Istio + Dex + oauth2-proxy + KFP + KServe + MinIO            │
│ qdrant namespace + kubeflow-vellum namespace                 │
│ TEI + backend/frontend workloads + optional local LLM        │
└───────────────────────────────────────────────────────────────┘
```

### Hybrid Development (Recommended)
Run backend and frontend locally against the Kind cluster. This avoids Docker rebuilds during normal feature work.

Completed Phase 1 local default:
- `INGESTION_MODE=direct` bypasses KFP/MLMD and ingests from MinIO straight into Qdrant. Use this for day-to-day local development until the Kubeflow metadata path is no longer on the critical path.
- `INGESTION_MODE=kfp` keeps the original Kubeflow Pipelines submission path and is only needed when you are explicitly debugging KFP itself.

#### Option A: Standard Hybrid Workflow
1. Terminal 1:
   ```bash
   ./scripts/dev.sh
   ```
   This runs `./scripts/connect.sh --hybrid` and then starts the backend with `KFP_NAMESPACE=kubeflow-vellum` inside the backend's `uv` environment.

2. Terminal 2:
   ```bash
   cd frontend
   pnpm dev
   ```

Use this mode when you are iterating on FastAPI handlers, React code, prompt wiring, or KFP trigger logic.

#### Option B: Manual Hybrid Workflow
1. Terminal 1:
   ```bash
   ./scripts/connect.sh --hybrid
   ```
2. Terminal 2:
   ```bash
   cd backend
   KFP_NAMESPACE=kubeflow-vellum uv run uvicorn main:app --reload --reload-dir app --host 0.0.0.0 --port 8006
   ```
   Add `INGESTION_MODE=kfp` only when you want to exercise the Kubeflow Pipelines path. The normal local fallback is `INGESTION_MODE=direct` from `.env`.
3. Terminal 3:
   ```bash
   cd frontend
   pnpm dev
   ```

### Full Kubernetes Deploy
Use this when you need the backend and frontend running as cluster workloads instead of local processes.

```bash
./scripts/deploy-local.sh
```

This Phase 1 deploy path:
- builds local images with Docker Compose
- loads backend, frontend, and ingestion images directly into Kind with `kind load docker-image`
- syncs the `vellum-env` secret from `.env`
- applies the Vellum app workload manifests without reapplying the full platform stack
- restarts backend/frontend workloads
- scales the KServe predictor according to `ENABLE_LOCAL_LLM`

For Phase 1 Kind runs:
- bootstrap with `./scripts/setup-kind.sh`
- switch to the merged context with `kubectl config use-context vellum` before `./scripts/deploy-local.sh`
- `./scripts/setup-kind.sh` automatically moves off `6551` when that local port is already occupied by another service
- the deploy scripts load local backend, frontend, and ingestion images directly into the Kind cluster

If the cluster does not advertise `nvidia.com/gpu`, the deploy helper scales the predictor back to zero and leaves the rest of the stack running.

On this WSL Docker setup, Kind node startup requires Docker's `default-runtime` to remain `runc`.

This host also needs `fs.inotify.max_user_instances>=1024` for Kind node boot. If `./scripts/setup-kind.sh` fails with `Failed to create control group inotify object: Too many open files`, raise that sysctl and rerun the bootstrap.

Use this for:
- validating image startup inside Kubernetes
- checking Istio/Dex/KServe/KFP interactions end to end
- testing the cluster-side frontend or backend

Do not use it for rapid iteration if hybrid mode is sufficient.

## Critical Commands

### Platform Operations
```bash
# Bootstrap the Kind Phase 1 platform
./scripts/setup-kind.sh

# One-shot first-time setup from a clean machine
./scripts/setup-local.sh

# Compatibility wrapper for the same action
./scripts/setup-platform.sh

# Start hybrid dev
./scripts/dev.sh

# Port-forward cluster services
./scripts/connect.sh

# Build, push, sync secret, and redeploy
./scripts/deploy-local.sh

# Sync the Kubernetes secret only
./scripts/sync-env-secret.sh

# Destroy the local platform runtime
./scripts/nuke-platform.sh
```

### Backend
```bash
cd backend && uv sync
uv run uvicorn main:app --reload
uv run pytest tests/
```

### Frontend
```bash
cd frontend && pnpm install
pnpm dev
pnpm build
pnpm lint
pnpm test
```

### Testing
Backend:
```bash
cd backend
uv sync --group dev
uv run pytest -v
uv run pytest tests/test_api.py -v
uv run pytest --cov=app --cov-report=html
```

Frontend:
```bash
cd frontend
pnpm test
pnpm test --ui
pnpm test tests/chat.spec.ts
```

Full stack:
```bash
./scripts/test.sh --reporter=list
```

### Ingestion Pipeline
```bash
# Trigger via the backend API on the active local backend (port 8006)
curl -X POST http://localhost:8006/api/v1/admin/upload-and-ingest \
   -H "kubeflow-userid: vellum@example.com"

# Watch resumable direct-ingestion progress and recent skipped files
curl http://localhost:8006/api/v1/admin/ingestion-status \
   -H "kubeflow-userid: vellum@example.com" | jq

# Force a clean-slate reindex only when you intentionally want to discard
# existing chunks and rebuild the collection from scratch.
curl -X POST "http://localhost:8006/api/v1/admin/upload-and-ingest?cleanup=true&reset_progress=true" \
   -H "kubeflow-userid: vellum@example.com"

# Submit directly to KFP only when INGESTION_MODE=kfp
uv run kubeflow/pipelines/ingestion/submit_run.py --chunk_size 256 --chunk_overlap 50

# Rebuild and republish the ingestion image only
./kubeflow/pipelines/ingestion/scripts/rebuild-ingestion.sh
```

Important Phase 1 note:
- A backend running inside the cluster does not mount the repo-local `data/source_documents` directory. For full-cluster ingestion verification, seed MinIO first and then call `/api/v1/admin/upload-and-ingest`, or use the hybrid local-backend workflow when you want the backend to read files directly from the repo checkout.
- The admin ingestion route now checks both the repo checkout path and `/data/source_documents`, so cluster-side runs can use manually staged pod data when present.
- `cleanup=true` means "start from a clean slate": delete and recreate the Qdrant collection before ingesting, which discards any existing chunks.
- `reset_progress=true` means "start scanning from the top again": ignore the saved `last_scanned_key` checkpoint and restart bucket traversal from the beginning.
- `cleanup=true` already implies a fresh scan in the current implementation, so `cleanup=true&reset_progress=true` is the most explicit full rebuild form rather than two unrelated toggles.
- Direct ingestion is append-or-replace by default: unchanged files are skipped, changed files replace their own prior chunks, and the collection is only cleared when you explicitly pass `cleanup=true`.
- Do not trigger a second direct-ingestion run while `status=running`; the backend now rejects concurrent runs for the same bucket/prefix to avoid overlapping progress and misleading unchanged detections.
- Progress is visible in two places: the streaming response from `/api/v1/admin/upload-and-ingest` and the persisted status payload from `/api/v1/admin/ingestion-status` (`current_file`, `last_scanned_key`, `indexed_source_doc_count`, `recent_skipped_files`, and `last_run_summary`).

### Kubernetes Debugging
```bash
kubectl config use-context vellum

kubectl get pods -n kubeflow
kubectl get pods -n kubeflow-vellum
kubectl get pods -n qdrant

kubectl logs -n kubeflow-vellum <pod-name> -f
kubectl rollout restart deployment -n kubeflow-vellum
kubectl rollout restart deployment -n kubeflow
```

## Port Reference

| Service | Port | URL | Source |
|---------|------|-----|--------|
| **Frontend (dev)** | 5173 | http://localhost:5173 | `pnpm dev` |
| **Frontend (K8s)** | 9090 | http://localhost:9090 | `./scripts/connect.sh` |
| **Backend API** | 8006 | http://localhost:8006/docs | local `uvicorn` in hybrid mode or `./scripts/connect.sh` in cluster mode |
| **Kubeflow Dashboard** | 8086 | http://localhost:8086 | Istio ingress port-forward |
| **LLM Service** | 8081 | http://localhost:8081 | Only when `ENABLE_LOCAL_LLM=true` |
| **Embeddings (TEI)** | 8082 | http://localhost:8082 | `./scripts/connect.sh` |
| **KFP API** | 8888 | http://localhost:8888 | `./scripts/connect.sh` |
| **Ray Dashboard** | 8265 | http://localhost:8265 | `./scripts/connect.sh` |
| **MinIO** | 9000 | http://localhost:9000 | `./scripts/connect.sh` |
| **Qdrant** | 6333 | http://localhost:6333 | `./scripts/connect.sh` |

Port rule of thumb:
- `8006` is always the backend API for local development. In hybrid mode it is the local `uvicorn` process. In full cluster mode it is the port-forwarded backend service.
- `8082` is the local port-forward for embeddings/TEI.
- `8888` is the local port-forward for the KFP API. If you are using `INGESTION_MODE=direct`, the app does not need KFP to ingest documents.
- Those ports are the preferred defaults. If any of them are already in use, `./scripts/connect.sh` picks the next free localhost port and writes the actual bindings to `.vellum-runtime.env` for the hybrid scripts to consume.

## Authentication

### Kubeflow Dashboard
- URL: http://localhost:8086
- Credentials: `vellum@example.com` / `12341234`

### Bypass App Auth for Local UI Work
Set in `.env`:
```bash
BYPASS_AUTH=True
VITE_BYPASS_AUTH=true
```

See [Authentication Guide](AUTHENTICATION.md) for the full split between Entra ID and Dex.

## Troubleshooting

### Backend Won't Start
- Check the active context: `kubectl config current-context`
- Check cluster access: `kubectl cluster-info`
- Check port-forwards: rerun `./scripts/connect.sh --hybrid`
- Sync backend deps: `cd backend && uv sync`

### `./scripts/deploy-local.sh` Fails Before Apply
- Ensure `docker info` succeeds.
- Ensure the `deployment/manifests` submodule is initialized.
- If `.env` changed, rerun `./scripts/sync-env-secret.sh` directly to isolate secret issues.

### Pipeline Submission Fails
- Verify KFP is running: `kubectl get pods -n kubeflow | grep ml-pipeline`
- Check the KFP API at http://localhost:8888
- Ensure the ingestion image exists in the local registry by rebuilding it if necessary.

### Local LLM Is Disabled but the App Still Tries `localhost:8081`
- If `ENABLE_LOCAL_LLM=false`, switch the active model provider away from the local KServe model in your config or admin UI.
- `./scripts/connect.sh` intentionally skips the `8081` port-forward when the local LLM is disabled.

### `401 Unauthorized` in Kubeflow
- KFP still relies on the `kubeflow-userid` header for multi-user flows.
- The dashboard still uses Dex credentials in Phase 1.

### Entra ID Issues
- `401 Unauthorized during redirect`: avoid backend routes that add a redirect before auth processing.
- `kid not found`: use the v2.0 common discovery endpoint.
- login loop: ensure the frontend initializes MSAL and calls `handleRedirectPromise()`.

### Ingestion Pipeline Issues
- `FileNotFoundError` for secrets: keep local backend runs pointed at the Vellum Profile namespace, `KFP_NAMESPACE=kubeflow-vellum`.
- `ModuleNotFoundError` from the local ingestion pipeline: run `uv sync` in `backend` so the editable local pipeline dependency is installed in the `uv` environment.
- old image reference: rebuild/push the ingestion image if KFP is still using a stale cached tag.
- If local ingestion is blocked by MLMD or KFP metadata instability, set `INGESTION_MODE=direct` and rerun the admin upload-and-ingest flow to populate Qdrant without Kubeflow Pipelines.

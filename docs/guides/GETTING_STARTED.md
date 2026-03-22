# Getting Started

Welcome to Vellum — an enterprise-grade RAG chatbot platform. This guide gets you from zero to a running local cluster.

> **Phase 4 (current):** Kubeflow, Dex, MinIO, and KFP are gone.
> The platform is now: **Kind + Istio Ambient + Qdrant + Dagster + Ray Serve**.
> Total resource footprint is significantly lighter than the Phase 1 Kubeflow stack.

---

## Prerequisites

### Required Tools

| Tool | Install | Notes |
|---|---|---|
| **Docker Engine** | [docs.docker.com](https://docs.docker.com/get-docker/) | Docker Desktop works too |
| **Kind** | [kind.sigs.k8s.io](https://kind.sigs.k8s.io/) | `v0.24+` recommended |
| **kubectl** | [kubernetes.io](https://kubernetes.io/docs/tasks/tools/) | |
| **Helm** | [helm.sh](https://helm.sh/docs/intro/install/) | `v3.16+` |
| **istioctl** | [istio.io/docs/setup/install/istioctl/](https://istio.io/docs/setup/install/istioctl/) | Must match Istio version in cluster |
| **Python 3.12+** | [python.org](https://python.org) | `uv` recommended for backend |
| **Node.js 24 LTS** | [nodejs.org](https://nodejs.org) | |
| **pnpm** | `corepack enable` | After Node install |
| **Git** | | |

### Resource Requirements

| Resource | Minimum | Recommended |
|---|---|---|
| **RAM** | **8 GB** | **16 GB** |
| **CPUs** | **4 cores** | **8 vCPUs** |
| **Disk** | **20 GB** | **40 GB** |
| **GPU** | Optional | NVIDIA GPU for local LLM |

> Phase 4 is significantly lighter than Phase 1. Kubeflow, Dex, MinIO, Cert-Manager and oauth2-proxy are gone.

### WSL2 Configuration (Windows)

1. Ensure NVIDIA drivers are installed on Windows (for GPU passthrough if needed).
2. In Docker Desktop → Settings → Resources → WSL Integration: enable for your distro.
3. Optional GPU verification: `docker run --rm --gpus all ubuntu nvidia-smi`

Host sysctl prerequisites for Kind:
```bash
sudo sysctl -w fs.inotify.max_user_instances=1024
echo 'fs.inotify.max_user_instances = 1024' | sudo tee /etc/sysctl.d/99-vellum-kind.conf
```

---

## Quick Start

### 1. Clone and enter the repo
```bash
git clone <repo-url>
cd Vellum
```

### 2. First-time machine setup
```bash
./scripts/setup-local.sh
```
This installs system-level tools (kind, kubectl, helm, istioctl). Safe to re-run.

### 3. Bootstrap the cluster
```bash
./scripts/setup-kind.sh
```
This will:
- Create the Kind cluster (if not already running)
- Install **Istio Ambient** via `istioctl install --set profile=ambient`
- Install **Qdrant** via Helm into the `qdrant` namespace
- Install **Dagster** via Helm into the `dagster` namespace
- Apply Vellum application resources (namespace, RBAC, PVC)
- Apply the full Vellum k8s stack via Kustomize

> ⏱ First run takes ~10-15 minutes (image pulls). Subsequent runs are much faster.

### 4. Install dependencies
```bash
cd backend && uv sync
cd ../frontend && pnpm install
```

### 5. Configure environment
```bash
cp .env.example .env
# Edit .env — at minimum set AZURE_CLIENT_ID and AZURE_TENANT_ID
```

### 6. Start port-forwards
```bash
./scripts/connect.sh
```
Port bindings are written to `.vellum-runtime.env` (auto-detected by the backend in hybrid mode).

### 7. Start local dev servers (hybrid mode)
In separate terminals:
```bash
cd backend && uv run uvicorn main:app --reload --port 8000
cd frontend && pnpm dev
```

Then open: [http://localhost:5173](http://localhost:5173)

---

## Environment Variables

Key variables in `.env`:

| Variable | Default | Description |
|---|---|---|
| `AZURE_CLIENT_ID` | — | Entra ID App Client ID (required) |
| `AZURE_TENANT_ID` | — | Entra ID Tenant ID (required) |
| `BYPASS_AUTH` | `false` | Set `true` for local dev without Entra ID |
| `INGESTION_MODE` | `direct` | `direct` (sync PVC) or `dagster` (async job) |
| `USE_S3_STORAGE` | `false` | `true` to use S3 instead of local PVC |
| `DOCUMENT_STORAGE_PATH` | `./data/source_documents` | Local document directory (PVC path in cluster) |
| `EMBEDDINGS_SERVICE_URL` | `http://localhost:8082/v1` | TEI embeddings endpoint |
| `DAGSTER_GRAPHQL_URL` | `http://localhost:3200/graphql` | Dagster UI GraphQL (port-forwarded) |
| `ENABLE_LOCAL_LLM` | `false` | Enable Ray Serve / vLLM inference |
| `LLM_SERVICE_URL` | `http://localhost:8081/v1` | Ray Serve endpoint (port-forwarded) |

---

## Port Reference

`connect.sh` dynamically allocates ports. Stable defaults after the standard Kind cluster bootstrap:

| Service | Default Port | URL |
|---|---|---|
| Frontend (cluster) | 9090 | http://localhost:9090 |
| Frontend (hybrid dev) | 5173 | http://localhost:5173 |
| Backend (hybrid dev) | 8000 | http://localhost:8000 |
| Backend (cluster) | 8006 | http://localhost:8006 |
| Istio Ingress | 8086 | http://localhost:8086 |
| Embeddings (TEI) | 8082 | http://localhost:8082/v1 |
| Dagster UI | 3200 | http://localhost:3200 |
| Qdrant | 6333 | http://localhost:6333 |
| Ray Dashboard | 8265 | http://localhost:8265 |
| Ray Serve LLM | 8081 | http://localhost:8081/v1 |

> Actual port bindings are written to `.vellum-runtime.env` by `connect.sh` and automatically read by the backend.

---

## Authentication

- **Local dev with BYPASS_AUTH=true**: no Entra ID required.
- **Full auth**: Entra ID (Azure AD). Configure `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, add redirect URI `http://localhost:8086/` in your App Registration.
- **No Dex/Kubeflow login** — the Kubeflow Central Dashboard and its auth stack are removed.

See [`docs/guides/AUTHENTICATION.md`](AUTHENTICATION.md) for full auth details.

---

## Ingestion

### Direct Ingestion (default, synchronous)
Place documents in `DOCUMENT_STORAGE_PATH` (default: `./data/source_documents/`) and trigger via the Admin UI or:
```bash
curl -X POST http://localhost:8000/api/v1/admin/upload-and-ingest
```
Or upload a file directly:
```bash
curl -X POST http://localhost:8000/api/v1/admin/upload-file \
  -F "file=@/path/to/document.pdf"
```

### Dagster Ingestion (async)
Set `INGESTION_MODE=dagster` to trigger Dagster jobs instead.
The `new_documents_sensor` polls storage every 30 s and fires automatically.
Monitor runs in the Dagster UI: http://localhost:3200

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `istioctl: command not found` | istioctl not installed | `brew install istioctl` or see [istio.io](https://istio.io) |
| Waypoint not ready | CRDs missing | `kubectl apply -f https://...gateway-api.../standard-install.yaml` |
| `ztunnel not running` | Ambient profile not installed | Re-run `istioctl install --set profile=ambient -y` |
| PVC pending | No RWX provisioner on Kind | Set `USE_S3_STORAGE=true` or install NFS provisioner |
| Dagster not reachable | Port-forward not running | `./scripts/connect.sh` |
| `No files found` on ingest | Wrong path | Check `DOCUMENT_STORAGE_PATH` in `.env` |

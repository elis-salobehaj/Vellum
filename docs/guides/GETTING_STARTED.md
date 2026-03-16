# Getting Started

This guide reflects the accepted completed Phase 1 baseline: Kind is the required local runtime, the slim Kubeflow overlay is the default platform boot, and direct ingestion is the normal operator path.

## Prerequisites

### Required Tools
- **Docker Desktop** or Docker Engine reachable from your shell
- **Kind**: [Installation Guide](https://kind.sigs.k8s.io/)
- **kubectl**: [Installation Guide](https://kubernetes.io/docs/tasks/tools/)
- **Helm**: [Installation Guide](https://helm.sh/docs/intro/install/)
- **Git** with submodule support
- **Python 3.12+** for backend and pipeline scripts (`uv` recommended)
- **Node.js 24.13.0+** for frontend development
- **pnpm** via `corepack enable`

### Resource Requirements (Phase 1 Slim Overlay)

| Resource | Minimum | Recommended | Why? |
| :--- | :--- | :--- | :--- |
| **RAM** | **12 GB** | **16-24 GB** | Phase 1 still keeps Istio, Dex, KFP, KServe, MinIO, TEI, and Qdrant, but removes Katib, Jupyter, TensorBoard, PVC Viewer, Volumes UI, and Trainer from the default local boot. |
| **CPUs** | **6 Cores** | **8+ vCPUs** | Kubeflow controllers, Istio ingress, and local model serving still compete for CPU. |
| **Disk** | **40 GB** | **80-100 GB** | Kubeflow images plus the local registry and model downloads are large. |
| **GPU** | Optional | 1 NVIDIA GPU | Required only when using the local KServe-hosted Qwen model. |

### WSL2 Configuration (Windows)

#### Docker Desktop + WSL2 Backend
1. Install current NVIDIA drivers on Windows if GPU passthrough is required.
2. In Docker Desktop, enable `Use the WSL 2 based engine`.
3. In Docker Desktop, enable WSL integration for your Linux distro.
4. Optional GPU check:
    ```bash
    docker run --rm --gpus all ubuntu nvidia-smi
    ```

#### WSL Runtime Note for Kind Node Containers
Keep Docker's default runtime on `runc` for the Kind workflow on this machine.

Required Docker daemon state:
```json
{
    "default-runtime": "runc",
    "runtimes": {
        "nvidia": {
            "path": "nvidia-container-runtime",
            "runtimeArgs": []
        }
    }
}
```

This keeps Kind node startup reliable while still preserving the NVIDIA runtime definition for explicit use later.

Additional WSL host prerequisite observed on this machine:
```bash
sudo sysctl -w fs.inotify.max_user_instances=1024
echo 'fs.inotify.max_user_instances = 1024' | sudo tee /etc/sysctl.d/99-vellum-kind.conf
```

If this value stays at `128`, Kind node containers can exit during boot with `Failed to create control group inotify object: Too many open files`.

#### Recommended `.wslconfig`
Create `%UserProfile%/.wslconfig`:
```ini
[wsl2]
memory=26GB
processors=12
```

Run `wsl --shutdown` after changing it.

## First-Time Setup

### 1. Clone the Repo
```bash
git clone --recursive https://github.com/elis-salobehaj/Vellum.git
cd Vellum
```

If you already cloned without submodules:
```bash
git submodule update --init --recursive deployment/manifests
```

### 2. Create Local Config
```bash
cp .env.example .env
```

Important defaults for Phase 1:
- `ENABLE_LOCAL_LLM=true` keeps the KServe predictor running.
- `ENABLE_LOCAL_LLM=false` scales the local LLM deployment to zero after deploy, which is useful when you are using Bedrock, OpenAI, or Gemini instead.
- If the cluster does not advertise `nvidia.com/gpu` capacity, the deploy scripts automatically scale the local LLM back to zero even when `ENABLE_LOCAL_LLM=true`.
- `./scripts/setup-kind.sh` now treats GPU support as a bootstrap requirement when `ENABLE_LOCAL_LLM=true`: it applies the NVIDIA `RuntimeClass`, deploys the device plugin, and fails fast if the Kind node itself was not created with `/dev/nvidia*` devices.
- `LLM_SERVICE_URL=http://localhost:8081/v1` is only valid when the local LLM is enabled and `./scripts/connect.sh` is forwarding it.

### Local LLM GPU Prerequisites

For local Qwen on Kind, all of the following must be true before the cluster can advertise `nvidia.com/gpu`:

1. The host shell can see the GPU:
    ```bash
    nvidia-smi -L
    ```
2. Docker can launch GPU-enabled containers:
    ```bash
    docker run --rm --gpus all ubuntu nvidia-smi -L
    ```
3. The Kind node container itself must be created with NVIDIA device access so `/dev/nvidia*` exists inside the node.
4. The cluster must have the `nvidia` `RuntimeClass` and NVIDIA device plugin installed.

This repo now automates step 4 during `./scripts/setup-kind.sh`, and it also provisions the Kind node with the NVIDIA runtime handler and host-side NVIDIA user-space files when they are available. If the cluster still cannot advertise stable `nvidia.com/gpu` capacity after that, the remaining problem is in the host/container runtime stack rather than the Vellum manifests.

### 3. Bootstrap the Kind Platform
Primary entrypoint:
```bash
./scripts/setup-kind.sh
```

First-time machine setup from a clean host:
```bash
./scripts/setup-local.sh
```

Compatibility wrapper:
```bash
./scripts/setup-platform.sh
```

What the bootstrap does in Phase 1:
- Validates Docker, `kubectl`, `helm`, and `kind`
- Initializes the `deployment/manifests` submodule if needed
- Creates a `Kind` cluster from `kind-config.yaml`
- Applies the slim Kubeflow Phase 1 manifest set and installs Qdrant
- Merges the cluster into `~/.kube/config`, normalizes the context to `vellum`, and auto-selects a free local API server port when `6551` is already in use

What `./scripts/setup-local.sh` adds on top:
- runs `./scripts/setup-kind.sh`
- runs `cd backend && uv sync`
- runs `cd frontend && pnpm install`
- installs Playwright Chromium for fresh-machine test runs
- runs `./scripts/deploy-local.sh`

### 4. Install App Dependencies
Backend:
```bash
cd backend
uv sync
```

Frontend:
```bash
cd frontend
pnpm install
```

### 5. Build, Push, and Deploy the App
```bash
./scripts/deploy-local.sh
```

This now:
- builds backend, frontend, and ingestion images locally
- loads them directly into the Kind cluster
- syncs the `vellum-env` Kubernetes secret from `.env`
- applies the Vellum app workload manifests on top of the already-bootstrapped platform
- optionally scales the local LLM deployment based on `ENABLE_LOCAL_LLM`

### 6. Connect to Services
```bash
./scripts/connect.sh
```

`./scripts/connect.sh` prefers the standard localhost ports shown below, but if any of them are already taken it automatically picks the next free port and records the live bindings in `.vellum-runtime.env`.

| Service | Local URL | Notes |
| :--- | :--- | :--- |
| **Kubeflow Dashboard** | http://localhost:8086 | Dex login: `vellum@example.com` / `12341234` |
| **Frontend** | http://localhost:9090 | Skipped in hybrid mode |
| **Backend API** | http://localhost:8006/docs | Skipped in hybrid mode |
| **KFP API** | http://localhost:8888 | Direct SDK/API access |
| **Qdrant** | http://localhost:6333 | Vector DB |
| **Embeddings** | http://localhost:8082 | TEI service |
| **MinIO** | http://localhost:9000 | Still used in Phase 1 |
| **LLM Service** | http://localhost:8081 | Only when `ENABLE_LOCAL_LLM=true` |

## Verify Installation

```bash
kubectl config use-context vellum

kubectl get pods -n kubeflow
kubectl get pods -n kubeflow-vellum
kubectl get pods -n qdrant
```

You should expect the slim Phase 1 stack to include:
- Kubeflow Pipelines
- Central Dashboard
- Dex and oauth2-proxy
- Istio ingress
- KServe + Knative
- MinIO
- TEI, backend, frontend, and Qwen model download job

You should not expect the default Phase 1 boot to include:
- Katib
- Jupyter web app or notebook controller
- TensorBoard controller or web app
- PVC Viewer
- Volumes web app
- Trainer

## Troubleshooting

### `kind` Is Missing
Install `kind` first. The Phase 1 bootstrap intentionally fails fast if the runtime is not installed.

### `deployment/manifests` Is Empty
Run:
```bash
git submodule update --init --recursive deployment/manifests
```

The repo should be pinned to Kubeflow manifests `v1.11.0` for Phase 1.

### Docker Is Installed but Unreachable
Make sure `docker info` succeeds in the same shell where you run `./scripts/setup-kind.sh`.

### Local LLM Is Consuming Too Much RAM or GPU
Disable it before deploy:
```bash
ENABLE_LOCAL_LLM=false ./scripts/deploy-local.sh
```

Re-enable it later:
```bash
ENABLE_LOCAL_LLM=true ./scripts/deploy-local.sh
```

### Reset / Uninstall
To destroy the local runtime:
```bash
./scripts/nuke-platform.sh
```

## Next Steps

Continue with:
- **[DEVELOPMENT.md](DEVELOPMENT.md)** for the hybrid workflow and troubleshooting
- **[../context/ARCHITECTURE.md](../context/ARCHITECTURE.md)** for Phase 1 architecture notes
- **[HELLO_WORLD_PIPELINE.md](HELLO_WORLD_PIPELINE.md)** for the KFP programming model

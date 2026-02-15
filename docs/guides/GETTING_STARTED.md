# Getting Started

## Prerequisites

### Required Tools
- **Docker Desktop** (or Docker Engine with WSL2 backend)
- **Minikube**: [Installation Guide](https://minikube.sigs.k8s.io/docs/start/)
- **kubectl**: [Installation Guide](https://kubernetes.io/docs/tasks/tools/)
- **Helm**: [Installation Guide](https://helm.sh/docs/intro/install/)
- **Python 3.12+**: For backend and pipeline scripts (`uv` recommended)
- **Node.js 24.13.0+**: For frontend development
- **pnpm**: Enabled via `corepack enable` (Node.js 24+)

### Resource Requirements

| Resource | Minimum | Recommended | Why? |
| :--- | :--- | :--- | :--- |
| **RAM** | **12 GB** | **24 GB+** | Istio (~4GB), Kubeflow (~4GB), ML workloads (~4GB) |
| **CPUs** | **6 Cores** | **8+ vCPUs**| Service mesh sidecars and multiple controllers need CPU |
| **Disk** | **40 GB** | **100 GB** | Docker images for Kubeflow are large |

### WSL2 Configuration (Windows)

#### Option A: Docker Desktop for Windows (WSL2 Backend)
*Most common setup. You run `docker` in WSL, but it talks to Docker Desktop on Windows.*

1. **Windows**: Install NVIDIA Drivers (if GPU needed).
2. **Docker Desktop Settings**:
   - Settings → General → "Use the WSL 2 based engine": **Checked**.
   - Settings → Resources → WSL Integration → "Ubuntu-24.04": **Toggled ON**.
3. **Verify GPU** (optional):
    ```bash
    docker run --rm --gpus all ubuntu nvidia-smi
    ```

#### WSL Memory Config (`.wslconfig`)
Create `%UserProfile%/.wslconfig`:
```ini
[wsl2]
memory=26GB
processors=12
```
*Run `wsl --shutdown` after creating/editing this file.*

---

## First-Time Setup

### 1. Clone & Initialize
```bash
git clone --recursive https://github.com/elis-salobehaj/Vellum.git
cd Vellum
```

> **Important**: The `--recursive` flag initializes the `deployment/manifests` submodule.

### 2. Start Minikube
```bash
minikube start --cpus 6 --memory 12288 --disk-size=40g --driver=docker
```

> **Note**: 6 CPUs and 12GB RAM are the recommended minimums for the full stack.

### 3. Install Platform
We provide a helper script to install all components in the correct order:
- **Kubeflow Manifests (v1.11.0)**: Core MLOps components (KFP, Katib, Dashboard)
- **Istio**: Service Mesh & Ingress
- **Dex**: OIDC Authentication (`vellum@example.com`)
- **Qdrant**: Vector Database for RAG
- **OAuth2 Proxy**: Dashboard authentication fixes

```bash
./scripts/setup-platform.sh
```

The script will apply the manifests and wait for the Central Dashboard to be ready.

### 4. Connect to Services
Once installation is complete, use the connection helper:

```bash
./scripts/connect.sh
```

| Service | Local URL | Credentials |
| :--- | :--- | :--- |
| **Kubeflow Dashboard** | http://localhost:8080 | `vellum@example.com` / `12341234` |
| **Frontend** | http://localhost:9090 | — |
| **Backend API** | http://localhost:8000/docs | — |
| **MinIO Console** | http://localhost:9001 | — |

### 5. Backend Setup
```bash
cd backend
uv sync
```

### 6. Frontend Setup
```bash
cd frontend
pnpm install
```

---

## Verify Installation

```bash
# Check all pods are running
kubectl get pods -n kubeflow

# Check Qdrant is healthy
kubectl get pods -n qdrant
```

---

## Troubleshooting

### "CrashLoopBackOff" on Initialization
It is normal for some pods (like `ml-pipeline`) to crash/restart a few times during first boot while waiting for MySQL/MinIO to become ready. Kubernetes will auto-heal them.

### "CERTIFICATE_VERIFY_FAILED"
If you see TLS errors in the dashboard, force a restart of platform pods:
```bash
kubectl rollout restart deployment -n kubeflow
```

### Reset / Uninstall
To completely remove the platform (**Destructive**):
```bash
./scripts/nuke-kubeflow.sh
```

---

## Next Steps

You're ready to develop! See:
- **[DEVELOPMENT.md](DEVELOPMENT.md)** for running and debugging
- **[../context/ARCHITECTURE.md](../context/ARCHITECTURE.md)** for code conventions
- **[HELLO_WORLD_PIPELINE.md](HELLO_WORLD_PIPELINE.md)** for your first KFP pipeline

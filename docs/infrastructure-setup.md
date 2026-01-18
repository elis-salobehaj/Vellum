# Infrastructure Setup Guide 🛠️

This guide details how to spin up the Vellum MLOps Platform (Kubeflow + Qdrant) from scratch on a local environment.

## Prerequisites

Before starting, ensure you have the following installed:

1.  **Docker Desktop** (or Docker Engine)
2.  **Minikube**: [Installation Guide](https://minikube.sigs.k8s.io/docs/start/)
3.  **kubectl**: [Installation Guide](https://kubernetes.io/docs/tasks/tools/)
4.  **Helm**: [Installation Guide](https://helm.sh/docs/intro/install/)
5.  **kustomize** (Optional, bundled with kubectl): [Installation Guide](https://kubectl.docs.kubernetes.io/installation/kustomize/)

## 1. Setup Repository

Clone the project and initialize submodules (important for `deployment/manifests`):

```bash
git clone --recursive https://github.com/elis-salobehaj/Vellum.git
cd Vellum
```

### Configuration (`deployment/kustomization.yaml`)
We use a wrapper kustomization file to track your environment-specific changes (e.g. disabling Spark/KServe).
Ensure `deployment/kustomization.yaml` exists. If you are starting fresh, it should be part of the repo.

## 2. Start Minikube

Start a Minikube cluster with sufficient resources (Kubeflow is heavy).

```bash
minikube start --cpus 6 --memory 12288 --disk-size=40g --driver=docker
```

> **Note**: 6 CPUs and 12GB RAM are the recommended minimums for the full stack.

## 3. Install Platform

We provide a helper script to install all components in the correct order:
-   **Kubeflow Manifests (v1.11.0)**: Core MLOps components (KFP, Katib, Dashboard).
-   **Istio**: Service Mesh & Ingress.
-   **Dex**: OIDC Authentication (`user@example.com`).
-   **Qdrant**: Vector Database for RAG.
-   **OAuth2 Proxy**: Fixes for dashboard authentication.

Run the setup script:

```bash
./scripts/setup-platform.sh
```

The script will apply the manifests and wait for the Central Dashboard to be ready.

## 4. Connect to Dashboard

Once installation is complete, use the connection helper to establish port-forwards:

```bash
./scripts/connect.sh
```

Access the UI:
-   **URL**: [http://localhost:8080](http://localhost:8080)
-   **Email**: `user@example.com`
-   **Password**: `12341234`

## Troubleshooting

### "CrashLoopBackOff" on Initialization
It is normal for some pods (like `ml-pipeline`) to crash/restart a few times during first boot while waiting for MySQL/MinIO to become ready. Kubernetes will auto-heal them.

### "CERTIFICATE_VERIFY_FAILED"
If you see TLS errors in the dashboard, the sidecar certificates might be out of sync. Force a restart of the platform pods:

```bash
kubectl rollout restart deployment -n kubeflow
```

### Reset / Uninstall
To completely remove the platform (Destructive):

```bash
./scripts/nuke-kubeflow.sh
```

# Phase 3: Platform Engineering (Kubeflow Upgrade)

## Goal
Transition Vellum from a "Developer Playground" (Standalone Components) to a **Production-Grade MLOps Platform** (Kubeflow Manifests v1.11.0 + Qdrant).

## Changes Implemented

### 1. The "Destructive Upgrade"
We deleted the `kubeflow` namespace and replaced standalone installs with the official integrated stack.
-   **Old Stack**: Manual Bitnami Helm Charts (MinIO, MySQL), Standalone KFP.
-   **New Stack**: `kubeflow/manifests` v1.11.0.
    -   **Istio**: Ingress Gateway, mTLS.
    -   **Dex**: OIDC Authentication (`user@example.com`).
    -   **KFP v2.2.0+**: Uses `ghcr.io` images (Fixed `gcr.io` deprecation issues).

### 2. Tuned for Minikube
-   **Disabled**: KServe, Spark Operator (to save RAM).
-   **Storage**: Tuned `seaweedfs` (S3) and `mysql` to 512Mi limits.
-   **Vector DB**: **Qdrant** installed in `qdrant` namespace.
-   **Fixes Applied**:
    -   **Certificate Refresh**: Performed global restart to fix `CERTIFICATE_VERIFY_FAILED` errors from sidecars holding old certs.
    -   **Auth Proxy**: Deployed `oauth2-proxy` to fix 401 errors in Dashboard sub-apps.

## Verification Results

### Infrastructure Status
| Component | Status | Notes |
| :--- | :--- | :--- |
| **Dashboard** | ✅ Running | Accessible at `localhost:8080` |
| **KFP Backend** | ✅ Running | API Ready for Ingestion Pipelines |
| **Katib** | ✅ Running | Ready for Hyperparameter Tuning |
| **Qdrant** | ✅ Running | Ready for Vector Storage |

### Key Commands
**Access Dashboard**:
```bash
./scripts/connect.sh
```
**Login**: `user@example.com` / `12341234`

## Next Steps (Phase 4)
1.  **Refactor Ingestion**: Update code to use `QdrantVectorStore`.
2.  **Re-run Tuning**: Validate the Katib -> KFP -> Qdrant loop.

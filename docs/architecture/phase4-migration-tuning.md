# Phase 4 Walkthrough: Qdrant Migration & Katib Tuning

## 1. Goal
Evaluate specific chunking strategies (Size: 256/512/1024, Overlap: 20/50) to optimize Retrieval Accuracy (`accuracy` metric).
Migrate from ChromaDB to Qdrant for vector storage.

## 2. Changes Implemented
- **Ingestion Pipeline**: Refactored `pipelines/ingestion` to use `llama-index-vector-stores-qdrant`.
- **Backend API**: Updated `rag_service.py` to query Qdrant.
- **Experiment**: Configured `experiments/rag-tuning.yaml` to run Grid Search on Qdrant-backed ingestion.
- **Infrastructure**: Updated `setup-platform.sh` and `connect.sh` to include Qdrant and MinIO.

## 3. Troubleshooting & Fixes

#### Istio Certificate Expiry
*   **Issue**: Global `503 Service Unavailable` and `upstream connect error` due to expired Istio sidecar and gateway certificates.
*   **Root Cause**: 11-hour network disconnect prevented automatic CSR rotation.
*   **Fix**: Performed a rollout restart of the `kubeflow` namespace and `istio-system` gateway to refresh all certificates.

#### Katib RBAC Permissions
*   **Issue**: Katib trials failed to create worker pods with `forbidden: User "system:serviceaccount:kubeflow:katib-controller" cannot create resource "pods"`.
*   **Fix**: Created a `RoleBinding` granting the `katib-controller` service account `edit` access to the `kubeflow-user-example-com` namespace.
    ```bash
    kubectl apply -f deployment/katib-rbac.yaml
    ```

## 4. Verification Steps
### A. Ingestion Verification
Ran `scripts/verify_ingest.py` which:
1.  Compiled the modified KFP pipeline.
2.  Submitted a run to Kubeflow.
3.  Verified `vellum_vectors` collection creation in Qdrant.
4.  Checked Vector Count (1 document).

**Result**: ✅ SUCESS
- Pipeline Run ID: `689bd1a9-75fc-453f-b2b3-bf5e0caa6713`
- Status: `SUCCEEDED`
- Qdrant Vector Count: `1`

### B. Experiment Launch
Launched Katib Experiment `rag-tuning`.
- **Namespace**: `kubeflow-user-example-com`
- **Objective**: Maximize `accuracy` (Goal: 0.7)
- **Parameters**: `chunk_size`, `chunk_overlap`
- **Algorithm**: Grid Search (6 Trials)

## 4. How to Monitor results
1.  **Dashboard**: Open Kubeflow Dashboard (via `scripts/connect.sh`).
2.  **Katib Link**: Navigate to "Experiments (AutoML)".
3.  **CLI**:
    ```bash
    kubectl get trials -n kubeflow-user-example-com
    kubectl describe experiment rag-tuning -n kubeflow-user-example-com
    ```
4.  **Best Trial**:
    Check `status.currentOptimalTrial` in the experiment YAML or UI.

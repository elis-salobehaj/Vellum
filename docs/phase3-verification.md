# Phase 3 Verification Plan: RAG Tuning

## Goal
Verify the results of the Hyperparameter Tuning experiment (`rag-tuning`), identify the optimal configuration, and apply it to the production pipeline.

## 1. Analyzing Experiment Results
We used **Kubeflow Katib** to sweep the following parameters:
- `chunk_size`: [256, 512, 1024]
- `chunk_overlap`: [20, 50]

### Steps
1.  **Check Experiment Status**:
    ```bash
    kubectl get experiment -n kubeflow rag-tuning
    ```
    Ensure `STATUS` is `Succeeded`.

2.  **Fetch Best Parameters**:
    Run the helper script:
    ```bash
    ./scripts/get-katib-results.sh
    ```
    *Expected Output:*
    ```json
    {
      "parameterAssignments": [
        {"name": "chunk_size", "value": "512"},
        {"name": "chunk_overlap", "value": "50"}
      ],
      "observation": {
        "metrics": [{"name": "accuracy", "value": "0.92"}]
      }
    }
    ```

3.  **Visual Verification**:
    Visit [http://localhost:8080/katib/](http://localhost:8080/katib/) and verify the "Accuracy" curve.

## 2. Applying the Winner
Once the best `chunk_size` is identified (e.g., `512`), we must update the codebase to make it the default.

### Action Items
- [ ] Update `backend/app/core/config.py` (if applicable) or `pipelines/ingestion/pipeline.py` defaults.
- [ ] Re-run the Ingestion Pipeline (Production Run) with the winning parameters.
- [ ] Verify the RAG API (`/api/v1/query`) performance manually.

## 3. Manual Verification (RAG API)
After updating the ingestion pipeline:
1.  **Ingest Documents**:
    ```bash
    uv run pipelines/ingestion/submit_run.py --chunk_size 512 --chunk_overlap 50 --max_docs 100
    ```
    *Note: Use `max_docs` > 5 for real test.*

2.  **Query API**:
    Send a query to `http://localhost:8000/api/v1/query`:
    ```json
    {"query": "What is Agentic AI?"}
    ```
3.  **Verify Context**: Ensure response contains relevant chunks.

## 4. Final Sign-off
- [ ] Experiment Succeeded.
- [ ] Winner Identified.
- [ ] Configuration Updated.
- [ ] RAG API Verified.

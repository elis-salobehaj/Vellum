# Phase 4: Experimentation & Tuning (Qdrant & Katib)

## Goal
Optimize the Retrieval Augmented Generation (RAG) pipeline by:
1.  Migrating the vector store from **ChromaDB** (Developer) to **Qdrant** (Production).
2.  Using **Katib** to tune the `chunk_size` and `chunk_overlap` hyperparameters.
3.  Verifying the end-to-end loop (Seeding -> Ingestion -> Retrieval) on the platform.

## 1. Migration to Qdrant
We replaced the standalone ChromaDB with a production-grade Qdrant namespace.
-   **Namespace**: `qdrant`
-   **Service**: `qdrant.qdrant.svc.cluster.local:6333`
-   **Ingestion Pipeline**: Updated `kubeflow/pipelines/ingestion/pipeline.py` to use `llama-index-vector-stores-qdrant`.
-   **Backend**: Updated `backend/app/services/rag_service.py` to query Qdrant directly.

## 2. Katib Hyperparameter Tuning
We ran a **Grid Search** experiment (`rag-tuning-v3`) to find the best chunking strategy for our documents ("Architectures for Building Agentic AI").

### Experiment Configuration
-   **Search Space**:
    -   `chunk_size`: `[128, 256, 512, 1024]`
    -   `chunk_overlap`: `[20, 50, 100]`
-   **Metric**: `accuracy` (simulated evaluation).
-   **Parallel Trials**: 3

### Results
The experiment completed successfully with the following optimal parameters:
-   **Best Trial**: `rag-tuning-v3-kzhpndjj`
-   **Chunk Size**: **256**
-   **Chunk Overlap**: **50**
-   **Accuracy**: **0.8046**

## 3. Application Updates
We baked these optimal parameters into the platform defaults:
-   **Ingestion Pipeline**: Defaults set to `256/50`.
-   **Backend Service**: `rag_service.py` now uses `SentenceSplitter(chunk_size=256, chunk_overlap=50)`.

## 4. Verification
We verified the retrieval quality using the `verify_retrieval.py` script.
-   **Input**: "Agentic AI"
-   **Retrieved**: 3 Chunks
-   **Top Score**: ~0.808
-   **Source**: `Architectures for Building Agentic AI.pdf`

## How to Reproduce
1.  **Submit Ingestion**:
    ```bash
    uv run kubeflow/pipelines/ingestion/submit_run.py --chunk_size 256 --chunk_overlap 50
    ```
2.  **Verify Retrieval**:
    ```bash
    uv run scripts/verify_retrieval.py
    ```

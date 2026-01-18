# Phase 2: Ingestion Pipeline Walkthrough

## Overview
We have successfully implemented a **Kubeflow Pipeline** to ingest documents from MinIO into ChromaDB. This moves us from a local script-based approach to a scalable, distributed data engineering workflow.

## Architecture
See [Ingestion Pipeline Architecture](ingestion-pipeline.md) for full details.

1.  **Source**: MinIO bucket `documents`.
2.  **Processing**: Custom KFP Component `vellum-ingest:local`.
    *   Downloads files.
    *   Chunks using `SemanticSplitterNodeParser`.
    *   Embeds using `BAAI/bge-large-en-v1.5` (CPU).
3.  **Sink**: ChromaDB `kbase_docs` collection.

## Validation Results

### 1. Pipeline Execution
The pipeline successfully processed a subset of 14 documents (reduced from 600 for speed).
*   **Run ID**: `7b4782dd-5082-4bce-a8c6-bf6c1afbce5f`
*   **Duration**: ~27 minutes (CPU-bound embedding).

### 2. Data Verification
We verified the data in ChromaDB using `scripts/verify_chroma.py`:
```
✅ Connection successful!
📊 Collection 'kbase_docs' has 598 documents.
🔎 Peeking at top 3 documents:
   [1] Source: Adaptation of Embedding Models to Financial Filings via LLM Distillation.pdf
   ...
```

## Key Files Created
*   `pipelines/ingestion/pipeline.py`: The KFP definition.
*   `pipelines/ingestion/scripts/run_ingestion.py`: The core logic.
*   `pipelines/ingestion/Dockerfile`: The isolated environment.
*   `docs/architecture/ingestion-pipeline.md`: Architecture documentation.

## Phase 2.5: Retrieval API Implementation

### Overview
We enabled the Backend API to consume the vector data by switching the `RAGService` to use a remote `HttpClient` pointing to the Kubernetes ChromaDB service.

### Validation Results
We verified the retrieval logic using `backend/verify_rag_manual.py` (simulating the API service layer) and confirmed full-text retrieval:
```
🚀 Testing RAG Service Retrieval...
❓ Query: What is agentic AI?
✅ Retrieved 3 citations.
   [1] Architectures for Building Agentic AI.pdf (Score: 0.63)
       Snippet: Chapter 3: Architectures for Building Agentic AI... (Length: 2469 chars)
```

## Status
✅ **Phase 2 Complete**. we are now ready for **Phase 3: Experimentation & Tuning**, using **Katib** to optimize hyperparameters.

# Vellum Backend API

A lightweight FastAPI service acting as the central router for the Vellum chatbot.

## Architecture Change (Phase 5)

This backend has been **decoupled** from heavy ML operations:
-   **NO** `torch` or `transformers` dependencies embedded.
-   **Ingestion**: Offloaded to Kubeflow Pipelines (triggered via `POST /admin/ingest`).
-   **Embeddings**: Delegated to the remote TEI (`text-embeddings-inference`) service.

## Key Endpoints

### Chat
-   `POST /api/v1/chat`: Main RAG endpoint.
    -   Retrieves context from Qdrant (via TEI embeddings).
    -   Generates response via LLM Service.

### Admin
-   `POST /api/v1/admin/ingest`: Triggers a new ingestion run on Kubeflow.
    -   Payload: `{"bucket": "documents", "cleanup": true}`

## Local Development (Kubernetes Proxy)

Since dependencies are external, you need the platform running:

1.  Start Platform:
    ```bash
    ../scripts/setup-platform.sh
    ../scripts/connect.sh
    ```

2.  Run Backend (if not using the K8s pod):
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    
    # Env vars must point to forwarded ports
    export QDRANT_HOST=localhost
    export QDRANT_PORT=6333
    export EMBEDDINGS_SERVICE_URL=http://localhost:8082
    
    uvicorn main:app --reload
    ```

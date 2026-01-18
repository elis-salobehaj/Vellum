# Vellum Ingestion Pipeline (Ultra-Pro Approach)

This directory contains the robust, streaming-based ingestion pipeline for Vellum.

## Architecture

1.  **Storage (MinIO)**: Documents are stored in the `documents` bucket.
2.  **Streaming Ingestion**: The ingestion worker (`vellum-ingest`) fetches files one by one directly from MinIO to avoid memory exhaustion (OOM).
3.  **Vector Store (Qdrant)**: Chunks are embedded using `BAAI/bge-small-en-v1.5` and stored in the `vellum_vectors` collection.
4.  **Orchestration (Kubeflow)**: The ingestion is managed as a Kubeflow Pipeline (KFP), allowing for scalability, retries, and monitoring.

## How to Trigger Ingestion

### Methodology 1: Via Backend (Recommended)
The backend provides an endpoint that triggers the Kubeflow pipeline:

```bash
# Triggers the KFP pipeline immediately
curl -X POST http://localhost:8000/api/v1/ingest
```

The call returns a `run_id`. You can track the progress in the Kubeflow Dashboard at `http://localhost:8080/_/pipeline-dashboard/`.

### Methodology 2: CLI (Manual)
You can run the ingestion script manually using `uv` if you have the dependencies installed. Ensure your port-forwards are active (via `connect.sh`).

```bash
# Set the embedding service URL to your local port-forward
export EMBEDDINGS_SERVICE_URL="http://localhost:8082/v1"

# Run from the ingestion directory
cd kubeflow/pipelines/ingestion
uv run scripts/run_ingestion.py \
  --bucket documents \
  --minio_endpoint localhost:9000 \
  --qdrant_host localhost \
  --qdrant_port 6333 \
  --cleanup
```

## Configuration

The pipeline behavior is controlled by several parameters:
- `splitter_mode`: `fixed` (default) or `semantic`.
- `chunk_size`: Size of chunks (recommended 512-1024).
- `max_docs`: Limit number of files (default 100).

## Why This Approach?
- **Isolation**: Ingestion runs in a separate pod, keeping the frontend/backend stable.
- **Scalability**: Can process thousands of large PDFs without crashing.
- **Observability**: Every ingestion run is logged and versioned in Kubeflow.

# Vellum Ingestion Pipeline

This directory contains the Kubeflow Pipeline definition for document ingestion.

## Directory Structure
- `pipeline.py`: The KFP pipeline definition (using KFP v2 SDK).
- `Dockerfile`: Dedicated Dockerfile for the ingestion worker.
- `requirements.txt`: Python dependencies for the ingestion worker (includes `kfp`, `chromadb`, `llama-index`).
- `scripts/run_ingestion.py`: The core logic script executed by the pipeline.

## Build Instructions
To build the ingestion image for the local Minikube environment:
```bash
# Run from project root
./scripts/build-ingest-local.sh
```

## Running the Pipeline
To submit a run to the KFP cluster:
```bash
# Run from project root
uv run pipelines/ingestion/submit_run.py
```

## MinIO Integration
The pipeline expects documents in the `documents` bucket in MinIO.
To upload local documents to MinIO:
```bash
# Ensure MinIO is port-forwarded (localhost:9000)
uv run scripts/upload_to_minio.py --local_dir backend/data/source_documents
```

## Dependencies
The ingestion worker runs in a separate container from the backend API.
Key dependencies:
- `kfp`: Required for KFP v2 Python components.
- `chromadb`: Client library (ensure compatibility with server version).
- `llama-index`: For document processing and RAG.
- `boto3/minio`: For fetching documents from S3/MinIO.

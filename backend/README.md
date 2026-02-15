# Vellum Backend API

Lightweight FastAPI service for the Vellum chatbot. No heavy ML dependencies — ingestion is handled by [Kubeflow Pipelines](../kubeflow/pipelines/ingestion/).

## Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/chat` | Main RAG endpoint (Qdrant retrieval + LLM response) |
| `POST` | `/api/v1/admin/ingest` | Triggers KFP ingestion pipeline |
| `GET`  | `/docs` | OpenAPI documentation |

## Quick Start

```bash
uv sync
uv run uvicorn main:app --reload
```

> **Note**: External services (Qdrant, Embeddings, MinIO) must be accessible via port-forwards. Run `../scripts/connect.sh` first.

## Full Documentation

- [Getting Started](../docs/guides/GETTING_STARTED.md)
- [Development Guide](../docs/guides/DEVELOPMENT.md)
- [Architecture & Conventions](../docs/context/ARCHITECTURE.md)

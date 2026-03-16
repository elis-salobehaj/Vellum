# Vellum Backend API

Lightweight FastAPI service for the Vellum chatbot. No heavy ML dependencies — Phase 1 defaults to backend-driven direct ingestion, while the retained [Kubeflow pipeline path](../kubeflow/pipelines/ingestion/) is now optional and mainly used for targeted KFP debugging.

## Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/chat` | Main RAG endpoint (Qdrant retrieval + LLM response) |
| `POST` | `/api/v1/admin/upload-and-ingest` | Triggers the current ingestion flow; defaults to direct ingestion unless `INGESTION_MODE=kfp` |
| `GET`  | `/api/v1/admin/ingestion-status` | Returns persisted direct-ingestion progress for the active bucket/prefix |
| `GET`  | `/docs` | OpenAPI documentation |

## Quick Start

```bash
uv sync
uv run uvicorn main:app --reload
```

> **Note**: External services such as Qdrant, TEI, and MinIO must be reachable from the backend. In local/hybrid mode, run `../scripts/connect.sh` first.

## Full Documentation

- [Getting Started](../docs/guides/GETTING_STARTED.md)
- [Development Guide](../docs/guides/DEVELOPMENT.md)
- [Architecture & Conventions](../docs/context/ARCHITECTURE.md)

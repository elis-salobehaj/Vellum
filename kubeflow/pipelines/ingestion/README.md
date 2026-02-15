# Vellum Ingestion Pipeline

Kubeflow Pipeline for document ingestion: MinIO → Chunking → Embedding → Qdrant.

## Quick Start

### Via Backend API (Recommended)
```bash
curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"bucket": "documents", "cleanup": true}'
```

### Via CLI (Manual)
```bash
export EMBEDDINGS_SERVICE_URL="http://localhost:8082/v1"
cd kubeflow/pipelines/ingestion
uv run scripts/run_ingestion.py \
  --bucket documents \
  --minio_endpoint localhost:9000 \
  --qdrant_host localhost \
  --qdrant_port 6333 \
  --cleanup
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `splitter_mode` | `fixed` | `fixed` or `semantic` |
| `chunk_size` | `256` | Size of text chunks (Katib-optimized) |
| `chunk_overlap` | `50` | Overlap between chunks (Katib-optimized) |
| `max_docs` | `100` | Limit number of files to process |

## Full Documentation

- [Ingestion Pipeline Architecture](../../docs/designs/ingestion-pipeline.md)
- [Ingestion Verification Guide](../../docs/guides/INGESTION_VERIFICATION.md)
- [Katib Tuning Guide](../../docs/guides/KATIB_TUNING.md)

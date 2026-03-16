# Vellum Ingestion Pipeline

Kubeflow pipeline for document ingestion: MinIO → chunking → embedding → Qdrant. This path is retained in Phase 1 for explicit Kubeflow debugging; the normal local ingestion path now goes through the backend's direct-ingestion service.

## Quick Start

### Via Backend API (Recommended for Day-to-Day Phase 1 Work)
```bash
curl -X POST "http://localhost:8006/api/v1/admin/upload-and-ingest?cleanup=true&reset_progress=true" \
  -H "kubeflow-userid: vellum@example.com"
```

That route uses direct ingestion by default. Only set `INGESTION_MODE=kfp` when you specifically want to exercise the Kubeflow submission path.

### Via CLI (Manual KFP Path)
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

# Ingestion Verification Guide

After triggering the **Upload & Ingest** process, follow these steps to verify success.

## 1. Verify MinIO Upload
Documents should be present in the `documents` bucket.
- **URL**: [MinIO Console](http://localhost:9000) (via `./scripts/connect.sh`)
- **Credentials**: `minio` / `minio123`
- **Check**: Browse the `documents` bucket and verify files are present.

## 2. Verify Kubeflow Pipeline
The ingestion process triggers a Kubeflow Pipeline run.
- **URL**: [Kubeflow Dashboard](http://localhost:8080/_/pipeline/#/runs)
- **Check**: Look for a run starting with `ingest-` in the `kubeflow-vellum` namespace.
- **Status**: Should transition to `Succeeded`.

## 3. Verify Vector DB (Qdrant)
The pipeline ingests data into Qdrant.
- **URL**: [Qdrant Dashboard](http://localhost:6333/dashboard)
- **Check**: Verify the `documents` collection has a non-zero count of vectors.

You can also verify via CLI:
```bash
uv run scripts/verify_retrieval.py
```

## 4. Test Chat
Once the pipeline succeeds, you should be able to ask questions about the uploaded documents in the main Chat page.

## See Also
- [Ingestion Pipeline Architecture](../designs/ingestion-pipeline.md) — Full architecture details
- [Development Guide](DEVELOPMENT.md) — Ingestion pipeline commands

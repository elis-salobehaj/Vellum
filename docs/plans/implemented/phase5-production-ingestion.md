---
title: "Phase 5: Production Ingestion & Serving"
status: implemented
priority: high
estimated_hours: 30-50
dependencies:
  - docs/plans/implemented/phase4-experimentation-tuning.md
created: 2026-01-15
date_updated: 2026-02-15
date_completed: 2026-02-15
related_files:
  - kubeflow/pipelines/ingestion/pipeline.py
  - kubeflow/pipelines/ingestion/scripts/run_ingestion.py
  - kubeflow/pipelines/ingestion/Dockerfile
  - backend/app/services/rag_service.py
  - deployment/llm-service.yaml
tags:
  - ingestion
  - microservices
  - tei
  - kfp
completion:
  - [x] Decouple ingestion from backend (separate Docker image) ✅
  - [x] KFP pipeline definition with KFP v2 SDK ✅
  - [x] Lightweight backend (no torch/transformers dependencies) ✅
  - [x] Dedicated TEI (Text Embeddings Inference) service deployment ✅
  - [x] S3 streaming ETL for large-scale document ingestion ✅
  - [x] KServe Inference with custom predictor ✅
  - [x] Remote embedding calls in ingestion pipeline (TEI instead of local CPU) ✅
  - [x] API trigger for ingestion (`POST /api/v1/admin/ingest`) ✅
---

## Goal

Decouple the Vellum platform into independent microservices for production-grade operation:
1. **Distributed Ingestion**: KFP pipelines handle document processing (S3 → Text → Embedding → Qdrant).
2. **Lightweight Backend**: API server stripped of heavy ML dependencies (`torch`, `transformers`).
3. **Remote Services**: Dedicated TEI service for embeddings, external LLM APIs for inference.

## Architecture

```
MinIO (S3)  →  KFP Pipeline  →  TEI Service  →  Qdrant
                    ↑                                ↓
              API Trigger              Backend API (queries only)
```

### Key Changes from Phase 4
| Component | Phase 4 | Phase 5 |
|-----------|---------|---------|
| **Embeddings** | Local CPU (BGE-Large in pipeline pod) | Remote TEI service |
| **Backend** | Includes torch, transformers | Lightweight (queries Qdrant only) |
| **Ingestion Trigger** | Manual `submit_run.py` | API endpoint + manual |

## Current Status

Most Phase 5 items are complete. The ingestion pipeline uses streaming ETL, TEI is deployed, and KServe handles inference. Remaining work focuses on wiring the ingestion pipeline to use remote TEI instead of local CPU embedding, and exposing the API trigger endpoint.

## How to Run

### Manual Ingestion
```bash
uv run kubeflow/pipelines/ingestion/submit_run.py --chunk_size 256 --chunk_overlap 50
```

### Verify Retrieval
```bash
uv run scripts/verify_retrieval.py
```

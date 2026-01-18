# Vellum Enterprise Chatbot

An enterprise-grade chatbot featuring Entra ID SSO, Multi-LLM support, and an advanced RAG pipeline orchestrated by **Kubeflow**.

## 🚀 Quick Start (Kubernetes)

This platform is designed to run on **Kubernetes** (Minikube for local dev).

**Prerequisites**:
- Docker & Minikube
- `kubectl` & `helm`
- Python 3.12+ (for scripts)

**Launch Platform**:
```bash
./scripts/setup-platform.sh
```
*This script initializes Minikube, installs Kubeflow Pipelines, MinIO, Qdrant, and deploys the Vellum services.*

**Access Services**:
After setup, use the connect script to port-forward all services:
```bash
./scripts/connect.sh
```

| Service | Local URL |
| :--- | :--- |
| **Frontend** | [http://localhost:9090](http://localhost:9090) |
| **Backend API** | [http://localhost:8000](http://localhost:8000/docs) |
| **Kubeflow Dashboard** | [http://localhost:8080](http://localhost:8080) |
| **MinIO Console** | [http://localhost:9001](http://localhost:9001) |

---

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Configuration](#configuration)
- [Ingestion Pipeline](#ingestion-pipeline)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)

## Features

**🤖 Multi-LLM Support**:
-   **Cloud**: OpenAI GPT-4, Google Gemini.
-   **Local**: Self-hosted LLMs via KServe/LocalAI (Llama 3, Mistral).

**📚 Advanced RAG Pipeline**:
-   **Orchestration**: Kubeflow Pipelines (KFP) for reliable, scalable ingestion.
-   **Vector Store**: Qdrant (Production Grade).
-   **Embeddings**: Dedicated **Text Embeddings Inference (TEI)** service.
-   **Source Diversity**: MMR (Maximal Marginal Relevance) & Unique File Post-processing.

**🔐 Enterprise Security**:
-   **SSO**: Microsoft Entra ID (Azure AD) integration.
-   **Air-Gapped Ready**: Fully containerized architecture.

## Architecture

**Vellum** follows a phased architectural evolution, designed for high scalability and enterprise security.

### Phase 1: The Foundation (Infrastructure)
Establishment of the core Kubernetes operators:
-   **Service Mesh**: Istio for mTLS and traffic management.
-   **Serverless**: Knative for scale-to-zero inference.
-   **ML Platform**: Kubeflow Pipelines (KFP), Katib (Tuning), and ML Metadata.

### Phase 2: Modern Data Engineering
Migration from legacy scripts to robust data pipelines:
-   **Data Lineage**: Explicit Input/Output artifacts in KFP.
-   **Retrieval API**: RAG implementation with Qdrant.
-   **Streaming ETL**: iterative S3 streaming for large-scale ingestion.

### Phase 3: Platform Engineering
Production-grade platform upgrades:
-   **Unified Dashboard**: Central UI for KFP, Katib, and Notebooks.
-   **Identity Provider**: OIDC integration (Dex/Entra ID) for secure multi-user access.
-   **Vector Storage**: Qdrant (Production Grade) replacing basic vector stores.

### Phase 4: Experimentation & Tuning
Automating the scientific loop:
-   **Hyperparameter Tuning**: Katib experiments for RAG optimization.
-   **Verification**: automated validation of RAG performance.

### Phase 5: Production Ingestion & Serving (Current)
Decoupled Microservices Architecture:
-   **Distributed Ingestion**: KFP pipelines handle document processing (S3 -> Text -> Embedding -> Qdrant).
-   **Lightweight Backend**: API server stripped of heavy ML dependencies (`torch`, `transformers`).
-   **Remote Services**:
    -   **Embeddings**: Dedicated **TEI** (`text-embeddings-inference`) service.
    -   **Inference**: Integration with external LLM APIs or KServe.

### Phase 6: Advanced Security & Scaling (Planned)
Enterprise hardening:
-   **Auth**: Kubernetes Service Account tokens for KFP triggers.
-   **RBAC**: Granular role-based access control based on OIDC groups.
-   **Scale**: Spark Operator for petabyte-scale data processing.

## Tech Stack

### Frontend
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

-   **Framework**: React 19 + Vite
-   **Auth**: MSAL (`@azure/msal-react`)

### Backend
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Kubeflow](https://img.shields.io/badge/Kubeflow-pipelines-blue?style=for-the-badge)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-red?style=for-the-badge)

-   **API**: FastAPI (Python 3.12)
-   **Orchestration**: Kubeflow Pipelines SDK
-   **Storage**: MinIO (S3), Qdrant

## Configuration

The application is configured via K8s ConfigMaps and Secrets.
See `deployment/manifests/` for details.

| Variable | Description |
| :--- | :--- |
| `LLM_SERVICE_URL` | Endpoint for Chat Completions |
| `EMBEDDINGS_SERVICE_URL` | Endpoint for TEI |
| `QDRANT_HOST` | Vector DB Host |

## Ingestion Pipeline

Ingestion is no longer handled by the backend process. It is a strictly defined Kubeflow Pipeline.

**Manual Trigger**:
```bash
cd kubeflow/pipelines/ingestion
uv run scripts/run_ingestion.py --cleanup
```

**API Trigger**:
POST `/api/v1/admin/ingest`
```json
{
  "bucket": "documents",
  "cleanup": true
}
```

## Project Structure

```
Vellum/
├── backend/            # FastAPI (Business Logic)
├── frontend/           # React App
├── kubeflow/           # KFP Pipelines & Components
│   └── pipelines/ingestion
├── deployment/         # K8s Manifests (Helm/Kustomize)
├── scripts/            # Platform Setup & Utilities
└── README.md           # Documentation
```

## Troubleshooting

-   **"CrashLoopBackOff"**: Check logs with `kubectl -n kubeflow-user-example-com logs <pod>`.
-   **"Connection Refused"**: Ensure you ran `./scripts/connect.sh`.
-   **"401 Unauthorized"**: KFP requires `kubeflow-userid` header (handled by backend).

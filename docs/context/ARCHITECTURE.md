# Architecture & Conventions

## Stack Overview

### Backend (Python 3.12+)
- **Framework**: FastAPI (async-first)
- **AI Layer**: LangGraph for stateful multi-step loops
- **Configuration**: Pydantic v2 schemas for all API models
- **Embeddings**: Dedicated TEI (Text Embeddings Inference) service
- **Vector Store**: Qdrant (production-grade, Rust-based)
- **Orchestration**: Kubeflow Pipelines (KFP v2) for data ingestion

**Key Libraries:**
- `llama-index` — RAG framework (ingestion pipeline)
- `qdrant-client` — Vector database client
- `kfp` — Kubeflow Pipelines SDK
- `boto3` — AWS/MinIO S3 client

### Frontend (React 19)
- **Language**: TypeScript
- **Build**: Vite
- **Styling**: Tailwind CSS
- **Auth**: MSAL (`@azure/msal-react`) for Entra ID SSO

### Infrastructure (Kubernetes)
- **Local Dev**: Minikube (6+ CPUs, 12+ GB RAM)
- **Service Mesh**: Istio (mTLS, traffic management)
- **ML Platform**: Kubeflow (KFP, Katib, Central Dashboard)
- **Auth**: Dex (OIDC) + OAuth2 Proxy
- **Storage**: MinIO (S3-compatible), Qdrant (vectors)

---

## Code Conventions

### Backend (Python)

#### Type Safety
All functions must have type hints:

```python
from typing import Optional

async def get_documents(query: str, top_k: int = 5) -> list[dict]:
    """Retrieve relevant documents from Qdrant."""
    ...
```

#### Pydantic Models
Use `BaseModel` for all API request/response schemas:

```python
from pydantic import BaseModel

class IngestRequest(BaseModel):
    bucket: str
    cleanup: bool = False
    chunk_size: int = 256
    chunk_overlap: int = 50
```

#### RAG Considerations
When touching retrieval code, always consider **MMR (Maximal Marginal Relevance)** to avoid redundant context in retrieved chunks.

---

### Frontend (TypeScript)

#### Data Fetching
Use React Query for server state management — avoid `useEffect` for data fetching.

#### Component Style
Functional components only. Keep components focused and composable.

---

## Project Structure

### Backend
```
backend/
├── app/
│   ├── services/         # Application services
│   │   └── rag_service.py  # Qdrant retrieval logic
│   └── routers/          # FastAPI route handlers
├── tests/                # Test suite
├── main.py               # FastAPI app entry
└── pyproject.toml        # uv dependencies
```

### Frontend
```
frontend/
├── src/
│   ├── pages/            # Page-level components
│   │   └── ChatPage.tsx
│   ├── components/       # Reusable UI components
│   └── App.tsx           # Root component
├── package.json          # pnpm dependencies
└── vite.config.ts        # Vite configuration
```

### Kubeflow Pipelines
```
kubeflow/
└── pipelines/
    └── ingestion/
        ├── pipeline.py       # KFP v2 pipeline definition
        ├── scripts/
        │   └── run_ingestion.py  # Core ingestion logic
        ├── submit_run.py     # Submit pipeline run to KFP
        └── Dockerfile        # Isolated ML environment
```

### Infrastructure
```
deployment/
├── manifests/            # Kubeflow manifests (submodule)
├── kustomization.yaml    # Environment-specific overrides
└── llm-service.yaml      # KServe inference service
scripts/
├── setup-platform.sh     # Bootstrap Kubeflow + Qdrant
├── connect.sh            # Port-forward all services
└── nuke-kubeflow.sh      # Full platform teardown
```

### Documentation
```
docs/
├── README.md             # Navigation hub & active work
├── guides/               # How-to guides
├── context/              # Reference documentation
├── designs/              # Architecture decisions & analysis
└── plans/                # Project planning
    ├── active/
    ├── implemented/
    └── backlog/
```

---

## Key Architectural Decisions

### Decoupled Ingestion (Phase 5)
The backend API does **not** perform document ingestion. Heavy ML work (chunking, embedding) runs in isolated KFP pipeline pods with their own Docker image and dependencies (`torch`, `transformers`, `llama-index`). The backend is kept lightweight — it only queries Qdrant for retrieval.

### Qdrant over ChromaDB
We migrated from ChromaDB to Qdrant in Phase 4. Qdrant is Rust-based, resource-efficient, and production-grade. See [`designs/vectordb-tradeoffs.md`](../designs/vectordb-tradeoffs.md) for the full analysis.

### Optimal Chunking Parameters
Katib hyperparameter tuning (Phase 4) found optimal parameters:
- **Chunk Size**: 256
- **Chunk Overlap**: 50
- **Accuracy**: 0.8046

These are the platform defaults in both the ingestion pipeline and the backend RAG service.

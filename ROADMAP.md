# Vellum Project Roadmap

## Phase 1: The Foundation (Infrastructure)
- [x] Establish the Kubernetes operators required for the native stack.
- [x] Install **Istio** (Service Mesh)
- [x] Install **Knative** (Serverless)
- [x] Install **KFP Dependencies** (MinIO, MySQL)
- [x] Install **Cert Manager** (via Kubeflow Manifests)
- [x] Install **Kubeflow Core Components**:
    -   [x] Dashboard (KFP UI)
    -   [x] Pipelines (KFP) + ML Metadata (MLMD)
    -   [x] Katib (Tuning)

> **Status**: Phase 1 Infrastructure Complete. See [Phase 1 Walkthrough](docs/architecture/phase1-infrastructure-walkthrough.md).

## Phase 2: Modern Data Engineering
Migrate ingestion logic to high-performance standard tools.
- [x] **Data Lineage**: Implement KFP pipeline with explicit Input/Output Artifacts.
- [x] **Retrieval API**: Implement Backend API to query ChromaDB (RAG).

> **Status**: Phase 2 Complete. See [Phase 2 Walkthrough](docs/architecture/phase2-walkthrough.md).

## Phase 3: Platform Engineering (Kubeflow Upgrade)
Upgrade from "Developer Standalone" to "Production Platform".
- [x] **Clean Build**: Replace standalone components with official `kubeflow/manifests`.
- [x] **Istio Service Mesh**: Enable gateway, traffic splitting, and mTLS.
- [x] **Central Dashboard**: Unified UI for KFP, Katib, and Notebooks.
- [x] **Auth**: OIDC integration (Dex) for multi-user security.
- [x] **Vector DB**: Install Qdrant (Production Grade).
- [ ] **Migration**: *Moved to Phase 4 (Re-ingestion)*.

> **Status**: Phase 3 Complete. See [Phase 3 Walkthrough](docs/architecture/phase3-platform-upgrade.md).

## Phase 4: Experimentation & Tuning (Verified on Platform)
Automate the scientific loop (re-verifying on the new stack).
- [x] **Re-verify Katib**: Ensure experiment CRDs work on the new platform.
- [x] **Refactor RAG**: Port Ingestion/Retrieval to Qdrant SDK.
- [x] **Re-verify RAG Tuning**: Run the 1-doc optimization sweep.

> **Status**: Phase 4 Complete. See [Phase 4 Walkthrough](docs/architecture/phase4-migration-tuning.md).

## Phase 5: Production Ingestion & Serving (Scalable Architecture)
Decouple Monolith to Microservices & Event-Driven Architecture.
- [x] **Distribute Ingestion**: Move ingestion logic from Backend to Kubeflow Pipelines (KFP).
- [x] **Streaming ETL**: Implement iterative S3 streaming to handle 1000s of files (OOM-proof).
- [x] **Lightweight Backend**: Remove all ML dependencies (`torch`, `transformers`) from API server.
- [x] **Self-Hosted Embeddings**: Deploy TEI (`text-embeddings-inference`) Service for low-latency vectorization.
- [x] **KServe Inference**: Deploy LLM as a KServe `InferenceService` with Custom Predictor.

## Future / Backlog
- [ ] **Infrastructure**: Investigate Istio OIDC `Jwt issuer is not configured` error to enable proper `kubectl create token` auth on port 8080.
- [ ] **MLOps**: Implement **Hybrid Registry** (MLflow -> KMR) and **Model Registry** for versioning/promotion.
- [ ] **Auth: Service Account Integration**: Port KFP/Infra triggers from hardcoded user IDs to secure Kubernetes Service Account tokens.
- [ ] **Scale: Spark Operator**: Adopt `SparkApplication` for petabyte-scale ingestion.
- [ ] **Security**: Implement true RBAC in Admin API by decoding OIDC roles/groups from the JWT token (e.g., allow only `groups: [admins]`).

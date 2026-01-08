# Vellum Project Roadmap

## Phase 1: The Foundation (Infrastructure)
- [x] Establish the Kubernetes operators required for the native stack.
- [x] Install **Istio** (Service Mesh)
- [x] Install **Knative** (Serverless)
- [x] Install **KFP Dependencies** (MinIO, MySQL)
- [ ] Install **Cert Manager**
- [ ] Install **Kubeflow Core Components**:
    -   [x] Dashboard (KFP UI)
    -   [x] Pipelines (KFP) + ML Metadata (MLMD)
    -   [ ] Katib (Tuning)
    -   [ ] Model Registry

> **Status**: Phase 1 Infrastructure Complete. See [Phase 1 Walkthrough](docs/architecture/phase1-infrastructure-walkthrough.md).

## Phase 2: Modern Data Engineering
Migrate ingestion logic to high-performance standard tools.
- [ ] **Data Lineage**: Implement KFP pipeline with explicit Input/Output Artifacts.

## Phase 3: Experimentation & Tuning
Automate the scientific loop.
- [ ] **Hyperparameter Tuning**: Create Katib Experiment to optimize RAG `chunk_size`.
- [ ] **Hybrid Registry**: Implement promotion workflow (MLflow -> KMR).

## Phase 4: Production Serving
Standardize inference on KServe.
- [ ] **Custom Predictor**: Wrap LlamaIndex application in KServe V2 Protocol.
- [ ] **Deployment**: Deploy `InferenceService` with scale-to-zero.

## Future / Backlog
- [ ] **Learning: Go Function**: Rewrite a Crossplane Composition Function in Go for performance.
- [ ] **Scale: Spark Operator**: Adopt `SparkApplication` for petabyte-scale ingestion.

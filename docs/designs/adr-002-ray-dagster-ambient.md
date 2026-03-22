# ADR-002: Ray + Dagster + Istio Ambient

**Status:** Accepted
**Date:** 2026-03-21
**Phases:** 3 (Ray Serve), 4 (Dagster + Ambient)

---

## Context

Phase 1 of Vellum's infrastructure migration established Kind as the local runtime and adopted the slim Kubeflow overlay (KFP, Dex, MinIO, Cert-Manager, oauth2-proxy, Knative). While functional, this stack carried significant resource overhead and operational complexity:

- **Kubeflow Pipelines (KFP)**: ~2 GB RAM, MySQL, SeaweedFS, 8+ components, OIDC/Dex auth chain for multi-user pipeline isolation.
- **MinIO**: a running S3 server solely to hold documents between upload and ingestion — unnecessary when local PVC storage is available.
- **Dex + oauth2-proxy**: added for the Kubeflow Central Dashboard; not needed once the dashboard is removed.
- **Cert-Manager**: only required by KFP and admission webhooks; removable post-KFP.
- **KServe + Knative**: originally chosen for LLM model serving; replaced by Ray Serve in Phase 3.

---

## Decisions

### Decision 1: Dagster replaces Kubeflow Pipelines (ADR-004)

**Chosen:** Dagster (Helm-installed, `dagster` namespace)
**Rejected:** Keep KFP, migrate to Argo Workflows, use raw K8s Jobs

**Rationale:**
- Dagster's `@asset` model is a better fit for the data-centric ingestion workload (read → chunk → embed → upsert) than KFP's `@dsl.pipeline` / component DAG approach.
- Dagster's built-in sensor framework (`@asset_sensor`) removes the need for a polling cron job to detect new documents.
- Drastically lower resource footprint: PostgreSQL (embedded) + webserver + daemon vs. KFP's MySQL + SeaweedFS + 8 controllers.
- GraphQL-based API (`/graphql`) integrates cleanly with the existing FastAPI service layer.
- Dagster's `ConfigurableResource` pattern maps directly to the `StorageService` / `QdrantResource` / `TEIResource` abstractions implemented in Phase 4.

**Trade-offs:**
- Dagster is a less common tool in ML teams familiar with KFP/Airflow. Mitigated by extensive inline documentation.
- Dagster's `LaunchPipelineExecution` GraphQL mutation requires the job to be materialisable from the `dagster_vellum.definitions` module — a one-time setup cost.

---

### Decision 2: StorageService abstraction replaces MinIO (ADR-006)

**Chosen:** `StorageService` (PVC local / S3 cloud) toggled by `USE_S3_STORAGE`
**Rejected:** Keep MinIO as an always-on sidecar

**Rationale:**
- For local development, a PVC is simpler, always available, and requires zero credentials.
- For production/cloud, any S3-compatible store (AWS S3, Google Cloud Storage via S3 shim, MinIO on cloud) works via the `S3StorageService` implementation.
- Removes a running MinIO pod, its port-forward, and MinIO credentials from `.env`.

**Migration path:** `USE_S3_STORAGE=false` (default) → documents stored in `DOCUMENT_STORAGE_PATH`. Set `USE_S3_STORAGE=true` + S3 credentials for cloud environments.

---

### Decision 3: Istio Ambient replaces sidecar mode (ADR-005)

**Chosen:** Istio Ambient (`istioctl install --set profile=ambient`)
**Rejected:** Keep Kubeflow-bundled sidecar mode, migrate to Linkerd, remove service mesh entirely

**Rationale:**
- Sidecar injection requires per-namespace labelling and per-pod Envoy containers (+50-100 MB RAM per pod). Ambient uses a node-level `ztunnel` DaemonSet (shared) + an optional per-namespace waypoint proxy.
- The Kubeflow-bundled Istio was tightly coupled to the KFP/Dex auth chain. Using a standalone `istioctl` install gives cleaner upgrade paths.
- Ambient mode enables L4 mTLS automatically for all pods in the enrolled namespace (zero-config mTLS), while the waypoint proxy provides L7 JWT `RequestAuthentication` and `AuthorizationPolicy`.
- Knative and the cluster-local-gateway (required specifically for Kubeflow serving) are no longer needed.

**Implementation:**
- `vellum-namespace.yaml` adds label `istio.io/dataplane-mode: ambient`.
- `vellum-istio.yaml` defines: `Gateway` (waypoint), `RequestAuthentication` (Entra ID JWKS), `AuthorizationPolicy` (JWT principals + internal namespaces).
- `setup-kind.sh` calls `istioctl install --set profile=ambient -y` and installs Gateway API CRDs.

---

### Decision 4: Remove Dex, oauth2-proxy, Cert-Manager, Central Dashboard

**Rationale:**
- Dex and oauth2-proxy exist solely for the Kubeflow Central Dashboard's multi-user auth.
- Once KFP and the Central Dashboard are removed, these components have no purpose.
- Cert-Manager was required only by KFP (OIDC certificate issuance) and the admission webhook — both gone.
- **Security improvement**: the `kubeflow-userid` header (injected by Dex → Istio → backend) was a spoofable auth bypass once Dex is removed. Removing the header fallback in `auth.py` eliminates this attack surface.

---

## Consequences

- **Phase 4 resource savings**: ~4-6 GB RAM freed (KFP stack: MySQL, SeaweedFS, 8 controllers; Dex; MinIO; Cert-Manager).
- **Developer onboarding simplified**: no Kubeflow login (`vellum@example.com` / `12341234`), no MinIO credential management, no Dex OIDC exchange.
- **Setup script simplified**: `setup-kind.sh` calls `istioctl` + Helm (Qdrant, Dagster) instead of applying ~30 Kustomize overlays from the Kubeflow manifests submodule.
- **`deployment/manifests` git submodule removed**: eliminates the 140 MB Kubeflow manifests clone from the repo.
- **Ingestion pipeline code**: `kfp_service.py` → `dagster_service.py`, `direct_ingestion_service.py` migrated from MinIO to PVC filesystem.

---

## Related

- [Phase 3 review report](../../docs/reports/current/phase3-review-20260320-50bb8a0.md)
- [ARCHITECTURE.md](../../docs/context/ARCHITECTURE.md)
- [infra-migration.md](../../docs/plans/active/infra-migration.md)

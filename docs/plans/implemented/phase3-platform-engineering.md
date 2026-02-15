---
title: "Phase 3: Platform Engineering"
status: implemented
priority: high
estimated_hours: 20-30
dependencies:
  - docs/plans/implemented/phase2-data-engineering.md
created: 2026-01-01
date_updated: 2026-01-10
date_completed: 2026-01-10
related_files:
  - scripts/setup-platform.sh
  - scripts/connect.sh
  - deployment/manifests/
tags:
  - platform
  - kubeflow
  - istio
  - qdrant
  - authentication
completion:
  - [x] Destructive upgrade from standalone to Kubeflow Manifests v1.11.0 ✅
  - [x] Istio ingress gateway with mTLS ✅
  - [x] Dex OIDC authentication ✅
  - [x] Central Dashboard (unified UI for KFP, Katib, Notebooks) ✅
  - [x] Qdrant deployment in dedicated namespace ✅
  - [x] OAuth2 Proxy for dashboard auth fixes ✅
  - [x] Disabled unnecessary components (KServe, Spark) for Minikube ✅
  - [x] Certificate refresh automation ✅
---

## Summary

Upgraded Vellum from a "Developer Playground" (standalone components) to a **Production-Grade MLOps Platform** using official Kubeflow Manifests v1.11.0. Deployed Qdrant as the production vector database.

### Key Changes
- **Old Stack**: Manual Bitnami Helm Charts (MinIO, MySQL), Standalone KFP
- **New Stack**: `kubeflow/manifests` v1.11.0 with Istio, Dex, KFP v2.2.0+

### Verification
| Component | Status |
| :--- | :--- |
| Dashboard | ✅ Running (localhost:8080) |
| KFP Backend | ✅ Ready for pipelines |
| Katib | ✅ Ready for tuning |
| Qdrant | ✅ Ready for vectors |

See [Phase 3 Report](../../designs/phase3-platform-upgrade.md) and [Kubeflow Platform Plan](../../designs/kubeflow-platform-plan.md) for details.

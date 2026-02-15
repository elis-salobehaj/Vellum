---
title: "Phase 6: Advanced Security & Scaling"
status: backlog
priority: medium
estimated_hours: 40-60
dependencies:
  - docs/plans/active/phase5-production-ingestion.md
created: 2026-02-14
date_updated: 2026-02-14
related_files: []
tags:
  - security
  - rbac
  - scaling
  - spark
---

## Goal

Enterprise hardening of the Vellum platform:
1. **Auth**: Kubernetes Service Account tokens for programmatic KFP pipeline triggers.
2. **RBAC**: Granular role-based access control based on OIDC groups (Dex/Entra ID).
3. **Scale**: Spark Operator for petabyte-scale data processing alongside KFP.

## Scope

### Authentication Hardening
- [ ] Investigate Istio OIDC `Jwt issuer is not configured` error to enable `kubectl create token` auth on port 8080
- [ ] Service Account tokens for KFP API calls (replace hardcoded user IDs)
- [ ] Token rotation and expiry policies
- [ ] Audit logging for pipeline triggers

### Role-Based Access Control
- [ ] OIDC group mapping from Entra ID to Kubeflow namespace profiles
- [ ] True RBAC in Admin API by decoding OIDC roles/groups from JWT token (`groups: [admins]`)
- [ ] Per-namespace resource quotas
- [ ] Read-only vs. admin roles for Dashboard access

### MLOps
- [ ] Hybrid Model Registry (MLflow → Kubeflow Model Registry) for versioning/promotion
- [ ] Model promotion workflow (experiment → staging → production)

### Scaling Infrastructure
- [ ] Spark Operator deployment for petabyte-scale ingestion (`SparkApplication`)
- [ ] Horizontal Pod Autoscaling for ingestion workers
- [ ] Multi-node Qdrant cluster (sharding/replication)

## Prerequisites
- Phase 5 must be complete (stable microservices architecture)
- Production Entra ID tenant configured

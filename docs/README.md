# Vellum Documentation

**For AI Agents & Developers**: This is your primary documentation reference.

---

## 🚀 Quick Start

### For AI Agents
1. **Check current work** → [`plans/active/`](plans/active/)
2. **Understand the stack** → [`context/ARCHITECTURE.md`](context/ARCHITECTURE.md)
3. **Follow workflows** → [`context/WORKFLOWS.md`](context/WORKFLOWS.md)

### For Developers
- **New to the project?** → [`guides/GETTING_STARTED.md`](guides/GETTING_STARTED.md)
- **Daily development?** → [`guides/DEVELOPMENT.md`](guides/DEVELOPMENT.md)

---

## 🔥 Active Plans

| # | Plan | Status | Summary |
|---|------|--------|---------|
| 6 | **Enterprise Auth Hardening** | ⏳ Backlog | RBAC, Service Account tokens, OIDC groups |

**Last Status Update**: 2026-02-15

**Recently Completed**:
- ✅ **Phase 5: Production Ingestion & Serving** — Decoupled microservices, TEI embeddings, lightweight backend, KFP ingestion
- ✅ **Dependency Standardization & Upgrades** — pnpm, uv, pyproject.toml, React 19, Vite 7, Playwright 1.58, httpx migration
- ✅ **Dev Tooling & Hybrid Mode** — nvm + pnpm + uv standardization, hybrid dev mode, deploy optimization, unified logging, backend test suite (16/16 passing)
- ✅ **Phase 4: Experimentation & Tuning** — Katib hyperparameter optimization, Qdrant migration
- ✅ **Phase 3: Platform Engineering** — Kubeflow v1.11.0, Istio, Dex OIDC, Central Dashboard
- ✅ **Phase 2: Modern Data Engineering** — KFP ingestion pipeline, ChromaDB → Qdrant
- ✅ **Phase 1: Foundation** — Kubernetes operators, Istio service mesh, Kubeflow Pipelines

---

## 📚 Essential Guides

### Development Workflow
- [Getting Started](guides/GETTING_STARTED.md) - First-time setup, prerequisites, Minikube
- [Development Guide](guides/DEVELOPMENT.md) - Running locally, debugging, commands

### Architecture & Patterns
- [Architecture](context/ARCHITECTURE.md) - Stack overview, project structure, conventions
- [Workflows](context/WORKFLOWS.md) - Documentation practices, plan lifecycle

### Specialized Topics
- [Authentication](guides/AUTHENTICATION.md) - Entra ID SSO, Dex, security architecture
- [Katib Tuning](guides/KATIB_TUNING.md) - Hyperparameter optimization for RAG
- [Ingestion Verification](guides/INGESTION_VERIFICATION.md) - Verifying pipeline runs
- [Hello World Pipeline](guides/HELLO_WORLD_PIPELINE.md) - Your first KFP pipeline tutorial
- [MinIO Model Management](guides/MINIO_MODEL_MANAGEMENT.md) - Managing LLM models in MinIO for KServe

### Design Documents
- [ADR 001: Kubeflow Native Pivot](designs/001-kubeflow-native-pivot.md) - Why we adopted Kubeflow Native architecture
- [KFP Components Architecture](designs/kfp-components.md) - Detailed KFP microservice breakdown
- [Ingestion Pipeline](designs/ingestion-pipeline.md) - Document ingestion architecture (KFP → Qdrant)
- [Vector DB Tradeoffs](designs/vectordb-tradeoffs.md) - ChromaDB vs Qdrant analysis
- [Language Choice Analysis](designs/language-choice-analysis.md) - Go vs Python for control plane
- [Infrastructure Analysis](designs/infra-structure-analysis.md) - Monorepo vs Polyrepo
- [Kubeflow Platform Plan](designs/kubeflow-platform-plan.md) - Platform upgrade strategy
- [Phase 2 Walkthrough](designs/phase2-walkthrough.md) - Ingestion pipeline implementation report
- [Phase 3 Platform Upgrade](designs/phase3-platform-upgrade.md) - Kubeflow v1.11.0 upgrade report
- [Phase 4 Migration & Tuning](designs/phase4-migration-tuning.md) - Qdrant migration & Katib results

---

## ✅ Recently Completed Work

| Plan | Completed | Summary |
|------|-----------|---------|
| **Dev Tooling & Hybrid Mode** | 2026-02-15 | Package manager standardization (nvm, pnpm, uv), hybrid development mode, deploy optimization, unified logging (structlog + LogLayer), backend test suite (16/16 passing) |
| **Phase 4: Experimentation & Tuning** | 2026-01 | Katib grid search (chunk_size=256, overlap=50, accuracy=0.8046), ChromaDB → Qdrant migration |
| **Phase 3: Platform Engineering** | 2026-01 | Kubeflow v1.11.0, Istio, Dex OIDC, Central Dashboard, Qdrant namespace |
| **Phase 2: Modern Data Engineering** | 2025-12 | KFP ingestion pipeline, semantic chunking, BGE-Large embeddings, retrieval API |
| **Phase 1: Foundation** | 2025-12 | Minikube cluster, Kubeflow Pipelines, Katib, MinIO, Istio operators |

See all completed plans: [`plans/implemented/`](plans/implemented/)

---

## 🗺️ Documentation Map

### Directory Structure
```
docs/
├── README.md              ← You are here
├── guides/                ← How-to guides for daily work
│   ├── GETTING_STARTED.md
│   ├── DEVELOPMENT.md
│   ├── AUTHENTICATION.md
│   ├── KATIB_TUNING.md
│   ├── INGESTION_VERIFICATION.md
│   ├── HELLO_WORLD_PIPELINE.md
│   ├── MINIO_MODEL_MANAGEMENT.md
│   └── MINIKUBE_SETUP_LEGACY.md
├── context/               ← Reference documentation
│   ├── ARCHITECTURE.md    ← Stack, project structure, patterns
│   └── WORKFLOWS.md       ← Documentation lifecycle
├── designs/               ← Architecture decision records & analysis
│   ├── 001-kubeflow-native-pivot.md
│   ├── kfp-components.md
│   ├── ingestion-pipeline.md
│   └── ...
└── plans/                 ← Task & project planning
    ├── active/            ← Current work (agents prioritize this)
    ├── implemented/       ← Completed plans
    └── backlog/           ← Future ideas
```

---

## 🤖 Agent Workflow Instructions

### When Implementing a Feature

**Step-by-Step**:
1. **Read** [`plans/active/`](plans/active/) to find relevant plan
2. **Check** plan frontmatter for `related_files`
3. **Read** linked files and relevant guides
4. **Implement** the task
5. **Update** plan frontmatter: Check off task in `completion` list
6. **Update** `date_updated` in plan frontmatter
7. **Update** this README.md if status changes
8. **Commit** with descriptive message referencing plan

### When Plan is 100% Complete

```bash
# 1. Move plan to implemented
mv docs/plans/active/plan-name.md docs/plans/implemented/

# 2. Update plan frontmatter
status: implemented
date_completed: YYYY-MM-DD

# 3. Update this README
# Move row from "Active Plans" to "Recently Completed Work" table
```

---

## 📋 Plan Frontmatter Template

All plan files should have YAML frontmatter:

```yaml
---
title: "Plan: Description"
status: active | implemented | backlog
priority: high | medium | low
estimated_hours: N-M
dependencies: []
created: YYYY-MM-DD
date_updated: YYYY-MM-DD
date_completed: YYYY-MM-DD  # only for implemented
related_files:
  - backend/path/to/file.py
  - kubeflow/path/to/pipeline.py
tags:
  - relevant-tag
completion:  # only for active plans
  - [x] Step 1 - Description ✅
  - [ ] Step 2 - Description
---
```

---

## 💡 Best Practices

### For AI Agents
- ✅ **DO** read `active/` plans first
- ✅ **DO** update progress after each task
- ✅ **DO** reference guides for coding standards
- ❌ **DON'T** read backlog unless explicitly asked
- ❌ **DON'T** create duplicate documentation

### For Developers
- ✅ Use README.md as your navigation hub
- ✅ Keep plans synchronized with code
- ✅ Archive completed work promptly

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
| 7 | **Infrastructure Migration to Kind + Ray-Native Architecture** | 🚧 Active | Phase 1 is complete. Phase 2 (KubeRay) is locally verified up to the head node, pending host GPU-passthrough environment validation. Work expands next to Phase 3. |
| 8 | **Multimodal RAG — Text + Image Search** | ⏳ Backlog | TEI → Infinity + SigLIP 2, dual-engine (vLLM + SGLang VLM), cross-modal Qdrant search. 6 phases. Depends on #7. |
| 9 | **Enterprise Security Hardening** | ⏳ Backlog | RBAC (Role Based Access Control), Service Account tokens, OIDC groups integration |

**Last Status Update**: 2026-03-20

**Recently Completed**:
- ✅ **Infrastructure Migration Phase 1 Closeout** — Kind is now the accepted local baseline: slim Kubeflow overlay, direct-ingestion default, clean-slate and resumable ingestion controls, concurrent-run rejection, auth enforcement, GPU-backed local LLM validation, and end-to-end tests are all documented and verified.
- ✅ **Frontend UI Enhancements** — Premium design language (Claude-inspired), relative push sidebar, OKLCH colors, directory restructuring, and context menus.
- ✅ **Frontend UI Overhaul** — shadcn/ui + OKLCH theming, dark mode, React Query, chat UX redesign, premium animations, and performance optimizations.
- ✅ **Phase 5: Production Ingestion & Serving** — Decoupled microservices, TEI embeddings, lightweight backend, KFP ingestion
- ✅ **Dependency Standardization & Upgrades** — pnpm, uv, pyproject.toml, React 19, Vite 7, Playwright 1.58, httpx migration
- ✅ **Dev Tooling & Hybrid Mode** — nvm + pnpm + uv standardization, hybrid dev mode, deploy optimization, unified logging, backend test suite. **Update: Fixed Entra ID loops and KFP local execution issues.**
- ✅ **Phase 4: Experimentation & Tuning** — Katib hyperparameter optimization, Qdrant migration
- ✅ **Phase 3: Platform Engineering** — Kubeflow v1.11.0, Istio, Dex OIDC, Central Dashboard
- ✅ **Phase 2: Modern Data Engineering** — KFP ingestion pipeline, ChromaDB → Qdrant
- ✅ **Phase 1: Foundation** — Kubernetes operators, Istio service mesh, Kubeflow Pipelines

---

## 📚 Essential Guides

### Development Workflow
- [Getting Started](guides/GETTING_STARTED.md) - First-time setup, prerequisites, Kind bootstrap
- [Development Guide](guides/DEVELOPMENT.md) - Running locally, debugging, commands

### Architecture & Patterns
- [Architecture](context/ARCHITECTURE.md) - Stack overview, project structure, conventions
- [Workflows](context/WORKFLOWS.md) - Documentation practices, plan lifecycle

### Specialized Topics
- [Authentication](guides/AUTHENTICATION.md) - Entra ID for Vellum, Dex for Kubeflow, and Phase 1 auth enforcement
- [Katib Tuning](guides/KATIB_TUNING.md) - Phase 1 optional tuning workflow; not part of the slim default boot
- [Ingestion Verification](guides/INGESTION_VERIFICATION.md) - Verifying the Phase 1 direct-ingestion path and optional KFP runs
- [Hello World Pipeline](guides/HELLO_WORLD_PIPELINE.md) - Optional Kubeflow-era tutorial for debugging KFP itself
- [MinIO Model Management](guides/MINIO_MODEL_MANAGEMENT.md) - Historical note for older MinIO-backed model distribution flows

### Design Documents
- [ADR 001: Kubeflow Native Pivot](designs/001-kubeflow-native-pivot.md) - Why we adopted Kubeflow Native architecture
- [KFP Components Architecture](designs/kfp-components.md) - Kubeflow-era control-plane reference for the retained KFP path
- [Ingestion Pipeline](designs/ingestion-pipeline.md) - Current Phase 1 ingestion architecture: direct by default, KFP optional
- [Vector DB Tradeoffs](designs/vectordb-tradeoffs.md) - ChromaDB vs Qdrant analysis
- [Language Choice Analysis](designs/language-choice-analysis.md) - Go vs Python for control plane
- [Infrastructure Analysis](designs/infra-structure-analysis.md) - Monorepo vs Polyrepo
- [Kubeflow Platform Plan](designs/kubeflow-platform-plan.md) - Historical plan for the earlier Kubeflow-platform consolidation
- [Phase 2 Walkthrough](designs/phase2-walkthrough.md) - Ingestion pipeline implementation report
- [Phase 3 Platform Upgrade](designs/phase3-platform-upgrade.md) - Kubeflow v1.11.0 upgrade report
- [Phase 4 Migration & Tuning](designs/phase4-migration-tuning.md) - Qdrant migration & Katib results

---

## ✅ Recently Completed Work

| Plan | Completed | Summary |
|------|-----------|---------|
| **Frontend UI Enhancements** | 2026-02-16 | Claude-inspired UI, relative push sidebar, OKLCH color tokens, and React 19 component refactoring. |
| **Frontend UI Overhaul** | 2026-02-15 | Move to shadcn/ui, OKLCH theming, dark mode, React Query, premium animations, and accessibility polish. |
| **Dev Tooling & Hybrid Mode** | 2026-02-15 | Package manager standardization (nvm, pnpm, uv), hybrid development mode, deploy optimization, unified logging (structlog + LogLayer), backend test suite (16/16 passing) |
| **Phase 4: Experimentation & Tuning** | 2026-01 | Katib grid search (chunk_size=256, overlap=50, accuracy=0.8046), ChromaDB → Qdrant migration |
| **Phase 3: Platform Engineering** | 2026-01 | Kubeflow v1.11.0, Istio, Dex OIDC, Central Dashboard, Qdrant namespace |
| **Phase 2: Modern Data Engineering** | 2025-12 | KFP ingestion pipeline, semantic chunking, BGE-Large embeddings, retrieval API |
| **Phase 1: Foundation** | 2025-12 | Initial pre-migration local platform on Minikube: Kubeflow Pipelines, Katib, MinIO, and Istio operators |

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
│   └── MINIKUBE_SETUP_LEGACY.md  ← Historical reference only
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

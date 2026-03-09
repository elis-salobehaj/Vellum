# Vellum: Agent Operating Manual

## 🎯 Mission
Enterprise-grade RAG chatbot with Kubeflow-orchestrated ingestion pipelines, Qdrant vector storage, and multi-LLM support.

## ⚙️ Stack Essentials
- **Package Managers**: `uv` (Backend), `pnpm` (Frontend)
- **Infrastructure**: Kubernetes (`kind` local runtime), Kubeflow Pipelines, Istio, Qdrant

## 🚨 Critical Rules
1. **Backend setup**: Run `cd backend && uv sync` to install all dependencies.
2. **Frontend setup**: Run `cd frontend && pnpm install`.
3. **Platform setup**: Run `./scripts/setup-kind.sh` to bootstrap the active local K8s cluster. `./scripts/setup-platform.sh` is only a compatibility wrapper.
4. **Never modify `.env` or AWS Secret keys directly**.
5. **Always ask** before changing a Kubeflow workflow ID or prompt version.
6. **Update Plans**: Check off tasks in `docs/plans/active/*.md` as you complete them.
7. **Update Index**: Update `docs/README.md` when plans change status.
8. **Commit Messages**: ALWAYS use [Conventional Commits](https://www.conventionalcommits.org/). Use `feat!:` or `fix!:` for breaking changes to trigger major version bumps via Release Please.

## 📖 Guides
- **Getting Started**: [`docs/guides/GETTING_STARTED.md`](docs/guides/GETTING_STARTED.md) ← Setup for new developers
- **Development**: [`docs/guides/DEVELOPMENT.md`](docs/guides/DEVELOPMENT.md) ← Running, debugging, commands
- **Architecture**: [`docs/context/ARCHITECTURE.md`](docs/context/ARCHITECTURE.md) ← Stack, patterns, conventions
- **Workflows**: [`docs/context/WORKFLOWS.md`](docs/context/WORKFLOWS.md) ← Documentation practices

## 🗺️ Active Work
Always check [`docs/README.md`](docs/README.md) for current plans and priorities.
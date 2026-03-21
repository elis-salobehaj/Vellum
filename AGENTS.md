# Vellum: Agent Operating Manual

## 🎯 Mission
Enterprise-grade RAG chatbot with a Kind-hosted Phase 1 platform, Qdrant vector storage, direct ingestion as the local default, and multi-LLM support.

## ⚙️ Stack Essentials
- **Package Managers**: `uv` (Backend), `pnpm` (Frontend)
- **Infrastructure**: Kubernetes (`kind` local runtime), slim Kubeflow Phase 1 stack, Istio, Qdrant, TEI, and optional KFP/KServe paths for targeted validation

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

## 🔧 Agent Skills

Skills follow the [Agent Skills open standard](https://agentskills.io).
Located at `.agents/skills/<skill-name>/SKILL.md`.
Auto-discovered by Cursor, VSCode Copilot, OpenCode, and Antigravity.

Current repo skills include:
- `plan-implementation` for producing thorough, repo-aware implementation plans
- `review-plan-implementation` for ruthless pre-implementation plan audits (architecture, security, dependencies, resilience)
- `review-plan-phase` for principal-engineer audits of plan-driven implementation phases with auto-remediation

## ✅ Plan Completion Gate

When work is driven by a markdown plan file, do not mark a phase, milestone, or plan item complete until you have run the `review-plan-phase` skill or performed the equivalent review standard yourself.

For plan-driven work, agents must:
- compare the implementation against the governing plan file item by item
- verify adherence to this file, including pnpm-only workflows for frontend, uv-only for backend, FastAPI schemas via Pydantic, and security requirements
- inspect whether the implementation is thorough rather than scaffolded, shallow, or shortcut-based
- verify tests are present and meaningful where the plan implies new behavior
- verify all required documentation and plan-tracking updates were completed, including `docs/README.md` and relevant files under `docs/plans/`
- produce a report that distinguishes what was implemented correctly from what was missed or still needs work

If the review identifies gaps, do not start remediation automatically unless the review determines no human decisions are needed. The `review-plan-phase` skill handles both review and remediation in a single pass — it auto-remediates when safe and stops for human input when architectural or scope decisions are required.

Do not present a plan phase as complete based only on passing checks, partial scaffolding, or code that roughly resembles the plan. Completion requires alignment across implementation, tests, documentation, and plan bookkeeping.

## 🗺️ Active Work

Always check [`docs/README.md`](docs/README.md) for current plans and priorities.
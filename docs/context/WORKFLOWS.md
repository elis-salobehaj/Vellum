# Documentation & Workflow

## Documentation Structure

### Primary Files
- **[`docs/README.md`](../README.md)**: Task and plan tracking (start here)
- **[`AGENTS.md`](../../AGENTS.md)**: Agent operating manual (root reference)

### Guides (How-To)
- `docs/guides/GETTING_STARTED.md` - First-time setup & Kind bootstrap
- `docs/guides/DEVELOPMENT.md` - Running and debugging
- `docs/guides/AUTHENTICATION.md` - Entra ID for Vellum, Dex for Kubeflow, security
- `docs/guides/KATIB_TUNING.md` - Phase 1 optional hyperparameter tuning
- `docs/guides/INGESTION_VERIFICATION.md` - Verifying direct ingestion and optional KFP runs
- `docs/guides/HELLO_WORLD_PIPELINE.md` - Optional KFP tutorial for Kubeflow debugging
- `docs/guides/MINIO_MODEL_MANAGEMENT.md` - Historical note for older model-distribution flow

### Context (Reference)
- `docs/context/ARCHITECTURE.md` - Stack & conventions
- `docs/context/WORKFLOWS.md` - This file

### Designs
- `docs/designs/` - Architecture Decision Records (ADRs) and trade-off analyses

### Plans
- `docs/plans/active/` - Current implementation plans
- `docs/plans/implemented/` - Completed work
- `docs/plans/backlog/` - Future ideas

---

## Maintenance Rules

### When Completing Tasks
1. **Check off items** in the plan's frontmatter completion list
2. **Update `date_updated`** in plan frontmatter
3. **Update status** in `docs/README.md` table

### Local Platform Workflow
1. Treat `./scripts/setup-kind.sh` as the primary completed Phase 1 bootstrap.
2. `./scripts/setup-platform.sh` is a compatibility wrapper and should mirror `setup-kind.sh` behavior.
3. Keep `deployment/kustomization.yaml` aligned with the active local default. In completed Phase 1, that means the slim Kubeflow overlay on Kind.
4. Document `INGESTION_MODE=direct` as the default ingestion path unless a guide is explicitly about debugging KFP.
5. Keep Kubeflow-era and Minikube-era guides clearly marked as optional or historical.

### When Completing a Plan
1. **Move file** from `plans/active/` to `plans/implemented/`
2. **Set** `status: implemented` and `date_completed: YYYY-MM-DD` in frontmatter
3. **Update** `docs/README.md` — move from Active to Recently Completed

### When Creating Artifacts
- **Plans**: Start in `docs/plans/active/`
- **Designs**: Save to `docs/designs/`

---

## Code Review Ignore List

Exclude from AI code suggestions:
- `docs/plans/backlog/` (not active work)
- `docs/plans/implemented/` (historical only)
- `docs/designs/phase*` (implementation reports, not active code)

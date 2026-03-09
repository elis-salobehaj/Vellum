# Documentation & Workflow

## Documentation Structure

### Primary Files
- **[`docs/README.md`](../README.md)**: Task and plan tracking (start here)
- **[`AGENTS.md`](../../AGENTS.md)**: Agent operating manual (root reference)

### Guides (How-To)
- `docs/guides/GETTING_STARTED.md` - First-time setup & Kind bootstrap
- `docs/guides/DEVELOPMENT.md` - Running and debugging
- `docs/guides/AUTHENTICATION.md` - Entra ID SSO, Dex, security
- `docs/guides/KATIB_TUNING.md` - Hyperparameter optimization
- `docs/guides/INGESTION_VERIFICATION.md` - Verifying pipeline runs
- `docs/guides/HELLO_WORLD_PIPELINE.md` - First KFP pipeline
- `docs/guides/MINIO_MODEL_MANAGEMENT.md` - Model storage

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
1. Treat `./scripts/setup-kind.sh` as the primary Phase 1 bootstrap.
2. `./scripts/setup-platform.sh` is a compatibility wrapper and should mirror `setup-kind.sh` behavior.
3. Keep `deployment/kustomization.yaml` aligned with the active local default. In Phase 1, that means the slim Kubeflow overlay.
4. Keep `docs/guides/MINIKUBE_SETUP_LEGACY.md` clearly marked as historical until the later archival phase is complete.

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

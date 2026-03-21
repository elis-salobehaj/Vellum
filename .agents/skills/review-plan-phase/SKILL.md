---
name: review-plan-phase
description: >
  Principal-engineer review and remediation workflow for Vellum implementation
  phases. Audits whether an implementation fully followed a plan, checks code
  and architecture against AGENTS.md, categorizes findings, saves a report,
  and executes remediation when no human decisions are required.
argument-hint: 'Describe the plan file, phase, and implementation scope to review.'
license: Apache-2.0
---

# Review Plan Phase

Use this skill to audit a completed implementation phase against its plan.

## Outcome
A report in `docs/reports/current/` ranking findings and proposing `[agent]` or `[human]` remediation steps. Can auto-remediate if only `[agent]` steps exist.

## Procedure

### Step 1 - Load Context
Read plan, `AGENTS.md`, `ARCHITECTURE.md`, `WORKFLOWS.md`.

### Step 2 - Extract Obligations
Determine what was supposed to be built (FastAPI routes, React components, KFP pipelines, Qdrant schemas, Istio configurations).

### Step 3 - Compare
Audit the current git changes. Detect unimplemented plan details or shallow implementations.

### Step 4 - Check Compliance
- Python: `uv`, Pydantic v2, `structlog`.
- Node: `pnpm`, React 19, Tailwind 4.
- K8s: Kind manifests updated.
- Docs/Plan bookkeeping updated.

### Step 5 - Classify
Group as `BLOCKER`, `RISK`, `OPTIMIZATION`. Provide alternative fix.

### Step 6 - Create Remediation Plan
Determine if `[human]` intervention is required. If not, auto-remediate `[agent]` steps and run validators:
- Backend: `cd backend && uv run ruff check && uv run pytest`
- Frontend: `cd frontend && pnpm check && pnpm test`
Save to `docs/reports/current/<phase>-review-<date>-<hash>.md`.

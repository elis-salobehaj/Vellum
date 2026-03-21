---
name: plan-implementation
description: >
  Produces thorough, repo-aware implementation plans for Vellum. Gathers deep
  context from AGENTS.md, docs/, and source code before proposing architecture,
  tech stack decisions, tradeoffs, and phased implementation steps. Produces a
  markdown plan file consistent with existing plan conventions. Asks the user
  clarifying questions when decisions impact architecture, structure, or tech stack
  before finalizing.
argument-hint: 'Describe the feature, change, or capability to plan. Include any constraints or preferences.'
license: Apache-2.0
---

# Plan Implementation

Use this skill to produce a detailed, actionable implementation plan for a new
feature, capability, or architectural change in Vellum. The plan must be
grounded in the actual codebase — not generic advice — and must follow the
conventions established by existing plans in this repository.

## Outcome

Produce a markdown plan file saved to `docs/plans/backlog/` (default) or `docs/plans/active/`
(when the user explicitly requests active, or when no active plans exist) that:
- is grounded in the current architecture, tech stack, and conventions of Vellum
- evaluates technology choices and tradeoffs when the feature introduces new tools, libraries, or patterns
- proactively suggests superior alternatives when a clearly better option exists
- proposes a phased implementation with concrete, checkable tasks per phase
- identifies affected files and systems across the repository (backend, frontend, kubeflow, deployment)
- includes a YAML frontmatter block consistent with existing plans
- includes a completion checklist with unchecked task IDs that match the phase structure
- places architectural diagrams and plan overview at the top of the document for fast human consumption

## When To Use

Use this skill for:
- planning a new feature or capability before implementation begins
- planning an architectural change, refactor, or migration
- evaluating and deciding on new libraries, tools, or runtime changes
- breaking down a large initiative into phased, reviewable implementation steps

Do not use this skill for:
- implementing code directly — this skill produces a plan, not code
- reviewing an existing implementation against a plan — use `review-plan-phase` instead

## Procedure

### Phase 1 — Deep Context Gathering

1. Read `AGENTS.md` in full.
2. Read `docs/README.md` to understand the documentation index.
3. Read context documentation under `docs/context/`:
   - `ARCHITECTURE.md` — stack overview, project structure, code conventions, design patterns
   - `WORKFLOWS.md` — documentation lifecycle, plan maintenance, code review practices
4. Read active plans under `docs/plans/active/` to understand in-flight work.
5. If the feature touches existing source code, read the relevant source files:
   - `backend/` — FastAPI API & RAG Retrieval
   - `frontend/` — React App, Vite, Tailwind
   - `kubeflow/` — KFP Pipeline definitions
   - `deployment/` — Kubernetes manifests, configs
6. Check compatibility with Vellum stack (Node 24, pnpm, Python 3.12, uv, FastAPI, Qdrant, Istio, Kind).

### Phase 2 — Scope and constraints
Identify blast radius, affected modules, and apply constraints:
- pnpm-only for Node.js
- uv-only for Python
- Pydantic v2 for FastAPI schemas
- Kubernetes and Istio boundaries
- Conventional Commits requirement

### Phase 3 — Tradeoffs
If introducing new dependencies, propose tradeoffs and include a decision table. Sketch Mermaid diagrams if architecture changes.

### Phase 4 — User Feedback
Ask the user if choices heavily impact the repository. Format clearly.

### Phase 5 — Plan Drafting
Produce frontmatter (title, status, priority, estimated_hours, related_files, completion checklist).
Structure:
1. Title
2. High-Level Architecture (Mermaid)
3. Executive Summary
4. Resolved Decisions
5. Problem Statement
6. Directory Structure
7. Phased Implementation (Each phase ends with docs overhaul and testing).
   - Backend testing: `cd backend && uv run pytest`
   - Frontend testing: `cd frontend && pnpm test`

### Phase 6 — Save
Save to `docs/plans/backlog/<name>.md` and update `docs/README.md`.

## Decision Rules
- Ground in actual codebase.
- Obey AGENTS.md rules.

## Completion Checks
- File written to disk
- YAML frontmatter correct
- Phases ordered with testing and documentation steps
- Checklist aligns

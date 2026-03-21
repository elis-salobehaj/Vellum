---
name: review-plan-implementation
description: >
  Ruthless pre-implementation review of Vellum implementation plans. Evaluates
  architecture and data flow, library and runtime choices, security and blast radius,
  resilience and edge cases. Categorizes findings as BLOCKER, RISK, or OPTIMIZATION
  with mandatory actionable alternatives. Use on a plan file before implementation
  begins. 
argument-hint: 'Path to the plan file to review, or omit to review the most recently created plan.'
license: Apache-2.0
---

# Review Plan Implementation

Use this skill to perform a exhaustive evaluation of an implementation plan **before any code is written**.

## Outcome
Produce a categorized review report classifying findings as `BLOCKER`, `RISK`, or `OPTIMIZATION` with alternatives.

## Target Plan Resolution
If no plan file is specified, use the most recently created one in `docs/plans/`.

## Procedure

### Step 1 — Load Context
Read `AGENTS.md`, the plan, `ARCHITECTURE.md`, `WORKFLOWS.md`, and any active plans.

### Step 2 — Architecture & Data Flow
Check module boundaries, Kubernetes deployments, FastAPI data flows, and Qdrant integration.

### Step 3 — Library & Runtime
Check Node 24/pnpm and Python 3.12/uv nativity. Validate maintenance health and avoid bloat.

### Step 4 — Security
Check OIDC token integration, Kubernetes RBAC, MinIO and Qdrant network policies. Ensure fast API inputs use Pydantic v2.

### Step 5 — Resilience
Check retry strategies for KFP, TEI, LLM endpoints. Handle malformed retrieval results gracefully.

### Step 6 — Classify and Report
Categorize as BLOCKER, RISK, OPTIMIZATION. Provide actionable alternatives.
Report format: Summary, BLOCKERs, RISKs, OPTIMIZATIONs, Strengths, Verdict.

## Rules
- Deliver concrete fixes.
- Focus strictly on architecture, security, scaling, and correctness.

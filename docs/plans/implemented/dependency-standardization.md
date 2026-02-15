---
title: "Plan: Dependency Standardization & Tooling Upgrades"
status: implemented
priority: medium
estimated_hours: 8-12
dependencies:
  - docs/plans/implemented/phase5-production-ingestion.md
created: 2026-02-15
date_updated: 2026-02-15
date_completed: 2026-02-15
related_files:
  - backend/pyproject.toml
  - frontend/package.json
  - kubeflow/pipelines/ingestion/pyproject.toml
  - deployment/manifests/tests/kserve/pyproject.toml
tags:
  - tooling
  - uv
  - pnpm
  - react19
  - vite7
completion:
  - [x] Migrate all requirements.txt to pyproject.toml ✅
  - [x] Switch backend to uv for dependency management ✅
  - [x] Switch frontend to pnpm and upgrade to React 19 + Vite 7 ✅
  - [x] Upgrade Playwright to v1.58.2 ✅
  - [x] Migrate requests to httpx for async consistency ✅
  - [x] Optimize Docker builds with root .dockerignore and multi-stage builds ✅
  - [x] Standardize ingestion pipeline with uv and pyproject.toml ✅
---

## Goal

Standardize the project's dependency management and modernize the toolchain for improved developer experience, faster builds, and better maintainability.

## Key Changes

### Python Tooling (`uv`)
- Removed all `requirements.txt` files.
- Unified backend, ingestion, and tests under `pyproject.toml`.
- Used `uv sync` and `uv lock` for reproducible builds.
- Added root `.python-version` (3.12.3).

### Frontend Tooling (`pnpm`)
- Migrated from `npm` to `pnpm`.
- Upgraded to **React 19** and **Vite 7**.
- Upgraded **Playwright** and **ESLint** to latest stable versions.

### Network Layer (`httpx`)
- Replaced `requests` with `httpx` in both application code and test suites.
- Enabled native async support for all network calls.

### Docker Optimization
- Created a root `.dockerignore` to reduce build context size from gigabytes to kilobytes.
- Refactored Dockerfiles to leverage `uv` caching and multi-stage builds.

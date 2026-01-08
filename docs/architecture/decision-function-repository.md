# Architecture Decision: Repository Structure for Crossplane Functions

## Context
We are introducing Go-based Crossplane Composition Functions to handle complex infrastructure logic. The question is whether to place these in the existing `Vellum` monorepo or create a dedicated repository (e.g., `vellum-functions`).

## Decision
**Keep Go Functions in the `Vellum` Monorepo.**

## Rationale

### 1. Developer Velocity (Priority #1)
- **Context Switching**: keeping code in one place allows simultaneous edits to the `Composition` (YAML) and the `Function` (Go) that powers it.
- **CI/CD**: Unified pipeline. One commit can trigger the Function build, push the image, and update the Composition version. separating them introduces "Dependency Hell" (did I push the new image? Is the submodule updated?).

### 2. Project Stage
- We are in the **Prototyping/Learning** phase. The overhead of managing multiple repositories (permissions, secrets, issue tracking) outweighs the "cleanliness" of separation.

### 3. Go Tooling Support
- Go modules support multi-module workspaces (`go.work`). We can have a `functions/` directory where each function is its own module, or a shared `go.mod` for all functions.

## Implementation Guide

Recommended structure:

```text
Vellum/
├── crossplane/          # YAML Definitions
│   ├── composition.yaml
│   └── ...
├── functions/           # Custom Logic
│   ├── go.mod           # Shared dependencies (optional, or per function)
│   ├── function-networking/
│   │   ├── main.go
│   │   └── Dockerfile
│   └── function-inference/
│       ├── main.go
│       └── Dockerfile
```

## Future Drivers for Split
We would only move to a separate repository if:
1.  **Shared Library**: The function is generic enough to be open-sourced or used by *other* companies/projects.
2.  **Build Times**: The monorepo CI becomes too slow (unlikely with Go's speed).
3.  **Ownership**: A separate team takes over infrastructure platforming entirely.

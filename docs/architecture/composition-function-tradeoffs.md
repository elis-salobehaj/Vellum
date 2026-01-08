# Crossplane Composition Functions: Language Trade-offs

As Vellum involves into a complex platform, the standard `function-patch-and-transform` (YAML) will hit limits. This document analyzes the alternatives for writing Composition Functions.

## 1. Patch & Transform (YAML)
The default "No-Code" approach.
- **Pros**:
    - Built-in, no extra images to build/push.
    - Declarative and safe.
    - Zero maintenance of toolchains.
- **Cons**:
    - **No Logic**: Cannot handle conditions (`if prod then x`), loops, or string manipulation easily.
    - **Verbose**: Patching deeply nested fields is painful.
    - **Debugging**: Hard to trace why a patch failed.
- **Verdict**: Keep for **Phase 1** (Simple Infrastructure). Abandon for sophisticated logic.

## 2. Templated YAML (function-go-templating)
Using Go templates (`{{ .val }}`) inside YAML patches.
- **Pros**:
    - **Logic Lite**: Adds loops (`range`) and conditionals (`if`) to YAML.
    - **No Build**: Still just configuration text, no binaries to compile.
- **Cons**:
    - **Complexity Wall**: "Programming in YAML" quickly becomes unreadable.
    - **Tooling**: Lacks IDE support, debuggers, and unit tests compared to real languages.
- **Verdict**: A middle ground, but often combines the "verbosity of YAML" with the "obscurity of templates". Better to jump straight to a real language for complex logic.

## 2. Python (function-script)
Writing logic in Python scripts embedded in the Composition or loaded from files.
- **Pros**:
    - **Team Fit**: We are an MLOps team; everyone knows Python.
    - **Flexible**: Full power of Python (loops, APIs, libraries).
    - **Fast Iteration**: Can often inline code in the Composition for quick hacks.
- **Cons**:
    - **Performance**: Slower cold starts compared to Go (though often negligible for control planes).
    - **Runtime Dependency**: Needs a Python function runner.
- **Verdict**: **Strong Candidate for Phase 2/3**. Allows us to write complex logic (e.g., "Take these 3 inputs and calculate a resource request") in a language we own.

## 3. Go (function-go)
The "Cloud Native" standard.
- **Pros**:
    - **Performance**: Extremely fast, low memory footprint.
    - **Type Safety**: Compile-time checks for Kubernetes APIs.
    - **Ecosystem**: Native access to all Kubernetes libraries.
    - **Learning Opportunity**: A chance to master the language of Kubernetes (User Goal).
- **Cons**:
    - **Friction**: Requires `go build`, `docker build`, `docker push` cycle for every change.
    - **Contex Switching**: MLOps engineers might not know Go.
- **Verdict**: Use only for **Shared Core Utilities** that rarely change or need high performance.

## 4. KCL (Kubernetes Configuration Language)
A domain-specific language for configuration.
- **Pros**:
    - Designed specifically for constraints and configuration logic.
    - Safer than general-purpose languages.
- **Cons**:
    - **Niche**: Another language to learn.
    - **Ecosystem**: Smaller community than Python/Go.
- **Verdict**: **Avoid** for now to reduce cognitive load.

## Recommendation

**Adopt a "Go-First" Strategy for Platform Logic.**

**Rationale**:
1.  **Role Separation**: As you noted, the *Platform* (Infrastructure) is built by MLOps Engineers, not Data Scientists. The "Python Gap" is less relevant here.
2.  **Performance & Safety**: Go's compile-time safety prevents runtime errors in our infrastructure automation.
3.  **Learning**: This aligns with your personal goal to master Go.

**Plan**:
1.  Use **Python** for *Application Code* (KFP Pipelines, Inference Logic).
2.  Use **Go** for *Platform Code* (Crossplane Functions, Operators).



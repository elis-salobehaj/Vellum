# ADR 001: Pivot to Kubeflow Native Architecture

**Date:** 2026-01-02
**Status:** Accepted

## Context
Vellum started as a "Franken-stack" (Airflow + BentoML + MLflow) on Minikube. To maximize learning of Kubernetes patterns and align with Enterprise MLOps standards, we evaluated pivoting to native Kubeflow components.

## Decision
We will adopt a "Kubeflow Native" architecture, prioritizing standard Operators over custom scripts.

### 1. KServe (Replacing BentoML)
We will wrap the LlamaIndex logic in a KServe `InferenceService` (V2 Protocol).
*   **Why**: Standardization (Triton compatible), Serverless scaling (Knative), and Canary deployments.

### 2. Polars (Replacing Pandas)
We will use Polars for data processing within Kubeflow Pipelines.
*   **Why**: High-performance "Single Node" processing. Bridges the gap to Spark logic (LazyFrames) without JVM overhead.

### 3. Kubeflow Pipelines & Metadata
We will use KFP as the core orchestration engine and explicitly define Artifacts.
*   **Why**: Automated Lineage Tracking via ML Metadata (MLMD).

### 4. Kubeflow Model Registry (Hybrid)
We will use a Dual Registry pattern.
*   **MLflow**: For Experiment Tracking (messy logs).
*   **Kubeflow Model Registry**: For Production "Gold Records" (clean CRDs).

### 5. Kubeflow Katib
We will use Katib for automated hyperparameter tuning.

## Consequences
*   **Infrastructure Complexity**: significantly increased. Requires maintaining Istio, Knative, and multiple Operators.
*   **Learning Curve**: Steeper, involving CRDs for everything (`InferenceService`, `Experiment`, `Pipeline`).

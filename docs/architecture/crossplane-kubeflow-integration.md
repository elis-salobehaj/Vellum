# Crossplane + Kubeflow: The Integration Model

You asked how these two giants work together. In our Vellum stack, they have distinct but complementary roles.

## The Concept: "Infrastructure as Data"
*   **Crossplane** is the **General Contractor**. It builds the building, installs the plumbing, and ensures the electricity works.
*   **Kubeflow** is the **Factory Equipment** installed inside the building. It runs the assembly lines (Pipelines) and machinery (Training/Inference).

## The Implementation: Declarative Stack
We will not just "run helm install commands" manually. We will make Crossplane manage Kubeflow itself.

### 1. Crossplane installs Kubeflow (The "Bootstrap")
We will use the **Crossplane Helm Provider**.
Instead of you typing `helm install kubeflow`, we define a Crossplane object:
```yaml
apiVersion: helm.crossplane.io/v1beta1
kind: Release
metadata:
  name: kubeflow-pipelines
spec:
  forProvider:
    chart:
      name: kfp-operator
      repository: https://...
```
*   **Benefit**: If the Kubeflow operator crashes or is deleted, Crossplane puts it back. The *entire platform* is defined in git.

### 2. Crossplane provisions Dependencies (The "Wiring")
Kubeflow Pipelines needs an Object Store (MinIO/S3) to store artifacts (PDF chunks, models).
*   **Without Crossplane**: KFP tries to self-provision a messy MinIO pod, or you manually set up buckets and secrets.
*   **With Crossplane**:
    1.  Crossplane creates a `Bucket` (e.g., `vellum-artifacts`).
    2.  Crossplane writes the `Secret` (access keys) into the `kubeflow` namespace.
    3.  KFP starts up and immediately uses that secure bucket.

### 3. The "Platform API" (XRD)
We can update our `MLOpsPlatform` XRD to include Kubeflow features.
*   **Developer Request (`Claim`)**:
    ```yaml
    kind: MLOpsPlatform
    spec:
      notebooks: enabled  # <--- New flag!
    ```
*   **Crossplane Action**:
    1.  Provisions Namespace.
    2.  Provisions Qdrant.
    3.  **Installs a Jupyter Notebook CR** into that namespace for the user.

## Summary of Responsibilities

| Feature | Managed By | Why? |
| :--- | :--- | :--- |
| **Namespaces** | Crossplane | Governance & Labels |
| **Vector DB (Qdrant)** | Crossplane | It's specialized Infrastructure |
| **Object Store (MinIO)** | Crossplane | It's Infrastructure |
| **KFP Operator** | Crossplane (Helm) | "Platform on Platform" management |
| **The Pipeline Logic** | Kubeflow | It's Application Code |
| **InferenceService** | KServe (via K8s) | It's a Deployment Workload |

## Phase 1 Implications
To achieve this, our first step in Phase 1 shouldn't just be "install Istio".
It should be: **"Install Crossplane Helm Provider, then use it to install Istio."**

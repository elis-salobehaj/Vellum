# Katib Hyperparameter Tuning Guide

Katib is Kubeflow's hyperparameter tuning engine. Vellum uses Katib to optimize RAG pipeline parameters (chunk size, chunk overlap) for retrieval quality.

## Prerequisites
- Kubeflow platform running (`./scripts/setup-platform.sh`)
- Port-forwards active (`./scripts/connect.sh`)
- Documents ingested into Qdrant

## Concepts

### What is Katib?
Katib automates hyperparameter search by:
1. Defining a **search space** (which parameters to tune and their ranges).
2. Running **trials** (pipeline runs with different parameter combinations).
3. Tracking a **metric** (the objective to optimize).
4. Selecting the **best trial** based on the metric.

### Katib Experiment CRD
An experiment is defined as a Kubernetes Custom Resource:

```yaml
apiVersion: kubeflow.org/v1beta1
kind: Experiment
metadata:
  name: rag-tuning-v1
  namespace: kubeflow
spec:
  objective:
    type: maximize
    goal: 0.95
    objectiveMetricName: accuracy
  algorithm:
    algorithmName: grid
  parallelTrialCount: 3
  maxTrialCount: 12
  parameters:
    - name: chunk_size
      parameterType: int
      feasibleSpace:
        list: ["128", "256", "512", "1024"]
    - name: chunk_overlap
      parameterType: int
      feasibleSpace:
        list: ["20", "50", "100"]
  trialTemplate:
    primaryContainerName: training-container
    trialParameters:
      - name: chunk_size
        reference: chunk_size
      - name: chunk_overlap
        reference: chunk_overlap
    trialSpec:
      apiVersion: batch/v1
      kind: Job
      spec:
        template:
          spec:
            containers:
              - name: training-container
                image: vellum-ingest:local
                command:
                  - "python"
                  - "/app/scripts/run_ingestion.py"
                  - "--chunk_size=$(trialParameters.chunk_size)"
                  - "--chunk_overlap=$(trialParameters.chunk_overlap)"
            restartPolicy: Never
```

## Running an Experiment

### 1. Submit the Experiment
```bash
kubectl apply -f kubeflow/experiments/rag-tuning.yaml
```

### 2. Monitor Progress
**Via Kubeflow Dashboard**:
- Navigate to http://localhost:8080
- Click **Katib** in the sidebar
- Select your experiment to see trial progress

**Via CLI**:
```bash
# Watch experiment status
kubectl get experiment rag-tuning-v1 -n kubeflow -w

# Check individual trials
kubectl get trials -n kubeflow

# View trial logs
kubectl logs -n kubeflow -l katib.kubeflow.org/experiment=rag-tuning-v1 -f
```

### 3. Get Best Parameters
```bash
kubectl get experiment rag-tuning-v1 -n kubeflow -o jsonpath='{.status.currentOptimalTrial}'
```

## Vellum's Optimal Parameters (Phase 4 Results)

Our Katib grid search (`rag-tuning-v3`) found:

| Parameter | Search Space | Optimal |
|-----------|-------------|---------|
| **chunk_size** | [128, 256, 512, 1024] | **256** |
| **chunk_overlap** | [20, 50, 100] | **50** |
| **accuracy** | — | **0.8046** |

These are the current platform defaults in:
- `kubeflow/pipelines/ingestion/pipeline.py` (ingestion defaults)
- `backend/app/services/rag_service.py` (retrieval defaults)

## Tips

### Choosing a Search Algorithm
| Algorithm | Use Case |
|-----------|----------|
| **grid** | Small search space, exhaustive coverage (what we used) |
| **random** | Large search space, good coverage with fewer trials |
| **bayesian** | Adaptive search, learns from previous trials |

### Resource Management
Katib trials run as Kubernetes Jobs. On Minikube, limit `parallelTrialCount` to avoid resource exhaustion:
```yaml
parallelTrialCount: 2  # Safe for 12GB RAM Minikube
maxTrialCount: 12
```

## See Also
- [Phase 4 Report](../designs/phase4-migration-tuning.md) — Detailed tuning results
- [Ingestion Pipeline](../designs/ingestion-pipeline.md) — Architecture being tuned
- [Vector DB Tradeoffs](../designs/vectordb-tradeoffs.md) — Why Qdrant

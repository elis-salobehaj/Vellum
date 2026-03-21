# Ray Cluster Operations Guide

This guide covers interacting with the `vellum-ray` RayCluster via the Ray Dashboard, KubeRay operator logs, and CLI.

## Accessing the Dashboard

The Ray Dashboard is the primary visual interface for monitoring the cluster. 

During local development with `./scripts/connect.sh`, you can access the dashboard at:
**http://localhost:8265**

## Cluster Topology

The cluster is defined in `deployment/ray-cluster.yaml` and deploys to the `vellum-ray` namespace:
- **Head Node**: Manages cluster state, dashboard, and job scheduling.
- **Worker Node (GPU)**: A specialized worker group with `nvidia.com/gpu=1` requested. Tasks decorated with `num_gpus=1` will automatically be scheduled here.

## Common Workflows

### 1. View Logs for a Custom Job
From the Dashboard `http://localhost:8265`:
1. Navigate to the **Jobs** tab.
2. Select the Job ID you submitted.
3. You can view standard out, standard error, and task breakdowns directly.

### 2. Inspect Memory and Actors
1. Navigate to the **Actors** tab to see running stateful actors.
2. The **Metrics** tab provides Prometheus-backed charts for CPU, GPU VRAM, and RAM utilization across the nodes.

### 3. Submitting a Job via CLI
If you want to run arbitrary Python scripts on the cluster without setting up a full Ray Serve deployment, use `ray job submit`:

```bash
# Ensure Ray Dashboard is port-forwarded over 8265
export RAY_ADDRESS="http://localhost:8265"

# Submit a job
ray job submit -- python scripts/gpu_smoke_test.py
```

## Troubleshooting

### KubeRay Operator
If the `RayCluster` CRD is failing to reconcile or Pods aren't being created:
```bash
# View KubeRay Operator logs
kubectl logs -n kuberay-system deploy/kuberay-operator
```

### Pod Scheduling Issues (Pending)
If the worker pod is stuck in `Pending`, usually it's waiting for resources (like a GPU):
```bash
kubectl describe pod -l ray.io/node-type=worker -n vellum-ray
```
On Kind, scaling down other GPU workloads (like `llm-service-predictor`) may be required:
```bash
kubectl scale deployment llm-service-predictor -n kubeflow-vellum --replicas=0
```

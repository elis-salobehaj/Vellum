#!/usr/bin/env bash
# Consolidated Port-Forward Script
# Usage: ./scripts/connect.sh

set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/cluster-common.sh"

ensure_project_root
load_env_file
require_commands kubectl
require_kubectl_access

echo "🔌 Establishing Port Forwards..."

pkill -f "kubectl port-forward" >/dev/null 2>&1 || true
sleep 2

HYBRID=false
if [[ "${1:-}" == "--hybrid" ]]; then
  HYBRID=true
  echo "🚀 Hybrid Mode: Skipping Backend (8000) and Frontend (9090) port-forwards..."
fi

start_port_forward() {
  local namespace="$1"
  local resource="$2"
  local ports="$3"
  local label="$4"
  local url="$5"

  if ! kubectl get -n "$namespace" "$resource" >/dev/null 2>&1; then
    echo "⚠️  Skipping ${label}: ${resource} not found in namespace ${namespace}."
    return 0
  fi

  nohup kubectl port-forward -n "$namespace" "$resource" "$ports" > /dev/null 2>&1 &
  echo "✅ ${label}: ${url}"
}

start_port_forward istio-system svc/istio-ingressgateway 8080:80 "Dashboard" "http://localhost:8080"
start_port_forward qdrant svc/qdrant 6333:6333 "Qdrant" "http://localhost:6333"
start_port_forward kubeflow svc/ml-pipeline 8888:8888 "KFP API" "http://localhost:8888"
start_port_forward kubeflow-vellum svc/embeddings-service 8082:80 "Embeddings" "http://localhost:8082"
start_port_forward kubeflow svc/minio-service 9000:9000 "MinIO" "http://localhost:9000"

if [[ "$HYBRID" == false ]]; then
  start_port_forward kubeflow-vellum svc/backend 8000:8000 "Backend" "http://localhost:8000"
fi

if bool_is_true "$ENABLE_LOCAL_LLM"; then
  if kubectl get deployment llm-service-predictor -n kubeflow-vellum -o jsonpath='{.spec.replicas}' 2>/dev/null | grep -qx '1'; then
    start_port_forward kubeflow-vellum svc/llm-service-predictor 8081:80 "LLM Service" "http://localhost:8081"
  else
    echo "ℹ️  Local LLM deployment is scaled down; skipping LLM port-forward."
  fi
else
  echo "ℹ️  ENABLE_LOCAL_LLM=${ENABLE_LOCAL_LLM}; skipping LLM port-forward."
fi

if [[ "$HYBRID" == false ]]; then
  start_port_forward kubeflow-vellum svc/frontend 9090:80 "Frontend" "http://localhost:9090"
fi

echo "Running in background. Kill with 'pkill -f \"kubectl port-forward\"'."

#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/cluster-common.sh"

use_default_kubeconfig

echo "☢️  NUKING Entire Vellum Platform..."
echo "⚠️  Press Ctrl+C within 5 seconds to cancel..."
sleep 5

pkill -f "kubectl port-forward" >/dev/null 2>&1 || true

if kind_cluster_exists; then
    echo "🧨 Deleting Kind cluster '${KIND_CLUSTER_NAME}'..."
    kind delete cluster --name "$KIND_CLUSTER_NAME"
    rm -f "$KIND_KUBECONFIG_PATH"
    exit 0
fi

echo "ℹ️  No managed local cluster detected. Falling back to namespace cleanup on the current context."

NAMESPACES=(
    kubeflow
    istio-system
    cert-manager
    auth
    oauth2-proxy
    knative-serving
    knative-eventing
    knative-operator
    kubeflow-vellum
    qdrant
    kubeflow-system
)

kubectl delete profiles --all --all-namespaces --wait=false 2>/dev/null || true
kubectl get profiles --all-namespaces -o name 2>/dev/null | xargs -r -n 1 kubectl patch -p '{"metadata":{"finalizers":[]}}' --type=merge 2>/dev/null || true

for ns in "${NAMESPACES[@]}"; do
    kubectl delete namespace "$ns" --wait=false 2>/dev/null || true
done

echo "✨ Cleanup request submitted to the active cluster context."

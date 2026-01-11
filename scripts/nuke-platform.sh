#!/bin/bash
set -e

# List of namespaces to destroy
NAMESPACES=(
    "kubeflow"
    "istio-system"
    "cert-manager"
    "auth"
    "oauth2-proxy"
    "knative-serving"
    "knative-eventing"
    "knative-operator"
    "kubeflow-user-example-com"
    "qdrant"
    "kubeflow-system"
)

echo "☢️  NUKING Entire Vellum Platform..."
echo "Targeting namespaces: ${NAMESPACES[*]}"
echo "⚠️  Press Ctrl+C within 5 seconds to cancel..."
sleep 5

# 0. Prerequisite: Delete Profiles to avoid Namespace Deadlocks
# Profiles manage user namespaces. If they exist, the namespace will fight deletion.
echo "🔪 Removing Kubeflow Profiles..."
kubectl delete profiles --all --all-namespaces --wait=false 2>/dev/null || true
# Patch them just in case
kubectl get profiles --all-namespaces -o name 2>/dev/null | xargs -r -n 1 kubectl patch -p '{"metadata":{"finalizers":[]}}' --type=merge 2>/dev/null || true

for ns in "${NAMESPACES[@]}"; do
    if kubectl get ns "$ns" &> /dev/null; then
        echo "🗑️  Deleting '$ns'..."
        kubectl delete ns "$ns" --wait=false || true
    else
        echo "Example '$ns' already gone."
    fi
done

echo "⏳ Waiting for resources to terminate & Force Patching..."

# Loop until all namespaces are gone
while true; do
    REMAINING_NS=()
    for ns in "${NAMESPACES[@]}"; do
        if kubectl get ns "$ns" &> /dev/null; then
            REMAINING_NS+=("$ns")
        fi
    done

    if [ ${#REMAINING_NS[@]} -eq 0 ]; then
        echo "✅ All namespaces deleted!"
        break
    fi

    echo "🔥 Remaining: ${REMAINING_NS[*]}"
    
    for ns in "${REMAINING_NS[@]}"; do
        echo "   👉 Assessing '$ns'..."
        
        # Ensure it is actually deleting
        kubectl delete ns "$ns" --wait=false 2>/dev/null || true
        
        # 1. Aggressively find and patch finalizers for EVERYTHING
        # We suppress errors because many resources will be deleting/gone
        kubectl get all -n "$ns" -o name 2>/dev/null | xargs -r -n 1 kubectl patch -n "$ns" -p '{"metadata":{"finalizers":[]}}' --type=merge 2>/dev/null || true
        
        # 2. Specific CRD types that hang or are important to clear
        for type in profiles viewers notebooks applications statefulsets replicasets jobs cronjobs daemonsets trainjobs trials experiments suggestions; do
             kubectl get "$type" -n "$ns" -o name 2>/dev/null | xargs -r -n 1 kubectl patch -n "$ns" -p '{"metadata":{"finalizers":[]}}' --type=merge 2>/dev/null || true
        done
        
        # 3. Force delete namespace if it's really stubborn (finalize)
         if command -v jq &> /dev/null; then
             kubectl get ns "$ns" -o json | jq '.spec.finalizers = []' | kubectl replace --raw "/api/v1/namespaces/$ns/finalize" -f - || true
         else
             echo "⚠️ jq not found, skipping API finalize call. Install jq for better cleanup."
         fi
    done

    echo "⏳ Waiting for ${#REMAINING_NS[@]} namespaces to vanish..."
    echo "😴 Sleeping 10s..."
    sleep 10
done

echo "🔍 Double Checking that NO resources remain in target namespaces..."
for ns in "${NAMESPACES[@]}"; do
    if kubectl get ns "$ns" &> /dev/null; then
         echo "❌ ERROR: Namespace $ns still exists!"
         exit 1
    fi
done

echo "🧹 Namespaces deleted."

echo "🗑️  Deleting Custom Resource Definitions (CRDs)..."
# List of CRD patterns to delete
CRD_PATTERNS=(
  "kubeflow.org"
  "istio.io"
  "knative.dev"
  "cert-manager.io"
  "dex.coreos.com"
  "argoproj.io"
  "kserve.io"
  "crossplane.io"
  "vellum.io"
  "metacontroller.k8s.io"
  "sparkoperator.k8s.io"
  "trainer.kubeflow.org"
  "jobset.x-k8s.io"
)

for PATTERN in "${CRD_PATTERNS[@]}"; do
    echo "Searching for CRDs matching: ${PATTERN}"
    # Find CRDs matching the pattern
    CRDS=$(kubectl get crds -o name | grep "${PATTERN}" || true)
    
    if [ -n "$CRDS" ]; then
        echo "Found CRDs to delete:"
        echo "$CRDS"
        
        # Patch finalizers to ensure they can be deleted
        echo "$CRDS" | xargs -r -I {} sh -c 'kubectl patch {} -p "{\"metadata\":{\"finalizers\":[]}}" --type=merge &> /dev/null && echo "🔨 Patched finalizer on {}"'
        
        # Delete the CRDs
        echo "$CRDS" | xargs -r kubectl delete --timeout=30s --wait=false
    fi
done

echo "✨ Cluster is nuke-clean! Ready for fresh setup."

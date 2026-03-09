#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/cluster-common.sh"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

ensure_project_root
load_env_file
require_commands docker kubectl helm kind
ensure_kubeflow_manifests_submodule

export CLUSTER_RUNTIME=kind

apply_with_retries() {
    local mode="$1"
    local target="$2"
    local description="$3"
    local max_retries="${4:-10}"
    local delay_seconds="${5:-30}"
    local count=0

    echo -e "${BLUE}🌐 Applying ${description}...${NC}"
    until if [[ "$mode" == "-k" ]]; then
        kubectl kustomize --load-restrictor=LoadRestrictionsNone "$target" | kubectl apply --server-side --force-conflicts -f -
    else
        kubectl apply "$mode" "$target" --server-side --force-conflicts
    fi; do
        count=$((count + 1))
        if [[ "$count" -ge "$max_retries" ]]; then
            echo "Failed to apply ${description} after ${max_retries} attempts." >&2
            return 1
        fi
        echo -e "${YELLOW}⚠️  ${description} apply failed. Waiting ${delay_seconds}s before retry (${count}/${max_retries})...${NC}"
        sleep "$delay_seconds"
    done
}

wait_for_endpoints() {
    local namespace="$1"
    local service_name="$2"
    local timeout_seconds="$3"
    local elapsed=0

    while [[ "$elapsed" -lt "$timeout_seconds" ]]; do
        if [[ -n "$(kubectl get endpoints "$service_name" -n "$namespace" -o jsonpath='{.subsets[*].addresses[*].ip}' 2>/dev/null)" ]]; then
            return 0
        fi
        sleep 10
        elapsed=$((elapsed + 10))
    done

    return 1
}

wait_for_knative_webhooks() {
    echo -e "${BLUE}⏳ Waiting for Knative webhooks to publish endpoints...${NC}"
    wait_for_endpoints knative-serving net-istio-webhook 300
    wait_for_endpoints knative-serving webhook 300
}

wait_for_istio_foundation() {
    echo -e "${BLUE}⏳ Waiting for the Istio control plane to stabilize before starting Knative...${NC}"
    wait_for_rollout deployment cert-manager cert-manager 300s
    wait_for_rollout deployment cert-manager-cainjector cert-manager 300s
    wait_for_rollout deployment cert-manager-webhook cert-manager 300s
    wait_for_rollout deployment dex auth 300s
    wait_for_rollout deployment oauth2-proxy oauth2-proxy 300s
    wait_for_rollout deployment istiod istio-system 300s
    wait_for_rollout deployment istio-ingressgateway istio-system 300s
    wait_for_rollout deployment cluster-local-gateway istio-system 300s
    sleep 30
}

wait_for_knative_components() {
    echo -e "${BLUE}⏳ Waiting for Knative Serving controllers...${NC}"
    wait_for_rollout deployment activator knative-serving 300s
    wait_for_rollout deployment autoscaler knative-serving 300s
    wait_for_rollout deployment controller knative-serving 300s
    wait_for_rollout deployment net-istio-controller knative-serving 300s
    wait_for_rollout deployment net-istio-webhook knative-serving 300s
    wait_for_rollout deployment webhook knative-serving 300s
}

wait_for_kubeflow_core() {
    echo -e "${BLUE}⏳ Waiting for Kubeflow core services...${NC}"
    wait_for_rollout deployment mysql kubeflow 600s
    wait_for_rollout deployment seaweedfs kubeflow 600s
    wait_for_rollout deployment admission-webhook-deployment kubeflow 600s
    wait_for_rollout deployment profiles-deployment kubeflow 600s
    wait_for_rollout deployment kubeflow-pipelines-profile-controller kubeflow 600s
    wait_for_rollout deployment metadata-grpc-deployment kubeflow 600s
    wait_for_rollout deployment metadata-envoy-deployment kubeflow 600s
    wait_for_rollout deployment metadata-writer kubeflow 600s
    wait_for_rollout deployment ml-pipeline kubeflow 600s
    wait_for_rollout deployment ml-pipeline-persistenceagent kubeflow 600s
    wait_for_rollout deployment ml-pipeline-ui kubeflow 600s
    wait_for_rollout deployment cache-server kubeflow 600s
    wait_for_rollout deployment workflow-controller kubeflow 600s
    wait_for_rollout deployment centraldashboard kubeflow 600s
}

wait_for_qdrant() {
    echo -e "${BLUE}⏳ Waiting for Qdrant...${NC}"
    wait_for_pods_ready_by_selector qdrant app.kubernetes.io/instance=qdrant 600s
}

wait_for_kserve_components() {
    echo -e "${BLUE}⏳ Waiting for KServe controllers...${NC}"
    wait_for_rollout deployment kserve-controller-manager kubeflow 600s
    wait_for_rollout deployment kserve-localmodel-controller-manager kubeflow 600s
    wait_for_rollout deployment kserve-models-web-app kubeflow 600s
}

wait_for_phase1_apps() {
    echo -e "${BLUE}⏳ Waiting for Phase 1 application workloads...${NC}"
    wait_for_job_completion model-downloader "$VELLUM_NAMESPACE" 5400s
    wait_for_rollout deployment embeddings-service "$VELLUM_NAMESPACE" 900s
    wait_for_rollout deployment backend "$VELLUM_NAMESPACE" 900s
    wait_for_rollout deployment frontend "$VELLUM_NAMESPACE" 900s

    if bool_is_true "$ENABLE_LOCAL_LLM" && cluster_has_nvidia_gpu_capacity; then
        wait_for_inferenceservice_ready llm-service "$VELLUM_NAMESPACE" 1800s
    fi
}

wait_for_vellum_profile() {
    local elapsed=0
    local timeout_seconds="${1:-180}"

    echo -e "${BLUE}⏳ Waiting for the kubeflow-vellum namespace, service accounts, and RBAC to be ready...${NC}"

    until kubectl get namespace "$VELLUM_NAMESPACE" >/dev/null 2>&1 \
        && kubectl get serviceaccount default-editor -n "$VELLUM_NAMESPACE" >/dev/null 2>&1 \
        && kubectl get serviceaccount default-viewer -n "$VELLUM_NAMESPACE" >/dev/null 2>&1 \
        && kubectl get rolebinding namespaceAdmin -n "$VELLUM_NAMESPACE" >/dev/null 2>&1 \
        && kubectl get rolebinding default-editor -n "$VELLUM_NAMESPACE" >/dev/null 2>&1 \
        && kubectl get rolebinding default-viewer -n "$VELLUM_NAMESPACE" >/dev/null 2>&1; do
        if [[ "$elapsed" -ge "$timeout_seconds" ]]; then
            echo "kubeflow-vellum profile bootstrap did not complete in time." >&2
            return 1
        fi
        sleep 5
        elapsed=$((elapsed + 5))
    done
}

apply_application_resources() {
    apply_with_retries -k "$PROJECT_ROOT/deployment/manifests/applications/kserve/kserve" "KServe core resources" 10 30
    apply_with_retries -k "$PROJECT_ROOT/deployment/manifests/applications/kserve/models-web-app/overlays/kubeflow" "the KServe models web app" 10 30

    apply_with_retries -f "$PROJECT_ROOT/deployment/vellum-namespace.yaml" "vellum-namespace.yaml" 10 30
    apply_with_retries -f "$PROJECT_ROOT/deployment/vellum-profile.yaml" "vellum-profile.yaml" 10 30
    apply_with_retries -f "$PROJECT_ROOT/deployment/vellum-profile-resources.yaml" "vellum-profile-resources.yaml" 10 30
    wait_for_vellum_profile

    apply_with_retries -k "$PROJECT_ROOT/deployment/platform-apps" "the Kind Phase 1 app stack" 10 30
}

require_kind_host_runtime_prereqs() {
    local default_runtime

    default_runtime="$(docker_default_runtime || true)"
    if [[ "$default_runtime" != "nvidia" ]]; then
        return 0
    fi

    cat >&2 <<'EOF'
Kind cannot boot reliably on this host while Docker's default runtime is set to nvidia.

Host fix required before rerunning setup-kind:
  1. Switch Docker's default runtime back to runc (or remove the default-runtime override).
  2. Restart Docker.
  3. Rerun ./scripts/setup-kind.sh.

Keep Docker on runc for the Kind workflow on this host.
EOF
    exit 1
}

require_kind_host_inotify_prereqs() {
        local max_user_instances

        max_user_instances="$(sysctl -n fs.inotify.max_user_instances 2>/dev/null || echo 0)"
        if [[ "$max_user_instances" -ge 1024 ]]; then
                return 0
        fi

        cat >&2 <<EOF
Kind node startup on this WSL host currently fails because fs.inotify.max_user_instances is too low (${max_user_instances}).

Required host fix before rerunning setup-kind:
    1. sudo sysctl -w fs.inotify.max_user_instances=1024
    2. echo 'fs.inotify.max_user_instances = 1024' | sudo tee /etc/sysctl.d/99-vellum-kind.conf
    3. rerun ./scripts/setup-kind.sh

Without that change, the Kind node container exits during boot with:
    Failed to create control group inotify object: Too many open files
EOF
        exit 1
}

if ! docker info >/dev/null 2>&1; then
    echo "Docker is installed but not reachable. Start Docker Desktop or Docker Engine and retry." >&2
    exit 1
fi

mkdir -p "$(dirname "$KIND_KUBECONFIG_PATH")"
require_kind_host_runtime_prereqs
require_kind_host_inotify_prereqs
require_kind_gpu_host_prereqs

echo -e "${BLUE}🚀 Bootstrapping Kind cluster '${KIND_CLUSTER_NAME}'...${NC}"
if kind_cluster_exists; then
    echo -e "${YELLOW}ℹ️  Cluster already exists. Reusing it.${NC}"
else
    kind create cluster \
        --name "$KIND_CLUSTER_NAME" \
        --config "$PROJECT_ROOT/kind-config.yaml" \
        --image "$KIND_NODE_IMAGE" \
        --kubeconfig "$KIND_KUBECONFIG_PATH" \
        --wait 300s
fi

export KUBECONFIG="$KIND_KUBECONFIG_PATH"
chmod 600 "$KIND_KUBECONFIG_PATH"
kubectl cluster-info >/dev/null

if kind_gpu_support_requested; then
    echo -e "${BLUE}🧠 Bootstrapping Kind GPU support for the local LLM...${NC}"
    bootstrap_kind_gpu_support
    echo -e "${GREEN}✅ Kind GPU prerequisites satisfied.${NC}"
fi

apply_with_retries -k "$PROJECT_ROOT/deployment/platform-foundation" "the Kind Phase 1 platform foundation" 10 30
wait_for_istio_foundation
apply_with_retries -k "$PROJECT_ROOT/deployment/manifests/common/knative/knative-serving/overlays/gateways" "Knative Serving" 10 30
wait_for_knative_webhooks
wait_for_knative_components
apply_with_retries -k "$PROJECT_ROOT/deployment/platform-kubeflow" "the Phase 1 Kubeflow core" 10 30
wait_for_kubeflow_core

echo -e "${BLUE}💾 Ensuring Qdrant release exists...${NC}"
helm repo add qdrant https://qdrant.github.io/qdrant-helm --force-update >/dev/null
helm repo update >/dev/null
if ! helm list -n qdrant | grep -q '^qdrant\b'; then
    helm install qdrant qdrant/qdrant -n qdrant --create-namespace --set replicas=1
else
    echo -e "${YELLOW}ℹ️  Qdrant already installed. Skipping Helm install.${NC}"
fi
wait_for_qdrant
apply_application_resources
wait_for_kserve_components
wait_for_phase1_apps

echo -e "${GREEN}✅ Kind Phase 1 platform setup complete.${NC}"
echo -e "${GREEN}KUBECONFIG=${KIND_KUBECONFIG_PATH}${NC}"
echo -e "${GREEN}Next steps:${NC}"
echo "  export KUBECONFIG=${KIND_KUBECONFIG_PATH}"
echo "  ./scripts/deploy-local.sh"
echo "  ./scripts/connect.sh"
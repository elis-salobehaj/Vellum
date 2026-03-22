#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/cluster-common.sh"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

ensure_project_root
load_env_file
require_commands docker kubectl helm kind istioctl

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

wait_for_istio_ambient() {
    echo -e "${BLUE}⏳ Waiting for Istio Ambient (istiod + ztunnel)...${NC}"
    wait_for_rollout deployment istiod istio-system 300s
    wait_for_rollout daemonset ztunnel istio-system 300s || true
    wait_for_rollout deployment istio-ingressgateway istio-system 300s || true
    sleep 10
}



wait_for_qdrant() {
    echo -e "${BLUE}⏳ Waiting for Qdrant...${NC}"
    wait_for_pods_ready_by_selector qdrant app.kubernetes.io/instance=qdrant 600s
}

wait_for_kserve_components() {
    echo -e "${YELLOW}ℹ️  KServe is removed from the platform in favor of Ray Serve.${NC}"
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

install_istio_ambient() {
    echo -e "${BLUE}🌐 Installing Istio Ambient mesh via istioctl...${NC}"
    if kubectl get deployment istiod -n istio-system > /dev/null 2>&1; then
        echo -e "${YELLOW}ℹ️  Istio already installed. Skipping istioctl install.${NC}"
        return 0
    fi
    istioctl install --set profile=ambient -y
    # Install the Kubernetes Gateway API CRDs required for waypoint proxies
    kubectl get crd gateways.gateway.networking.k8s.io > /dev/null 2>&1 || \
        kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.0/standard-install.yaml
    echo -e "${GREEN}✅ Istio Ambient installed.${NC}"
}

apply_application_resources() {
    apply_with_retries -f "$PROJECT_ROOT/deployment/vellum-namespace.yaml" "vellum-namespace.yaml" 3 10
    apply_with_retries -f "$PROJECT_ROOT/deployment/vellum-backend-rbac.yaml" "vellum-backend-rbac.yaml" 3 10
    apply_with_retries -f "$PROJECT_ROOT/deployment/documents-pvc.yaml" "documents-pvc.yaml" 3 10
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
    local target_value=1024

    max_user_instances="$(sysctl -n fs.inotify.max_user_instances 2>/dev/null || echo 0)"
    if [[ "$max_user_instances" -ge "$target_value" ]]; then
        return 0
    fi

    echo -e "${BLUE}🔧 Raising fs.inotify.max_user_instances from ${max_user_instances} to ${target_value} for Kind startup...${NC}"

    if [[ "$EUID" -eq 0 ]]; then
        sysctl -w fs.inotify.max_user_instances="$target_value" >/dev/null
        printf 'fs.inotify.max_user_instances = %s\n' "$target_value" > /etc/sysctl.d/99-vellum-kind.conf
    elif command -v sudo >/dev/null 2>&1; then
        sudo sysctl -w fs.inotify.max_user_instances="$target_value" >/dev/null
        printf 'fs.inotify.max_user_instances = %s\n' "$target_value" | sudo tee /etc/sysctl.d/99-vellum-kind.conf >/dev/null
    fi

    max_user_instances="$(sysctl -n fs.inotify.max_user_instances 2>/dev/null || echo 0)"
    if [[ "$max_user_instances" -ge "$target_value" ]]; then
        echo -e "${GREEN}✅ fs.inotify.max_user_instances is now ${max_user_instances}.${NC}"
        return 0
    fi

    cat >&2 <<EOF
Kind node startup on this WSL host currently fails because fs.inotify.max_user_instances is too low (${max_user_instances}).

Required host fix before rerunning setup-kind:
    1. sudo sysctl -w fs.inotify.max_user_instances=${target_value}
    2. echo 'fs.inotify.max_user_instances = ${target_value}' | sudo tee /etc/sysctl.d/99-vellum-kind.conf
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

render_kind_config() {
    local api_server_port="$1"
    local temp_config_path="$2"

    sed -E "s/(apiServerPort: ).*/\1${api_server_port}/" "$PROJECT_ROOT/kind-config.yaml" > "$temp_config_path"
}

mkdir -p "$(dirname "$MAIN_KUBECONFIG_PATH")"
touch "$MAIN_KUBECONFIG_PATH"
chmod 600 "$MAIN_KUBECONFIG_PATH"
export KUBECONFIG="$MAIN_KUBECONFIG_PATH"
require_kind_host_inotify_prereqs
require_kind_gpu_host_prereqs

echo -e "${BLUE}🚀 Bootstrapping Kind cluster '${KIND_CLUSTER_NAME}'...${NC}"
if kind_cluster_exists; then
    echo -e "${YELLOW}ℹ️  Cluster already exists. Reusing it.${NC}"
else
    api_server_port="$(find_available_local_port "$KIND_DEFAULT_API_SERVER_PORT")"
    temp_kind_config="$(mktemp)"
    trap 'rm -f "${temp_kind_config:-}"' EXIT
    render_kind_config "$api_server_port" "$temp_kind_config"

    if [[ "$api_server_port" != "$KIND_DEFAULT_API_SERVER_PORT" ]]; then
        echo -e "${YELLOW}ℹ️  Port ${KIND_DEFAULT_API_SERVER_PORT} is already in use. Using Kind API server port ${api_server_port} instead.${NC}"
    fi

    kind create cluster \
        --name "$KIND_CLUSTER_NAME" \
        --config "$temp_kind_config" \
        --image "$KIND_NODE_IMAGE" \
        --wait 300s
fi

kind export kubeconfig --name "$KIND_CLUSTER_NAME" --kubeconfig "$MAIN_KUBECONFIG_PATH" >/dev/null
ensure_kind_context
kubectl cluster-info >/dev/null

if kind_gpu_support_requested; then
    echo -e "${BLUE}🧠 Bootstrapping Kind GPU support for the local LLM...${NC}"
    bootstrap_kind_gpu_support
    echo -e "${GREEN}✅ Kind GPU prerequisites satisfied.${NC}"
fi

install_istio_ambient
wait_for_istio_ambient

echo -e "${BLUE}⚡ Ensuring KubeRay Operator exists...${NC}"
helm repo add kuberay https://ray-project.github.io/kuberay-helm/ --force-update >/dev/null
helm repo update >/dev/null
if ! helm list -n kuberay-system | grep -q '^kuberay-operator\b'; then
    helm install kuberay-operator kuberay/kuberay-operator -n kuberay-system --create-namespace --wait
else
    echo -e "${YELLOW}ℹ️  KubeRay Operator already installed. Skipping Helm install.${NC}"
fi

echo -e "${BLUE}💾 Ensuring Qdrant release exists...${NC}"
helm repo add qdrant https://qdrant.github.io/qdrant-helm --force-update >/dev/null
helm repo update >/dev/null
if ! helm list -n qdrant | grep -q '^qdrant\b'; then
    helm install qdrant qdrant/qdrant -n qdrant --create-namespace --set replicas=1
else
    echo -e "${YELLOW}ℹ️  Qdrant already installed. Skipping Helm install.${NC}"
fi
wait_for_qdrant

echo -e "${BLUE}📅 Ensuring Dagster release exists...${NC}"
helm repo add dagster https://dagster-io.github.io/helm --force-update > /dev/null
helm repo update > /dev/null
if ! helm list -n kubeflow-vellum | grep -q '^dagster\b'; then
    helm install dagster dagster/dagster -n kubeflow-vellum --create-namespace \
        -f "$PROJECT_ROOT/deployment/helm-values/dagster-values.yaml"
else
    echo -e "${YELLOW}ℹ️  Dagster already installed. Skipping Helm install.${NC}"
fi

apply_application_resources

# Deploy Vellum application stack (backend, frontend, Istio resources, etc.)
apply_with_retries -k "$PROJECT_ROOT/deployment" "Vellum application stack" 5 20

echo -e "${GREEN}✅ Vellum platform setup complete — Istio Ambient, Qdrant, Dagster, KubeRay installed.${NC}"
if bool_is_true "$ENABLE_LOCAL_LLM_REQUESTED" && ! bool_is_true "$ENABLE_LOCAL_LLM"; then
    echo -e "${YELLOW}⚠️  Local LLM bootstrap was skipped for this run. API-backed providers are available now; the local GPU model can be enabled after Docker's NVIDIA runtime is configured.${NC}"
fi
echo -e "${GREEN}Kubeconfig merged into ${MAIN_KUBECONFIG_PATH}.${NC}"
echo -e "${GREEN}Next steps:${NC}"
echo "  ./scripts/setup-local.sh          # first-time machine setup"
echo "  kubectl config use-context ${KIND_CONTEXT_NAME}"
echo "  cd backend && uv sync"
echo "  cd frontend && pnpm install"
echo "  ./scripts/deploy-local.sh"
echo "  ./scripts/connect.sh"
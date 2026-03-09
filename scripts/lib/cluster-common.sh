#!/usr/bin/env bash

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VELLUM_NAMESPACE="${VELLUM_NAMESPACE:-kubeflow-vellum}"
KIND_CLUSTER_NAME="${KIND_CLUSTER_NAME:-vellum}"
KIND_NODE_IMAGE="${KIND_NODE_IMAGE:-kindest/node:v1.34.0@sha256:7416a61b42b1662ca6ca89f02028ac133a309a2a30ba309614e8ec94d976dc5a}"
KIND_KUBECONFIG_PATH="${KIND_KUBECONFIG_PATH:-$HOME/.kube/kind-${KIND_CLUSTER_NAME}.yaml}"
KIND_IMAGE_BACKEND="${KIND_IMAGE_BACKEND:-vellum-backend:latest}"
KIND_IMAGE_FRONTEND="${KIND_IMAGE_FRONTEND:-vellum-frontend:latest}"
KIND_IMAGE_INGESTION="${KIND_IMAGE_INGESTION:-vellum-ingest:local}"

ensure_project_root() {
    cd "$PROJECT_ROOT"
}

use_default_kubeconfig() {
    if [[ -n "${KUBECONFIG:-}" ]]; then
        return 0
    fi

    if [[ -f "$KIND_KUBECONFIG_PATH" ]]; then
        export KUBECONFIG="$KIND_KUBECONFIG_PATH"
    fi
}

kind_cluster_exists() {
    if ! command -v kind >/dev/null 2>&1; then
        return 1
    fi

    kind get clusters 2>/dev/null | grep -Fxq "$KIND_CLUSTER_NAME"
}

require_commands() {
    local missing=()
    local command_name

    for command_name in "$@"; do
        if ! command -v "$command_name" >/dev/null 2>&1; then
            missing+=("$command_name")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        printf 'Missing required command(s): %s\n' "${missing[*]}" >&2
        exit 1
    fi
}

load_env_file() {
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        set -a
        # shellcheck disable=SC1091
        source "$PROJECT_ROOT/.env"
        set +a
    fi

    export ENABLE_LOCAL_LLM="${ENABLE_LOCAL_LLM:-true}"
}

bool_is_true() {
    case "${1,,}" in
        true|1|yes|on)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

docker_default_runtime() {
    if ! command -v docker >/dev/null 2>&1; then
        return 1
    fi

    docker info --format '{{.DefaultRuntime}}' 2>/dev/null
}

docker_has_nvidia_runtime() {
    if ! command -v docker >/dev/null 2>&1; then
        return 1
    fi

    docker info --format '{{range $key, $value := .Runtimes}}{{$key}}{{"\n"}}{{end}}' 2>/dev/null | grep -Fxq 'nvidia'
}

host_has_nvidia_gpu() {
    command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1
}

kind_gpu_support_requested() {
    bool_is_true "$ENABLE_LOCAL_LLM"
}

kind_node_has_nvidia_devices() {
    local node_name

    if ! kind_cluster_exists || ! command -v docker >/dev/null 2>&1; then
        return 1
    fi

    node_name="$(kind get nodes --name "$KIND_CLUSTER_NAME" 2>/dev/null | head -n 1 || true)"
    [[ -n "$node_name" ]] || return 1

    docker exec "$node_name" sh -lc 'ls /dev/nvidia* >/dev/null 2>&1'
}

cluster_has_nvidia_gpu_capacity() {
    local allocatable

    allocatable="$(kubectl get nodes -o jsonpath='{range .items[*]}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}' 2>/dev/null || true)"
    [[ "$allocatable" =~ [1-9] ]]
}

cluster_has_nvidia_runtime_class() {
    kubectl get runtimeclass nvidia >/dev/null 2>&1
}

cluster_has_nvidia_device_plugin() {
    kubectl get daemonset -A -o jsonpath='{range .items[*]}{.metadata.namespace}{"/"}{.metadata.name}{"\n"}{end}' 2>/dev/null | grep -Eqi '(^|/)nvidia(-|.)*device(-|.)*plugin'
}

wait_for_nvidia_gpu_capacity() {
    local attempts="${1:-24}"
    local sleep_seconds="${2:-5}"
    local count=0

    while [[ "$count" -lt "$attempts" ]]; do
        if cluster_has_nvidia_gpu_capacity; then
            return 0
        fi

        sleep "$sleep_seconds"
        count=$((count + 1))
    done

    return 1
}

require_kind_gpu_host_prereqs() {
    if ! kind_gpu_support_requested; then
        return 0
    fi

    if ! host_has_nvidia_gpu; then
        cat >&2 <<'EOF'
ENABLE_LOCAL_LLM=true requires a host-visible NVIDIA GPU, but `nvidia-smi` is not working in this shell.

Fix the host GPU driver/toolkit first, then rerun ./scripts/setup-kind.sh.
EOF
        exit 1
    fi

    if ! docker_has_nvidia_runtime; then
        cat >&2 <<'EOF'
ENABLE_LOCAL_LLM=true requires Docker to expose an `nvidia` runtime.

Add the runtime to /etc/docker/daemon.json, restart Docker, verify `docker info` lists `nvidia`, then rerun ./scripts/setup-kind.sh.
EOF
        exit 1
    fi
}

bootstrap_kind_gpu_support() {
    if ! kind_gpu_support_requested; then
        return 0
    fi

    if ! kind_node_has_nvidia_devices; then
        echo "ENABLE_LOCAL_LLM=true, but the Kind node container has no /dev/nvidia* devices." >&2
        print_local_llm_diagnostics >&2
        exit 1
    fi

    kubectl apply -f "$PROJECT_ROOT/deployment/nvidia-runtimeclass.yaml" >/dev/null
    kubectl apply -f "$PROJECT_ROOT/deployment/nvidia-device-plugin.yaml" >/dev/null
    kubectl rollout status daemonset/nvidia-device-plugin-daemonset -n kube-system --timeout=180s >/dev/null

    if ! wait_for_nvidia_gpu_capacity 24 5; then
        echo "The NVIDIA device plugin and runtime class were applied, but the cluster still does not advertise nvidia.com/gpu." >&2
        print_local_llm_diagnostics >&2
        exit 1
    fi
}

print_local_llm_diagnostics() {
    local host_gpu_status="missing"
    local docker_runtime_status="missing"
    local kind_node_gpu_status="missing"
    local runtime_class_status="missing"
    local device_plugin_status="missing"
    local cluster_gpu_status="missing"

    if host_has_nvidia_gpu; then
        host_gpu_status="ok"
    fi

    if docker_has_nvidia_runtime; then
        docker_runtime_status="ok"
    fi

    if kind_node_has_nvidia_devices; then
        kind_node_gpu_status="ok"
    fi

    if cluster_has_nvidia_runtime_class; then
        runtime_class_status="ok"
    fi

    if cluster_has_nvidia_device_plugin; then
        device_plugin_status="ok"
    fi

    if cluster_has_nvidia_gpu_capacity; then
        cluster_gpu_status="ok"
    fi

    cat <<EOF
Local LLM diagnostics:
  - Host GPU visibility: ${host_gpu_status}
  - Docker NVIDIA runtime installed: ${docker_runtime_status}
  - Kind node has /dev/nvidia*: ${kind_node_gpu_status}
  - Cluster RuntimeClass/nvidia: ${runtime_class_status}
  - NVIDIA device plugin in cluster: ${device_plugin_status}
  - Cluster allocatable nvidia.com/gpu: ${cluster_gpu_status}
EOF

    if [[ "$kind_node_gpu_status" != "ok" ]]; then
        cat <<EOF
Action required:
  - The current Kind node container was created without NVIDIA devices, so Kubernetes cannot advertise nvidia.com/gpu.
  - Recreate the cluster after fixing the Kind GPU passthrough setup on the host; the repo does not provision that automatically today.
  - Until that is fixed, set ENABLE_LOCAL_LLM=false or use a remote provider.
EOF
        return 0
    fi

    if [[ "$runtime_class_status" != "ok" || "$device_plugin_status" != "ok" || "$cluster_gpu_status" != "ok" ]]; then
        cat <<EOF
Action required:
  - The node can see NVIDIA devices, but the cluster GPU plumbing is incomplete.
  - Ensure the NVIDIA RuntimeClass and device plugin are installed before expecting the KServe predictor to schedule.
  - Until that is fixed, set ENABLE_LOCAL_LLM=false or use a remote provider.
EOF
    fi
}

require_kubectl_access() {
    use_default_kubeconfig

    if ! kubectl cluster-info >/dev/null 2>&1; then
        echo "kubectl cannot reach a cluster. Export KUBECONFIG or run ./scripts/setup-kind.sh first." >&2
        exit 1
    fi
}

ensure_kubeflow_manifests_submodule() {
    if [[ -d "$PROJECT_ROOT/deployment/manifests/common" ]]; then
        return 0
    fi

    if ! command -v git >/dev/null 2>&1; then
        echo "Kubeflow manifests are missing and git is not available to initialize the submodule." >&2
        exit 1
    fi

    echo "📦 Initializing deployment/manifests submodule..."
    git submodule update --init --recursive deployment/manifests

    if [[ ! -d "$PROJECT_ROOT/deployment/manifests/common" ]]; then
        echo "Kubeflow manifests submodule is still unavailable after initialization." >&2
        exit 1
    fi
}

publish_image() {
    local source_image="$1"
    local component="$2"
    local target_image

    case "$component" in
        backend)
            target_image="$KIND_IMAGE_BACKEND"
            ;;
        frontend)
            target_image="$KIND_IMAGE_FRONTEND"
            ;;
        ingestion)
            target_image="$KIND_IMAGE_INGESTION"
            ;;
        *)
            echo "Unsupported component: ${component}" >&2
            return 1
            ;;
    esac

    require_commands kind docker
    docker tag "$source_image" "$target_image"
    kind load docker-image "$target_image" --name "$KIND_CLUSTER_NAME"
}

scale_local_llm() {
    local replicas=0

    if bool_is_true "$ENABLE_LOCAL_LLM" && cluster_has_nvidia_gpu_capacity; then
        replicas=1
    elif bool_is_true "$ENABLE_LOCAL_LLM"; then
        echo "⚠️  ENABLE_LOCAL_LLM=${ENABLE_LOCAL_LLM}, but the cluster does not advertise nvidia.com/gpu capacity. Scaling the local LLM deployment to zero."
        print_local_llm_diagnostics
    fi

    if ! kubectl get deployment llm-service-predictor -n "$VELLUM_NAMESPACE" >/dev/null 2>&1; then
        echo "ℹ️  KServe predictor deployment not present yet; skipping local LLM scaling."
        return 0
    fi

    kubectl scale deployment/llm-service-predictor -n "$VELLUM_NAMESPACE" --replicas="$replicas" >/dev/null

    if [[ "$replicas" -eq 1 ]]; then
        echo "✅ Local LLM deployment enabled."
    else
        echo "✅ Local LLM deployment scaled to zero."
    fi
}

restart_if_present() {
    local deployment_name="$1"
    local namespace="${2:-$VELLUM_NAMESPACE}"

    if kubectl get deployment "$deployment_name" -n "$namespace" >/dev/null 2>&1; then
        kubectl rollout restart "deployment/${deployment_name}" -n "$namespace"
    fi
}

wait_for_rollout() {
    local resource_kind="$1"
    local resource_name="$2"
    local namespace="$3"
    local timeout="${4:-300s}"

    kubectl rollout status "${resource_kind}/${resource_name}" -n "$namespace" --timeout="$timeout"
}

wait_for_job_completion() {
    local job_name="$1"
    local namespace="$2"
    local timeout="${3:-1800s}"

    kubectl wait --for=condition=complete "job/${job_name}" -n "$namespace" --timeout="$timeout"
}

wait_for_pods_ready_by_selector() {
    local namespace="$1"
    local selector="$2"
    local timeout="${3:-300s}"

    kubectl wait --for=condition=Ready pod -n "$namespace" -l "$selector" --timeout="$timeout"
}

wait_for_inferenceservice_ready() {
    local service_name="$1"
    local namespace="$2"
    local timeout="${3:-900s}"

    kubectl wait --for=condition=Ready "inferenceservice/${service_name}" -n "$namespace" --timeout="$timeout"
}
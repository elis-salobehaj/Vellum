#!/usr/bin/env bash

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VELLUM_NAMESPACE="${VELLUM_NAMESPACE:-kubeflow-vellum}"
KIND_CLUSTER_NAME="${KIND_CLUSTER_NAME:-vellum}"
KIND_CONTEXT_NAME="${KIND_CONTEXT_NAME:-vellum}"
KIND_BOOTSTRAP_CONTEXT="kind-${KIND_CLUSTER_NAME}"
KIND_NODE_IMAGE="${KIND_NODE_IMAGE:-kindest/node:v1.34.0@sha256:7416a61b42b1662ca6ca89f02028ac133a309a2a30ba309614e8ec94d976dc5a}"
MAIN_KUBECONFIG_PATH="${MAIN_KUBECONFIG_PATH:-$HOME/.kube/config}"
KIND_DEFAULT_API_SERVER_PORT="${KIND_DEFAULT_API_SERVER_PORT:-6551}"
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

    export KUBECONFIG="$MAIN_KUBECONFIG_PATH"
}

kind_context_exists() {
    local context_name="$1"

    kubectl config get-contexts -o name 2>/dev/null | grep -Fxq "$context_name"
}

ensure_kind_context() {
    local cluster_name
    local user_name

    use_default_kubeconfig

    if kind_context_exists "$KIND_BOOTSTRAP_CONTEXT"; then
        cluster_name="$(kubectl config view -o jsonpath="{.contexts[?(@.name==\"${KIND_BOOTSTRAP_CONTEXT}\")].context.cluster}")"
        user_name="$(kubectl config view -o jsonpath="{.contexts[?(@.name==\"${KIND_BOOTSTRAP_CONTEXT}\")].context.user}")"

        if [[ -z "$cluster_name" || -z "$user_name" ]]; then
            echo "Could not resolve the Kind kubeconfig entries for cluster '${KIND_CLUSTER_NAME}'." >&2
            return 1
        fi

        kubectl config delete-context "$KIND_CONTEXT_NAME" >/dev/null 2>&1 || true
        kubectl config set-context "$KIND_CONTEXT_NAME" --cluster="$cluster_name" --user="$user_name" >/dev/null
        if [[ "$KIND_BOOTSTRAP_CONTEXT" != "$KIND_CONTEXT_NAME" ]]; then
            kubectl config delete-context "$KIND_BOOTSTRAP_CONTEXT" >/dev/null 2>&1 || true
        fi
    elif ! kind_context_exists "$KIND_CONTEXT_NAME"; then
        echo "Could not find a kubeconfig context for Kind cluster '${KIND_CLUSTER_NAME}'." >&2
        return 1
    fi

    kubectl config use-context "$KIND_CONTEXT_NAME" >/dev/null
}

cleanup_kind_kubeconfig() {
    use_default_kubeconfig

    kubectl config delete-context "$KIND_CONTEXT_NAME" >/dev/null 2>&1 || true
    if [[ "$KIND_BOOTSTRAP_CONTEXT" != "$KIND_CONTEXT_NAME" ]]; then
        kubectl config delete-context "$KIND_BOOTSTRAP_CONTEXT" >/dev/null 2>&1 || true
    fi
    kubectl config delete-cluster "$KIND_BOOTSTRAP_CONTEXT" >/dev/null 2>&1 || true
    kubectl config unset "users.${KIND_BOOTSTRAP_CONTEXT}" >/dev/null 2>&1 || true
}

port_is_available() {
    local port="$1"

    if command -v ss >/dev/null 2>&1; then
        ! ss -Htanl "( sport = :${port} )" 2>/dev/null | grep -q .
        return
    fi

    if command -v netstat >/dev/null 2>&1; then
        ! netstat -tanl 2>/dev/null | awk '{print $4}' | grep -Eq "(^|[:.])${port}$"
        return
    fi

    return 0
}

find_available_local_port() {
    local starting_port="${1:-$KIND_DEFAULT_API_SERVER_PORT}"
    local attempts="${2:-50}"
    local port="$starting_port"
    local count=0

    while [[ "$count" -lt "$attempts" ]]; do
        if port_is_available "$port"; then
            echo "$port"
            return 0
        fi

        port=$((port + 1))
        count=$((count + 1))
    done

    echo "No free local port found for the Kind API server after ${attempts} attempts starting at ${starting_port}." >&2
    return 1
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
    export ENABLE_LOCAL_LLM_REQUESTED="${ENABLE_LOCAL_LLM_REQUESTED:-$ENABLE_LOCAL_LLM}"
    export ALLOW_LOCAL_LLM_FALLBACK="${ALLOW_LOCAL_LLM_FALLBACK:-true}"
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

local_llm_fallback_allowed() {
    bool_is_true "$ALLOW_LOCAL_LLM_FALLBACK"
}

disable_local_llm_bootstrap() {
    local reason="$1"

    echo "⚠️  ${reason}" >&2
    echo "⚠️  Continuing with the cluster bootstrap, but the local GPU-backed LLM will remain disabled until the host runtime is fixed." >&2
    export ENABLE_LOCAL_LLM=false
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

kind_node_name() {
    if ! kind_cluster_exists || ! command -v kind >/dev/null 2>&1; then
        return 1
    fi

    kind get nodes --name "$KIND_CLUSTER_NAME" 2>/dev/null | head -n 1
}

kind_node_has_nvidia_runtime_handler() {
    local node_name

    node_name="$(kind_node_name || true)"
    [[ -n "$node_name" ]] || return 1

    docker exec "$node_name" sh -lc "grep -q 'containerd.runtimes.nvidia' /etc/containerd/config.toml"
}

kind_node_has_nvidia_user_space() {
    local node_name

    node_name="$(kind_node_name || true)"
    [[ -n "$node_name" ]] || return 1

    docker exec "$node_name" sh -lc 'test -x /usr/bin/nvidia-container-runtime && ldconfig -p 2>/dev/null | grep -q libnvidia-ml.so.1 && ldconfig -p 2>/dev/null | grep -q libnvidia-container.so.1'
}

copy_file_to_kind_node() {
    local node_name="$1"
    local host_path="$2"
    local target_path="$3"

    [[ -f "$host_path" ]] || return 0

    docker exec "$node_name" sh -lc "mkdir -p '$(dirname "$target_path")'"
    docker cp "$host_path" "$node_name:$target_path"
}

copy_matching_files_to_kind_node() {
    local node_name="$1"
    shift

    local pattern
    local host_path

    for pattern in "$@"; do
        for host_path in $pattern; do
            if [[ -f "$host_path" ]]; then
                copy_file_to_kind_node "$node_name" "$host_path" "$host_path"
            fi
        done
    done
}

copy_directory_contents_to_kind_node() {
    local node_name="$1"
    local host_dir="$2"
    local target_dir="$3"

    [[ -d "$host_dir" ]] || return 0

    docker exec "$node_name" sh -lc "mkdir -p '$target_dir'"
    docker cp "$host_dir/." "$node_name:$target_dir/"
}

configure_kind_node_nvidia_runtime() {
    local node_name

    node_name="$(kind_node_name || true)"
    [[ -n "$node_name" ]] || return 1

    if kind_node_has_nvidia_runtime_handler && kind_node_has_nvidia_user_space; then
        return 0
    fi

    echo "🔧 Provisioning NVIDIA user-space tooling inside Kind node ${node_name}..."

    copy_file_to_kind_node "$node_name" /usr/bin/nvidia-container-runtime /usr/bin/nvidia-container-runtime
    copy_file_to_kind_node "$node_name" /usr/bin/nvidia-container-runtime-hook /usr/bin/nvidia-container-runtime-hook
    copy_file_to_kind_node "$node_name" /usr/bin/nvidia-container-cli /usr/bin/nvidia-container-cli
    copy_file_to_kind_node "$node_name" /usr/bin/nvidia-ctk /usr/bin/nvidia-ctk
    copy_directory_contents_to_kind_node "$node_name" /etc/nvidia-container-runtime /etc/nvidia-container-runtime

    copy_matching_files_to_kind_node "$node_name" \
        /usr/lib/x86_64-linux-gnu/libnvidia-container.so* \
        /usr/lib/x86_64-linux-gnu/libnvidia-container-go.so* \
        /lib/x86_64-linux-gnu/libnvidia*.so* \
        /lib/x86_64-linux-gnu/libcuda.so*

    docker exec "$node_name" sh -lc "grep -q 'containerd.runtimes.nvidia' /etc/containerd/config.toml || cat >> /etc/containerd/config.toml <<'EOF'
[plugins.\"io.containerd.grpc.v1.cri\".containerd.runtimes.nvidia]
  runtime_type = \"io.containerd.runc.v2\"
  privileged_without_host_devices = false
[plugins.\"io.containerd.grpc.v1.cri\".containerd.runtimes.nvidia.options]
  BinaryName = \"/usr/bin/nvidia-container-runtime\"
EOF"

    docker exec "$node_name" sh -lc 'kill -HUP $(pidof containerd) >/dev/null 2>&1 || true'
    sleep 5
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
        if local_llm_fallback_allowed; then
            disable_local_llm_bootstrap 'ENABLE_LOCAL_LLM=true, but `nvidia-smi` is not working in this shell.'
            return 0
        fi

        cat >&2 <<'EOF'
ENABLE_LOCAL_LLM=true requires a host-visible NVIDIA GPU, but `nvidia-smi` is not working in this shell.

Fix the host GPU driver/toolkit first, then rerun ./scripts/setup-kind.sh.
EOF
        exit 1
    fi

    if ! docker_has_nvidia_runtime; then
        if local_llm_fallback_allowed; then
            disable_local_llm_bootstrap 'ENABLE_LOCAL_LLM=true, but Docker does not expose an `nvidia` runtime.'
            return 0
        fi

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
        if local_llm_fallback_allowed; then
            disable_local_llm_bootstrap 'ENABLE_LOCAL_LLM=true, but the Kind node container has no /dev/nvidia* devices.'
            print_local_llm_diagnostics >&2
            return 0
        fi

        echo "ENABLE_LOCAL_LLM=true, but the Kind node container has no /dev/nvidia* devices." >&2
        print_local_llm_diagnostics >&2
        exit 1
    fi

    if ! configure_kind_node_nvidia_runtime; then
        if local_llm_fallback_allowed; then
            disable_local_llm_bootstrap 'ENABLE_LOCAL_LLM=true, but the Kind node could not be provisioned with NVIDIA runtime tooling.'
            print_local_llm_diagnostics >&2
            return 0
        fi

        echo "ENABLE_LOCAL_LLM=true, but the Kind node could not be provisioned with NVIDIA runtime tooling." >&2
        print_local_llm_diagnostics >&2
        exit 1
    fi

    kubectl apply -f "$PROJECT_ROOT/deployment/nvidia-runtimeclass.yaml" >/dev/null
    kubectl apply -f "$PROJECT_ROOT/deployment/nvidia-device-plugin.yaml" >/dev/null
    kubectl rollout status daemonset/nvidia-device-plugin-daemonset -n kube-system --timeout=180s >/dev/null

    if ! wait_for_nvidia_gpu_capacity 24 5; then
        if local_llm_fallback_allowed; then
            disable_local_llm_bootstrap 'The NVIDIA device plugin was applied, but the cluster still does not advertise nvidia.com/gpu.'
            print_local_llm_diagnostics >&2
            return 0
        fi

        echo "The NVIDIA device plugin and runtime class were applied, but the cluster still does not advertise nvidia.com/gpu." >&2
        print_local_llm_diagnostics >&2
        exit 1
    fi
}

print_local_llm_diagnostics() {
    local host_gpu_status="missing"
    local docker_runtime_status="missing"
    local kind_node_gpu_status="missing"
    local kind_node_runtime_status="missing"
    local kind_node_userspace_status="missing"
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

    if kind_node_has_nvidia_runtime_handler; then
        kind_node_runtime_status="ok"
    fi

    if kind_node_has_nvidia_user_space; then
        kind_node_userspace_status="ok"
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
    - Kind node containerd nvidia handler: ${kind_node_runtime_status}
    - Kind node NVIDIA user-space libs/tools: ${kind_node_userspace_status}
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
    - The node can see NVIDIA devices, but the Kind GPU plumbing is incomplete.
    - The Kind node itself also needs the NVIDIA runtime handler and user-space tooling, not just the Kubernetes RuntimeClass and device plugin.
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
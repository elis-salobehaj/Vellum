#!/usr/bin/env bash
# scripts/deploy-local.sh
# This script syncs your local .env with Kubernetes and redeploys the application.

set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/cluster-common.sh"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ensure_project_root
load_env_file
require_commands docker kubectl
require_kubectl_access

echo -e "${BLUE}🚀 Syncing environment and redeploying Vellum...${NC}"

echo -e "${GREEN}📖 Exporting variables from .env...${NC}"

NO_CACHE=""
if [[ "${1:-}" == "--no-cache" ]]; then
    NO_CACHE="--no-cache"
    echo -e "${GREEN}🛠️  Building images with --no-cache...${NC}"
fi

echo -e "${GREEN}🛠️  Building backend image first (required by ingestion)...${NC}"
docker compose build $NO_CACHE backend

echo -e "${GREEN}🛠️  Building frontend and dagster images...${NC}"
docker compose build $NO_CACHE frontend
docker build $NO_CACHE -t dagster-vellum:local dagster/

echo -e "${GREEN}📦 Loading local images into Kind cluster ${KIND_CLUSTER_NAME}...${NC}"
publish_image "vellum-backend:latest" backend
publish_image "vellum-frontend:latest" frontend
publish_image "dagster-vellum:local" dagster-vellum

echo -e "${GREEN}🔐 Synchronizing Kubernetes secret from .env...${NC}"
bash ./scripts/sync-env-secret.sh

echo -e "${GREEN}🧹 Recreating the model downloader job to pick up any local model changes...${NC}"
kubectl delete job/model-downloader -n "$VELLUM_NAMESPACE" --ignore-not-found >/dev/null 2>&1 || true

echo -e "${GREEN}⛵ Applying app manifests (server-side)...${NC}"
kubectl kustomize --load-restrictor=LoadRestrictionsNone "$PROJECT_ROOT/deployment" | kubectl apply --server-side --force-conflicts -f -

if kind_gpu_support_requested; then
    echo -e "${GREEN}🧰 Refreshing Kind GPU support before local LLM scaling...${NC}"
    bootstrap_kind_gpu_support
fi

echo -e "${GREEN}🤖 Applying local LLM toggle...${NC}"
scale_local_llm

echo -e "${GREEN}🔄 Restarting pods to pick up any code changes...${NC}"
restart_if_present backend
restart_if_present frontend
restart_if_present llm-service-predictor

echo -e "${GREEN}⏳ Waiting for app workloads to become ready...${NC}"
wait_for_job_completion model-downloader "$VELLUM_NAMESPACE" 5400s
wait_for_rollout deployment embeddings-service "$VELLUM_NAMESPACE" 900s
wait_for_rollout deployment backend "$VELLUM_NAMESPACE" 900s
wait_for_rollout deployment frontend "$VELLUM_NAMESPACE" 900s

if bool_is_true "$ENABLE_LOCAL_LLM" && cluster_has_nvidia_gpu_capacity; then
    wait_for_inferenceservice_ready llm-service "$VELLUM_NAMESPACE" 1800s
fi

echo -e "${BLUE}✅ Deployment complete!${NC}"
echo -e "${BLUE}🔗 Running 'scripts/connect.sh' to establish port forwards...${NC}"

bash ./scripts/connect.sh


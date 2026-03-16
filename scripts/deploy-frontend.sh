#!/usr/bin/env bash
# scripts/deploy-frontend.sh

set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/cluster-common.sh"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Redeploying Frontend...${NC}"

ensure_project_root
load_env_file
require_commands docker kubectl
require_kubectl_access

NO_CACHE=""
if [[ "${1:-}" == "--no-cache" ]]; then
    NO_CACHE="--no-cache"
fi
docker compose build $NO_CACHE frontend

echo -e "${GREEN}🔐 Synchronizing Kubernetes secret from .env...${NC}"
bash ./scripts/sync-env-secret.sh

echo -e "${GREEN}📦 Loading frontend image into Kind cluster ${KIND_CLUSTER_NAME}...${NC}"
publish_image "vellum-frontend:latest" frontend

restart_if_present frontend

echo -e "${GREEN}✅ Frontend redeployed successfully.${NC}"

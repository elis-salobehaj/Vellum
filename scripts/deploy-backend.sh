#!/usr/bin/env bash
# scripts/deploy-backend.sh

set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/cluster-common.sh"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Redeploying Backend...${NC}"

ensure_project_root
load_env_file
require_commands docker kubectl
require_kubectl_access

NO_CACHE=""
if [[ "${1:-}" == "--no-cache" ]]; then
    NO_CACHE="--no-cache"
fi
docker compose build $NO_CACHE backend

echo -e "${GREEN}📦 Loading backend image into Kind cluster ${KIND_CLUSTER_NAME}...${NC}"
publish_image "vellum-backend:latest" backend

restart_if_present backend

echo -e "${GREEN}✅ Backend redeployed successfully.${NC}"

#!/usr/bin/env bash
# scripts/deploy-ingestion.sh

set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/cluster-common.sh"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Redeploying Ingestion service...${NC}"

ensure_project_root
load_env_file
require_commands docker

NO_CACHE=""
if [[ "${1:-}" == "--no-cache" ]]; then
    NO_CACHE="--no-cache"
fi
docker compose build $NO_CACHE ingestion

echo -e "${GREEN}📦 Loading ingestion image into Kind cluster ${KIND_CLUSTER_NAME}...${NC}"
publish_image "vellum-ingest:local" ingestion

echo -e "${GREEN}✅ Ingestion image rebuilt and pushed successfully.${NC}"

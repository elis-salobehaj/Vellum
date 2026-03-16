#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/cluster-common.sh"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

ensure_project_root
require_commands bash uv pnpm kubectl docker helm kind

echo -e "${BLUE}🚀 Running full local Vellum setup...${NC}"

echo -e "${BLUE}1/5 Bootstrapping the Kind platform...${NC}"
bash ./scripts/setup-kind.sh

echo -e "${BLUE}2/5 Syncing backend dependencies with uv...${NC}"
(
    cd backend
    uv sync
)

echo -e "${BLUE}3/5 Installing frontend dependencies with pnpm...${NC}"
(
    cd frontend
    pnpm install
)

echo -e "${BLUE}4/5 Installing Playwright Chromium for fresh-machine E2E runs...${NC}"
(
    cd frontend
    pnpm exec playwright install chromium
)

echo -e "${BLUE}5/5 Building, deploying, and connecting the Vellum workloads...${NC}"
bash ./scripts/deploy-local.sh

echo -e "${GREEN}✅ Full local Vellum setup complete.${NC}"
echo -e "${GREEN}Active context:${NC} kubectl config use-context ${KIND_CONTEXT_NAME}"
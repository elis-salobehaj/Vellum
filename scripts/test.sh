#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/cluster-common.sh"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

ensure_project_root
load_env_file
require_commands uv pnpm kubectl
use_default_kubeconfig

backend_status=0
playwright_status=0

echo -e "${BLUE}🧪 Running backend test suite with uv...${NC}"
(
    cd backend
    uv sync --group dev >/dev/null
    uv run pytest tests/ -v
) || backend_status=$?

echo -e "${BLUE}🎭 Running Playwright suite through the hybrid test harness...${NC}"
bash ./scripts/test_playwright.sh "$@" || playwright_status=$?

if [[ "$backend_status" -ne 0 || "$playwright_status" -ne 0 ]]; then
    echo -e "${RED}❌ Full test suite failed.${NC}"
    echo -e "${RED}backend=${backend_status} playwright=${playwright_status}${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Full test suite passed.${NC}"
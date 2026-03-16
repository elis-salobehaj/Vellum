#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/cluster-common.sh"

# Vellum Comprehensive Test Script
# One-command to run Playwright against the Phase 1 hybrid stack

# Set terminal colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🧪 Starting Vellum Automated Testing Environment...${NC}"

ensure_project_root
load_env_file
require_commands kubectl lsof curl uv pnpm
use_default_kubeconfig

# 1. Connect to Infrastructure
echo -e "${BLUE}🔌 Connecting to Kubernetes infrastructure...${NC}"
bash ./scripts/connect.sh --hybrid || { echo -e "${RED}Failed to connect to infra${NC}"; exit 1; }

if [[ -f "$PROJECT_ROOT/.vellum-runtime.env" ]]; then
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.vellum-runtime.env"
fi

# 2. Ensure the harness controls port 8006 and starts a fresh local backend
EXISTING_BACKEND_PIDS="$(lsof -ti :8006 || true)"
if [[ -n "$EXISTING_BACKEND_PIDS" ]]; then
    echo -e "${BLUE}🧹 Reclaiming port 8006 from existing process(es): ${EXISTING_BACKEND_PIDS}${NC}"
    kill $EXISTING_BACKEND_PIDS 2>/dev/null || true
    sleep 2
fi

echo -e "${BLUE}🐍 Starting Backend (uvicorn) on http://localhost:8006...${NC}"
export PATH="$HOME/.local/bin:$PATH"
(cd backend && \
    BYPASS_AUTH=true \
    QDRANT_HOST=localhost \
    QDRANT_PORT="${VELLUM_QDRANT_PORT:-${QDRANT_PORT:-6333}}" \
    MINIO_ENDPOINT="${VELLUM_MINIO_ENDPOINT:-${MINIO_ENDPOINT:-localhost:9000}}" \
    EMBEDDINGS_SERVICE_URL="${VELLUM_EMBEDDINGS_URL:-${EMBEDDINGS_SERVICE_URL:-http://localhost:8082/v1}}" \
    KFP_HOST="${VELLUM_KFP_URL:-${KFP_HOST:-http://localhost:8888}}" \
    LLM_SERVICE_URL="${VELLUM_LLM_URL:-${LLM_SERVICE_URL:-http://localhost:8081/v1}}" \
    KFP_NAMESPACE=kubeflow-vellum \
    uv run uvicorn main:app --port 8006) &
BACKEND_PID=$!
BACKEND_STARTED=true

# Wait for backend to be ready
echo -e "${BLUE}⏳ Waiting for backend to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8006/health > /dev/null; then
        echo -e "${GREEN}✅ Backend is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Backend failed to start in time${NC}"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# 3. Run Frontend Tests
echo -e "${BLUE}⚛️  Starting Frontend Playwright Tests (on http://localhost:5174)...${NC}"
echo -e "${BLUE}⏳  Waiting for frontend to initialize... (This may take 30s in WSL)${NC}"

cd frontend
pnpm test "$@"
TEST_EXIT_CODE=$?
cd ..

# 4. Cleanup
if [ "$BACKEND_STARTED" = true ]; then
    echo -e "${BLUE}🛑 Stopping backend...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
fi

echo -e "${BLUE}------------------------------------------------------------${NC}"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED SUCCESSFULLY!${NC}"
else
    echo -e "${RED}❌ TESTS FAILED (Exit Code: $TEST_EXIT_CODE)${NC}"
fi
echo -e "${BLUE}------------------------------------------------------------${NC}"

exit $TEST_EXIT_CODE

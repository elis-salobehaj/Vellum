#!/usr/bin/env bash
# Vellum Hybrid Development Script
# Starts Infrastructure Connect + Backend Server + Frontend Server

set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/cluster-common.sh"

# Set terminal colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Vellum hybrid development mode (Kind + direct-ingestion default)...${NC}"

ensure_project_root
load_env_file
require_commands kubectl uv pnpm
use_default_kubeconfig

# 1. Connect to Infrastructure
echo -e "${BLUE}🔌 Connecting to Kubernetes infrastructure on the active kubeconfig...${NC}"
bash ./scripts/connect.sh --hybrid

if [[ -f "$PROJECT_ROOT/.vellum-runtime.env" ]]; then
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.vellum-runtime.env"
fi

# 2. Start Backend (Foreground)
echo -e "${GREEN}🐍 Starting Backend (uvicorn) on http://localhost:8006...${NC}"
# Ensure uv is in path for shells
export PATH="$HOME/.local/bin:$PATH"

# Move into backend directory for uvicorn to find main.py
cd backend

# Use --reload-dir to optimize watching on WSL
# We run this in foreground so logs are visible.
# User must start frontend in a separate terminal.
# KFP_NAMESPACE still selects the Kubeflow profile namespace when the optional
# KFP path is being exercised, but normal local ingestion stays in direct mode.
QDRANT_HOST=localhost \
QDRANT_PORT="${VELLUM_QDRANT_PORT:-${QDRANT_PORT:-6333}}" \
MINIO_ENDPOINT="${VELLUM_MINIO_ENDPOINT:-${MINIO_ENDPOINT:-localhost:9000}}" \
EMBEDDINGS_SERVICE_URL="${VELLUM_EMBEDDINGS_URL:-${EMBEDDINGS_SERVICE_URL:-http://localhost:8082/v1}}" \
KFP_HOST="${VELLUM_KFP_URL:-${KFP_HOST:-http://localhost:8888}}" \
LLM_SERVICE_URL="${VELLUM_LLM_URL:-${LLM_SERVICE_URL:-http://localhost:8081/v1}}" \
KFP_NAMESPACE=kubeflow-vellum \
uv run uvicorn main:app --reload --reload-dir app --host 0.0.0.0 --port 8006

# Handle shutdown
cleanup() {
    echo -e "\n${BLUE}🛑 Stopping services...${NC}"
    # Backend stops on Ctrl+C (SIGINT)
    pkill -f "kubectl port-forward" 2>/dev/null || true
    exit
}

trap cleanup SIGINT SIGTERM

wait

#!/bin/bash
# Vellum Hybrid Development Script
# Starts Infrastructure Connect + Backend Server + Frontend Server

# Set terminal colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Vellum Hybrid Development Mode...${NC}"

# Ensure we are in the project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 1. Connect to Infrastructure
echo -e "${BLUE}🔌 Connecting to Kubernetes infrastructure...${NC}"
./scripts/connect.sh --hybrid

# 2. Start Backend (Foreground)
echo -e "${GREEN}🐍 Starting Backend (uvicorn) on http://localhost:8000...${NC}"
# Ensure uv is in path for shells
export PATH="$HOME/.local/bin:$PATH"

# Move into backend directory for uvicorn to find main.py
cd backend

# Use --reload-dir to optimize watching on WSL
# We run this in foreground so logs are visible. 
# User must start frontend in a separate terminal.
# We set PYTHONPATH to root so we can import the local 'kubeflow' package
# We set KFP_NAMESPACE to prevent kfp client from looking for k8s secrets locally
KFP_NAMESPACE=kubeflow-vellum PYTHONPATH=.. uv run uvicorn main:app --reload --reload-dir app --host 0.0.0.0 --port 8000

# Handle shutdown
cleanup() {
    echo -e "\n${BLUE}🛑 Stopping services...${NC}"
    # Backend stops on Ctrl+C (SIGINT)
    pkill -f port-forward 2>/dev/null || true
    exit
}

trap cleanup SIGINT SIGTERM

wait

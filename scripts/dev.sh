#!/bin/bash
# Vellum Hybrid Development Script
# Starts Infrastructure Connect + Backend Server + Frontend Server

# Set terminal colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Vellum Hybrid Development Mode...${NC}"

# 1. Connect to Infrastructure
echo -e "${BLUE}🔌 Connecting to Kubernetes infrastructure...${NC}"
./scripts/connect.sh --hybrid

# 2. Start Backend
echo -e "${GREEN}🐍 Starting Backend (uvicorn) on http://localhost:8000...${NC}"
# Ensure uv is in path for shells
export PATH="$HOME/.local/bin:$PATH"
(cd backend && uv run uvicorn main:app --reload --port 8000) &
BACKEND_PID=$!

# 3. Start Frontend
echo -e "${GREEN}⚛️ Starting Frontend (Vite) on http://localhost:5173...${NC}"
# Ensure nvm/node is available
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
# Try to use the version in .nvmrc if available, otherwise fallback
if [ -f .nvmrc ]; then
    nvm use
else
    nvm use 24.13.0
fi

(cd frontend && pnpm dev --port 5173) &
FRONTEND_PID=$!

echo -e "${BLUE}------------------------------------------------------------${NC}"
echo -e "${BLUE}Hybrid Mode is active:${NC}"
echo -e "  - Frontend: http://localhost:5173"
echo -e "  - Backend API: http://localhost:8000/docs"
echo -e "  - Kubeflow Dashboard: http://localhost:8080"
echo -e "${BLUE}------------------------------------------------------------${NC}"
echo -e "Press Ctrl+C to stop everything."

# Handle shutdown
cleanup() {
    echo -e "\n${BLUE}🛑 Stopping services...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    pkill -f port-forward 2>/dev/null || true
    exit
}

trap cleanup SIGINT SIGTERM

wait

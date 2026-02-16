#!/bin/bash
# Vellum Comprehensive Test Script
echo "DEBUG: test.sh starting..."
# One-command to run full stack tests in Hybrid Mode

# Set terminal colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🧪 Starting Vellum Automated Testing Environment...${NC}"

# 1. Connect to Infrastructure
echo -e "${BLUE}🔌 Connecting to Kubernetes infrastructure...${NC}"
./scripts/connect.sh --hybrid || { echo -e "${RED}Failed to connect to infra${NC}"; exit 1; }

# 2. Check if Backend is already running on 8000
if lsof -i :8000 > /dev/null; then
    echo -e "${GREEN}✅ Backend already running on http://localhost:8000${NC}"
    BACKEND_STARTED=false
else
    echo -e "${BLUE}🐍 Starting Backend (uvicorn) on http://localhost:8000...${NC}"
    export PATH="$HOME/.local/bin:$PATH"
    (cd backend && uv run uvicorn main:app --port 8000) &
    BACKEND_PID=$!
    BACKEND_STARTED=true
    
    # Wait for backend to be ready
    echo -e "${BLUE}⏳ Waiting for backend to be ready...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null; then
            echo -e "${GREEN}✅ Backend is ready!${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ Backend failed to start in time${NC}"
            kill $BACKEND_PID 2>/dev/null
            exit 1
        fi
        sleep 1
    done
fi

# 3. Run Frontend Tests
echo -e "${BLUE}⚛️  Starting Frontend Playwright Tests (on http://localhost:5174)...${NC}"
echo -e "${BLUE}⏳  Waiting for frontend to initialize... (This may take 30s in WSL)${NC}"

# We run with VITE_BYPASS_AUTH=true and force the reporter to be verbose
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

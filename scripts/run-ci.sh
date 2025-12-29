#!/bin/bash
set -e

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting Vellum Fast CI Test Suite...${NC}"

# Backend Tests
echo -e "\n${GREEN}=== Backend Tests ===${NC}"
echo "Building backend test image..."
cd "$PROJECT_ROOT/backend"
# Build target: test
docker build --target test --build-arg BUILD_MODE=ci -t vellum-backend-test .

echo "Running backend tests..."
docker run --rm -e BYPASS_AUTH=true vellum-backend-test

# Frontend Tests
echo -e "\n${GREEN}=== Frontend Tests ===${NC}"
echo "Building frontend test image..."
cd "$PROJECT_ROOT/frontend"
# Build target: test (which includes Playwright env)
docker build --target test -t vellum-frontend-test .

echo "Running frontend linting..."
# Override CMD to run lint instead of full E2E
docker run --rm vellum-frontend-test npm run lint

echo -e "\n${GREEN}All tests passed successfully!${NC}"

#!/bin/bash
set -e

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo -e "${BLUE}Starting Vellum Heavy E2E Test Suite...${NC}"
echo -e "${YELLOW}Warning: This will pull large Docker images and may take time.${NC}"

cd "$PROJECT_ROOT"

echo -e "\n${BLUE}Building E2E Environment...${NC}"
# Build images separately to leverage Docker layer cache
# Only rebuild if --build flag is explicitly passed or images don't exist
if [ "$1" == "--build" ] || ! docker images | grep -q "vellum-backend.*latest"; then
    echo "Building images..."
    docker compose -f docker-compose.test.yml build
else
    echo "Using cached images (pass --build to force rebuild)"
fi

echo -e "\n${BLUE}Starting E2E Tests...${NC}"
# Run without --build to use cached images
docker compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from e2e

# Get exit code of the previous command
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}E2E Tests Passed!${NC}"
else
    echo -e "\n${RED}E2E Tests Failed!${NC}"
fi

exit $EXIT_CODE

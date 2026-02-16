#!/bin/bash
# scripts/deploy-frontend.sh

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Redeploying Frontend...${NC}"

# 1. Point Docker to Minikube's registry
if command -v minikube >/dev/null 2>&1 && minikube status >/dev/null 2>&1; then
    eval $(minikube -p minikube docker-env)
fi

# 2. Export variables from .env
set -a
[ -f .env ] && source .env
set +a

# 3. Build only frontend
NO_CACHE=""
if [[ "$1" == "--no-cache" ]]; then
    NO_CACHE="--no-cache"
fi
docker compose build $NO_CACHE frontend

# 4. Restart deployment
kubectl rollout restart deployment/frontend -n kubeflow-vellum

echo -e "${GREEN}✅ Frontend redeployed successfully.${NC}"

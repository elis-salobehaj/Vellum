#!/bin/bash
# scripts/deploy-local.sh
# This script syncs your local .env with Kubernetes and redeploys the application.

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Syncing environment and redeploying Vellum...${NC}"

# 1. Point Docker to Minikube's registry
if command -v minikube >/dev/null 2>&1 && minikube status >/dev/null 2>&1; then
    echo -e "${GREEN}📦 Pointing to minikube docker-env...${NC}"
    eval $(minikube -p minikube docker-env)
else
    echo -e "${BLUE}ℹ️  Minikube not found or not running, using local docker context.${NC}"
fi

# 2. Export variables from .env for Docker Compose
echo -e "${GREEN}📖 Exporting variables from .env...${NC}"
set -a
source .env
set +a

# 3. Build images using Docker Compose
# Use --no-cache=true if you want a clean build
NO_CACHE=""
if [[ "$1" == "--no-cache" ]]; then
    NO_CACHE="--no-cache"
    echo -e "${GREEN}🛠️  Building images with --no-cache...${NC}"
fi

echo -e "${GREEN}🛠️  Building images (frontend, backend, ingestion)...${NC}"
docker compose build $NO_CACHE frontend backend ingestion

# 4. Apply Kubernetes manifests using root Kustomization
echo -e "${GREEN}⛵ Applying Kubernetes manifests (server-side)...${NC}"
kubectl apply -k . --server-side --force-conflicts

# 5. Explicit rolling restarts
echo -e "${GREEN}🔄 Restarting pods to pick up any code changes...${NC}"
kubectl rollout restart deployment/backend -n kubeflow-vellum
kubectl rollout restart deployment/frontend -n kubeflow-vellum

echo -e "${BLUE}✅ Deployment complete!${NC}"
echo -e "${BLUE}🔗 Running 'scripts/connect.sh' to establish port forwards...${NC}"

./scripts/connect.sh


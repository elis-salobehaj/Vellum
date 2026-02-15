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
# This correctly injects VITE_ build arguments for the frontend from your .env
echo -e "${GREEN}🛠️  Building images with Docker Compose...${NC}"
# Use the root docker-compose.yml which points to the correct build context
docker compose build --no-cache frontend backend ingestion

# 4. Apply Kubernetes manifests using root Kustomization
# Using --server-side to handle large manifests and --force-conflicts for local development
echo -e "${GREEN}⛵ Applying Kubernetes manifests (server-side)...${NC}"
kubectl apply -k . --server-side --force-conflicts

# 5. Explicit rolling restarts
# Ensures that even if .env didn't change, the new code is picked up
echo -e "${GREEN}🔄 Restarting pods to pick up any code changes...${NC}"
kubectl rollout restart deployment/backend -n kubeflow-vellum
kubectl rollout restart deployment/frontend -n kubeflow-vellum

echo -e "${BLUE}✅ Deployment complete! Your environment and code are now in sync.${NC}"
echo -e "${BLUE}🔗 Running 'scripts/connect.sh' to establish port forwards...${NC}"

echo "🔌 Establishing Port Forwards..."

# Kill any existing port-forwards
pkill -f port-forward && sleep 15

# 1. Istio Ingress (Central Dashboard)
# Access at http://localhost:8080
nohup kubectl port-forward -n istio-system svc/istio-ingressgateway 8080:80 > /dev/null 2>&1 &
echo "✅ Dashboard: http://localhost:8080 (Ingress Gateway)"

# 2. Qdrant
# Access gRPC at localhost:6334, HTTP at localhost:6333
nohup kubectl port-forward -n qdrant svc/qdrant 6333:6333 > /dev/null 2>&1 &
echo "✅ Qdrant: http://localhost:6333"

# 3. Kubeflow Pipelines (API)
# Useful for SDK access bypassing Istio Auth (port 8888)
# Use 'ml-pipeline' in 'kubeflow' namespace
nohup kubectl port-forward -n kubeflow svc/ml-pipeline 8888:8888 > /dev/null 2>&1 &
echo "✅ KFP API: http://localhost:8888"

# 4. Embeddings Service
# Access at localhost:8082
nohup kubectl port-forward svc/embeddings-service -n kubeflow-vellum 8082:80 > /dev/null 2>&1 &
echo "✅ Embeddings: http://localhost:8082"

# 5. MinIO (S3)
# Access at localhost:9000
nohup kubectl port-forward -n kubeflow svc/minio-service 9000:9000 > /dev/null 2>&1 &
echo "✅ MinIO: http://localhost:9000"

# 6. Vellum Backend
# Access at localhost:8000
nohup kubectl port-forward -n kubeflow-vellum svc/backend 8000:8000 > /dev/null 2>&1 &
echo "✅ Backend: http://localhost:8000"

# 6. LLM Service (KServe)
# Access at localhost:8081 (mapped from 80)
nohup kubectl port-forward -n kubeflow-vellum svc/llm-service-predictor 8081:80 > /dev/null 2>&1 &
echo "✅ LLM Service: http://localhost:8081"

# 7. Frontend
# Access at localhost:9090
nohup kubectl port-forward -n kubeflow-vellum svc/frontend 9090:80 > /dev/null 2>&1 &
echo "✅ Frontend: http://localhost:9090"

echo "Running in background. Kill with 'pkill -f port-forward'."


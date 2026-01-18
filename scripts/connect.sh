#!/bin/bash
# Consolidated Port-Forward Script
# Usage: ./scripts/connect.sh

echo "🔌 Establishing Port Forwards..."

# Kill any existing port-forwards
pkill -f port-forward && sleep 2

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
nohup kubectl port-forward svc/embeddings-service -n kubeflow-user-example-com 8082:80 > /dev/null 2>&1 &
echo "✅ Embeddings: http://localhost:8082"

# 5. MinIO (S3)
# Access at localhost:9000
nohup kubectl port-forward -n kubeflow svc/minio-service 9000:9000 > /dev/null 2>&1 &
echo "✅ MinIO: http://localhost:9000"

# 6. Vellum Backend
# Access at localhost:8000
nohup kubectl port-forward -n kubeflow-user-example-com svc/backend 8000:8000 > /dev/null 2>&1 &
echo "✅ Backend: http://localhost:8000"

# 6. LLM Service (KServe)
# Access at localhost:8081 (mapped from 80)
nohup kubectl port-forward -n kubeflow-user-example-com svc/llm-service-predictor 8081:80 > /dev/null 2>&1 &
echo "✅ LLM Service: http://localhost:8081"

# 7. Frontend
# Access at localhost:9090
nohup kubectl port-forward -n kubeflow-user-example-com svc/frontend 9090:80 > /dev/null 2>&1 &
echo "✅ Frontend: http://localhost:9090"

echo "Running in background. Kill with 'pkill -f port-forward'."

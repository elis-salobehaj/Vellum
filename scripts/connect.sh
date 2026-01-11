#!/bin/bash
# Consolidated Port-Forward Script
# Usage: ./scripts/connect.sh

echo "🔌 Establishing Port Forwards..."

# 1. Istio Ingress (Central Dashboard)
# Access at http://localhost:8080
nohup kubectl port-forward -n istio-system svc/istio-ingressgateway 8080:80 > /dev/null 2>&1 &
echo "✅ Dashboard: http://localhost:8080 (Ingress Gateway)"

# 2. Qdrant
# Access gRPC at localhost:6334, HTTP at localhost:6333
nohup kubectl port-forward -n qdrant svc/qdrant 6333:6333 > /dev/null 2>&1 &
echo "✅ Qdrant: http://localhost:6333"

echo "Running in background. Kill with 'pkill -f port-forward'."

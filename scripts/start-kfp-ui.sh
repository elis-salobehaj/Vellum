#!/bin/bash

# Kill any existing port-forward on port 3000
pkill -f "kubectl port-forward.*3000:80"

# Start new port-forwards in background
nohup kubectl port-forward -n kubeflow svc/ml-pipeline-ui 3000:80 > /dev/null 2>&1 &
nohup kubectl port-forward -n kubeflow svc/minio-service 9000:9000 > /dev/null 2>&1 &
nohup kubectl port-forward -n kubeflow svc/chroma-service 8001:8000 > /dev/null 2>&1 &

echo "✅ Port-Forwards started:"
echo "   🌍 KFP UI:    http://localhost:3000"
echo "   💾 MinIO:     http://localhost:9000"
echo "   🧠 ChromaDB:  http://localhost:8001"
echo "🛑 To stop all: pkill -f 'kubectl port-forward'"

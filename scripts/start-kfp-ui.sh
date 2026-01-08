#!/bin/bash

# Kill any existing port-forward on port 3000
pkill -f "kubectl port-forward.*3000:80"

# Start new port-forward in background
nohup kubectl port-forward -n kubeflow svc/ml-pipeline-ui 3000:80 > /dev/null 2>&1 &

echo "✅ KFP UI Port-Forward started in background."
echo "🌍 Access at: http://localhost:3000"
echo "🛑 To stop: pkill -f 'kubectl port-forward.*3000:80'"

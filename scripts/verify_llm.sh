#!/bin/bash
NAMESPACE="kubeflow-vellum"
POD=$(kubectl get pod -n $NAMESPACE -l app=backend -o jsonpath='{.items[0].metadata.name}')

echo "Backend Pod: $POD"

echo "Checking LLM Service Health from Backend Pod..."
kubectl exec -n $NAMESPACE $POD -- curl -s -o /dev/null -w "%{http_code}" http://llm-service-predictor/health
echo ""

echo "Listing Models..."
kubectl exec -n $NAMESPACE $POD -- curl -s http://llm-service-predictor/v1/models

echo ""
echo "Testing Chat Completion (Qwen3.5)..."
kubectl exec -n $NAMESPACE $POD -- curl -s -X POST http://llm-service-predictor/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/mnt/models/Qwen3.5-2B",
    "messages": [{"role": "user", "content": "Hello, are you running on GPU?"}],
    "max_tokens": 50
  }'

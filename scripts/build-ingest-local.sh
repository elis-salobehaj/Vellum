#!/bin/bash
set -e

APP_NAME="vellum-ingest"
TAG="local"
IMAGE_NAME="$APP_NAME:$TAG"

echo "🐳 configuring Docker environment to use Minikube..."
eval $(minikube -p minikube docker-env)

echo "🔨 Building Image: $IMAGE_NAME inside Minikube..."
# Build from pipelines/ingestion context
docker build -f pipelines/ingestion/Dockerfile -t $IMAGE_NAME pipelines/ingestion/

echo "✅ Build Complete!"
echo "ℹ️  The image '$IMAGE_NAME' is now available to your cluster."
echo "    In your KFP YAML, ensure you set 'imagePullPolicy: Never' or 'IfNotPresent'."

#!/bin/bash
set -e

# Default Username
USERNAME="elis-salobehaj"
IMAGE_NAME="ghcr.io/$USERNAME/vellum-ingest"
TAG="latest"

echo "🐳 Building Docker Image for Ingestion..."
echo "Target: $IMAGE_NAME:$TAG"

# Build Image
docker build -f backend/Dockerfile.ingest -t $IMAGE_NAME:$TAG .

echo "✅ Build Complete."
echo "📤 Pushing to GHCR (This requires 'docker login ghcr.io')..."

# Push Image
docker push $IMAGE_NAME:$TAG

echo "🎉 Successfully pushed to $IMAGE_NAME:$TAG"
echo ""
echo "NOTE: If this failed with 'denied', run:"
echo "      echo <YOUR_GITHUB_PAT> | docker login ghcr.io -u $USERNAME --password-stdin"

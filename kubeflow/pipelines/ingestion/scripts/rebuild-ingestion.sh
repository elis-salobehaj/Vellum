#!/bin/bash
set -e

echo "🐳 Building Ingestion Image..."
docker build -t vellum-ingest:local -f pipelines/ingestion/Dockerfile pipelines/ingestion

echo "📦 Loading into Minikube..."
minikube image load vellum-ingest:local

echo "✅ Done! Image 'vellum-ingest:local' is ready in the cluster."

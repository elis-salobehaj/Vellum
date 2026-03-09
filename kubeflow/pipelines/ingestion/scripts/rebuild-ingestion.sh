#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "$PROJECT_ROOT/scripts/lib/cluster-common.sh"

ensure_project_root
require_commands docker

echo "🐳 Building Ingestion Image..."
docker build -t vellum-ingest:local -f kubeflow/pipelines/ingestion/Dockerfile .

echo "📦 Loading ingestion image into Kind cluster ${KIND_CLUSTER_NAME}..."
publish_image "vellum-ingest:local" ingestion

echo "✅ Done! Image '${KIND_IMAGE_INGESTION}' is ready for KFP runs."

#!/bin/bash
set -e

echo "🚀 Starting Vellum Platform Setup..."

# 1. Prerequisites Check
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl could not be found"
    exit 1
fi

if ! command -v helm &> /dev/null; then
    echo "❌ helm could not be found"
    exit 1
fi

# 2. Install Kubeflow Manifests (v1.11.0)
echo "📦 Applying Kubeflow Manifests (this may take a few minutes)..."

# 2.1 Pre-Install Known CRDs to reduce race conditions
echo "   👉 Pre-installing CRDs (Cert-Manager, Istio)..."
# We ignore errors here because they might be re-applied later, verification comes in the main step
kubectl apply -k deployment/manifests/common/cert-manager/base --server-side --force-conflicts &> /dev/null || true
kubectl apply -k deployment/manifests/common/istio/istio-crds/base --server-side --force-conflicts &> /dev/null || true
echo "   ⏳ Waiting 10s for CRD registration..."
sleep 10

# 2.2 Main Install
echo "   👉 Applying Full Platform..."
# We apply server-side to avoid "Resource too large" errors with CRDs
# We use a loop to handle Webhook/CRD race conditions (common in Kubeflow)
MAX_RETRIES=5
COUNT=0
set +e
until kubectl apply -k deployment/ --server-side --force-conflicts; do
    EXIT_CODE=$?
    COUNT=$((COUNT+1))
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "❌ Max retries reached. Installation failed."
        exit $EXIT_CODE
    fi
    echo "⚠️  Apply failed (Attempt $COUNT/$MAX_RETRIES). Likely Webhook/CRD race condition. Waiting 20s..."
    sleep 20
done
set -e
echo "✅ Manifests applied successfully."

# 3. Apply Auth Proxy Fix (Retry to fix possible race conditions)
# Required for Central Dashboard sub-apps (Notebooks, Volumes) to receive User Headers
echo "🔑 Applying OAuth2 Proxy Fix (Ensuring consistency)..."
kubectl apply -k deployment/manifests/common/oauth2-proxy/overlays/m2m-dex-only

# 4. Install Qdrant (Vector DB)
echo "💾 Installing Qdrant..."
if ! helm list -n qdrant | grep -q qdrant; then
    helm repo add qdrant https://qdrant.github.io/qdrant-helm --force-update
    helm repo update
    helm install qdrant qdrant/qdrant -n qdrant --create-namespace --set replicas=1
else
    echo "   (Qdrant already installed, skipping)"
fi

# 5. Wait for Core Components
echo "⏳ Waiting for Central Dashboard to be ready..."
kubectl wait --for=condition=ready pod -l app=centraldashboard -n kubeflow --timeout=300s

echo "✅ Platform Setup Complete!"
echo "➡️  Access the Dashboard: ./scripts/connect.sh"
echo "   Login: user@example.com / 12341234"

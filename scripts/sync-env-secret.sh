#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/cluster-common.sh"

ensure_project_root
require_commands kubectl mktemp tac awk
require_kubectl_access

if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
    echo ".env is required to create the vellum-env Kubernetes secret." >&2
    exit 1
fi

TMP_ENV="$(mktemp)"
cleanup() {
    rm -f "$TMP_ENV"
}
trap cleanup EXIT

# Keep the last definition for duplicate keys so local override blocks in .env win.
tac "$PROJECT_ROOT/.env" | awk -F= '
    /^[A-Za-z_][A-Za-z0-9_]*=/ {
        if (!seen[$1]++) {
            lines[++count] = $0
        }
        next
    }
    {
        lines[++count] = $0
    }
    END {
        for (i = count; i >= 1; i--) {
            print lines[i]
        }
    }
' > "$TMP_ENV"

kubectl create secret generic vellum-env \
    --namespace "$VELLUM_NAMESPACE" \
    --from-env-file="$TMP_ENV" \
    --dry-run=client \
    -o yaml | kubectl apply -f -

echo "✅ Kubernetes secret '$VELLUM_NAMESPACE/vellum-env' synchronized from .env"

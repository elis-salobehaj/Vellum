#!/usr/bin/env bash
set -euo pipefail

# This script is meant for CI/CD or local test validation.
# It bootstraps the cluster, deploys the stack, runs tests, and ensures the cluster is nuked afterwards.

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/cluster-common.sh"
ensure_project_root

START_TIME=$(date +%s)
echo -e "\033[0;34m========================================================\033[0m"
echo -e "\033[0;34m🚀 Starting Vellum End-to-End Kind Lifecycle Validation\033[0m"
echo -e "\033[0;34m========================================================\033[0m"

# Trap to ensure cleanup regardless of exit status
cleanup() {
    local exit_code=$?
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    echo -e "\n\033[0;34m========================================================\033[0m"
    echo -e "\033[0;34m🧹 Cleaning up the E2E cluster environment...\033[0m"
    bash ./scripts/nuke-platform.sh >/dev/null 2>&1 || true
    echo -e "\033[0;34m========================================================\033[0m"

    if [[ $exit_code -eq 0 ]]; then
        echo -e "\033[0;32m✅ E2E Lifecycle completed successfully in ${DURATION} seconds.\033[0m"
    else
        echo -e "\033[1;31m❌ E2E Lifecycle FAILED after ${DURATION} seconds.\033[0m"
    fi
    exit $exit_code
}

trap cleanup EXIT

echo -e "\033[0;34m▶️  1. Setting up Local Stack (Kind + Apps)...\033[0m"
export ENABLE_LOCAL_LLM=false # Disable GPU passthrough to expedite CI runs
bash ./scripts/setup-local.sh

echo -e "\033[0;34m▶️  2. Running Automated Test Suite...\033[0m"
bash ./scripts/test.sh

echo -e "\033[0;34m▶️  3. Validation successful. Proceeding to cleanup.\033[0m"

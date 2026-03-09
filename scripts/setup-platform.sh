#!/usr/bin/env bash
set -euo pipefail

echo "setup-platform.sh now delegates to the Kind Phase 1 bootstrap."
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/setup-kind.sh" "$@"

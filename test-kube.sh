#!/bin/bash
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/scripts/lib/cluster-common.sh"
use_default_kubeconfig
echo "KUBECONFIG is $KUBECONFIG"
kubectl cluster-info

#!/bin/bash
set -e

echo "=== Vellum Phase 1 Verification ==="

echo -e "\n1. Checking Crossplane Providers..."
kubectl get providers

echo -e "\n2. Checking Managed Resources Sync Status..."
kubectl get managed

echo -e "\n3. Checking Istio System Pods..."
kubectl get pods -n istio-system

echo -e "\n4. Checking Knative Operator..."
kubectl get knativeservings -A
kubectl get deployment -n knative-operator

echo -e "\n5. Checking Knative Serving Components..."
# Knative Operator should create these in knative-serving namespace
kubectl get pods -n knative-serving

echo -e "\n6. Checking Vellum Platform Claim..."
kubectl get vellumplatform

echo -e "\n=== Verification Complete ==="

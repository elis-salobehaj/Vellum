#!/bin/bash
set -e

# Namespace
NS="kubeflow"

# 1. Get Credentials from Crossplane Secrets
# Note: Adjust secret names based on actual Crossplane output `kubectl get secrets -n kubeflow`
# We use label selectors to find them consistently if names are random
MINIO_SECRET=$(kubectl get secrets -n $NS -l app=minio -o jsonpath="{.items[0].metadata.name}")
MYSQL_SECRET=$(kubectl get secrets -n $NS -l app.kubernetes.io/name=mysql -o jsonpath="{.items[0].metadata.name}")

echo "Found MinIO Secret: $MINIO_SECRET"
echo "Found MySQL Secret: $MYSQL_SECRET"

MINIO_USER=$(kubectl get secret $MINIO_SECRET -n $NS -o jsonpath="{.data.rootUser}" | base64 -d)
MINIO_PASS=$(kubectl get secret $MINIO_SECRET -n $NS -o jsonpath="{.data.rootPassword}" | base64 -d)

MYSQL_PASS=$(kubectl get secret $MYSQL_SECRET -n $NS -o jsonpath="{.data.mysql-root-password}" | base64 -d)

# 2. Create MinIO Secret for KFP (mlpipeline-minio-artifact)
# Expected structure: accesskey, secretkey
kubectl create secret generic mlpipeline-minio-artifact -n $NS \
  --from-literal=accesskey="$MINIO_USER" \
  --from-literal=secretkey="$MINIO_PASS" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Created secret: mlpipeline-minio-artifact"

# 3. Create MySQL Secret for KFP (mysql-secret)
# Expected structure: username, password, host, port (sometimes) via db-details usually
# But KFP core usually looks for 'mysql-secret' with 'username' and 'password'
kubectl create secret generic mysql-secret -n $NS \
  --from-literal=username="root" \
  --from-literal=password="$MYSQL_PASS" \
  --from-literal=host="vellum-mlops-stack-9hnwf-1bb657336ff0-mysql.kubeflow.svc.cluster.local" \
  --from-literal=port="3306" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Created secret: mysql-secret"

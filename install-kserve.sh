#!/bin/bash
set -e

echo "========================================"
echo "Installing KServe v0.15.2"
echo "========================================"

cd ~/Downloads/kserve

echo "Checking KServe version..."
git checkout v0.15.2

echo "Installing KServe..."
kubectl apply --server-side --force-conflicts -f install/v0.15.2/kserve.yaml

echo "Waiting for CRDs..."
kubectl wait --for=condition=Established crd/inferenceservices.serving.kserve.io --timeout=180s
kubectl wait --for=condition=Established crd/clusterservingruntimes.serving.kserve.io --timeout=180s
kubectl wait --for=condition=Established crd/servingruntimes.serving.kserve.io --timeout=180s

echo "Waiting for controller..."
kubectl rollout status deployment/kserve-controller-manager -n kserve --timeout=300s

echo "Installing default runtimes..."
kubectl apply -f install/v0.15.2/kserve-cluster-resources.yaml

echo
echo "========================================"
echo "KServe installation completed."
echo "========================================"

kubectl get pods -n kserve
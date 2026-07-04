#!/bin/bash

echo "🚀 Starting Minikube..."
minikube start --extra-config=apiserver.service-node-port-range=3000-65535

echo "⏳ Waiting for Kubernetes API..."
kubectl wait --for=condition=Ready node/minikube --timeout=180s

echo "📦 Applying manifest..."
kubectl apply -f ../final-kubernetes-manifest.yaml

echo "⏳ Waiting for controller..."
kubectl rollout status deployment/defense-automation-controller -n security-monitoring

echo "🌐 Opening Frontend..."
minikube service frontend-service -n core-app

echo
echo "==============================="
echo "Controller Logs"
echo "==============================="

kubectl logs -f deployment/defense-automation-controller \
    -n security-monitoring
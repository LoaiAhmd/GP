#!/bin/bash
set -e

echo "🔄 Configured shell to use Minikube's internal Docker daemon..."
eval $(minikube -p minikube docker-env)

echo "📦 Rebuilding controller Docker image (loaiahmd/controller:v11)..."
docker build -t loaiahmd/controller:v11 /home/loai/Documents/GP/controller-mohanned

echo "🚀 Restarting the controller deployment in Kubernetes..."
kubectl rollout restart deployment/defense-automation-controller -n security-monitoring

echo "⏳ Waiting for deployment rollout to complete..."
kubectl rollout status deployment/defense-automation-controller -n security-monitoring

echo "✅ Success! The controller is now running with the latest code."

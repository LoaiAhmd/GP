#!/bin/bash

echo "📦 Deploying Application..."

kubectl apply -f ../final-kubernetes-manifest.yaml

echo "⏳ Waiting for Controller..."

kubectl rollout status deployment/defense-automation-controller \
-n security-monitoring

echo "⏳ Waiting for KServe..."

kubectl rollout status deployment/kserve-controller-manager \
-n kserve

echo "✅ Deployment Finished."
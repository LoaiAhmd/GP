#!/bin/bash

echo -e "\tDeploying Application..."

kubectl apply -f ../final-kubernetes-manifest.yaml

echo -e "\n\tWaiting for Controller..."

kubectl rollout status deployment/defense-automation-controller \
-n security-monitoring

echo -e "\n\tWaiting for KServe..."

kubectl rollout status deployment/kserve-controller-manager \
-n kserve

echo -e "\n\tDeployment Finished."
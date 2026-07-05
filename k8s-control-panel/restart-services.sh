#!/bin/bash

echo -e "\tRestarting Core Application..."
kubectl rollout restart deployment -n core-app

echo -e "\n\tRestarting Security Monitoring..."
kubectl rollout restart deployment -n security-monitoring

echo
echo -e "\tWaiting for Core Application..."

for d in $(kubectl get deployment -n core-app -o jsonpath='{.items[*].metadata.name}')
do
    kubectl rollout status deployment/$d -n core-app
done

echo
echo -e "\n\tWaiting for Security Monitoring..."

for d in $(kubectl get deployment -n security-monitoring -o jsonpath='{.items[*].metadata.name}')
do
    kubectl rollout status deployment/$d -n security-monitoring
done

echo
echo "✅ Restart Complete."
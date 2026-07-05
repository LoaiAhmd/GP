#!/bin/bash

echo -e "\tRestarting Core Application..."

CORE_DEPLOYMENTS=(
    frontend-service
    notification-db
    notification-service
    order-db
    order-service
    reporting-service
    staff-db
    staff-service
)

for d in "${CORE_DEPLOYMENTS[@]}"
do
    kubectl rollout restart deployment/$d -n core-app
done

echo
echo -e "\tRestarting Security Monitoring..."

kubectl rollout restart deployment/defense-automation-controller \
    -n security-monitoring

echo
echo -e "\tWaiting for Core Application..."

for d in "${CORE_DEPLOYMENTS[@]}"
do
    kubectl rollout status deployment/$d -n core-app
done

echo
echo -e "\tWaiting for Controller..."

kubectl rollout status deployment/defense-automation-controller \
    -n security-monitoring

echo
echo "✅ Restart Complete."
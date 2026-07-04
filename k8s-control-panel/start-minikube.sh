#!/bin/bash

echo "🚀 Starting Minikube..."

minikube start \
--extra-config=apiserver.service-node-port-range=3000-65535

echo "✅ Minikube Ready."
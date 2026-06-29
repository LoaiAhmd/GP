#!/bin/bash

green="\e[1;32m"
yellow="\e[1;33m"
red="\e[1;31m"
nocolor="\e[0m"

echo -e "${yellow}🚀 Starting Minikube...${nocolor}"
minikube start --extra-config=apiserver.service-node-port-range=3000-65535 > /dev/null 2>&1
echo -e "${green}✅ Minikube is ready!${nocolor}"

echo -e "${red}🔧 Switching to Minikube Docker environment...${nocolor}"
eval $(minikube docker-env) > /dev/null 2>&1

kubectl apply -f final-kubernetes-manifest.yaml
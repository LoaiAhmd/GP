import time
import requests
from scapy.all import sniff, IP, TCP, UDP
from kubernetes import client, config

try:
    config.load_incluster_config()
    print("✅ Loaded in-cluster Kubernetes Configuration Successfully!")
except Exception as e_incluster:
    try:
        config.load_kube_config()
        print("✅ Loaded local Kubernetes Configuration Successfully!")
    except Exception as e_local:
        print(f"❌ Failed to load kube config (in-cluster: {e_incluster}, local: {e_local})")
        exit(1)

apps_v1 = client.AppsV1Api()

AI_MODEL_URL = "http://ai-threat-detector-predictor.security-monitoring.svc.cluster.local/v1/models/custom-model:predict"

MODEL_FEATURE_COUNT = 82

DECOY_SERVICES = {
    "decoy-order-service": "loaiahmd/order-service:latest",
    "decoy-staff-service": "loaiahmd/staff-service:latest",
    "decoy-notification-service": "loaiahmd/notification-service:latest",
    "decoy-reporting-service": "loaiahmd/reporting-service:latest",
    "decoy-frontend-service": "loaiahmd/frontend-service:latest"
}

def deploy_decoy_microservices():
    print("🚨 [Controller] Attack Verified! Triggering Cyber Deception Workspace...")
    for app_name, image_url in DECOY_SERVICES.items():
        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(name=app_name, namespace="deception-workspace"),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(match_labels={"app": app_name}),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": app_name}),
                    spec=client.V1PodSpec(containers=[client.V1Container(name=app_name, image=image_url)])
                )
            )
        )
        try:
            apps_v1.create_namespaced_deployment(namespace="deception-workspace", body=deployment)
            print(f"✅ Successfully deployed Decoy Mirror: {app_name}")
        except client.exceptions.ApiException as e:
            if e.status == 409: print(f"ℹ️ Decoy {app_name} already active.")
            else: print(f"❌ Failed to deploy {app_name}: {e}")

def process_packet_flow(packet):
    if packet.haslayer(IP):
        ip_layer = packet[IP]
        proto = ip_layer.proto
        size = len(packet)

        sport, dport = 0, 0
        if packet.haslayer(TCP):
            sport, dport = packet[TCP].sport, packet[TCP].dport
        elif packet.haslayer(UDP):
            sport, dport = packet[UDP].sport, packet[UDP].dport

        if dport in [3000, 80, 8000, 8001, 8002, 8003]:
            print(f"📊 [Traffic Caught] Proto: {proto}, Size: {size} bytes, Src Port: {sport} -> Dst Port: {dport}")

            base_features = [6, 44, 55555, 80]
            features_row = base_features + [0] * (82 - len(base_features))

            try:
                payload = {"instances": [features_row]}
                response = requests.post(AI_MODEL_URL, json=payload, timeout=2)
                result = response.json()

                predictions = result.get("predictions", ["Normal"])
                prediction = predictions[0] if predictions else "Normal"
                print(f"🤖 [AI Decision]: {prediction}")

                if prediction == "Attack":
                    deploy_decoy_microservices()
            except Exception as e:
                print(f"⚠️ AI Server status check: {e}")

print("🚀 Pure Python Automation Controller Active. Sniffing live on network...")

sniff(filter="tcp port 3000 or tcp port 80", prn=process_packet_flow, store=0)
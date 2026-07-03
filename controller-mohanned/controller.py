import traceback
import requests
from scapy.all import sniff, IP, TCP, UDP
from kubernetes import client, config

print("========== CONTROLLER STARTED ==========", flush=True)

try:
    config.load_incluster_config()
    print("✅ Loaded in-cluster Kubernetes Configuration Successfully!", flush=True)
except Exception as e_incluster:
    try:
        config.load_kube_config()
        print("✅ Loaded local Kubernetes Configuration Successfully!", flush=True)
    except Exception as e_local:
        print(f"❌ Failed to load kube config", flush=True)
        print(e_incluster, flush=True)
        print(e_local, flush=True)
        exit(1)

print("✅ Creating Kubernetes client...", flush=True)
apps_v1 = client.AppsV1Api()

AI_MODEL_URL = "http://ai-threat-detector-predictor.security-monitoring.svc.cluster.local/v1/models/custom-model:predict"

LABELS = {
    "0": "Normal",
    "1": "Attack",
    "2": "Suspicious"
}

DECOY_SERVICES = {
    "decoy-order-service": "loaiahmd/order-service:latest",
    "decoy-staff-service": "loaiahmd/staff-service:latest",
    "decoy-notification-service": "loaiahmd/notification-service:latest",
    "decoy-reporting-service": "loaiahmd/reporting-service:latest",
    "decoy-frontend-service": "loaiahmd/frontend-service:latest"
}


def deploy_decoy_microservices():
    print("🚨 Attack verified. Deploying deception services...", flush=True)

    for app_name, image_url in DECOY_SERVICES.items():
        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(
                name=app_name,
                namespace="deception-workspace"
            ),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(
                    match_labels={"app": app_name}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={"app": app_name}
                    ),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name=app_name,
                                image=image_url
                            )
                        ]
                    )
                )
            )
        )

        try:
            apps_v1.create_namespaced_deployment(
                namespace="deception-workspace",
                body=deployment
            )
            print(f"✅ Created {app_name}", flush=True)

        except client.exceptions.ApiException as e:
            if e.status == 409:
                print(f"ℹ️ {app_name} already exists.", flush=True)
            else:
                print(e, flush=True)


def process_packet_flow(packet):

    if not packet.haslayer(IP):
        return

    ip_layer = packet[IP]

    sport = 0
    dport = 0

    if packet.haslayer(TCP):
        sport = packet[TCP].sport
        dport = packet[TCP].dport
    elif packet.haslayer(UDP):
        sport = packet[UDP].sport
        dport = packet[UDP].dport

    print(
        f"📊 Packet: {ip_layer.src}:{sport} -> {ip_layer.dst}:{dport}",
        flush=True
    )

    if dport not in [80, 3000, 8000, 8001, 8002, 8003]:
        return

    features = [6, 44, 55555, 80] + [0] * 78

    try:
        response = requests.post(
            AI_MODEL_URL,
            json={"instances": [features]},
            timeout=5
        )

        print(response.text, flush=True)

        prediction = str(response.json()["predictions"][0])

        print(
            f"🤖 AI Decision: {LABELS.get(prediction, prediction)}",
            flush=True
        )

        if prediction == "1":
            deploy_decoy_microservices()

    except Exception:
        traceback.print_exc()


print("🚀 Controller Ready.", flush=True)
print("👂 Starting packet capture on eth0...", flush=True)

sniff(
    iface="eth0",
    filter="tcp port 80 or tcp port 3000",
    prn=process_packet_flow,
    store=False
)
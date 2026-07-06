from __future__ import annotations

"""
Defense Automation Controller
=============================

Main orchestrator for the AI-Driven Kubernetes Cyber Deception pipeline.

Workflow:
  1. Load Kubernetes configuration
  2. Start live packet capture with CICFlowMeter flow extraction
  3. As completed flows arrive, parse their features
  4. Send feature vectors to KServe for inference
  5. If the prediction is "Attack" -> deploy decoy microservices
"""

import time
import json
import traceback

from kubernetes import client, config

from config import DECOY_NAMESPACE, DECOY_SERVICES, LABELS
from flow_capture import LiveFlowCapture
from feature_parser import parse_features
from kserve_client import predict


SERVICE_PORTS = {
    "3000": "frontend",
    "8000": "order",
    "8001": "staff",
    "8002": "notification",
    "8003": "reporting",
    "8443": "kubernetes-api",
    "22": "ssh",
}

MONITORED_SERVICES = {"frontend", "order", "staff", "notification", "reporting"}
SKIP_LOG_EVERY = 25


# ---------------------------------------------------------
# Kubernetes Initialisation
# ---------------------------------------------------------

def load_k8s_config() -> None:
    """Load in-cluster config, falling back to local kubeconfig."""
    try:
        config.load_incluster_config()
        print("[OK] Loaded in-cluster Kubernetes config", flush=True)
    except Exception as e_incluster:
        try:
            config.load_kube_config()
            print("[OK] Loaded local Kubernetes config", flush=True)
        except Exception as e_local:
            print("[ERROR] Failed to load kube config", flush=True)
            print(e_incluster, flush=True)
            print(e_local, flush=True)
            exit(1)


# ---------------------------------------------------------
# Decoy Deployment  (unchanged from original)
# ---------------------------------------------------------

apps_v1: client.AppsV1Api | None = None
decoys_deployed = False


def deploy_decoy_microservices() -> None:
    global decoys_deployed

    if decoys_deployed:
        print("[INFO] Decoys already deployed.", flush=True)
        return

    print("[ALERT] Attack verified. Deploying deception services...", flush=True)
    try:
        apps_v1.list_namespaced_deployment(DECOY_NAMESPACE)
    except Exception:
        return
    for app_name, image_url in DECOY_SERVICES.items():
        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(
                name=app_name,
                namespace=DECOY_NAMESPACE,
            ),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(
                    match_labels={"app": app_name},
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={"app": app_name},
                    ),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name=app_name,
                                image=image_url,
                            )
                        ]
                    ),
                ),
            ),
        )

        try:
            apps_v1.create_namespaced_deployment(
                namespace=DECOY_NAMESPACE,
                body=deployment,
            )
            print(f"  [OK] Created {app_name}", flush=True)

        except client.exceptions.ApiException as e:
            if e.status == 409:
                print(f"  [INFO] {app_name} already exists.", flush=True)
            else:
                print(e, flush=True)
    decoys_deployed = True


def describe_flow(row: dict) -> str:
    src = row.get("src_ip", "?")
    dst = row.get("dst_ip", "?")
    src_port = str(row.get("src_port", "?"))
    dst_port = str(row.get("dst_port", "?"))
    protocol = row.get("protocol", "?")
    service = SERVICE_PORTS.get(dst_port, SERVICE_PORTS.get(src_port, "other"))
    return (
        f"{src}:{src_port} -> {dst}:{dst_port} "
        f"proto={protocol} service={service}"
    )


def get_flow_service(row: dict) -> str:
    src_port = str(row.get("src_port", "?"))
    dst_port = str(row.get("dst_port", "?"))
    return SERVICE_PORTS.get(dst_port, SERVICE_PORTS.get(src_port, "other"))


# ---------------------------------------------------------
# Main Loop
# ---------------------------------------------------------

def main() -> None:
    global apps_v1

    print("=" * 55, flush=True)
    print("  DEFENSE AUTOMATION CONTROLLER STARTED", flush=True)
    print("=" * 55, flush=True)

    # 1. Kubernetes
    load_k8s_config()
    print("[OK] Creating Kubernetes client...", flush=True)
    apps_v1 = client.AppsV1Api()

    # Query cluster to see if decoy deployments are already present
    global decoys_deployed
    try:
        existing = apps_v1.list_namespaced_deployment(DECOY_NAMESPACE)
        existing_names = {dep.metadata.name for dep in existing.items}
        if any(name in existing_names for name in DECOY_SERVICES.keys()):
            decoys_deployed = True
            print("[INFO] Detected existing decoy deployments. Deception active.", flush=True)
    except Exception as e:
        print(f"[WARN] Failed to query existing decoy deployments: {e}", flush=True)

    # 2. Start live packet capture
    capture = LiveFlowCapture()
    capture.start()

    print("[READY] Controller active -- entering main loop", flush=True)
    print("-" * 55, flush=True)

    # 3. Process completed flows from the queue
    flow_count = 0
    skipped_count = 0
    while True:
        try:
            # Block for up to 1 second waiting for a flow
            row = capture.flow_queue.get(timeout=1.0)
        except Exception:
            # Queue empty -- just loop
            continue

        flow_count += 1
        flow_summary = describe_flow(row)

        service = get_flow_service(row)
        if service not in MONITORED_SERVICES:
            skipped_count += 1
            if skipped_count == 1 or skipped_count % SKIP_LOG_EVERY == 0:
                print(
                    f"[SKIP] ignored {skipped_count} non-app flow(s); "
                    f"latest={flow_summary}",
                    flush=True,
                )
            continue

        # 3a. Parse feature vector
        features = parse_features(row)
        if features is None:
            continue

        # 3b. Send to KServe
        prediction = predict(features, flow_id=flow_count)
        if prediction is None:
            continue

        # 3c. Act on prediction
        label = LABELS.get(prediction, prediction)
        normalized_label = label.strip().lower()

        action = "normal traffic -- no action"
        if prediction == "2" or normalized_label == "suspicious":
            action = "suspicious traffic -- monitoring"
        elif prediction == "0" or normalized_label in {"normal", "benign"}:
            action = "normal traffic -- no action"
        else:
            if decoys_deployed:
                action = "ATTACK detected -- decoys already deployed"
            else:
                action = "ATTACK detected -- deploying deception services"
                deploy_decoy_microservices()

        # Print formatted JSON block for flow
        src_ip = row.get("src_ip", "?")
        dst_ip = row.get("dst_ip", "?")
        src_port = str(row.get("src_port", "?"))
        dst_port = str(row.get("dst_port", "?"))
        
        src_service = SERVICE_PORTS.get(src_port, "client" if src_ip == "192.168.49.1" else "other")
        dst_service = SERVICE_PORTS.get(dst_port, "client" if dst_ip == "192.168.49.1" else "other")

        # Determine attack type
        attack_type = "None"
        if prediction not in ("0", "2") and normalized_label not in ("normal", "benign", "suspicious"):
            if service in ("frontend", "order", "staff", "notification", "reporting"):
                attack_type = "SSRF (Server-Side Request Forgery)"
            else:
                attack_type = "Reconnaissance (Reconn)"

        flow_log = {
            "source": f"{src_service} ({src_ip}:{src_port})",
            "destination": f"{dst_service} ({dst_ip}:{dst_port})",
            "protocol": row.get("protocol"),
            "service": service,
            "features": len(features),
            "prediction": label,
            "attack_type": attack_type,
            "action": action
        }
        print(f"\nFLOW {flow_count} {json.dumps(flow_log, indent=2)}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[STOP] Controller shutting down", flush=True)
    except Exception:
        traceback.print_exc()
        exit(1)

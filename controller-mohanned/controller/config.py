AI_MODEL_URL = (
    "http://ai-threat-detector-predictor.security-monitoring.svc.cluster.local"
    "/v1/models/custom-model:predict"
)

MONITORED_PORTS = [80, 3000, 8000, 8001, 8002, 8003]

LABELS = {
    "0": "Normal",
    "1": "Attack",
    "2": "Suspicious"
}

DECOY_NAMESPACE = "deception-workspace"

DECOY_SERVICES = {
    "decoy-order-service": "loaiahmd/order-service:latest",
    "decoy-staff-service": "loaiahmd/staff-service:latest",
    "decoy-notification-service": "loaiahmd/notification-service:latest",
    "decoy-reporting-service": "loaiahmd/reporting-service:latest",
    "decoy-frontend-service": "loaiahmd/frontend-service:latest"
}
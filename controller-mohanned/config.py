"""
Centralized configuration constants for the Defense Automation Controller.

All tunable parameters and service definitions live here
so they can be adjusted without modifying business logic.
"""

# ─────────────────────────────────────────────
# KServe / AI Model
# ─────────────────────────────────────────────
AI_MODEL_URL = (
    "http://ai-threat-detector-service"
    ".security-monitoring.svc.cluster.local"
    "/v1/models/custom-model:predict"
)

KSERVE_TIMEOUT = 5  # seconds

LABELS = {
    "0": "Normal",
    "1": "Attack",
    "2": "Suspicious",
}

# ─────────────────────────────────────────────
# Network Capture
# ─────────────────────────────────────────────
CAPTURE_INTERFACE = "eth0"

# How many seconds of inactivity before a flow is considered expired
FLOW_EXPIRED_SECONDS = 10

# How often (seconds) the garbage collector checks for expired flows
GC_INTERVAL = 5

# Keep the main controller log focused on analyzed flows.
VERBOSE_GC = False

# ─────────────────────────────────────────────
# Deception / Decoy Services
# ─────────────────────────────────────────────
DECOY_NAMESPACE = "deception-workspace"

DECOY_SERVICES = {
    "decoy-order-service":        "loaiahmd/order-service:latest",
    "decoy-staff-service":        "loaiahmd/staff-service:latest",
    "decoy-notification-service": "loaiahmd/notification-service:latest",
    "decoy-reporting-service":    "loaiahmd/reporting-service:latest",
    "decoy-frontend-service":     "loaiahmd/frontend-service:latest",
}

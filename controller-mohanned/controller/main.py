import traceback
from kubernetes import config

from packet_capture import start


print("=" * 40)
print("Defense Automation Controller")
print("=" * 40)

try:

    config.load_incluster_config()

    print("Loaded in-cluster configuration.")

except Exception:

    try:

        config.load_kube_config()

        print("Loaded local kubeconfig.")

    except Exception:

        traceback.print_exc()

        exit(1)

print("Starting packet capture...")

start()
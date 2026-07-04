from scapy.all import sniff, IP, TCP, UDP

from config import MONITORED_PORTS, LABELS
from feature_extractor import extract_features
from inference_client import predict
from deception import deploy_decoy_microservices


def process_packet(packet):

    if not packet.haslayer(IP):
        return

    port = None

    if packet.haslayer(TCP):
        port = packet[TCP].dport

    elif packet.haslayer(UDP):
        port = packet[UDP].dport

    if port not in MONITORED_PORTS:
        return

    features = extract_features(packet)

    prediction = predict(features)

    print(
        f"Prediction: {LABELS.get(prediction, prediction)}",
        flush=True
    )

    if prediction == "1":
        deploy_decoy_microservices()


def start():

    sniff(
        iface="eth0",
        filter="tcp port 80 or tcp port 3000",
        prn=process_packet,
        store=False
    )
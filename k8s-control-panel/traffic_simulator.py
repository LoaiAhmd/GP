import sys
import socket
import urllib.request
import urllib.error
import subprocess
import time
import os

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QTextEdit
)
from PySide6.QtCore import QThread, Signal, Slot, Qt

class SimulatorWorker(QThread):
    log_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, action_type, target_ip, target_port=3000):
        super().__init__()
        self.action_type = action_type
        self.target_ip = target_ip
        self.target_port = target_port

    def run(self):
        if self.action_type == "recon":
            self.run_recon()
        elif self.action_type == "ssrf":
            self.run_ssrf()
        self.finished_signal.emit()

    def run_recon(self):
        ports = [22, 80, 3000, 8000, 8001, 8002, 8003, 8443]
        self.log_signal.emit(f"[*] Starting reconnaissance connection probes on {self.target_ip}...")
        for port in ports:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.2)
                result = s.connect_ex((self.target_ip, port))
                if result == 0:
                    self.log_signal.emit(f"  [+] Port {port}: OPEN (Connection established)")
                else:
                    self.log_signal.emit(f"  [-] Port {port}: CLOSED (Connection refused/timeout)")
                s.close()
            except Exception as e:
                self.log_signal.emit(f"  [!] Port {port} error: {e}")
            time.sleep(0.1)
        self.log_signal.emit("[*] Reconnaissance probe simulation finished.\n")

    def run_ssrf(self):
        self.log_signal.emit(f"[*] Starting SSRF request simulation to target {self.target_ip}:{self.target_port}...")
        # Simulate standard HTTP request containing various metadata redirect/query params
        payloads = [
            "?url=http://169.254.169.254/latest/meta-data/",
            "?path=http://127.0.0.1:8000/admin",
            "?file=http://order-service.core-app.svc.cluster.local:8000",
        ]
        
        for payload in payloads:
            url = f"http://{self.target_ip}:{self.target_port}/{payload}"
            self.log_signal.emit(f"  [→] GET request: {url}")
            try:
                req = urllib.request.Request(
                    url, 
                    headers={'User-Agent': 'Security-Testing-Simulator'}
                )
                with urllib.request.urlopen(req, timeout=1.5) as response:
                    status = response.status
                    self.log_signal.emit(f"  [←] Response Status: {status}")
            except urllib.error.HTTPError as e:
                self.log_signal.emit(f"  [←] HTTP Error: {e.code}")
            except urllib.error.URLError as e:
                self.log_signal.emit(f"  [←] URL/Connection Error: {e.reason}")
            except Exception as e:
                self.log_signal.emit(f"  [!] Error: {e}")
            time.sleep(0.5)
        self.log_signal.emit("[*] SSRF request simulation finished.\n")


class TrafficSimulatorWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kubernetes Cyber Deception - Traffic Simulator")
        self.resize(600, 450)
        
        # Load theme.qss if available to match control panel
        self.load_theme()

        layout = QVBoxLayout(self)
        
        # IP config layout
        ip_layout = QHBoxLayout()
        self.lbl_ip = QLabel("Target IP:")
        self.txt_ip = QLineEdit()
        self.txt_ip.setText(self.detect_ip())
        self.lbl_port = QLabel("Target Port:")
        self.txt_port = QLineEdit()
        self.txt_port.setText("3000")
        
        ip_layout.addWidget(self.lbl_ip)
        ip_layout.addWidget(self.txt_ip)
        ip_layout.addWidget(self.lbl_port)
        ip_layout.addWidget(self.txt_port)
        
        layout.addLayout(ip_layout)
        
        # Buttons layout
        btn_layout = QHBoxLayout()
        self.btn_recon = QPushButton("Simulate Reconnaissance Scan")
        self.btn_ssrf = QPushButton("Simulate SSRF Request")
        
        btn_layout.addWidget(self.btn_recon)
        btn_layout.addWidget(self.btn_ssrf)
        layout.addLayout(btn_layout)
        
        # Logs text edit
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)
        
        # Connect signals
        self.btn_recon.clicked.connect(self.start_recon)
        self.btn_ssrf.clicked.connect(self.start_ssrf)
        
        self.worker = None
        self.log_output.append("Traffic Simulator Ready.\nTarget IP auto-detected via 'minikube ip'.")

    def load_theme(self):
        try:
            with open("theme.qss", "r") as f:
                self.setStyleSheet(f.read())
        except Exception:
            try:
                theme_path = os.path.join(os.path.dirname(__file__), "theme.qss")
                with open(theme_path, "r") as f:
                    self.setStyleSheet(f.read())
            except Exception:
                pass

    def detect_ip(self):
        try:
            output = subprocess.check_output(["minikube", "ip"], stderr=subprocess.DEVNULL)
            return output.decode().strip()
        except Exception:
            return "127.0.0.1"

    def start_recon(self):
        self.toggle_buttons(False)
        ip = self.txt_ip.text().strip()
        self.worker = SimulatorWorker("recon", ip)
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished_signal.connect(lambda: self.toggle_buttons(True))
        self.worker.start()

    def start_ssrf(self):
        self.toggle_buttons(False)
        ip = self.txt_ip.text().strip()
        port = int(self.txt_port.text().strip())
        self.worker = SimulatorWorker("ssrf", ip, port)
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished_signal.connect(lambda: self.toggle_buttons(True))
        self.worker.start()

    def toggle_buttons(self, enabled):
        self.btn_recon.setEnabled(enabled)
        self.btn_ssrf.setEnabled(enabled)

    def append_log(self, text):
        self.log_output.append(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TrafficSimulatorWindow()
    window.show()
    sys.exit(app.exec())

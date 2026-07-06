from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
)

from PySide6.QtCore import QTimer, QProcess


class DataWidget(QWidget):

    def __init__(self):
        super().__init__()

        self.pod_process = None
        self.event_process = None
        self.log_process = None
        self.log_buffer = ""
        self.attacks_data = []

        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()

        layout.addWidget(self.tabs)

        # =====================================================
        # Pods Tab
        # =====================================================

        pods_page = QWidget()
        pods_layout = QVBoxLayout(pods_page)

        pods_layout.addWidget(QLabel("<h2>Pods</h2>"))

        self.pods = QTableWidget()

        self.pods.setColumnCount(6)
        self.pods.setHorizontalHeaderLabels([
            "Namespace",
            "Pod",
            "Ready",
            "Status",
            "Restarts",
            "Age",
        ])

        pods_layout.addWidget(self.pods)

        self.tabs.addTab(pods_page, "Pods")

        # =====================================================
        # Events Tab
        # =====================================================

        events_page = QWidget()
        events_layout = QVBoxLayout(events_page)

        events_layout.addWidget(QLabel("<h2>Cluster Events</h2>"))

        self.events = QTableWidget()

        self.events.setColumnCount(5)
        self.events.setHorizontalHeaderLabels([
            "Namespace",
            "Reason",
            "Object",
            "Type",
            "Age",
        ])

        events_layout.addWidget(self.events)

        self.tabs.addTab(events_page, "Cluster Events")

        # =====================================================
        # Attacks Tab
        # =====================================================
        attacks_page = QWidget()
        attacks_layout = QVBoxLayout(attacks_page)
        attacks_layout.addWidget(QLabel("<h2>Detected Attacks</h2>"))

        self.attacks_table = QTableWidget()
        self.attacks_table.setColumnCount(4)
        self.attacks_table.setHorizontalHeaderLabels([
            "Flow ID",
            "Source -> Destination",
            "Attack Type",
            "Time",
        ])
        attacks_layout.addWidget(self.attacks_table)

        self.tabs.addTab(attacks_page, "Attacks")

        # =====================================================
        # Timer
        # =====================================================

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)

        # Connect tab change signal after everything is fully initialized
        self.tabs.currentChanged.connect(self.refresh)

    # =====================================================
    # Public API
    # =====================================================

    def start(self):
        if not self.timer.isActive():
            self.timer.start(5000)

        if self.log_process is None:
            self.log_process = QProcess(self)
            self.log_process.readyReadStandardOutput.connect(self.read_controller_logs)
            self.log_process.start("kubectl", [
                "logs",
                "-f",
                "deployment/defense-automation-controller",
                "-n",
                "security-monitoring",
                "--tail=100"
            ])

        self.refresh()

    def stop(self):
        self.timer.stop()

        for process in (self.pod_process, self.event_process, self.log_process):
            if process is None:
                continue

            if process.state() != QProcess.NotRunning:
                process.terminate()
                if not process.waitForFinished(1000):
                    process.kill()
                    process.waitForFinished()
            process.deleteLater()

        self.pod_process = None
        self.event_process = None
        self.log_process = None

    def refresh(self):
        idx = self.tabs.currentIndex()
        if idx == 0:
            self.load_pods()
        elif idx == 1:
            self.load_events()
        elif idx == 2:
            self.update_attacks_table()

    # =====================================================
    # Pods
    # =====================================================

    def load_pods(self):

        if self.pod_process is not None:

            if self.pod_process.state() != QProcess.NotRunning:
                return

            self.pod_process.deleteLater()

        self.pod_process = QProcess(self)

        self.pod_process.finished.connect(self.update_pods)

        self.pod_process.start(
            "kubectl",
            [
                "get",
                "pods",
                "-A",
                "--no-headers",
            ],
        )

    def update_pods(self):

        if self.pod_process is None:
            return

        output = bytes(
            self.pod_process.readAllStandardOutput()
        ).decode(errors="ignore")

        rows = [
            line.split()
            for line in output.splitlines()
            if line.strip()
        ]

        self.pods.setRowCount(len(rows))

        for r, row in enumerate(rows):

            for c in range(min(6, len(row))):
                self.pods.setItem(
                    r,
                    c,
                    QTableWidgetItem(row[c]),
                )

        self.pods.resizeColumnsToContents()

        self.pod_process.deleteLater()
        self.pod_process = None

    # =====================================================
    # Events
    # =====================================================

    def load_events(self):

        if self.event_process is not None:

            if self.event_process.state() != QProcess.NotRunning:
                return

            self.event_process.deleteLater()

        self.event_process = QProcess(self)

        self.event_process.finished.connect(self.update_events)

        self.event_process.start(
            "kubectl",
            [
                "get",
                "events",
                "-A",
                "--no-headers",
            ],
        )

    def update_events(self):

        if self.event_process is None:
            return

        output = bytes(
            self.event_process.readAllStandardOutput()
        ).decode(errors="ignore")

        rows = [
            line.split(None, 4)
            for line in output.splitlines()
            if line.strip()
        ]

        self.events.setRowCount(len(rows))

        for r, row in enumerate(rows):

            for c in range(min(5, len(row))):
                self.events.setItem(
                    r,
                    c,
                    QTableWidgetItem(row[c]),
                )

        self.events.resizeColumnsToContents()

        self.event_process.deleteLater()
        self.event_process = None

    # =====================================================
    # Attacks Stream Parser
    # =====================================================

    def read_controller_logs(self):
        if self.log_process is None:
            return
        text = bytes(self.log_process.readAllStandardOutput()).decode(errors="ignore")
        self.log_buffer += text

        import re
        import json

        pattern = re.compile(r"FLOW (\d+) (\{.*?^})", re.DOTALL | re.MULTILINE)
        matches = list(pattern.finditer(self.log_buffer))

        if matches:
            last_end = 0
            for match in matches:
                flow_id = match.group(1)
                json_str = match.group(2)
                try:
                    data = json.loads(json_str)
                    prediction = data.get("prediction", "")
                    attack_type = data.get("attack_type", "None")

                    # If this is an attack
                    if attack_type != "None" or "attack" in prediction.lower():
                        pod_port = f"{data.get('source')} -> {data.get('destination')}"
                        timestamp = data.get("time", "unknown")
                        
                        record = (f"Flow #{flow_id}", pod_port, attack_type, timestamp)
                        if record not in self.attacks_data:
                            self.attacks_data.insert(0, record)
                            self.update_attacks_table()
                except Exception:
                    pass
                last_end = match.end()
            self.log_buffer = self.log_buffer[last_end:]

    def update_attacks_table(self):
        self.attacks_table.setRowCount(len(self.attacks_data))
        for r, (flow_id, pod_port, attack_type, timestamp) in enumerate(self.attacks_data):
            self.attacks_table.setItem(r, 0, QTableWidgetItem(flow_id))
            self.attacks_table.setItem(r, 1, QTableWidgetItem(pod_port))
            self.attacks_table.setItem(r, 2, QTableWidgetItem(attack_type))
            self.attacks_table.setItem(r, 3, QTableWidgetItem(timestamp))
        self.attacks_table.resizeColumnsToContents()
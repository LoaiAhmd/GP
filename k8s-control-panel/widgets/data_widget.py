from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
)

from PySide6.QtCore import QTimer, QProcess


class DataWidget(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        #
        # Pods
        #

        layout.addWidget(QLabel("<h2>Pods</h2>"))

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

        layout.addWidget(self.pods)

        #
        # Events
        #

        layout.addWidget(QLabel("<h2>Cluster Events</h2>"))

        self.events = QTableWidget()

        self.events.setColumnCount(5)

        self.events.setHorizontalHeaderLabels([
            "Namespace",
            "Reason",
            "Object",
            "Type",
            "Age",
        ])

        layout.addWidget(self.events)

        #
        # Timer
        #

        self.timer = QTimer()

        self.timer.timeout.connect(self.refresh)

        self.timer.start(3000)

    def refresh(self):

        self.load_pods()

        self.load_events()

    #
    # Pods
    #

    def load_pods(self):

        self.pod_process = QProcess()

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

        output = bytes(
            self.pod_process.readAllStandardOutput()
        ).decode()

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

    #
    # Events
    #

    def load_events(self):

        self.event_process = QProcess()

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

        output = bytes(
            self.event_process.readAllStandardOutput()
        ).decode()

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
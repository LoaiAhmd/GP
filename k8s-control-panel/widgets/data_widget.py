from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
)

from PySide6.QtCore import QTimer, QProcess
from PySide6.QtWidgets import QTabWidget


class DataWidget(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()

        #
        # Pods Tab
        #

        pods_page = QWidget()
        pods_layout = QVBoxLayout(pods_page)

        self.pods = QTableWidget()
        self.pods.horizontalHeader().setStretchLastSection(True)
        self.pods.verticalHeader().setVisible(False)
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

        #
        # Events Tab
        #

        events_page = QWidget()
        events_layout = QVBoxLayout(events_page)

        self.events = QTableWidget()
        self.events.verticalHeader().setVisible(False)
        self.events.horizontalHeader().setStretchLastSection(True)
        self.events.setColumnCount(5)
        self.events.setHorizontalHeaderLabels([
            "Namespace",
            "Reason",
            "Object",
            "Type",
            "Age",
        ])

        events_layout.addWidget(self.events)

        #
        # Add Tabs
        #

        self.tabs.addTab(pods_page, "Pods")
        self.tabs.addTab(events_page, "Cluster Events")

        layout.addWidget(self.tabs)

        #
        # Timer
        #

        self.timer = QTimer()
        self.pod_process = QProcess(self)
        self.event_process = QProcess(self)

        self.pod_process.finished.connect(self.update_pods)
        self.event_process.finished.connect(self.update_events)

        self.timer.timeout.connect(self.refresh)

        self.timer.start(3000)

    def refresh(self):

        self.load_pods()

        self.load_events()

    #
    # Pods
    #

    def load_pods(self):

        if self.pod_process.state() != QProcess.NotRunning:
            return

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

        if self.event_process.state() != QProcess.NotRunning:
            return

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

    def stop(self):

        self.timer.stop()

        for process in (self.pod_process, self.event_process):

            if process.state() != QProcess.NotRunning:
                process.kill()
                process.waitForFinished()
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

        self.refresh()

    def stop(self):

        self.timer.stop()

        for process in (self.pod_process, self.event_process):

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

    # =====================================================
    # Refresh
    # =====================================================

    def refresh(self):

        if self.tabs.currentIndex() == 0:
            self.load_pods()
        else:
            self.load_events()

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
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QTabWidget
)

from widgets.terminal_widget import TerminalWidget
from widgets.status_card import StatusCard
from widgets.data_widget import DataWidget

from services.process_manager import ProcessManager
from services.cluster_monitor import ClusterMonitor


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "AI-Driven Kubernetes Cyber Deception Control Panel"
        )

        self.resize(1400, 800)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)

        # ===========================
        # Left Panel
        # ===========================

        left_layout = QVBoxLayout()

        # Status Cards
        self.minikube_card = StatusCard("Minikube")
        self.controller_card = StatusCard("Controller")
        self.kserve_card = StatusCard("KServe")
        self.frontend_card = StatusCard("Frontend")

        cards = QGridLayout()
        cards.addWidget(self.minikube_card, 0, 0)
        cards.addWidget(self.controller_card, 0, 1)
        cards.addWidget(self.kserve_card, 1, 0)
        cards.addWidget(self.frontend_card, 1, 1)

        left_layout.addLayout(cards)
        left_layout.addSpacing(15)

        # Cluster Buttons
        self.btn_start = QPushButton("Start Minikube")
        self.btn_stop_cluster = QPushButton("Stop Minikube")
        self.btn_deploy = QPushButton("Deploy Application")
        self.btn_frontend = QPushButton("Open Frontend")

        left_layout.addWidget(self.btn_start)
        left_layout.addWidget(self.btn_stop_cluster)
        left_layout.addWidget(self.btn_deploy)
        left_layout.addWidget(self.btn_frontend)

        left_layout.addSpacing(20)

        # Monitoring Buttons
        self. btn_data = QPushButton("Kubernetes Data")
        self.btn_controller = QPushButton("Controller Logs")
        self.btn_kserve = QPushButton("KServe Logs")

        left_layout.addWidget(self. btn_data)
        left_layout.addWidget(self.btn_controller)
        left_layout.addWidget(self.btn_kserve)

        left_layout.addSpacing(20)

        # Utility Buttons
        self.btn_stop = QPushButton("Stop Current Command")
        self.btn_clear = QPushButton("Clear Output")
        self.btn_exit = QPushButton("Exit")


        left_layout.addWidget(self.btn_stop)
        left_layout.addWidget(self.btn_clear)
        left_layout.addWidget(self.btn_exit)

        left_layout.addStretch()

        # ===========================
        # Right Panel
        # ===========================

        self.tabs = QTabWidget()

        self.terminal = TerminalWidget()
        self.data = DataWidget()

        self.tabs.addTab(self.terminal, "Terminal")
        self.tabs.addTab(self.data, "Data")

        main_layout.addLayout(left_layout, 1)
        main_layout.addWidget(self.tabs, 4)

        # ===========================
        # Services
        # ===========================

        self.process_manager = ProcessManager(self.terminal)
        self.monitor = ClusterMonitor(self)

        # ===========================
        # Signals
        # ===========================

        self.btn_start.clicked.connect(self.start_minikube)
        self.btn_stop_cluster.clicked.connect(self.stop_minikube)
        self.btn_deploy.clicked.connect(self.deploy_application)
        self.btn_frontend.clicked.connect(self.open_frontend)

        self. btn_data.clicked.connect(self.kubernetes_data)
        self.btn_controller.clicked.connect(self.controller_logs)
        self.btn_kserve.clicked.connect(self.kserve_logs)

        self.btn_stop.clicked.connect(self.stop_command)
        self.btn_clear.clicked.connect(self.terminal.clear_output)
        self.btn_exit.clicked.connect(self.exit)

        self.statusBar().showMessage("Ready")

    # =====================================================
    # Cluster
    # =====================================================

    def start_minikube(self):

        self.tabs.setCurrentWidget(self.terminal)
        self.terminal.clear_output()

        self.process_manager.run_script("./start-minikube.sh")

        self.statusBar().showMessage("Starting Minikube...")

    def stop_minikube(self):

        self.tabs.setCurrentWidget(self.terminal)
        self.terminal.clear_output()

        self.process_manager.run_command(
            "minikube",
            ["stop"]
        )

        self.statusBar().showMessage("Stopping Minikube...")

    def deploy_application(self):

        self.tabs.setCurrentWidget(self.terminal)
        self.terminal.clear_output()

        self.process_manager.run_script("./deploy-app.sh")

        self.statusBar().showMessage("Deploying Application...")

    def open_frontend(self):

        self.tabs.setCurrentWidget(self.terminal)
        self.terminal.clear_output()

        self.process_manager.run_script("./open-frontend.sh")

        self.statusBar().showMessage("Opening Frontend...")

    # =====================================================
    # Monitoring
    # =====================================================

    def kubernetes_data(self):

        self.tabs.setCurrentWidget(self.data)

        self.statusBar().showMessage("Showing Kubernetes Data")

    def controller_logs(self):

        self.tabs.setCurrentWidget(self.terminal)
        self.terminal.clear_output()

        self.process_manager.run_command(
            "kubectl",
            [
                "logs",
                "-f",
                "deployment/defense-automation-controller",
                "-n",
                "security-monitoring",
            ]
        )

        self.statusBar().showMessage("Controller Logs")

    def kserve_logs(self):

        self.tabs.setCurrentWidget(self.terminal)
        self.terminal.clear_output()

        self.process_manager.run_command(
            "kubectl",
            [
                "logs",
                "-f",
                "deployment/kserve-controller-manager",
                "-n",
                "kserve"
            ]
        )

        self.statusBar().showMessage("KServe Logs")

    # =====================================================
    # Utility
    # =====================================================

    def stop_command(self):

        self.process_manager.stop()

        self.statusBar().showMessage("Command Stopped")

    def exit(self):
        self.close()
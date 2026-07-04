from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLabel
)

from widgets.terminal_widget import TerminalWidget
from services.process_manager import ProcessManager

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "AI-Driven Kubernetes Cyber Deception Control Panel"
        )

        self.resize(1300, 750)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)

        # Left panel
        left_layout = QVBoxLayout()

        self.btn_start = QPushButton("Start Cluster")
        self.btn_manifest = QPushButton("Deploy Manifest")
        self.btn_pods = QPushButton("Watch Pods")
        self.btn_controller = QPushButton("Controller Logs")
        self.btn_kserve = QPushButton("KServe Logs")
        self.btn_stop = QPushButton("Stop Current Command")
        self.btn_clear = QPushButton("Clear Output")

        left_layout.addWidget(self.btn_start)
        left_layout.addWidget(self.btn_manifest)
        left_layout.addWidget(self.btn_pods)
        left_layout.addWidget(self.btn_controller)
        left_layout.addWidget(self.btn_kserve)

        left_layout.addStretch()

        left_layout.addWidget(self.btn_clear)

        # Right panel
        self.terminal = TerminalWidget()

        main_layout.addLayout(left_layout, 1)
        main_layout.addWidget(self.terminal, 4)

        self.statusBar().showMessage("Ready")
        self.process_manager = ProcessManager(self.terminal)
        self.btn_start.clicked.connect(self.start_cluster)
        self.btn_pods.clicked.connect(self.watch_pods)
        self.btn_stop.clicked.connect(self.stop_command)
    def start_cluster(self):
        self.terminal.clear_output()
        self.process_manager.run_script("./run-cluster.sh")
    def watch_pods(self):
        self.terminal.clear_output()

        self.process_manager.run_command(
            "kubectl",
            ["get", "pods", "-A", "-w"]
        )

        self.statusBar().showMessage("Watching Pods...")
    def stop_command(self):
        self.process_manager.stop()
        self.statusBar().showMessage("Stopped")
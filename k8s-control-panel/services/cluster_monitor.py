from PySide6.QtCore import QObject, QProcess, QTimer


class ClusterMonitor(QObject):

    def __init__(self, window):

        super().__init__()

        self.window = window

        self.timer = QTimer()

        self.timer.timeout.connect(self.refresh)

        self.timer.start(5000)

    def refresh(self):

        self.check_minikube()
        self.check_controller()
        self.check_kserve()
        self.check_frontend()

    def run(self, command, callback):

        process = QProcess()

        process.finished.connect(
            lambda:
            callback(
                bytes(process.readAllStandardOutput()).decode()
            )
        )

        process.start("bash", ["-c", command])

    def check_minikube(self):

        self.run(
            "minikube status",
            self.parse_minikube
        )

    def parse_minikube(self, output):

        if "Running" in output:
            self.window.minikube_card.set_running()
        else:
            self.window.minikube_card.set_stopped()

    def check_controller(self):

        cmd = (
            "kubectl get deployment "
            "defense-automation-controller "
            "-n security-monitoring"
        )

        self.run(cmd, self.parse_controller)

    def parse_controller(self, output):

        if "1/1" in output:
            self.window.controller_card.set_running()
        else:
            self.window.controller_card.set_stopped()

    def check_kserve(self):

        cmd = (
            "kubectl get deployment "
            "kserve-controller-manager "
            "-n kserve"
        )

        self.run(cmd, self.parse_kserve)

    def parse_kserve(self, output):

        if "1/1" in output or "2/2" in output:
            self.window.kserve_card.set_running()
        else:
            self.window.kserve_card.set_stopped()

    def check_frontend(self):

        cmd = (
            "kubectl get deployment "
            "frontend-service "
            "-n core-app"
        )

        self.run(cmd, self.parse_frontend)

    def parse_frontend(self, output):

        if "1/1" in output:
            self.window.frontend_card.set_running()
        else:
            self.window.frontend_card.set_stopped()
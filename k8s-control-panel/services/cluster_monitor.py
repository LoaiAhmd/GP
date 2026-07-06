from PySide6.QtCore import QObject, QProcess, QTimer


class ClusterMonitor(QObject):

    def __init__(self, window):
        super().__init__()

        self.window = window

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(5000)

        self.minikube_process = None
        self.controller_process = None
        self.kserve_process = None
        self.frontend_process = None

    # =====================================================
    # Timer
    # =====================================================

    def refresh(self):

        self.check_minikube()
        self.check_controller()
        self.check_kserve()
        self.check_frontend()

    # =====================================================
    # Generic Runner
    # =====================================================

    def run(self, process_attr, command, callback):

        process = getattr(self, process_attr)

        if process is not None:
            if process.state() != QProcess.NotRunning:
                return

            process.deleteLater()

        process = QProcess(self)

        setattr(self, process_attr, process)

        process.finished.connect(
            lambda: self.process_finished(process_attr, callback)
        )

        process.start("bash", ["-c", command])

    def process_finished(self, process_attr, callback):

        process = getattr(self, process_attr)

        if process is None:
            return

        output = bytes(
            process.readAllStandardOutput()
        ).decode(errors="ignore")

        callback(output)

        process.deleteLater()

        setattr(self, process_attr, None)

    # =====================================================
    # Minikube
    # =====================================================

    def check_minikube(self):

        self.run(
            "minikube_process",
            "minikube status",
            self.parse_minikube,
        )

    def parse_minikube(self, output):

        if "Running" in output:
            self.window.minikube_card.set_running()
        else:
            self.window.minikube_card.set_stopped()

    # =====================================================
    # Controller
    # =====================================================

    def check_controller(self):

        self.run(
            "controller_process",
            "kubectl get deployment defense-automation-controller -n security-monitoring",
            self.parse_controller,
        )

    def parse_controller(self, output):

        if "1/1" in output:
            self.window.controller_card.set_running()
        else:
            self.window.controller_card.set_stopped()

    # =====================================================
    # KServe
    # =====================================================

    def check_kserve(self):

        self.run(
            "kserve_process",
            "kubectl get deployment kserve-controller-manager -n kserve",
            self.parse_kserve,
        )

    def parse_kserve(self, output):

        if "1/1" in output or "2/2" in output:
            self.window.kserve_card.set_running()
        else:
            self.window.kserve_card.set_stopped()

    # =====================================================
    # Frontend
    # =====================================================

    def check_frontend(self):

        self.run(
            "frontend_process",
            "kubectl get deployment frontend-service -n core-app",
            self.parse_frontend,
        )

    def parse_frontend(self, output):

        if "1/1" in output:
            self.window.frontend_card.set_running()
        else:
            self.window.frontend_card.set_stopped()

    # =====================================================
    # Shutdown
    # =====================================================

    def stop(self):

        self.timer.stop()

        for name in (
            "minikube_process",
            "controller_process",
            "kserve_process",
            "frontend_process",
        ):

            process = getattr(self, name)

            if process is None:
                continue

            if process.state() != QProcess.NotRunning:

                process.terminate()

                if not process.waitForFinished(1000):
                    process.kill()
                    process.waitForFinished()

            process.deleteLater()

            setattr(self, name, None)
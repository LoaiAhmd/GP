from PySide6.QtCore import QObject, QProcess, QTimer


class ClusterMonitor(QObject):

    def __init__(self, window):
        super().__init__()

        self.window = window

        self.processes = []

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(15000)

        self.refresh()

    # =========================================================

    def refresh(self):

        self.check_minikube()
        self.check_deployments()

    # =========================================================

    def run(self, command, callback):

        process = QProcess(self)

        self.processes.append(process)

        process.finished.connect(
            lambda exitCode, exitStatus, p=process:
            self.finished(p, callback)
        )

        process.start("bash", ["-c", command])

    def finished(self, process, callback):

        output = bytes(
            process.readAllStandardOutput()
        ).decode()

        callback(output)

        if process in self.processes:
            self.processes.remove(process)

        process.deleteLater()

    # =========================================================

    def stop(self):

        self.timer.stop()

        for process in self.processes:

            if process.state() != QProcess.NotRunning:
                process.kill()
                process.waitForFinished()

        self.processes.clear()

    # =========================================================

    def check_minikube(self):

        self.run(
            "minikube status",
            self.parse_minikube,
        )

    def parse_minikube(self, output):

        if "Running" in output:
            self.window.minikube_card.set_running()
        else:
            self.window.minikube_card.set_stopped()

    # =========================================================

    def check_deployments(self):

        self.run(
            "kubectl get deployments -A --no-headers",
            self.parse_deployments,
        )

    def parse_deployments(self, output):

        controller = False
        kserve = False
        frontend = False

        for line in output.splitlines():

            cols = line.split()

            if len(cols) < 3:
                continue

            namespace = cols[0]
            name = cols[1]
            ready = cols[2]

            if (
                namespace == "security-monitoring"
                and name == "defense-automation-controller"
            ):
                controller = ready.startswith("1/1")

            elif (
                namespace == "kserve"
                and name == "kserve-controller-manager"
            ):
                kserve = ready.startswith("2/2") or ready.startswith("1/1")

            elif (
                namespace == "core-app"
                and name == "frontend-service"
            ):
                frontend = ready.startswith("1/1")

        if controller:
            self.window.controller_card.set_running()
        else:
            self.window.controller_card.set_stopped()

        if kserve:
            self.window.kserve_card.set_running()
        else:
            self.window.kserve_card.set_stopped()

        if frontend:
            self.window.frontend_card.set_running()
        else:
            self.window.frontend_card.set_stopped()
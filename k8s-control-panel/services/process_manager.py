from PySide6.QtCore import QObject, QProcess


class ProcessManager(QObject):

    def __init__(self, terminal):
        super().__init__()

        self.terminal = terminal

        self.process = QProcess(self)

        self.process.readyReadStandardOutput.connect(self.read_stdout)
        self.process.readyReadStandardError.connect(self.read_stderr)
        self.process.finished.connect(self.finished)

    # ---------------------------------------------------------
    # Run
    # ---------------------------------------------------------

    def run_script(self, script):
        self.run_command("bash", [script])

    def run_command(self, program, arguments):

        self.stop()

        self.process.start(program, arguments)

    # ---------------------------------------------------------
    # Output
    # ---------------------------------------------------------

    def read_stdout(self):

        text = bytes(
            self.process.readAllStandardOutput()
        ).decode(errors="ignore")

        if text:
            self.terminal.append(text.rstrip())

    def read_stderr(self):

        text = bytes(
            self.process.readAllStandardError()
        ).decode(errors="ignore")

        if text:
            self.terminal.append(text.rstrip())

    # ---------------------------------------------------------
    # Stop
    # ---------------------------------------------------------

    def stop(self):

        if self.process.state() == QProcess.NotRunning:
            return

        self.process.terminate()

        if not self.process.waitForFinished(2000):

            self.process.kill()
            self.process.waitForFinished()

    # ---------------------------------------------------------
    # Finished
    # ---------------------------------------------------------

    def finished(self):

        self.terminal.append("\n===== Process Finished =====")

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def is_running(self):

        return self.process.state() != QProcess.NotRunning
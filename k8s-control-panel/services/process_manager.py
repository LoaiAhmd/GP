from PySide6.QtCore import QObject, QProcess


class ProcessManager(QObject):

    def __init__(self, terminal):
        super().__init__()

        self.terminal = terminal
        self.process = QProcess()

        self.process.readyReadStandardOutput.connect(self.read_stdout)
        self.process.readyReadStandardError.connect(self.read_stderr)
        self.process.finished.connect(self.finished)

    def run_script(self, script):
        self.run_command("bash", [script])

    def read_stdout(self):
        text = bytes(self.process.readAllStandardOutput()).decode()
        self.terminal.append(text.rstrip())

    def read_stderr(self):
        text = bytes(self.process.readAllStandardError()).decode()
        self.terminal.append(text.rstrip())

    def finished(self):
        self.terminal.append("\n===== Process Finished =====")

    def run_command(self, program, arguments):
        if self.process.state() != QProcess.NotRunning:
            self.process.kill()
            self.process.waitForFinished()

        self.process.start(program, arguments)
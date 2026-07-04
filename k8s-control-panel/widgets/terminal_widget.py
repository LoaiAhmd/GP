from PySide6.QtWidgets import QPlainTextEdit


class TerminalWidget(QPlainTextEdit):

    def __init__(self):
        super().__init__()

        self.setReadOnly(True)

        self.setStyleSheet("""
            QPlainTextEdit {
                background: #1E1E1E;
                color: #00FF66;
                font-family: Consolas;
                font-size: 11pt;
            }
        """)

    def append(self, text):
        self.appendPlainText(text)

    def clear_output(self):
        self.clear()
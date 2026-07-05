from PySide6.QtWidgets import QPlainTextEdit


class TerminalWidget(QPlainTextEdit):

    def __init__(self):
        super().__init__()

        self.setReadOnly(True)

        self.setStyleSheet("""
            QPlainTextEdit {
                background: #000000;
                color: #49fa5e;
                font-family: Consolas;
                font-size: 12pt;
            }
        """)

    def append(self, text):
        self.appendPlainText(text)

    def clear_output(self):
        self.clear()
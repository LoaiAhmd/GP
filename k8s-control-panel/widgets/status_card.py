from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
)
from PySide6.QtCore import Qt


class StatusCard(QFrame):

    def __init__(self, title):
        super().__init__()

        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumHeight(90)

        main_layout = QVBoxLayout(self)

        self.title = QLabel(title)
        self.title.setAlignment(Qt.AlignCenter)

        status_layout = QHBoxLayout()
        status_layout.setAlignment(Qt.AlignCenter)

        self.circle = QLabel()
        self.circle.setFixedSize(14, 14)
        self.circle.setStyleSheet("""
            QLabel {
                background: gray;
                border-radius: 7px;
            }
        """)

        self.status = QLabel("Unknown")

        status_layout.addWidget(self.circle)
        status_layout.addWidget(self.status)

        main_layout.addWidget(self.title)
        main_layout.addLayout(status_layout)
        self.set_unknown()

    def set_running(self):
        self.setStyleSheet("""
            StatusCard {
                background-color: #092617;
                border: 2px solid #27ae60;
                border-radius: 5px;
            }
        """)
        self.circle.setStyleSheet("""
            QLabel {
                background: #27ae60;
                border-radius: 7px;
            }
        """)
        self.status.setText("Running")

    def set_stopped(self):
        self.setStyleSheet("""
            StatusCard {
                background-color: #280d0d;
                border: 2px solid #e74c3c;
                border-radius: 5px;
            }
        """)
        self.circle.setStyleSheet("""
            QLabel {
                background: #e74c3c;
                border-radius: 7px;
            }
        """)
        self.status.setText("Stopped")

    def set_unknown(self):
        self.setStyleSheet("""
            StatusCard {
                background-color: #0b0f18;
                border: 1px solid #1f2937;
                border-radius: 5px;
            }
        """)
        self.circle.setStyleSheet("""
            QLabel {
                background: gray;
                border-radius: 7px;
            }
        """)
        self.status.setText("Unknown")
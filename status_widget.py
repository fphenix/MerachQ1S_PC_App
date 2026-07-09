from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QHBoxLayout, QWidget


class StatusWidget(QWidget):

    COLORS = {
        "Connecté": "#3CB043",
        "Recherche...": "#F5B041",
        "Déconnecté": "#D64541",
        "Arrêt": "#808080",
    }

    def __init__(self, title="Bluetooth"):
        super().__init__()

        self.title = QLabel(title)

        self.led = QLabel("●")
        self.led.setAlignment(Qt.AlignCenter)

        self.text = QLabel("Recherche...")

        layout = QHBoxLayout(self)

        layout.addWidget(self.title)
        layout.addStretch()
        layout.addWidget(self.led)
        layout.addWidget(self.text)

        self.set_status("Recherche...")

    def set_status(self, status):

        color = self.COLORS.get(status, "#808080")

        self.led.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size:22px;
                font-weight:bold;
            }}
            """
        )

        self.text.setText(status)
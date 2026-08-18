from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QHBoxLayout, QWidget

from constants import USE_REPLAY

# =============================================================================
class StatusWidget(QWidget):

    COLORS = {
        "Connecté": "#3CB043",
        "Recherche...": "#F5B041",
        "Déconnecté": "#D64541",
        "Arrêt": "#808080",
        "Replay": "#AA00CC",
    }

    # -------------------------------------------------------------------------
    def __init__(self, title="Bluetooth"):
        super().__init__()

        self.bt_led = QLabel("●")
        self.bt_led.setAlignment(Qt.AlignCenter)
        self.title = QLabel(title)

        self.led = QLabel("●")
        self.led.setAlignment(Qt.AlignCenter)

        self.text = QLabel("---")

        layout = QHBoxLayout(self)

        layout.addWidget(self.bt_led)
        layout.addWidget(self.title)
        layout.addStretch()
        layout.addWidget(self.led)
        layout.addWidget(self.text)

        self.bt_status()
        self.set_status("Recherche...")

    # -------------------------------------------------------------------------
    def bt_status(self):

        if USE_REPLAY:
            color = self.COLORS["Déconnecté"]

        else:
            color = self.COLORS["Connecté"]

        self.bt_led.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size:22px;
                font-weight:bold;
            }}
                """
        )

    # -------------------------------------------------------------------------
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

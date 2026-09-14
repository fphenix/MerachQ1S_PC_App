from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QHBoxLayout,
    QWidget,
)

from setup.constants import USE_REPLAY

# =============================================================================
class StatusWidget(QWidget):

    COLORS = {
        "Connecté":     "#3CB043",
        "Recherche...": "#F5B041",
        "Déconnecté":   "#D64541",
        "Pause":        "#8B4E08",
        "Arrêt":        "#5A05B7",
        "Replay":       "#AA00CC",
    }

    # -------------------------------------------------------------------------
    def __init__(self, title="Bluetooth"):
        
        super().__init__()

        self.title = title

        self._create_ui()

    # ------------------------------------------------------------------
    def _create_ui(self):
        self.bt_led_label = QLabel("●")
        self.bt_led_label.setAlignment(Qt.AlignCenter)
        self.title_label = QLabel(self.title)

        self.led_label = QLabel("●")
        self.led_label.setAlignment(Qt.AlignCenter)

        self.text_label = QLabel("---")

        layout = QHBoxLayout(self)

        layout.addWidget(self.bt_led_label)
        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.led_label)
        layout.addWidget(self.text_label)

        self.bt_status()
        self.set_status("Recherche...")

    # -------------------------------------------------------------------------
    def bt_status(self):

        if USE_REPLAY:
            color = self.COLORS["Déconnecté"]

        else:
            color = self.COLORS["Connecté"]

        self.bt_led_label.setStyleSheet(
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

        self.led_label.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size:22px;
                font-weight:bold;
            }}
            """
        )

        self.text_label.setText(status)

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QHBoxLayout,
    QWidget,
)

from setup.lang import get_text
from setup.constants import USE_REPLAY

from setup.cnx_enum import CnxState

# =============================================================================
class StatusWidget(QWidget):

    # -------------------------------------------------------------------------
    def __init__(self, title="Bluetooth") -> None:
        
        super().__init__()

        self.title = title

        self.init_tables()

        self._create_ui()

    # ------------------------------------------------------------------
    def init_tables(self) -> None:

        self.STATUS_TEXT = [
            get_text("CNX_CONNECTED"),
            get_text("CNX_SEEKING"),
            get_text("CNX_DISCONNECTED"),
            get_text("CNX_PAUSE"),
            get_text("CNX_STOPPED"),
            get_text("CNX_REPLAY"),
        ]

        self.STATUS_COLORS = [
            "#3CB043", # CNX_CONNECTED
            "#F5B041", # CNX_SEEKING
            "#D64541", # CNX_DISCONNECTED
            "#8B4E08", # CNX_PAUSE
            "#5A05B7", # CNX_STOPPED
            "#AA00CC", # CNX_REPLAY
        ]

    # ------------------------------------------------------------------
    def _create_ui(self) -> None:

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
        self.set_status(CnxState.SEEKING)

    # -------------------------------------------------------------------------
    def _get_color(self, status) -> str:
        if 0 <= status.value < len(self.STATUS_COLORS):
            return self.STATUS_COLORS[status.value]
        return "#808080"

    # -------------------------------------------------------------------------
    def _get_text(self, status) -> str:
        if 0 <= status.value < len(self.STATUS_COLORS):
            return self.STATUS_TEXT[status.value]
        return "???"
    
    # -------------------------------------------------------------------------
    def bt_status(self) -> None:

        if USE_REPLAY:
            color = self._get_color(CnxState.DISCONNECTED)

        else:
            color = self._get_color(CnxState.CONNECTED)

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
    def set_status(self, status) -> None:

        color = self._get_color(status)
        text  = self._get_text(status)

        self.led_label.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size:22px;
                font-weight:bold;
            }}
            """
        )

        self.text_label.setText(text)

"""
widgets.py

Widgets réutilisables pour l'interface graphique.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
)

from setup.constants import (
    TITLE_FONT,
    MAIN_FONT,
)

from ui.progbar_widget import GradientGauge

# =============================================================================
# MetricWidget
# =============================================================================
class MetricWidget(QFrame):
    """
    Affiche une métrique sous la forme (exemple) :

        Cadence

          24.5

         spm

    En option on peut aussi ajouter une jauge.
    """

    # -------------------------------------------------------------------------
    def __init__(
            self,
            title: str,
            unit: str = "",
            gauge: GradientGauge | None = None,
        ):

        super().__init__()

        self.title = title
        self.unit = unit
        self.gauge = gauge

        self._create_ui()

        self._scroll_target_index = None

    # ------------------------------------------------------------------
    def _create_ui(self):

        self.setFrameShape(QFrame.Box)
        self.setLineWidth(2)

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.title_label = QLabel(self.title)
        self.title_label.setAlignment(Qt.AlignCenter)

        self.value_label = QLabel("--")
        self.value_label.setAlignment(Qt.AlignCenter)

        self.unit_label = QLabel(self.unit)
        self.unit_label.setAlignment(Qt.AlignCenter)

        title_font = QFont(TITLE_FONT, 11)
        title_font.setBold(True)

        value_font = QFont(MAIN_FONT, 28)
        value_font.setBold(True)

        unit_font = QFont(TITLE_FONT, 10)

        self.title_label.setFont(title_font)
        self.value_label.setFont(value_font)
        self.unit_label.setFont(unit_font)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.value_label)
        layout.addStretch()
        layout.addWidget(self.unit_label)

        if self.gauge is not None:
            layout.addWidget(self.gauge)

    # -------------------------------------------------------------------------
    def setValue(self, textvalue, gaugevalue: int|float|None = None):

        self.value_label.setText(str(textvalue))

        if gaugevalue is not None:
            self.gauge.set_value(gaugevalue)

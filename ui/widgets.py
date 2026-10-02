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
    QHBoxLayout,
)

from setup.constants import (
    TITLE_FONT,
    MAIN_FONT,
    WIDGET_TITLE_FONT_SIZE,
    WIDGET_VALUE_FONT_SIZE,
    WIDGET_UNIT_FONT_SIZE,
    WIDGET_SECONDARY_FONT_SIZE,
)

from ui.progbar_widget import GradientGauge

# =============================================================================
class MetricWidget(QFrame):
    """
    Affiche une métrique sous la forme (exemple) :

        Cadence

          24.5

          spm

    En option on peut aussi ajouter une jauge.
    En option une valeur secondaire peut être affichée.
    """

    # -------------------------------------------------------------------------
    def __init__(
            self,
            title: str,
            unit: str = "",
            gauge: GradientGauge | None = None,
            secondary_title: str | None = None,
            secondary_unit: str | None = None
        ) -> None:

        super().__init__()

        self.title: str = title
        self.secondary_title: str | None = secondary_title

        self.unit: str = unit
        self.secondary_unit: str | None = secondary_unit

        self.gauge: GradientGauge | None = gauge

        self.widget_shared: bool = (
            secondary_unit is not None
            and secondary_title is not None
        )

        self._create_ui()

        if self.widget_shared:
            self.setSecondaryVisible(visible= True)

        self._scroll_target_index = None

    # ------------------------------------------------------------------
    def _create_ui(self) -> None:

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

        title_font = QFont(TITLE_FONT, WIDGET_TITLE_FONT_SIZE)
        title_font.setBold(True)

        value_font = QFont(MAIN_FONT, WIDGET_VALUE_FONT_SIZE)
        value_font.setBold(True)

        unit_font = QFont(TITLE_FONT, WIDGET_UNIT_FONT_SIZE)

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

        #
        # If squeeze the main metric in the widget
        # we can insert a second metric
        #

        if self.widget_shared:

            self.secondary_label = QLabel(
                f"{self.secondary_title} :"
            )
            self.secondary_value_label = QLabel("--")
            self.secondary_unit_label = QLabel(
                self.secondary_unit
            )

            self.secondary_label.setAlignment(Qt.AlignLeft)
            self.secondary_value_label.setAlignment(Qt.AlignCenter)
            self.secondary_unit_label.setAlignment(Qt.AlignCenter)

            secondary_font = QFont(MAIN_FONT, WIDGET_SECONDARY_FONT_SIZE)
            secondary_font.setBold(True)

            secondary_unit_font = QFont(
                TITLE_FONT,
                WIDGET_UNIT_FONT_SIZE,
            )

            self.secondary_label.setFont(secondary_font)
            self.secondary_value_label.setFont(secondary_font)
            self.secondary_unit_label.setFont(secondary_unit_font)

            secondary_layout = QHBoxLayout()
            secondary_layout.setContentsMargins(0, 0, 0, 0)
            secondary_layout.setSpacing(4)

            secondary_layout.addWidget(self.secondary_label)
            secondary_layout.addWidget(self.secondary_value_label)
            secondary_layout.addWidget(self.secondary_unit_label)

            layout.addLayout(secondary_layout)            

    # -------------------------------------------------------------------------
    def setValue(
        self,
        textvalue: int|str,
        gaugevalue: int|float|None = None,
        secondary_textvalue: int|str | None = None,
    ) -> None:

        self.value_label.setText(str(textvalue))

        if gaugevalue is not None:
            self.gauge.set_value(gaugevalue)

        if secondary_textvalue is not None:
            self.secondary_value_label.setText(
                str(secondary_textvalue)
            )   

    # -------------------------------------------------------------------------
    def setSecondaryVisible(
        self,
        visible: bool,
    ) -> None:

        self.secondary_label.setVisible(visible)
        self.secondary_value_label.setVisible(visible)
        self.secondary_unit_label.setVisible(visible)

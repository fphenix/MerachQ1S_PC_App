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


class MetricWidget(QFrame):
    """
    Affiche une métrique sous la forme :

        Cadence

          24.5

         spm
    """

    def __init__(self, title: str, unit: str = ""):
        super().__init__()

        self.setFrameShape(QFrame.Box)
        self.setLineWidth(2)

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.title = QLabel(title)
        self.title.setAlignment(Qt.AlignCenter)

        self.value = QLabel("--")
        self.value.setAlignment(Qt.AlignCenter)

        self.unit = QLabel(unit)
        self.unit.setAlignment(Qt.AlignCenter)

        title_font = QFont("Segoe UI", 11)
        title_font.setBold(True)

        value_font = QFont("Consolas", 28)
        value_font.setBold(True)

        unit_font = QFont("Segoe UI", 10)

        self.title.setFont(title_font)
        self.value.setFont(value_font)
        self.unit.setFont(unit_font)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        layout.addWidget(self.title)
        layout.addStretch()
        layout.addWidget(self.value)
        layout.addStretch()
        layout.addWidget(self.unit)


    def setValue(self, value):
        self.value.setText(str(value))
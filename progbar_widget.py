from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QHBoxLayout,
    QProgressBar,
)
from utils import debug

# =============================================================================
class GradientGauge(QFrame):
    """
    Jauge horizontale graduée avec dégradé de couleur.

    La valeur affichée n'est pas modifiée : la jauge ne fait
    qu'une représentation visuelle de cette valeur.
    """

    ZONES_COLOR = [
        "#083daf",
        "#2f6fed",
        "#35b95c",
        "#fdf148",
        "#e53935",
    ]

    def __init__(
        self,
        zones: list[float],
        decimals: int = 1,
    ):
        super().__init__()

        if not zones:
            raise ValueError("zones ne peut pas être vide")

        self.zones = sorted(zones)
        
        self.minimum = self.zones[0]
        self.maximum = self.zones[-1]

        self.decimals = decimals

        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setTextVisible(False)

        self.min_label = QLabel()
        self.value_label = QLabel()
        self.max_label = QLabel()

        self.min_label.setAlignment(Qt.AlignLeft)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.max_label.setAlignment(Qt.AlignRight)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(2)

        layout.addWidget(self.progress)

        labels = QHBoxLayout()
        labels.setContentsMargins(0, 0, 0, 0)
        labels.addWidget(self.min_label)
        labels.addWidget(self.value_label, 1)
        labels.addWidget(self.max_label)

        layout.addLayout(labels)

        self.min_label.setText(
            self._format_value(self.minimum)
        )
        self.max_label.setText(
            self._format_value(self.maximum)
        )

        self.set_value(self.minimum)

    # -------------------------------------------------------------------------
    def set_value(self, value: float) -> None:

        value = max(
            self.minimum,
            min(self.maximum, float(value)),
        )

        ratio = (
            (value - self.minimum)
            / (self.maximum - self.minimum)
        )

        self.progress.setValue(
            int(ratio * 1000)
        )

        self.value_label.setText(
            self._format_value(value)
        )

        self._update_style(value)

    # -------------------------------------------------------------------------
    def _format_value(self, value: float) -> str:
        return f"{value:.{self.decimals}f}"

    # -------------------------------------------------------------------------
    def _update_style(self, value: float) -> None:

        color = self._color_for_value(value)

        self.progress.setStyleSheet(
            f"""
            QProgressBar {{
                border: 1px solid #505050;
                border-radius: 4px;
                background-color: #202020;
                height: 10px;
            }}

            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
            """
        )

    # -------------------------------------------------------------------------
    def _color_for_value(self, value: float) -> str:
        """
        Interpolation linéaire entre les couleurs définies dans zones.

        zones : [seuil0, seuil1, ...]
        ZONES_COLOR : [color0, color1, ...]

        """

        # si valeur sou le seuil retourne la 1er valeurs
        if value <= self.zones[0]:
            return self.ZONES_COLOR[0]

        # sinon calcule le gradient en fonction d'où la valeur se trouve
        # (dans quelle zone et quelles sont les 2 couleurs extrémum de cette zone)
        for (v1, c1, v2, c2) in zip(
            self.zones,
            self.ZONES_COLOR,
            self.zones[1:],
            self.ZONES_COLOR[1:]
        ):
            # cherche la zone
            if value <= v2:
                ratio = (
                    (value - v1)
                    / (v2 - v1)
                )
                # retourne la couleur
                return self._interpolate_color(
                    c1,
                    c2,
                    ratio,
                )

        #sinon retourne la dernière colour dans la list
        return self.ZONES_COLOR[-1]

    # -------------------------------------------------------------------------
    @staticmethod
    def _interpolate_color(
        color1: str,
        color2: str,
        ratio: float,
    ) -> str:

        from PySide6.QtGui import QColor

        c1 = QColor(color1)
        c2 = QColor(color2)

        r = int(
            c1.red()
            + (c2.red() - c1.red()) * ratio
        )
        g = int(
            c1.green()
            + (c2.green() - c1.green()) * ratio
        )
        b = int(
            c1.blue()
            + (c2.blue() - c1.blue()) * ratio
        )

        return f"#{r:02x}{g:02x}{b:02x}"
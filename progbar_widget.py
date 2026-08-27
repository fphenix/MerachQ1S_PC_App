from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QProgressBar,
)

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
        inverted: bool = False,
        decimals: int = 1,
    ):
        super().__init__()

        if not zones:
            raise ValueError("GradientGauge : zones ne peut pas être vide")

        if len(zones) != 5:
            raise ValueError(
                "GradientGauge : zones doit contenir exactement 5 points."
            )

        if len(set(zones)) != 5:
            raise ValueError(
                "GradientGauge : les 5 points de zones doivent être différents."
            )

        self.zones = sorted(zones)

        self.minimum = min(self.zones)
        self.maximum = max(self.zones)

        self.inverted = inverted

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

        # Commented out because we chose inverted to only switch colors.
        # If we vant the inverted=True to flip the bar values as well
        # then we need to swap the Texts for min & Max.
        #if not self.inverted:
        self.min_label.setText(self._format_value(self.minimum))
        self.max_label.setText(self._format_value(self.maximum))
        #else:
        #    self.min_label.setText(self._format_value(self.maximum))
        #   self.max_label.setText(self._format_value(self.minimum))
            

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

        # Commented out because we will only flip the colors when inverted is True.
        # If we want to flip the bar, then do:
        #if self.inverted:
        #    ratio = 1.0 - ratio

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

        # Commented out because we will only flip the colors when inverted is True.
        # If we want to flip the bar values, then do:
        #if self.inverted:
        #    value = self.maximum + self.minimum - value

        # si valeur sous le seuil retourne la 1er couleur
        if value <= self.minimum:
            return self.ZONES_COLOR[0] if not self.inverted else self.ZONES_COLOR[-1]

        # sinon, si on est dans une des zones, calcule le gradient en fonction d'où la
        # valeur se trouve sur la barre (ie. dans quelle zone et quelles sont les deux
        # couleurs bornes de cette zone)
        for idx, (v1, v2) in enumerate(zip(
            self.zones,
            self.zones[1:],
        )):

            # pour éviter div by 0, mais le "raise" dans __init__ doit éviter que cela n'arrive.
            if v1 == v2:
                raise ValueError ("GradientGauge : Deux valeurs identiques dans la définition de zones dans gui.py")

            idx_color1 = idx if not self.inverted else len(self.ZONES_COLOR) - 1 - idx
            idx_color2 = idx_color1 + 1 if not self.inverted else idx_color1 - 1

            # cherche la zone et renvoie la couleur
            if value <= v2:
                ratio = ( (value - v1) / (v2 - v1) )
                # retourne la couleur
                return self._interpolate_color(
                    self.ZONES_COLOR[idx_color1],
                    self.ZONES_COLOR[idx_color2],
                    ratio,
                )

        # sinon on est hors zone (et au dessus) alors retourne la dernière
        # couleur dans la liste.
        return self.ZONES_COLOR[-1] if not self.inverted else self.ZONES_COLOR[0]

    # -------------------------------------------------------------------------
    # Trouve la couleur intermédiaire entre color1 et color2
    # en fonction du ratio.
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

"""Petit cercle pulsant réutilisable par les vues de jeux."""

import math

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QBrush, QPen, QPainter

# =============================================================================
class Pulsator:
    """Dessine un cercle dont le rayon varie à la fréquence de cadence (CPM)."""

    # -------------------------------------------------------------------------
    def __init__(
        self,
        min_radius: float = 2.0,
        max_radius: float = 14.0,
        pen_width: float = 2.0,
        outlined: bool = False
    ) -> None:
 
        self.min_radius: float = float(min_radius)
        self.max_radius: float = float(max_radius)
        self.pen_width: float = float(pen_width)
        self.outlined: bool = outlined

    # -------------------------------------------------------------------------
    def radius_at(self, elapsed: float, cadence: float) -> float:

        if cadence <= 0.0:
            return self.min_radius

        phase = 2.0 * math.pi * elapsed * cadence / 60.0
        pulse = (1.0 - math.cos(phase)) / 2.0
        
        return self.min_radius + (self.max_radius - self.min_radius) * pulse

    # -------------------------------------------------------------------------
    def paint(
        self,
        painter: QPainter,
        center_x: float, center_y: float,
        elapsed: float,
        cadence: float,
        color: QColor
    ) -> None:

        radius = self.radius_at(elapsed, cadence)

        painter.save()

        if self.outlined:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(color), 1))
            painter.drawEllipse(QRectF(
                center_x - self.max_radius, center_y - self.max_radius,
                self.max_radius * 2.0, self.max_radius * 2.0)
            )

        painter.setPen(QPen(QColor(color), self.pen_width))
        painter.setBrush(QBrush(QColor(color)))
        painter.drawEllipse(QRectF(
            center_x - radius, center_y - radius, radius * 2.0, radius * 2.0)
        )
        
        painter.restore()

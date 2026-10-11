"""Rendu Qt partagé par les variantes Fishing."""

import math

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontMetrics, QPainter, QPen

# =============================================================================
class FishingWidget:
    """Objet de rendu, utilisé par GameWidget sans hériter de QWidget."""

    # -------------------------------------------------------------------------
    def paint(self, painter: QPainter, game) -> None:
        """Dessine le terrain dans un repère dont l'origine est le haut du jeu."""

        painter.save()
        painter.translate(0, game.HUD_HEIGHT)

        # Couloirs
        lane_height = game.LANE_HEIGHT
        painter.setPen(QPen(Qt.GlobalColor.darkGray))
        for lane in range(1, game.LANE_COUNT):
            y = round(lane * lane_height)
            painter.drawLine(0, y, game.WIDTH, y)

        # Repères de cadence et pulse
        lane_font = QFont("Courier New", 14)
        painter.setFont(lane_font)
        pulse_time = game.elapsed if game.phase == game.PHASE_PLAYING else game.phase_elapsed

        for row, spm in enumerate(reversed(game.SPM_LEVELS)):
            center_y = round((row + 0.5) * lane_height)
            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.drawText(5, center_y - 3, f"{spm} CPM")
            pulse = (1.0 + math.cos(
                2.0 * math.pi * pulse_time * spm / 60.0
            )) / 2.0
            radius = round(2 + 8 * pulse)
            dot_x = 36
            dot_y = center_y + 18
            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.setBrush(Qt.GlobalColor.white)
            painter.drawEllipse(dot_x - radius, dot_y - radius, radius * 2, radius * 2)

        # The model's rest offset lowers the net within the 16 CPM lane.
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(
            game.NET_LEFT_MARGIN,
            round(game.net_y),
            game.NET_WIDTH,
            game.NET_HEIGHT
        )

        # Insectes
        symbols = {
            "bee": ("B", Qt.GlobalColor.yellow),
            "butterfly": ("P", Qt.GlobalColor.magenta),
            "hornet": ("F", Qt.GlobalColor.red),
        }

        for insect in game.insects:
            size = game.INSECTS_DATA[insect.kind]["pxsize"]
            symbol, color = symbols[insect.kind]

            painter.save()
            painter.setPen(QPen(color))
            painter.setBrush(color)
            painter.drawEllipse(
                round(insect.x), round(insect.y),
                size, size
            )

            painter.setPen(QPen(Qt.GlobalColor.black))
            insect_font = QFont("Courier New")
            insect_font.setPixelSize(max(10, size // 2))
            painter.setFont(insect_font)

            fm = QFontMetrics(insect_font)
            text_x = round(
                insect.x + (size - fm.horizontalAdvance(symbol)) / 2
            )
            text_y = round(
                insect.y + (size - fm.height()) / 2 + fm.ascent()
            )
            painter.drawText(text_x, text_y, symbol)
            painter.restore()

        painter.restore()

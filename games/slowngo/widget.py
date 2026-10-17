"""Rendu de Slow N'Go : trois zones colorées et un pulsateur."""

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QBrush, QPen, QPainter, QFont

from setup.lang import get_text
from setup.constants import GAME_FONT

from games.pulsator import Pulsator
from games.game import Game

# =============================================================================
class SlowNGoWidget:

    PULSATOR = Pulsator(min_radius= 12.0, max_radius= 22.0, pen_width= 3.0)

    COLORS = {
        "slow": QColor("#174a78"),
        "medium": QColor("#176b68"),
        "fast": QColor("#794124"),
    }

    # -------------------------------------------------------------------------
    def paint(self, painter: QPainter, game: Game) -> None:

        painter.save()

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        area_y = game.HUD_HEIGHT + 70
        area_h = 360
        margin = 35
        gap = 18
        col_w = (game.WIDTH - margin * 2 - gap * 2) / 3

        labels = {
            "slow": get_text("GAME_SLOWNGO_SLOW"),
            "medium": get_text("GAME_SLOWNGO_MEDIUM"),
            "fast": get_text("GAME_SLOWNGO_FAST"),
        }

        # draw the 3 boxes
        for index, band in enumerate(("slow", "medium", "fast")):
            x = margin + index * (col_w + gap)
            active = band == game.target_band
            color = self.COLORS[band]

            painter.setPen(QPen(QColor("#ffffff") if active else color.darker(105), 4 if active else 1))
            painter.setBrush(QBrush(color if active else color.darker(190)))
            painter.drawRoundedRect(QRectF(x, area_y, col_w, area_h), 16, 16)

            painter.setPen(QPen(QColor("#ffffff" if active else "#697781")))
            painter.setFont(QFont(GAME_FONT, 20, QFont.Weight.Bold))
            painter.drawText(
                QRectF(x + 8, area_y + 22, col_w - 16, 42),
                Qt.AlignmentFlag.AlignCenter,
                labels[band]
            )
            painter.setFont(QFont(GAME_FONT, 23, QFont.Weight.Bold))
            targets = str(game.CADENCE_TARGETS[band])
            painter.drawText(
                QRectF(x + 8, area_y + 90, col_w - 16, 36),
                Qt.AlignmentFlag.AlignCenter,
                targets
            )
            painter.setFont(QFont(GAME_FONT, 13, QFont.Weight.Bold))
            painter.drawText(
                QRectF(x + 8, area_y + 124, col_w - 16, 24),
                Qt.AlignmentFlag.AlignCenter,
                get_text("SPM_UNIT")
            )

            if active:
                center_x = x + col_w / 2
                center_y = area_y + 210
                self.PULSATOR.paint(
                    painter, center_x, center_y, game.elapsed,
                    game.target_spm, QColor("#ffffff")
                )
                painter.setFont(QFont(GAME_FONT, 25, QFont.Weight.Bold))
                painter.drawText(
                    QRectF(x + 8, area_y + 260, col_w - 16, 48),
                    Qt.AlignmentFlag.AlignCenter,
                    f"{game.target_spm} {get_text('SPM_UNIT')}"
                )

        # Target Cadence text
        painter.setPen(QPen(QColor("#ffffff")))
        painter.setFont(QFont(GAME_FONT, 25, QFont.Weight.Bold))
        painter.drawText(
            QRectF(50, area_y + area_h + 24, game.WIDTH - 100, 50),
            Qt.AlignmentFlag.AlignCenter,
            get_text("GAME_SLOWNGO_TARGET").format(spm=game.target_spm)
        )

        # Consignes
        painter.setFont(QFont(GAME_FONT, 16))
        if game.current_spm is None:
            status = get_text("GAME_SLOWNGO_WAITING_CADENCE")
        elif game.match_quality >= 1.0:
            status = get_text("GAME_SLOWNGO_ON_TARGET")
        elif game.match_quality > 0.0:
            status = get_text("GAME_SLOWNGO_CLOSE")
        else:
            status = get_text("GAME_SLOWNGO_ADJUST")
        
        painter.drawText(
            QRectF(50, area_y + area_h + 76, game.WIDTH - 100, 34),
            Qt.AlignmentFlag.AlignCenter,
            status
        )

        painter.restore()

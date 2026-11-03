"""Interface TV du jeu RowMaths."""

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QBrush, QFont, QPen, QPainter

from setup.constants import GAME_FONT
from setup.utils import clamp_between, clamp_to_min
from setup.lang import get_text

from games.game import Game
from games.game_painter import GamePainter
from games.pulsator import Pulsator

# =============================================================================
class RowMathsWidget(GamePainter):

    PULSATOR: Pulsator = Pulsator(
        min_radius= 3.0, max_radius= 25.0, pen_width= 2.0, outlined= True
    )

    COLORS: tuple[QColor, ...] = (
        QColor("#39b9a5"), QColor("#e5b84b"),
        QColor("#5b9de5"), QColor("#d779a8"),
    )

    # -------------------------------------------------------------------------
    def paint(self, painter: QPainter, game: Game) -> None:

        painter.save()

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        painter.fillRect(
            QRectF(0, game.HUD_HEIGHT, game.WIDTH, game.HEIGHT - game.HUD_HEIGHT),
            QColor("#101d30"),
        )
        self._draw_header(painter, game)
        self._draw_question(painter, game)
        self._draw_answers(painter, game)

        painter.restore()

    # -------------------------------------------------------------------------
    def _draw_header(self, painter: QPainter, game: Game) -> None:

        painter.setPen(QPen(QColor("#9fb4ca")))
        painter.setFont(QFont(GAME_FONT, 15, QFont.Weight.Bold))
        painter.drawText(
            35, 105,
            f"{get_text("GAME_ROWMATHS_QUESTION").upper()}  {game.question_number:02d}"
        )

        mode = (
            f"⚡ {get_text("GAME_ROWMATHS_QFLASH").upper()}  ⚡"
            if game.flash_round
            else ""
        )
        painter.drawText(730, 105, mode)

        remaining = (
            (game.FLASH_SECONDS if game.flash_round else game.ROUND_SECONDS)
            - game.round_elapsed
        )
        if game.showing_result:
            remaining = game.RESULT_SECONDS - game.result_elapsed

        painter.setPen(QPen(QColor("#f2d37b")))
        painter.setFont(QFont(GAME_FONT, 24, QFont.Weight.Bold))
        painter.drawText(
            420, 107,
            f"{clamp_to_min(remaining, 0):04.1f} s"
        )

        # Barre de progression du compte à rebours.
        duration = game.FLASH_SECONDS if game.flash_round else game.ROUND_SECONDS
        progress = clamp_between(remaining / duration, 0.0, 1.0)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#34465c")))
        painter.drawRoundedRect(QRectF(35, 120, 930, 8), 4, 4)
        painter.setBrush(QBrush(QColor("#e5b84b" if game.flash_round else "#39b9a5")))
        painter.drawRoundedRect(QRectF(35, 120, 930 * progress, 8), 4, 4)

    # -------------------------------------------------------------------------
    def _draw_question(self, painter: QPainter, game: Game) -> None:

        panel = QRectF(65, 155, 870, 190)
        painter.setPen(QPen(QColor("#344b65"), 2))
        painter.setBrush(QBrush(QColor("#1a2d45")))
        painter.drawRoundedRect(panel, 22, 22)

        painter.setPen(QPen(QColor("#ffffff")))
        painter.setFont(QFont(GAME_FONT, 66, QFont.Weight.Bold))
        painter.drawText(
            panel,
            Qt.AlignmentFlag.AlignCenter,
            game.question
        )

        if game.flash_round:
            painter.setPen(QPen(QColor("#f5d36e")))
            painter.setFont(QFont(GAME_FONT, 15, QFont.Weight.Bold))
            painter.drawText(
                QRectF(70, 315, 860, 24),
                Qt.AlignmentFlag.AlignCenter,
                f"{get_text("GAME_ROWMATHS_FLASH").upper()}  •  {game.POINTS_FLASH} {get_text("GAME_POINTS").upper()}"
            )

    # -------------------------------------------------------------------------
    def _draw_answers(self, painter: QPainter, game: Game) -> None:

        left, gap, width = 35.0, 16.0, 220.75
        top, height = 390.0, 205.0

        for index, answer in enumerate(game.answers):
            x = left + index * (width + gap)
            rect = QRectF(x, top, width, height)
            color = self.COLORS[index]

            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(QColor("#1b2a3d")))
            painter.drawRoundedRect(rect, 18, 18)

            painter.setPen(QPen(QColor("#aabbd0")))
            painter.setFont(QFont(GAME_FONT, 14, QFont.Weight.Bold))
            painter.drawText(
                QRectF(x, top + 15, width, 28),
                Qt.AlignmentFlag.AlignCenter,
                f"RÉPONSE {index + 1}"
            )

            painter.setPen(QPen(QColor("#ffffff")))
            painter.setFont(QFont(GAME_FONT, 39, QFont.Weight.Bold))
            painter.drawText(
                QRectF(x + 5, top + 48, width - 10, 72),
                Qt.AlignmentFlag.AlignCenter,
                str(answer)
            )

            target = game.ANSWER_CADENCES[index]
            self.PULSATOR.paint(
                painter,
                x + width / 2, top + 151,
                game.elapsed, target, color,
            )

            painter.setPen(QPen(color))
            painter.setFont(QFont(GAME_FONT, 15, QFont.Weight.Bold))
            painter.drawText(
                QRectF(x, top + 174, width, 24),
                Qt.AlignmentFlag.AlignCenter,
                f"{target} {get_text("SPM_UNIT")}"
            )

        if game.showing_result:
            overlay = QRectF(0, 145, game.WIDTH, 500)
            painter.fillRect(overlay, QColor(8, 16, 28, 205))

            painter.setPen(QPen(QColor("#73e0ad" if game.result_correct else "#f1b65b")))
            painter.setFont(QFont(GAME_FONT, 34, QFont.Weight.Bold))
            painter.drawText(
                QRectF(40, 300, 920, 65),
                Qt.AlignmentFlag.AlignCenter,
                game.result_message
            )

            painter.setPen(QPen(QColor("#ffffff")))
            painter.setFont(QFont(GAME_FONT, 22, QFont.Weight.Bold))
            painter.drawText(
                QRectF(40, 370, 920, 45),
                Qt.AlignmentFlag.AlignCenter,
                f"{get_text("GAME_ROWMATHS_ANSWER")} : {game.correct_answer} "
                f"( {game.ANSWER_CADENCES[game.correct_index]} {get_text("SPM_UNIT")} )"
            )

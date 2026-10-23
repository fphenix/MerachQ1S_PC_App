"""Rendu de Simon : disque circulaire divisé en trois secteurs de cadence."""

import math

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QBrush, QPen, QPainter, QFont

from setup.constants import GAME_FONT
from setup.lang import get_text

from games.game import Game
from games.game_painter import GamePainter
from games.pulsator import Pulsator

# =============================================================================
class SimonWidget(GamePainter):

    PULSATOR = Pulsator(min_radius= 3.0, max_radius= 18.0, pen_width= 2.0, outlined= True)

    SECTIONS_COLORS: list[QColor] = [
        QColor("#35a853"),  # 18 CPM : lent
        QColor("#f4d03f"),  # 24 CPM : moyen
        QColor("#e74c3c"),  # 30 CPM : rapide
    ]
    # Les centres des secteurs sont respectivement en haut, en bas à gauche,
    # et en bas à droite. Les angles Qt sont exprimés en seizièmes de degré.
    SECTOR_START_ANGLES: tuple[int]  = (30, 150, 270)
    SECTOR_CENTER_ANGLES: tuple[int] = (90, 210, 330)

    # -------------------------------------------------------------------------
    def paint(self, painter: QPainter, game: Game) -> None:
        
        painter.save()
        
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Le fond distingue clairement la démonstration de Simon du tour joueur.
        background = QColor("#243557" if game.showing_sequence else "#204736")
        painter.fillRect(
            QRectF(0, game.HUD_HEIGHT, game.WIDTH, game.HEIGHT - game.HUD_HEIGHT),
            background,
        )

        diameter = 390
        disk = QRectF(
            (game.WIDTH - diameter) / 2, 118,
            diameter, diameter,
        )
        center_x = disk.center().x()
        center_y = disk.center().y()
        radius = diameter / 2

        # Fond et contour du disque.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#171717")))
        painter.drawEllipse(disk.adjusted(-7, -7, 7, 7))

        # Sections de disque et pulsateur toujours visible pour chaque cadence.
        for lane, color in enumerate(self.SECTIONS_COLORS):
            active = lane == game.active_lane
            fill = color.lighter(185) if active else color.darker(185)
            painter.setBrush(QBrush(fill))
            painter.setPen(QPen(QColor("#171717"), 5))
            painter.drawPie(
                disk,
                self.SECTOR_START_ANGLES[lane] * 16,
                120 * 16,
            )

            # Indication de cadence au milieu de chaque secteur.
            angle = math.radians(self.SECTOR_CENTER_ANGLES[lane])
            label_radius = radius * 0.80
            label_x = center_x + math.cos(angle) * label_radius
            label_y = center_y - math.sin(angle) * label_radius
            label_rect = QRectF(label_x - 48, label_y - 27, 96, 54)

            text_color = (
                QColor("#202020")
                if lane == 1
                else QColor("#ffffff")
            )
            if active:
                text_color = QColor("#171717")
            painter.setPen(QPen(text_color))
            painter.setFont(QFont(GAME_FONT, 23, QFont.Weight.Bold))
            painter.drawText(
                label_rect,
                Qt.AlignmentFlag.AlignCenter,
                f"{str(int(game.CADENCE_TARGETS[lane]))}\n{get_text('SPM_UNIT')}",
            )

            # Pulsateur placé juste sous le texte CPM, battant à la cadence cible.
            self.PULSATOR.paint(
                painter,
                label_x,
                label_y + 48,
                game.elapsed,
                game.CADENCE_TARGETS[lane],
                color.lighter(145),
            )

        # Petit moyeu central avec titre du jeu, comme sur le Simon classique.
        hub_diameter = 150
        hub = QRectF(
            center_x - hub_diameter / 2,
            center_y - hub_diameter / 2,
            hub_diameter,
            hub_diameter,
        )
        painter.setPen(QPen(QColor("#080808"), 3))
        painter.setBrush(QBrush(QColor("#292929")))
        painter.drawEllipse(hub)

        painter.setPen(QPen(QColor("#eeeeee")))
        painter.setFont(QFont(GAME_FONT, 13, QFont.Weight.Bold))
        painter.drawText(
            hub,
            Qt.AlignmentFlag.AlignCenter,
            get_text("MENU_GAMES_SIMON").upper()
        )

        # message
        painter.setFont(QFont(GAME_FONT, 22, QFont.Weight.Bold))
        painter.drawText(
            QRectF(40, 520, game.WIDTH - 80, 38),
            Qt.AlignmentFlag.AlignCenter,
            get_text(game.message_key),
        )

        # Texte : "Manche <number>"
        painter.setFont(QFont(GAME_FONT, 16))
        painter.drawText(
            QRectF(40, 565, game.WIDTH - 80, 30),
            Qt.AlignmentFlag.AlignCenter,
            get_text("GAME_SIMON_ROUND").format(round=game.round_number),
        )

        # Rappel de cadences par bouton
        painter.drawText(
            QRectF(40, 603, game.WIDTH - 80, 32),
            Qt.AlignmentFlag.AlignCenter,
            get_text("GAME_SIMON_CADENCE_HINT"),
        )

        # Rappel animé des trois cibles, sous les consignes textuelles.
        for lane, color in enumerate(self.SECTIONS_COLORS):
            self.PULSATOR.paint(
                painter,
                center_x + (lane - 1) * 195,
                665,
                game.elapsed,
                game.CADENCE_TARGETS[lane],
                color.lighter(145),
            )

        painter.restore()

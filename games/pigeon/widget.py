"""Rendu du jeu de tir au pigeon."""

import math

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont

from setup.lang import get_text
from setup.constants import GAME_FONT

from games.game import Game
from games.pigeon.engine import Pigeon
from games.pulsator import Pulsator

# =============================================================================
class PigeonWidget:

    PULSATOR = Pulsator(min_radius=2.0, max_radius=14.0, pen_width=2.0)

    # -------------------------------------------------------------------------
    def paint(self, painter: QPainter, game: Game) -> None:

        painter.save()

        # Cages rectangulaires : porte fermée dans le cadre, ouverte vers l'extérieur.
        for x, opens_right in ((18, True), (game.WIDTH - 78, False)):
            self._draw_cage(painter, game, x, opens_right)

        # Fusil stylisé, fixe en bas au centre.
        self._draw_cannon(painter, game)

        # Pigeons : silhouette simple, mouvement sinusoïdal dans le tiers haut.
        for bird in game.pigeons:
            self._draw_bird(painter, game, bird)

        # Balles, retirées du modèle dès la collision ou la sortie de l'écran.
        painter.setPen(QPen(QColor("#ffd54a"), 3))
        for bullet in game.bullets:
            painter.drawLine(round(bullet.x), round(bullet.y), round(bullet.x), round(bullet.y + 10))

        # 2 pulsateurs: ouverture de la cage ou canon pour le tir.
        painter.setFont(QFont(GAME_FONT, 15, QFont.Weight.Bold))
        for pn in range(2):
            # Pulse Open
            if pn == 0:
                target_spm = game.CADENCE_OPEN
                color = QColor("#a8e6a1" if game.cages_open else "#ffffff")
                pulse_x = 100
                message = get_text("GAME_PIGEON_OPENING_PROMPT")

            # Pulse Shoot
            else:
                target_spm = game.CADENCE_SHOOT
                color = QColor("#ffd54a")
                pulse_x = round(game.WIDTH / 2 + 200)
                message = get_text("GAME_PIGEON_SHOOTING_PROMPT")

            pulse_y = game.HUD_HEIGHT + 350
            text_width = 220
            alignment = Qt.AlignmentFlag.AlignLeft

            self.PULSATOR.paint(
                painter, pulse_x, pulse_y, game.elapsed, target_spm, color
            )
            painter.setPen(QPen(color))
            painter.drawText(
                pulse_x + 25, pulse_y -12,
                text_width, 25,
                alignment,
                message
            )

        painter.restore()

    # -------------------------------------------------------------------------
    def _draw_bird(self, canvas: QPainter, game: Game, bird: Pigeon) -> None:

        canvas.save()

        canvas.translate(bird.x + game.PIGEON_SIZE / 2, bird.y + game.PIGEON_SIZE / 2)
        canvas.scale(float(bird.direction), 1.0)
        canvas.setPen(QPen(QColor("#eeeeee"), 2))
        canvas.setBrush(QBrush(QColor("#cfcfcf")))
        canvas.drawEllipse(-8, -4, 17, 11)
        canvas.drawEllipse(-1, -10, 11, 10)
        canvas.setPen(QPen(QColor("#d9b15f"), 2))
        canvas.drawLine(9, -5, 14, -3)
        canvas.setPen(QPen(QColor("#eeeeee"), 3))
        wing_y = round(math.sin(bird.phase * 2) * 4)
        canvas.drawLine(-3, 0, -11, wing_y - 7)
            
        canvas.restore()

    # -------------------------------------------------------------------------
    def _draw_cage(self, canvas: QPainter, game: Game, cage_x: int, opens_right: bool) -> None:

        # Cage
        cage_color = QColor("#8df782") if game.cages_open else QColor("#b0b0b0")
        canvas.setPen(QPen(cage_color, 2))
        canvas.setBrush(Qt.BrushStyle.NoBrush)
        cage_y = game.HUD_HEIGHT + 8
        canvas.drawRect(cage_x, cage_y, 60, 55)
        
        # Bars
        for bar_x in range(cage_x + 10, cage_x + 60, 12):
            canvas.drawLine(bar_x, cage_y, bar_x, cage_y + 55)

        # Porte: elle s'ouvre vers la droite pour la cage gauche,
        # vers la gauche pour la cage droite.
        if game.cages_open:
            bottom_x = cage_x + 60 if opens_right else cage_x
            bottom_y = cage_y + 55
            outer_x = bottom_x + (50 if opens_right else -50)
            canvas.drawLine(bottom_x, bottom_y, outer_x,bottom_y)
            canvas.drawLine(outer_x, bottom_y, outer_x, bottom_y - 10)

    # -------------------------------------------------------------------------
    def _draw_cannon(self, canvas: QPainter, game: Game) -> None:

        gun_x = game.WIDTH / 2
        gun_y = game.HEIGHT - 82
        canvas.setPen(QPen(QColor("#d8d8d8"), 5))
        canvas.drawLine(round(gun_x), round(gun_y), round(gun_x), round(gun_y - 38))
        canvas.setPen(QPen(QColor("#a0a0a0"), 2))
        canvas.setBrush(QBrush(QColor("#555555")))
        canvas.drawRect(round(gun_x - 23), round(gun_y - 8), 46, 22)

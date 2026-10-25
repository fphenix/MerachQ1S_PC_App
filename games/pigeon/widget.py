"""Rendu du jeu de tir au pigeon."""

import math

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont

from setup.lang import get_text
from setup.constants import GAME_FONT

from games.game import Game
from games.game_painter import GamePainter
from games.pigeon.engine import Pigeon
from games.pulsator import Pulsator

# =============================================================================
class PigeonWidget(GamePainter):

    PULSATOR: Pulsator = Pulsator(min_radius= 2.0, max_radius= 20.0, pen_width= 2.0, outlined= True)

    # -------------------------------------------------------------------------
    def paint(self, painter: QPainter, game: Game) -> None:

        painter.save()

        # Ciel et Sol
        painter.fillRect(
            0, game.HUD_HEIGHT + 60,
            game.WIDTH, game.HEIGHT - game.HUD_HEIGHT - 60,
            QColor("#91c252")
        )
        painter.fillRect(
            0, game.HUD_HEIGHT,
            game.WIDTH, 60,
            QColor("#6fb8f3")
        )

        # Décor de campagne : nuages, collines
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.setBrush(QBrush(QColor("#eaf5fb")))
        for cx, cy in ((95, game.HUD_HEIGHT + 12), (370, game.HUD_HEIGHT + 22), (740, game.HUD_HEIGHT + 8)):
            painter.drawEllipse(cx, cy, 43, 17)
            painter.drawEllipse(cx + 12, cy - 8, 24, 23)
            painter.drawEllipse(cx + 26, cy - 3, 26, 19)
        painter.setBrush(QBrush(QColor("#a5d17c")))
        painter.drawEllipse(-100, game.HUD_HEIGHT + 48, 500, 130)
        painter.drawEllipse(250, game.HUD_HEIGHT + 52, 500, 120)
        painter.drawEllipse(600, game.HUD_HEIGHT + 44, 520, 135)

        # Clôture basse en bois
        painter.setPen(QPen(QColor("#8c6337"), 4))
        fence_y = game.HEIGHT - 105
        painter.drawLine(0, fence_y, game.WIDTH, fence_y)
        painter.drawLine(0, fence_y + 18, game.WIDTH, fence_y + 18)
        painter.setPen(QPen(QColor("#a77a49"), 3))
        for fx in range(45, game.WIDTH, 82):
            painter.drawLine(fx, fence_y - 8, fx, fence_y + 25)

        # Cages rectangulaires
        for x, opens_right in ((18, True), (game.WIDTH - 78, False)):
            self._draw_cage(painter, game, x, opens_right)

        # Haies et feuillage
        painter.setPen(QPen(QColor("#81b14a"), 3))
        painter.setBrush(QBrush(QColor("#477f42")))
        painter.drawRoundedRect(0, game.HUD_HEIGHT + 155, game.WIDTH, 42, 12, 12)
        painter.setBrush(QBrush(QColor("#5b914b")))
        for hx in range(12, game.WIDTH, 38):
            painter.drawEllipse(hx, game.HUD_HEIGHT + 145 + (hx % 3) * 3, 35, 28)

        # Fusil fixe
        self._draw_cannon(painter, game)

        # Pigeons animés
        for bird in game.pigeons:
            self._draw_bird(painter, game, bird)

        # Balles
        painter.setPen(QPen(QColor("#ffd54a"), 3))
        for bullet in game.bullets:
            painter.drawLine(round(bullet.x), round(bullet.y), round(bullet.x), round(bullet.y + 10))

        # Pulsateurs: Ouverture de la cage et Tir canon
        painter.setFont(QFont(GAME_FONT, 15, QFont.Weight.Bold))
        for pn in range(2):
            # Pulse Open
            if pn == 0:
                target_spm = game.CADENCE_OPEN
                color = QColor("#105f07" if game.cages_open else "#ffffff")
                pulse_x = 200
                message = get_text("GAME_PIGEON_OPENING_PROMPT")

            # Pulse Shoot
            else:
                target_spm = game.CADENCE_SHOOT
                color = QColor("#ff5f4a" if len(game.bullets) > 0 else "#ffffff")
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
                pulse_x -90, pulse_y -42,
                text_width, 25,
                alignment,
                message
            )

        painter.restore()

    # -------------------------------------------------------------------------
    def _draw_bird(self, canvas: QPainter, game: Game, bird: Pigeon) -> None:

        canvas.save()

        canvas.translate(bird.x + game.PIGEON_SIZE / 2, bird.y + game.PIGEON_SIZE / 2)
        canvas.scale(float(bird.direction) * 2.0, 2.0)
        canvas.setPen(QPen(QColor("#555555"), 1)) # outline body & head
        canvas.setBrush(QBrush(QColor("#cfcfcf"))) # body
        canvas.drawEllipse(-8, -4, 17, 11) # body
        canvas.drawEllipse(-1, -10, 11, 10) # head
        canvas.drawEllipse(5, -7, 2, 2) # eye
        canvas.setPen(QPen(QColor("#e4a21d"), 2)) # beak
        canvas.drawLine(9, -5, 14, -3) # beak (top)
        canvas.drawLine(8, -4, 14, -3) # beak (bottom)
        canvas.setPen(QPen(QColor("#666666"), 1)) # tail
        canvas.drawLine(-8, 1, -11, -1) # tail
        canvas.drawLine(-6, 3, -13, 6) # tail
        canvas.drawLine(-11, -1, -13, 6) # tail
        canvas.drawLine(-8, 2, -12, 2) # tail
        canvas.setPen(QPen(QColor("#aaaaaa"), 4)) # wing
        wing_y = round(math.sin(bird.phase * 2) * 4)
        canvas.drawLine(-1, 0, -11, wing_y - 7)
            
        canvas.restore()

    # -------------------------------------------------------------------------
    def _draw_cage(self, canvas: QPainter, game: Game, cage_x: int, opens_right: bool) -> None:

        canvas.save()

        # Cage
        cage_color = QColor("#ee8d3e") if game.cages_open else QColor("#854f11")
        canvas.setPen(QPen(cage_color, 4))
        canvas.setBrush(Qt.BrushStyle.NoBrush)
        cage_y = game.HUD_HEIGHT + 15
        canvas.drawRect(cage_x, cage_y, 60, 55)
        
        # Bars
        for bar_x in range(cage_x + 10, cage_x + 60, 12):
            canvas.drawLine(bar_x, cage_y, bar_x, cage_y + 55)
            canvas.drawLine(bar_x + 1, cage_y, bar_x + 1, cage_y + 55)

        # Feet
        canvas.setPen(QPen(QColor("#6d400c"), 5))
        canvas.drawLine(cage_x + 15, cage_y + 55, cage_x, cage_y + 135)
        canvas.drawLine(cage_x + 45, cage_y + 55, cage_x + 60, cage_y + 135)
        canvas.drawLine(cage_x + 10, cage_y + 105, cage_x + 50, cage_y + 105)

        # Porte: elle s'ouvre vers la droite pour la cage gauche,
        # vers la gauche pour la cage droite.
        if game.cages_open:
            bottom_x = cage_x + 60 if opens_right else cage_x
            bottom_y = cage_y + 55
            outer_x = bottom_x + (50 if opens_right else -50)
            canvas.drawLine(bottom_x, bottom_y, outer_x,bottom_y)
            canvas.drawLine(outer_x, bottom_y, outer_x, bottom_y - 10)

        canvas.restore()

    # -------------------------------------------------------------------------
    def _draw_cannon(self, canvas: QPainter, game: Game) -> None:

        canvas.save()

        gun_x = game.WIDTH / 2
        gun_y = game.HEIGHT - 82
        canvas.setPen(QPen(QColor("#3B1D1D"), 5))
        canvas.drawLine(round(gun_x), round(gun_y), round(gun_x), round(gun_y - 38))
        canvas.setPen(QPen(QColor("#636363"), 2))
        canvas.setBrush(QBrush(QColor("#555555")))
        canvas.drawRect(round(gun_x - 23), round(gun_y - 8), 46, 22)

        canvas.restore()

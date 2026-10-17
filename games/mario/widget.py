"""Rendu provisoire du jeu de plateforme : décor et sprites vectoriels."""

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QBrush, QPen, QPainter, QFont

from setup.constants import GAME_FONT
from setup.utils import is_between

from games.game import Game

# =============================================================================
class MarioWidget:

    # -------------------------------------------------------------------------
    def paint(self, painter: QPainter, game: Game) -> None:

        painter.save()

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        # Ciel et collines en couches simples.
        painter.fillRect(0, game.HUD_HEIGHT, game.WIDTH, game.HEIGHT - game.HUD_HEIGHT, QColor("#79c9f2"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#58b957")))
        for i in range(-1, 5):
            x = i * 300 - int(game.world_distance * 0.22) % 300
            painter.drawEllipse(QRectF(x, 210, 390, 210))
        ground_y = game.GROUND_Y
        painter.fillRect(0, ground_y, game.WIDTH, game.HEIGHT - ground_y, QColor("#b86b3d"))
        painter.fillRect(0, ground_y, game.WIDTH, 18, QColor("#54a83b"))
        
        # Sol en blocs, défilant avec le monde.
        painter.setPen(QPen(QColor("#6b3827"), 2))
        for i in range(-1, 14):
            x = i * 80 - int(game.world_distance) % 80
            painter.drawRect(x, ground_y + 18, 80, 44)
       
        # Petites plateformes / briques.
        for i in range(5):
            x = 570 + i * 75 - int(game.world_distance) % 650
            if 250 < x < game.WIDTH - 40:
                painter.setBrush(QBrush(QColor("#d88943")))
                painter.setPen(QPen(QColor("#81451f"), 2))
                painter.drawRect(x, ground_y - 110, 52, 40)
        
        # Pièces à collecter.
        for coin in game.coins:
            if coin.collected:
                continue
            x = coin.x - game.world_distance + game.PLAYER_X
            if is_between(x, -30, game.WIDTH + 30):
                painter.setPen(QPen(QColor("#b77b00"), 2))
                painter.setBrush(QBrush(QColor("#ffd83d")))
                painter.drawEllipse(QRectF(x - 11, ground_y - 102, 22, 22))
                painter.setPen(QPen(QColor("#fff4a8"), 2))
                painter.drawLine(round(x), round(ground_y - 98), round(x), round(ground_y - 84))
        
        # Personnage original, non issu d'un sprite existant.
        self._draw_mario(painter, game, ground_y)
        
        # Titre de prototype, discret.
        painter.setPen(QPen(QColor("#17334c")))
        painter.setFont(QFont(GAME_FONT, 12, QFont.Weight.Bold))
        painter.drawText(24, game.HEIGHT - 18, "Prototype plateforme · ramez pour sauter et attraper les pièces")
        
        painter.restore()

    # -------------------------------------------------------------------------
    def _draw_mario(
        self,
        painter: QPainter,
        game: Game,
        ground_y: int
    ) -> None:
         
        painter.save()

        jump_height = game._jump_height()
        x, y = game.PLAYER_X, ground_y - 54 - jump_height

        painter.setPen(QPen(QColor("#4b2b1c"), 2))
        painter.setBrush(QBrush(QColor("#e34a3b")))
        painter.drawRoundedRect(QRectF(x - 20, y, 40, 20), 5, 5)
        painter.setBrush(QBrush(QColor("#f1bd83")))
        painter.drawEllipse(QRectF(x - 15, y + 14, 30, 25))
        painter.setBrush(QBrush(QColor("#3276c9")))
        painter.drawRoundedRect(QRectF(x - 17, y + 35, 34, 21), 4, 4)
        painter.setBrush(QBrush(QColor("#51392c")))
        painter.drawRect(QRectF(x - 17, y + 51, 13, 8))
        painter.drawRect(QRectF(x + 4, y + 51, 13, 8))
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawEllipse(QRectF(x + 2, y + 21, 5, 6))
        painter.setBrush(QBrush(QColor("#222222")))
        painter.drawEllipse(QRectF(x + 4, y + 23, 2, 3))

        painter.restore()

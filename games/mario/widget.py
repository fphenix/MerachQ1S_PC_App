"""Rendu de Ramio : terrain lisible, plateformes solides et héros original."""

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QBrush, QPen, QPainter, QFont, QPolygonF

from setup.constants import GAME_FONT
from setup.utils import is_between

from games.game import Game
from games.game_painter import GamePainter
from games.pulsator import Pulsator

# =============================================================================
class MarioWidget(GamePainter):

    PULSATOR = Pulsator(min_radius= 2.0, max_radius= 20.0, pen_width= 2.0, outlined= True)

    # -------------------------------------------------------------------------
    def paint(self, painter: QPainter, game: Game) -> None:

        painter.save()

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Ciel et décor non bloquant.
        painter.fillRect(0, game.HUD_HEIGHT, game.WIDTH, game.HEIGHT - game.HUD_HEIGHT, QColor("#8bd2f4"))
        painter.setPen(Qt.PenStyle.NoPen)

        painter.setBrush(QBrush(QColor("#f6f3dc")))
        for i in range(-1, 5):
            x = i * 280 - int(game.world_distance * 0.12) % 280
            painter.drawEllipse(QRectF(x, 135 + (i % 2) * 35, 90, 28))
            painter.drawEllipse(QRectF(x + 24, 120 + (i % 2) * 35, 76, 42))

        painter.setBrush(QBrush(QColor("#69bd72")))
        for i in range(-1, 5):
            x = i * 320 - int(game.world_distance * 0.22) % 320
            painter.drawEllipse(QRectF(x, 270, 410, 190))

        # Repères pulsés : 24 CPM pour courir, 30 CPM pour déclencher un saut.
        cadence_targets = (game.RUN_CADENCE_TARGET, game.JUMP_CADENCE_TARGET)
        cadence_colors = (QColor("#4c8e59"), QColor("#d9584e"))
        for index, (target, color) in enumerate(zip(cadence_targets, cadence_colors)):
            center_x = 150
            center_y = 400 + index * 50
            self.PULSATOR.paint(
                painter, center_x, center_y, game.elapsed, target, color,
            )
            painter.setPen(QPen(QColor("#17334c")))
            painter.setFont(QFont(GAME_FONT, 14, QFont.Weight.Bold))
            painter.drawText(
                QRectF(center_x + 28, center_y, 96, 22),
                Qt.AlignmentFlag.AlignCenter,
                f"{int(target)} CPM",
            )

        # Sol
        ground_y = game.GROUND_Y
        painter.fillRect(QRectF(0, ground_y, game.WIDTH, game.HEIGHT - ground_y), QColor("#a9683e"))
        painter.fillRect(QRectF(0, ground_y, game.WIDTH, 18), QColor("#5cae48"))

        painter.setPen(QPen(QColor("#784326"), 2))    
        for i in range(-1, 14):
            x = i * 80 - int(game.world_distance) % 80
            painter.drawRect(QRectF(x, ground_y + 18, 80, 44))
       
        # Plateformes : 3 types: lévitantes, liées au sol ou escaliers.
        for platform in game.platforms:
            x = platform.x - game.world_distance + game.PLAYER_X
            if x + platform.width < -20 or x > game.WIDTH + 20:
                continue
            top = platform.top
            if platform.kind == "floating":
                painter.setPen(QPen(QColor("#684a35"), 2))
                painter.setBrush(QBrush(QColor("#a97b50")))
                painter.drawRoundedRect(QRectF(x, top, platform.width, 20), 3, 3)
                painter.fillRect(QRectF(x + 2, top, platform.width - 4, 5), QColor("#6ab34b"))
            elif platform.kind == "linked":
                # Bloc massif relié au sol : sa face verticale bloque le passage.
                painter.setPen(QPen(QColor("#68452f"), 2))
                painter.setBrush(QBrush(QColor("#a9774b")))
                painter.drawRect(QRectF(x, top, platform.width, ground_y - top))
                painter.fillRect(QRectF(x, top, platform.width, 12), QColor("#5cae48"))
                for bx in range(int(x + 8), int(x + platform.width - 8), 34):
                    painter.drawLine(bx, int(top + 18), bx + 18, int(top + 18))
            else:
                # Triangle/marches : montée accessible en courant.
                painter.setPen(QPen(QColor("#68452f"), 2))
                painter.setBrush(QBrush(QColor("#a9774b")))
                steps = max(3, int(platform.width // 35))
                step_w = platform.width / steps
                for step in range(steps):
                    step_h = (ground_y - top) * (step + 1) / steps
                    painter.drawRect(QRectF(x + step * step_w, ground_y - step_h, step_w, step_h))
                    painter.fillRect(QRectF(x + step * step_w, ground_y - step_h, step_w, 7), QColor("#5cae48"))

        # Pièces/Tokens
        for coin in game.coins:
            if coin.collected:
                continue
            x = coin.x - game.world_distance + game.PLAYER_X
            y = coin.y
            if is_between(x, -30, game.WIDTH + 30):
                painter.setPen(QPen(QColor("#a56c00"), 2))
                painter.setBrush(QBrush(QColor("#ffdc43")))
                painter.drawEllipse(QRectF(x - 10, y - 10, 20, 20))
                painter.setPen(QPen(QColor("#fff4a8"), 2))
                painter.drawLine(round(x), round(y - 6), round(x), round(y + 6))

        # Ennemis
        for enemy in game.enemies:
            if enemy.hit:
                continue
            x = enemy.x - game.world_distance + game.PLAYER_X
            if is_between(x, -40, game.WIDTH + 40):
                painter.setPen(QPen(QColor("#542d40"), 2))
                painter.setBrush(QBrush(QColor("#9d4b65")))
                painter.drawEllipse(QRectF(x - 16, enemy.y - 25, 32, 30))
                painter.setBrush(QBrush(QColor("#fff3d7")))
                painter.drawEllipse(QRectF(x - 8, enemy.y - 17, 5, 6))
                painter.drawEllipse(QRectF(x + 3, enemy.y - 17, 5, 6))
                painter.setPen(QPen(QColor("#542d40"), 2))
                painter.drawLine(round(x - 13), round(enemy.y + 3), round(x - 20), round(enemy.y + 9))
                painter.drawLine(round(x + 13), round(enemy.y + 3), round(x + 20), round(enemy.y + 9))

        # Avatar
        self._draw_hero(painter, game)

        # Château visible à l'approche de la fin du niveau.
        castle_x = game.LEVEL_LENGTH - game.world_distance + game.PLAYER_X
        if game.remaining() <= 20.0:
            castle_x = max(castle_x, game.PLAYER_X + 250)
        if castle_x < game.WIDTH + 240:
            painter.setPen(QPen(QColor("#5a465e"), 3))
            painter.setBrush(QBrush(QColor("#d6c6dc")))
            painter.drawRect(QRectF(castle_x, ground_y - 125, 150, 125))
            painter.drawRect(QRectF(castle_x - 18, ground_y - 155, 44, 155))
            painter.drawRect(QRectF(castle_x + 124, ground_y - 155, 44, 155))
            painter.setBrush(QBrush(QColor("#b65d63")))
            painter.drawPolygon(QPolygonF([
                QPointF(castle_x - 24, ground_y - 155),
                QPointF(castle_x + 4, ground_y - 190),
                QPointF(castle_x + 32, ground_y - 155)
            ]))
            painter.drawPolygon(QPolygonF([
                QPointF(castle_x + 118, ground_y - 155),
                QPointF(castle_x + 146, ground_y - 190),
                QPointF(castle_x + 174, ground_y - 155)
            ]))
            painter.setBrush(QBrush(QColor("#684b6c")))
            painter.drawRect(QRectF(castle_x + 58, ground_y - 55, 34, 55))

        painter.setPen(QPen(QColor("#17334c")))
        painter.setFont(QFont(GAME_FONT, 12, QFont.Weight.Bold))
        painter.drawText(
            24, game.HEIGHT - 18,
            f"Ramio  ·  {int(game.current_spm or 0)} CPM  ·  DIST {int(game.world_distance)}"
        )
        
        painter.restore()

    # -------------------------------------------------------------------------
    def _draw_hero(
        self,
        painter: QPainter,
        game: Game,
    ) -> None:
         
        painter.save()

        jump_height = game._jump_height()
        x = game.PLAYER_X
        y = game.player_ground_y - 54 - jump_height

        # Héros original : cheveux sombres, tunique turquoise et pantalon ocre.
        painter.setPen(QPen(QColor("#263746"), 2))
        painter.setBrush(QBrush(QColor("#2e414d")))
        painter.drawEllipse(QRectF(x - 13, y + 1, 26, 13))
        painter.setBrush(QBrush(QColor("#e8b58a")))
        painter.drawRoundedRect(QRectF(x - 12, y + 8, 24, 23), 5, 5)
        painter.setBrush(QBrush(QColor("#f3d7b5")))
        painter.drawRect(QRectF(x - 8, y + 15, 4, 3))
        painter.drawRect(QRectF(x + 4, y + 15, 4, 3))
        painter.setBrush(QBrush(QColor("#263746")))
        painter.drawEllipse(QRectF(x - 7, y + 15, 3, 4))
        painter.drawEllipse(QRectF(x + 5, y + 15, 3, 4))
        painter.setBrush(QBrush(QColor("#268b91")))
        painter.drawRoundedRect(QRectF(x - 15, y + 30, 30, 19), 4, 4)
        painter.setBrush(QBrush(QColor("#d9a441")))
        painter.drawRect(QRectF(x - 13, y + 47, 11, 7))
        painter.drawRect(QRectF(x + 2, y + 47, 11, 7))
        painter.setBrush(QBrush(QColor("#57433a")))
        painter.drawRoundedRect(QRectF(x - 16, y + 51, 15, 7), 2, 2)
        painter.drawRoundedRect(QRectF(x + 1, y + 51, 15, 7), 2, 2)
        painter.setBrush(QBrush(QColor("#e8b58a")))
        painter.drawEllipse(QRectF(x - 20, y + 31, 9, 10))
        painter.drawEllipse(QRectF(x + 11, y + 31, 9, 10))
        
        painter.restore()

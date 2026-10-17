"""Rendu du Dino Runner."""

import math

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QBrush, QPen, QPainter, QPolygonF, QFont

from setup.lang import get_text
from setup.utils import is_between
from setup.constants import GAME_FONT

from games.game import Game
from games.pulsator import Pulsator
from games.jump.engine import Obstacle

# =============================================================================
class JumpWidget:

    PULSATOR = Pulsator(min_radius= 2.0, max_radius= 15.0, pen_width= 2.0)

    HORIZON_HEIGHT: int = 135
    ZONES_COLOR = {
        "slow": QColor("#267c8a"),
        "medium": QColor("#72543c"),
        "fast": QColor("#26753d"),
    }

    # -------------------------------------------------------------------------
    def paint(self, painter: QPainter, game: Game) -> None:

        painter.save()

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Ciel et montagnes en couches de parallaxe.
        horizon = game.HUD_HEIGHT + self.HORIZON_HEIGHT
        painter.fillRect(
            0, horizon + 75,
            game.WIDTH, game.HEIGHT - game.HUD_HEIGHT - horizon,
            QColor("#c2b063")
        )
        painter.fillRect(
            0, horizon,
            game.WIDTH, 75,
            QColor("#94874c")
        )
        painter.fillRect(
            0,  game.HUD_HEIGHT,
            game.WIDTH, self.HORIZON_HEIGHT,
            QColor("#abf2ff")
        )
        self._mountain_layer(painter, game, 420, horizon + 28, 0.12, QColor("#9bbfa9"), 115.0)
        self._mountain_layer(painter, game, 480, horizon + 75, 0.27, QColor("#6e9c79"), 175.0)
        self._mountain_layer(painter, game, 520, horizon + 105, 0.48, QColor("#386b44"), 105.0)

        # Repères de cadence pulsés : déplacement, saut simple et saut double.
        painter.setFont(QFont(GAME_FONT, 12, QFont.Weight.Bold))
        pulse_items = (
            ("slow", game.CADENCE_RUN, get_text("GAME_JUMP_RUN"), 200),
            ("medium", game.CADENCE_ROCK, get_text("GAME_JUMP_ROCK"), 450),
            ("fast", game.CADENCE_CACTUS, get_text("GAME_JUMP_CACTUS"), 700),
        )
        pulse_y = 650
        for zone, target, label, center_x in pulse_items:
            pulse_color = QColor(self.ZONES_COLOR.get(zone, QColor("#c6c9b9")))
            self.PULSATOR.paint(
                painter, center_x, pulse_y, game.elapsed, target, pulse_color
            )
            painter.setPen(QPen(QColor("#32134f")))
            painter.drawText(
                round(center_x + 25), pulse_y + 5,
                f"{label} {target} {get_text('SPM_UNIT')}"
            )

        # Sol et bande de déplacement.
        ground_y = game.PLAYER_GROUND_Y + 6
        painter.setPen(QPen(QColor("#6a4b32"), 4))
        painter.drawLine(0, ground_y, game.WIDTH, ground_y)
        painter.setPen(QPen(QColor("#92724b"), 2))
        for index in range(-2, 16):
            x = (index * 90 - game.scroll_offset) % (game.WIDTH + 90) - 30
            painter.drawLine(round(x), ground_y + 17, round(x + 22), ground_y + 17)

        # Bande de zones à la même échelle que la route : un pixel de bande
        # défile à la même vitesse qu’un pixel d’obstacle.
        band_y = ground_y + 23
        band_height = 17
        painter.setPen(Qt.PenStyle.NoPen)
        zone_remaining = max(0.0, game.zone_duration - game.zone_elapsed)
        # Le bord de la zone est à une distance temporelle * SCROLL_SPEED,
        # comme les obstacles. Il peut rester hors écran pendant la majeure
        # partie d'une zone de 30–45 secondes.
        marker_x = round(zone_remaining * game.SCROLL_SPEED)
        current_color = self.ZONES_COLOR.get(game.zone_kind, QColor("#c6c9b9"))
        next_color = self.ZONES_COLOR.get(game.next_zone_kind, current_color)
        if marker_x >= game.WIDTH:
            painter.setBrush(QBrush(current_color))
            painter.drawRect(0, band_y, game.WIDTH, band_height)
        elif marker_x > 0:
            painter.setBrush(QBrush(current_color))
            painter.drawRect(0, band_y, marker_x, band_height)
            painter.setBrush(QBrush(next_color))
            painter.drawRect(marker_x, band_y, game.WIDTH - marker_x, band_height)
        else:
            painter.setBrush(QBrush(next_color))
            painter.drawRect(0, band_y, game.WIDTH, band_height)

        # Repère de fin visible uniquement lorsqu'il entre dans l'écran.
        if is_between(marker_x, 0, game.WIDTH):
            painter.setPen(QPen(QColor("#f5f0dc"), 2))
            painter.drawLine(marker_x, band_y - 3, marker_x, band_y + band_height + 3)

        # Décor simple entre les montagnes et la route : deux lignes de
        # petits éléments non interactifs, avec des vitesses de parallaxe.
        self._draw_background_decor(painter, game, ground_y)

        # Fleurs décoratives régulières au sol.
        for index in range(-1, 12):
            x = (index * 135 - game.scroll_offset * 1.05) % (game.WIDTH + 135)
            self._draw_flower(painter, x, ground_y - 2, False)
        for flower in game.flowers:
            self._draw_flower(painter, flower.x, ground_y - 2, flower.rare)

        # Obstacle sprites (Rocher ou Cactus).
        for obstacle in game.obstacles:
            if obstacle.kind == "rock":
                self._draw_rock(painter, obstacle, ground_y)
            elif obstacle.kind == "cactus":
                self._draw_cactus(painter, obstacle, ground_y)
            # Les événements "empty" sont volontairement invisibles.

        # Dino simple mais animé par une alternance des pattes.
        jump_offset = 0.0
        if game.jump_type is not None and game.jump_duration > 0.0:
            phase = min(1.0, game.jump_elapsed / game.jump_duration)
            jump_offset = math.sin(math.pi * phase) * game.jump_height
        dino_y = game.PLAYER_GROUND_Y - game.PLAYER_HEIGHT - jump_offset
        self._draw_dino(painter, game.PLAYER_X, dino_y, game.elapsed, jumping= game.jump_type is not None)

        # points animés quand on réussi un saut (si on est à la bonne cadence)
        painter.setFont(QFont(GAME_FONT, 17, QFont.Weight.Bold))
        for x, y, points, age in game._score_popups:
            painter.setPen(QPen(QColor("#176c36")))
            painter.drawText(round(x), round(y), f"+{points}")

        painter.restore()

    # -------------------------------------------------------------------------
    def _mountain_layer(
        self,
        painter: QPainter,
        game: Game,
        base_x: int, base_y: int,
        speed_factor: float,
        color: QColor,
        peak_height: float
    ) -> None:

        painter.save()

        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.setBrush(QBrush(color))
        offset = (game.scroll_offset * speed_factor) % base_x
        for i in range(-1, 5):
            x = i * base_x - offset
            # 2 peaks in a M shape, first peak shorter than the 2nd
            painter.drawPolygon(QPolygonF([
                QPointF(x, base_y),
                QPointF(x + int(0.23 * base_x), base_y - peak_height * 0.72),
                QPointF(x + int(0.48 * base_x), base_y),
                QPointF(x + int(0.71 * base_x), base_y - peak_height),
                QPointF(x + base_x, base_y),
            ]))

        painter.restore()

    # -------------------------------------------------------------------------
    def _draw_background_decor(self, painter: QPainter, game: Game, ground_y: float) -> None:
        """Décor de fond déterministe, sans collision ni lien avec le gameplay."""

        rows = (
            # facteur de parallaxe, hauteur au-dessus du sol, espacement
            (0.51, 180, 173),
            (0.58, 105, 137),
        )
        for row_index, (speed, height, spacing) in enumerate(rows):
            travel = game.scroll_offset * speed
            offset = travel % spacing
            first_world_index = int(travel // spacing)
            y = ground_y - height
            for slot in range(-1, game.WIDTH // spacing + 2):
                world_index = first_world_index + slot
                # Variation pseudo-aléatoire stable : pas de scintillement
                # d'une image à l'autre et aucun générateur aléatoire partagé.
                seed = (world_index * 37 + row_index * 19 + 11) % 17
                if seed in (0, 5, 12):
                    continue
                x = round(slot * spacing - offset + (seed % 5) * 9)
                kind = (seed + row_index * 2) % 3
                scale = 1.12 + (seed % 4) * 0.10
                painter.save()
                painter.translate(x, y)
                painter.scale(scale, scale)
                if kind == 0:
                    # Petit rocher arrondi.
                    painter.setPen(QPen(QColor("#655f55"), 1.5))
                    painter.setBrush(QBrush(QColor("#918779")))
                    painter.drawPolygon(QPolygonF([
                        QPointF(-11, 0), QPointF(-8, -8), QPointF(-1, -12),
                        QPointF(7, -9), QPointF(12, 0),
                    ]))
                elif kind == 1:
                    # Fleur minuscule, purement décorative.
                    painter.setPen(QPen(QColor("#3b7139"), 1.5))
                    painter.drawLine(0, 0, 0, -11)
                    petal = QColor("#e6a5c8" if seed % 2 else "#f0d978")
                    painter.setPen(QPen(petal, 1))
                    painter.setBrush(QBrush(petal))
                    painter.drawEllipse(-4, -16, 5, 5)
                    painter.drawEllipse(1, -16, 5, 5)
                    painter.drawEllipse(-2, -19, 5, 5)
                else:
                    # Cactus bas, nettement plus petit que l'obstacle jouable.
                    cactus = QColor("#4b8752")
                    painter.setPen(QPen(QColor("#326540"), 1.5))
                    painter.setBrush(QBrush(cactus))
                    painter.drawRoundedRect(-3, -19, 7, 19, 2, 2)
                    painter.drawRoundedRect(-8, -13, 5, 8, 2, 2)
                    painter.drawRoundedRect(4, -11, 5, 7, 2, 2)

                painter.restore()

    # -------------------------------------------------------------------------
    def _draw_rock(
        self,
        painter: QPainter,
        obstacle: Obstacle,
        ground_y: float,
    ) -> None:

        painter.setPen(QPen(QColor("#5b5148"), 2))
        painter.setBrush(QBrush(QColor("#82796e")))
        painter.drawPolygon(QPolygonF([
            QPointF(obstacle.x, ground_y), QPointF(obstacle.x + 8, ground_y - 25),
            QPointF(obstacle.x + 28, ground_y - 37), QPointF(obstacle.x + 47, ground_y - 20),
            QPointF(obstacle.x + 53, ground_y),
        ]))

    # -------------------------------------------------------------------------
    def _draw_cactus(
        self,
        painter: QPainter,
        obstacle: Obstacle,
        ground_y: float,
    ) -> None:

        painter.setPen(QPen(QColor("#226c3b"), 3))
        painter.setBrush(QBrush(QColor("#399d50")))
        painter.drawRoundedRect(round(obstacle.x + 14), round(ground_y - 92), 24, 92, 8, 8)
        painter.drawRoundedRect(round(obstacle.x), round(ground_y - 66), 16, 40, 6, 6)
        painter.drawRoundedRect(round(obstacle.x + 36), round(ground_y - 59), 16, 36, 6, 6)
        painter.setPen(QPen(QColor("#b3e0a0"), 2))
        painter.drawLine(round(obstacle.x + 22), round(ground_y - 82), round(obstacle.x + 22), round(ground_y - 63))

    # -------------------------------------------------------------------------
    def _draw_flower(
        self,
        painter: QPainter,
        ground_x: float, ground_y: float,
        rare: bool,
    ) -> None:

        # Pedicel/Stem
        painter.setPen(QPen(QColor("#24642f"), 2))
        painter.drawLine(round(ground_x), round(ground_y), round(ground_x), round(ground_y - 12))
        # Leaf
        painter.setPen(QPen(QColor("#175021"), 2))
        right_side = 1 if rare else 0
        painter.drawEllipse(round(ground_x - 4 + (6 * right_side)), round(ground_y - 6), 2, 4)
        # Petals
        petals = QColor("#7e55f0" if rare else "#e932a3")
        painter.setBrush(QBrush(petals))
        painter.setPen(QPen(petals, 1))
        radius = 5 if rare else 3
        for dx, dy in ((0, -15), (-5, -11), (5, -11), (0, -7)):
            painter.drawEllipse(round(ground_x + dx - radius / 2), round(ground_y + dy - radius / 2), radius, radius)
        # Anthers & Filaments
        painter.setBrush(QBrush(QColor("#e2d734")))
        painter.drawEllipse(round(ground_x - 2), round(ground_y - 13), 4, 4)

    # -------------------------------------------------------------------------
    def _draw_dino(
        self,
        painter: QPainter,
        x: float, y: float,
        elapsed: float,
        jumping: bool = False,
    ) -> None:
        """Silhouette de petit T-Rex : grosse tête, mâchoire, bras courts et une queue."""

        painter.save()

        skin_color = QColor("#356b4b")
        outline_color = QColor("#1e4933")
        belly_color = QColor("#a4bd79")

        painter.setPen(QPen(outline_color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(QBrush(skin_color))

        # Queue longue et effilée, puis corps incliné.
        painter.drawPolygon(QPolygonF([
            QPointF(x + 11, y + 34), QPointF(x - 17, y + 27),
            QPointF(x + 5, y + 43), QPointF(x + 20, y + 48),
        ]))
        painter.drawPolygon(QPolygonF([
            QPointF(x + 8, y + 31), QPointF(x + 20, y + 17),
            QPointF(x + 38, y + 21), QPointF(x + 43, y + 43),
            QPointF(x + 32, y + 53), QPointF(x + 12, y + 49),
        ]))
        # Ventre clair.
        painter.setPen(QPen(belly_color, 1))
        painter.setBrush(QBrush(belly_color))
        painter.drawPolygon(QPolygonF([
            QPointF(x + 17, y + 39), QPointF(x + 35, y + 38),
            QPointF(x + 34, y + 46), QPointF(x + 18, y + 45),
        ]))
        # Cou et crâne surdimensionné, avec museau et mâchoire bien visibles.
        painter.setPen(QPen(outline_color, 2))
        painter.setBrush(QBrush(skin_color))
        painter.drawPolygon(QPolygonF([
            QPointF(x + 31, y + 30), QPointF(x + 35, y + 12),
            QPointF(x + 43, y + 3), QPointF(x + 57, y + 5),
            QPointF(x + 62, y + 13), QPointF(x + 55, y + 20),
            QPointF(x + 43, y + 22), QPointF(x + 41, y + 35),
        ]))
        jaw_drop = 6 if jumping else 0
        painter.drawPolygon(QPolygonF([
            QPointF(x + 43, y + 20), QPointF(x + 61, y + 17),
            QPointF(x + 57, y + 26 + jaw_drop), QPointF(x + 44, y + 25 + jaw_drop),
        ]))
        # Petite main à deux doigts.
        painter.setPen(QPen(outline_color, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(round(x + 37), round(y + 32), round(x + 43), round(y + 35))
        painter.drawLine(round(x + 43), round(y + 35), round(x + 46), round(y + 33))
        painter.drawLine(round(x + 43), round(y + 35), round(x + 47), round(y + 37))
        # Œil et quelques dents contrastées.
        painter.setPen(QPen(QColor("#fff4cf"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawPoint(round(x + 52), round(y + 10))
        painter.setPen(QPen(QColor("#f5f2d8"), 1))
        painter.drawLine(round(x + 51), round(y + 22), round(x + 53), round(y + 24))
        painter.drawLine(round(x + 56), round(y + 21), round(x + 57), round(y + 23))
        # Pattes arrière épaisses, animées quand le dinosaure court.
        painter.setPen(QPen(outline_color, 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        if y < 500:
            painter.drawLine(round(x + 18), round(y + 46), round(x + 17), round(y + 59))
            painter.drawLine(round(x + 33), round(y + 46), round(x + 36), round(y + 59))
        else:
            leg = 7 if int(elapsed * 8) % 2 else -4
            painter.drawLine(round(x + 18), round(y + 46), round(x + 15 + leg), round(y + 60))
            painter.drawLine(round(x + 33), round(y + 46), round(x + 36 - leg), round(y + 60))

        painter.restore()

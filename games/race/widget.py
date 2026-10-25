"""Rendu des courses avec caméra rapprochée et échelle de progression."""

import math

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPolygonF, QFont

from setup.constants import GAME_FONT
from setup.lang import get_text
from setup.utils import (
    clamp_between, clamp_to_zero,
    clamp_to_max, clamp_to_min,
    is_between,
)

from games.game import Game
from games.game_painter import GamePainter

# =============================================================================
class RaceWidget(GamePainter):

    RULER_HEIGHT: int = 42 # pixels
    VISIBLE_DISTANCE: float = 55.0 # meters

    # -------------------------------------------------------------------------
    def paint(self, painter: QPainter, game: Game) -> None:

        painter.save()

        # River
        top = game.HUD_HEIGHT
        ruler_top = game.HEIGHT - self.RULER_HEIGHT
        course_height = ruler_top - top
        painter.fillRect(0, top, game.WIDTH, course_height, QColor("#153f35"))

        # Lanes
        lane_count = len(game.boats)
        lane_height = course_height / clamp_to_min(lane_count, 1)
        for lane in range(lane_count + 1):
            y = round(top + lane * lane_height)
            painter.setPen(QPen(QColor("#7c9d8f"), 1, Qt.PenStyle.DashLine))
            painter.drawLine(0, y, game.WIDTH, y)

        # Zoom sur les bateaux
        scale = (game.WIDTH - 40.0) / self.VISIBLE_DISTANCE
        player_x = game.PLAYER_X
        player_distance = game.player_boat.distance
        course_x = lambda distance: player_x + (distance - player_distance) * scale

        # Repères de 50 m / 100 m sur toute la longueur du bassin
        first_marker = clamp_to_zero(int(player_distance // 50) * 50 - 50)
        last_marker = min(int(game.race_distance), int(player_distance + self.VISIBLE_DISTANCE))
        painter.setFont(QFont(GAME_FONT, 10))
        for marker_m in range(first_marker, last_marker + 1, 50):
            marker_x = course_x(marker_m)
            if not is_between(marker_x, 0, game.WIDTH):
                continue
            major = marker_m % 100 == 0

            painter.setPen(QPen(QColor("#b9d1c7" if major else "#6e9284"), 2 if major else 1))
            painter.drawLine(round(marker_x), top, round(marker_x), ruler_top)
            if major:
                painter.setPen(QPen(QColor("#e0eee7")))
                painter.drawText(round(marker_x + 4), top + 14, f"{marker_m} m")

        # Lignes de départ et d'arrivée
        for distance, label, color, is_finish in (
            (0.0, get_text("GAME_RACE_START_LINE"), QColor("#ffffff"), False),
            (game.race_distance, get_text("GAME_RACE_FINISH_LINE"), QColor("#ffe082"), True),
        ):
            line_x = course_x(distance)
            if is_between(line_x, 0, game.WIDTH):
                painter.setPen(QPen(color, 3))
                painter.drawLine(round(line_x), top, round(line_x), ruler_top)
                painter.setFont(QFont(GAME_FONT, 11, QFont.Weight.Bold))
                painter.drawText(round(line_x + 5), top + 32, label)
                if is_finish:
                    painter.setPen(QPen(color, 1))
                    for y in range(top + 42, ruler_top, 18):
                        painter.drawLine(round(line_x - 5), y, round(line_x + 5), y + 9)

        # Bateaux et animation de coups de rame
        for boat in game.boats:
            lane_center = top + (boat.lane + 0.5) * lane_height
            x = player_x if boat.is_player else course_x(boat.distance)
            x = clamp_between(x, 48.0, game.WIDTH - 48.0)

            # Coup actif: pour un bâteau allant de gauche à droite, balayage de rame
            # de gauche à droite, bref (au plus 1 s).
            # Retour: de droite à gauche, récupération lente hors de l'eau.
            period = clamp_to_min(boat.stroke_period, 0.1)
            # Le timer du joueur repart à zéro sur un vrai coup de rame. On ne
            # fait surtout pas de modulo : cela relancerait une propulsion fantôme
            # même si aucun nouveau coup n'arrive. Les adversaires, eux, gardent
            # leur cycle automatique.
            cycle_time = boat.stroke_timer if boat.is_player else boat.stroke_timer % period
            active_duration = clamp_to_max(period * 0.32, 1.0)
            if cycle_time >= period:
                stroke_progress = 0.0
            elif cycle_time <= active_duration:
                t = clamp_between(cycle_time / clamp_to_min(active_duration, 0.001), 0.0, 1.0)
                stroke_progress = t * t * (3.0 - 2.0 * t)
            else:
                t = clamp_between((cycle_time - active_duration) / clamp_to_min(period - active_duration, 0.001), 0.0, 1.0)
                recovery = t * t * (3.0 - 2.0 * t)
                stroke_progress = 1.0 - recovery
            stroke_progress = clamp_between(stroke_progress, 0.0, 1.0)
            hull_y = lane_center - 10
            if boat.is_player:
                hull_y -= 7.0 * game.stroke_impulse

            # Remous permanents autour de la coque, avec une phase propre à
            # chaque bateau pour éviter une animation parfaitement synchronisée.
            ripple_phase = game.race_elapsed * 0.72 + boat.lane * 0.31
            self.draw_ripple(painter, x - 22.0, hull_y + 1.0, ripple_phase, 1.75)
            self.draw_ripple(painter, x + 15.0, hull_y + 1.0, ripple_phase + 0.28, 1.45)

            # Hull
            color = QColor(boat.color)
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(color))
            hull = QPolygonF([
                QPointF(x - 35, hull_y - 7),
                QPointF(x + 24, hull_y - 7),
                QPointF(x + 42, hull_y),
                QPointF(x + 24, hull_y + 7),
                QPointF(x - 35, hull_y + 7),
            ])
            painter.drawPolygon(hull)

            # Coup de rame
            strength = stroke_progress
            in_drive = cycle_time < period and cycle_time <= active_duration
            if strength > 0.03:
                painter.setPen(QPen(QColor("#a8f0ff") if boat.is_player else color.lighter(150), 2))
                angle = math.radians(-135.0 + 90.0 * strength)
                length = 27.0
                pivot_x = x - 8.0
                tip_x = round(pivot_x + length * math.cos(angle))
                tip_y = round(hull_y + length * math.sin(angle))
                painter.drawLine(round(pivot_x), round(hull_y), tip_x, tip_y)
                # Rame symétrique de l'autre côté du bateau.
                lower_angle = -angle
                lower_tip_x = round(pivot_x + length * math.cos(lower_angle))
                lower_tip_y = round(hull_y + length * math.sin(lower_angle))
                painter.drawLine(round(pivot_x), round(hull_y), lower_tip_x, lower_tip_y)

                # Petites rides à l'endroit où chaque pale touche l'eau.
                # Leur taille suit le mouvement de la rame et reste contenue
                # dans la voie du bateau.
                if in_drive:
                    self.draw_ripple(painter, tip_x, tip_y, ripple_phase + 0.16, 0.8 + 0.35 * strength)
                    self.draw_ripple(painter, lower_tip_x, lower_tip_y, ripple_phase + 0.58, 0.8 + 0.35 * strength)

            # Nom sur le bâteau
            painter.setPen(QPen(QColor("#111111"), 1))
            painter.setFont(QFont(GAME_FONT, 10, QFont.Weight.Bold))
            label = (
                get_text("GAME_PLAYER")
                if boat.is_player
                else f"{get_text('GAME_OPPONENT')} #{boat.name.removeprefix('ADV_')}"
            )
            painter.drawText(round(x - 32), round(hull_y + 4), label)

        # Échelle complète du parcours : les points représentent la position de chaque bateau.
        painter.fillRect(0, ruler_top, game.WIDTH, self.RULER_HEIGHT, QColor("#101d19"))
        painter.setPen(QPen(QColor("#8da99b"), 1))
        painter.drawLine(20, ruler_top + 20, game.WIDTH - 20, ruler_top + 20)
        painter.setFont(QFont(GAME_FONT, 9))
        for marker_m in range(0, int(game.race_distance) + 1, 100):
            x = 20 + (game.WIDTH - 40) * marker_m / game.race_distance
            painter.drawLine(round(x), ruler_top + 15, round(x), ruler_top + 25)
            painter.drawText(round(x - 10), ruler_top + 12, str(marker_m))
        for boat in game.boats:
            x = 20 + (game.WIDTH - 40) * min(game.race_distance, boat.distance) / game.race_distance
            painter.setPen(QPen(QColor(boat.color), 2))
            painter.setBrush(QBrush(QColor(boat.color)))
            painter.drawEllipse(round(x - 5), ruler_top + 15, 10, 10)

        # 3..., 2..., 1... GO!
        if game.phase == game.Phase.PLAYING and not game.countdown_finished:
            count = 3 - int(game.countdown_elapsed)
            message = (
                str(clamp_to_min(count, 1))
                if game.countdown_elapsed < 3.0
                else get_text("GAME_GO")
            )
            painter.fillRect(0, top, game.WIDTH, course_height, QColor(0, 0, 0, 115))
            painter.setPen(QPen(QColor("#ffffff")))
            painter.setFont(QFont(GAME_FONT, 54, QFont.Weight.Bold))
            painter.drawText(0, top + 140, game.WIDTH, 100, Qt.AlignmentFlag.AlignCenter, message)

        painter.restore()

    # -------------------------------------------------------------------------
    # Ondulations animées de l'eau : anneaux discrets qui s'élargissent
    # autour d'un point, puis s'effacent avant le cycle suivant.
    def draw_ripple(
        self,
        painter: QPainter,
        cx: float, cy: float,
        phase: float,
        size: float = 1.0
    ) -> None:

        phase %= 1.0
        # Trois anneaux déphasés
        for ring_index, offset in enumerate((0.0, 0.34, 0.68)):
            progress = (phase + offset) % 1.0
            radius_x = (5.0 + progress * 22.0) * size
            radius_y = (2.0 + progress * 6.0) * size
            alpha = int(95 * (1.0 - progress) ** 0.8)
            if alpha <= 0:
                continue
            ripple_color = QColor(174, 239, 234, alpha)
            painter.setPen(QPen(ripple_color, 1.7 if ring_index == 0 else 1.3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), radius_x, radius_y)


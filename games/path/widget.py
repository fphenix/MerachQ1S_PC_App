"""Rendu en perspective du parcours à trois voies."""

import math

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QBrush, QPen, QPainter, QPolygonF, QFont

from setup.lang import get_text
from setup.constants import GAME_FONT

from games.pulsator import Pulsator
from games.game import Game

# =============================================================================
class PathWidget:

    PULSATOR = Pulsator(min_radius=3.0, max_radius=15.0, pen_width=2.0)

    # Le chemin commence exactement sur la ligne d’horizon du paysage.
    ROAD_TOP_Y = 265.0
    ROAD_BOTTOM_Y = 698.0
    HORIZON_X = 500.0

    # -------------------------------------------------------------------------
    def paint(self, painter: QPainter, game: Game) -> None:

        painter.save()

        # Sky and Ground
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(0, game.HUD_HEIGHT, game.WIDTH, game.HEIGHT - game.HUD_HEIGHT, QColor("#a8d4ec"))
        painter.fillRect(0, 265, game.WIDTH, game.HEIGHT - 265, QColor("#426d42"))

        # Soleil et collines en arrière-plan.
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.setBrush(QBrush(QColor("#f5d77a")))
        painter.drawEllipse(780, 105, 58, 58)
        painter.setBrush(QBrush(QColor("#6b9c67")))

        # Les montagnes reposent sur l’horizon (y=265) et leurs sommets
        # restent au-dessus : elles ne semblent plus flotter sous l’horizon.
        painter.drawPolygon(QPolygonF([QPointF(0, 265), QPointF(140, 165), QPointF(290, 265), QPointF(430, 185), QPointF(610, 265), QPointF(800, 175), QPointF(1000, 265)]))

        # Route
        top_y = self.ROAD_TOP_Y
        bottom_y = self.ROAD_BOTTOM_Y
        painter.setPen(QPen(QColor("#c8c0a6"), 2))
        painter.setBrush(QBrush(QColor("#77786e")))
        painter.drawPolygon(QPolygonF([
            QPointF(self.HORIZON_X - 25, top_y), QPointF(self.HORIZON_X + 25, top_y),
            QPointF(900, bottom_y), QPointF(100, bottom_y),
        ]))

        # Trois voies en perspective ; les segments verts montrent le chemin à suivre.
        lane_centers = []
        for lane in range(3):
            lane_centers.append(250 + lane * 250)
        for lane_x in (375, 625):
            painter.setPen(QPen(QColor("#d7d1bd"), 2, Qt.PenStyle.DashLine))
            painter.drawLine(round(self.HORIZON_X + (lane_x - 500) * 0.1), round(top_y), lane_x, round(bottom_y))

        # Chaque segment forme une portion de route reliant la voie précédente à la suivante.
        visible = sorted(game.segments, key=lambda segment: segment.distance, reverse=True)
        
        for index, segment in enumerate(visible):
            next_segment = visible[index - 1] if index > 0 else None
            near_dist = max(-500.0, min(1400.0, segment.distance))
            far_dist = max(-500.0, min(1400.0, segment.distance + game.SEGMENT_LENGTH))
            y_near = self._project_y(near_dist)
            y_far = self._project_y(far_dist)
            x_near = self._project_x(segment.lane, y_near)
            far_lane = next_segment.lane if next_segment is not None else segment.lane
            x_far = self._project_x(far_lane, y_far)
            width_near = self._project_width(y_near)
            width_far = self._project_width(y_far)
            color = QColor("#c7b88a") if segment.lane == 1 else QColor("#a8c58b")

            if segment.distance <= 0 and game.matching:
                color = QColor("#9ce27c")

            painter.setPen(QPen(color.darker(130), 1))
            painter.setBrush(QBrush(color))
            painter.drawPolygon(QPolygonF([
                QPointF(x_far - width_far / 2, y_far),
                QPointF(x_far + width_far / 2, y_far),
                QPointF(x_near + width_near / 2, y_near),
                QPointF(x_near - width_near / 2, y_near),
            ]))

        # Pulsateurs de cadence pour les trois voies.
        # lane, target_spm, center_x, text
        pulse_specs = (
            (0, game.CADENCE_LEFT, 350, get_text("GAME_PATH_LEFT")),
            (1, game.CADENCE_MIDDLE, 500, get_text("GAME_PATH_CENTER")),
            (2, game.CADENCE_RIGHT, 650, get_text("GAME_PATH_RIGHT"))
        )
        section_ahead = 3
        painter.setFont(QFont(GAME_FONT, 12, QFont.Weight.Bold))
        for lane, target, center_x, label in pulse_specs:
            pulse_color = (
                QColor("#27779c")
                if game.segments[section_ahead].lane == lane
                else QColor("#32134f")
            )
            self.PULSATOR.paint(painter, center_x, 500, game.elapsed, target, pulse_color)
            painter.drawText(
                round(center_x - 25), 475,
                label
            )
            painter.drawText(
                round(center_x - 25), 545,
                f"{int(target)} {get_text('SPM_UNIT')}"
            )

        # Position du joueur et indicateur de voie.
        player_x = lane_centers[game.player_lane] if game.player_lane is not None else 500
        run_bounce = 5.0 * math.sin(3.0 * math.pi * game.elapsed * 24.0 / 60.0)
        player_y = game.PLAYER_Y + run_bounce
        painter.setPen(QPen(QColor("#202d36"), 2))
        painter.setBrush(QBrush(QColor("#42d7f5" if game.matching else "#f0bd55")))
        painter.drawRoundedRect(round(player_x - 22), round(player_y - 38), 44, 30, 8, 8)
        painter.setBrush(QBrush(QColor("#d9f7ff")))
        painter.drawEllipse(round(player_x - 14), round(player_y - 54), 28, 23)

        # message de consigne
        painter.setFont(QFont(GAME_FONT, 22, QFont.Weight.Bold))
        painter.setPen(QPen(QColor("#32134f")))
        if game.player_lane is None:
            message = get_text("GAME_PATH_FIND_CADENCE")
        elif game.matching:
            message = get_text("GAME_PATH_ON_TRACK")
        else:
            lane_name = (
                get_text("GAME_PATH_LEFT"),
                get_text("GAME_PATH_CENTER"),
                get_text("GAME_PATH_RIGHT")
            )[game.segments[0].lane]
            message = get_text("GAME_PATH_MOVE_TO").format(lane=lane_name)
        painter.drawText(
            QRectF(40, game.HEIGHT - 52, game.WIDTH - 80, 34),
            Qt.AlignmentFlag.AlignCenter,
            message
        )
        
        painter.restore()

    # -------------------------------------------------------------------------
    def _project_y(self, distance: float) -> float:
        progress = max(0.0, min(1.4, 1.0 - distance / 1400.0))
        return self.ROAD_TOP_Y + (self.ROAD_BOTTOM_Y - self.ROAD_TOP_Y) * progress

    # -------------------------------------------------------------------------
    def _project_x(self, lane: int, y: float) -> float:
        progress = (y - self.ROAD_TOP_Y) / (self.ROAD_BOTTOM_Y - self.ROAD_TOP_Y)
        far_x = 500.0 + (lane - 1) * 22.0
        near_x = 500.0 + (lane - 1) * 250.0
        return far_x + (near_x - far_x) * progress

    # -------------------------------------------------------------------------
    def _project_width(self, y: float) -> float:
        progress = (y - self.ROAD_TOP_Y) / (self.ROAD_BOTTOM_Y - self.ROAD_TOP_Y)
        return 18.0 + 205.0 * max(0.0, min(1.0, progress))

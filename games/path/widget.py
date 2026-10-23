"""Rendu en perspective du parcours à trois voies."""

import math

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QColor, QBrush, QPen,
    QPainter, QPolygonF, QFont,
    QLinearGradient, QPainterPath,
)

from setup.lang import get_text
from setup.constants import GAME_FONT
from setup.utils import clamp_between

from games.game import Game
from games.game_painter import GamePainter
from games.pulsator import Pulsator

# =============================================================================
class PathWidget(GamePainter):

    PULSATOR = Pulsator(min_radius= 3.0, max_radius= 20.0, pen_width= 2.0)

    PLAYER_Y: float = 620.0

    ROAD_CENTER_X: float = 500.0
    ROAD_TOP_Y: float = 265.0
    ROAD_BOTTOM_Y: float = 699.0
    ROAD_TOP_WIDTH: float = 50.0
    ROAD_BOTTOM_WIDTH: float = 800.0
    ROAD_TOP_LEFT_X: float = ROAD_CENTER_X - ROAD_TOP_WIDTH / 2
    ROAD_TOP_RIGHT_X: float = ROAD_CENTER_X + ROAD_TOP_WIDTH / 2
    ROAD_BOTTOM_LEFT_X: float = ROAD_CENTER_X - ROAD_BOTTOM_WIDTH / 2
    ROAD_BOTTOM_RIGHT_X: float = ROAD_CENTER_X + ROAD_BOTTOM_WIDTH / 2

    ROAD_DEPTH: float = 1400.0
    ROAD_TOP_WIDTH_RATIO: float = ROAD_TOP_WIDTH / ROAD_BOTTOM_WIDTH
    ROAD_LANE_COUNT: int = 3
    BAND_OPACITY: float = 0.22

    SEGMENT_NEAR_LIMIT: float = -500.0
    SEGMENT_FAR_LIMIT: float = 1400.0
    SCENERY_NEAR_LIMIT: float = -100.0
    SCENERY_FAR_LIMIT: float = 1450.0

    # -------------------------------------------------------------------------
    def paint(self, painter: QPainter, game: Game) -> None:

        painter.save()

        self._draw_background(painter, game)

        lane_centers = self._draw_road(painter)

        self._draw_road_scenery(painter, game)

        self._draw_segments(painter, game)

        self._draw_road_bands(painter, game)

        self._draw_pulses(painter, game)

        self._draw_runner(painter, lane_centers, game)

        self._draw_messages(painter, game)

        painter.restore()

    # -------------------------------------------------------------------------
    def _draw_messages(self, painter: QPainter, game: Game) -> None:

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

    # -------------------------------------------------------------------------
    def _draw_pulses(self, painter: QPainter, game: Game) -> None:

        # Pulsateurs de cadence pour les trois voies.
        # lane, target_spm, center_x, text
        pulse_specs = (
            (0, game.CADENCE_LEFT, 350, get_text("GAME_PATH_LEFT")),
            (1, game.CADENCE_MIDDLE, 500, get_text("GAME_PATH_CENTER")),
            (2, game.CADENCE_RIGHT, 650, get_text("GAME_PATH_RIGHT"))
        )

        section_ahead = min(3, max(0, len(game.segments) - 1))
        painter.setFont(QFont(GAME_FONT, 12, QFont.Weight.Bold))
        for lane, target, center_x, label in pulse_specs:
            pulse_color = (
                QColor("#27779c")
                if game.segments and game.segments[section_ahead].lane == lane
                else QColor("#32134f")
            )
            self.PULSATOR.paint(painter, center_x, 500, game.elapsed, target, pulse_color)
            painter.setPen(pulse_color)
            painter.drawText(
                round(center_x - 25), 465,
                label
            )
            painter.drawText(
                round(center_x - 25), 545,
                f"{int(target)} {get_text('SPM_UNIT')}"
            )

    # -------------------------------------------------------------------------
    def _draw_segments(self, painter: QPainter, game: Game) -> None:

        # Chaque segment forme une portion de route lié au suivant pour
        # former le chemin à suivre
        visible = sorted(
            game.segments,
            key=lambda segment: segment.distance,
            reverse=True,
        )
        road_path = QPainterPath()
        road_path.addPolygon(self._road_polygon())

        painter.save()

        painter.setClipPath(road_path)

        for index, segment in enumerate(visible):
            farther = visible[index - 1] if index > 0 else None
            near_distance = max(0.0, segment.distance)
            far_distance = min(
                segment.distance + game.SEGMENT_LENGTH,
                self.SEGMENT_FAR_LIMIT,
            )
            if far_distance <= near_distance:
                continue

            y_near = self._project_y(near_distance)
            y_far = self._project_y(far_distance)
            far_lane = farther.lane if farther is not None else segment.lane
            left_near = self._lane_boundary(segment.lane, y_near)
            right_near = self._lane_boundary(segment.lane + 1, y_near)
            left_far = self._lane_boundary(far_lane, y_far)
            right_far = self._lane_boundary(far_lane + 1, y_far)
            color = QColor("#c7b88a") if segment.lane == 1 else QColor("#a8c58b")

            if segment.distance <= 0 and game.matching:
                color = QColor("#9ce27c")

            painter.setPen(QPen(color.darker(130), 1))
            painter.setBrush(QBrush(color))
            painter.drawPolygon(QPolygonF([
                QPointF(left_far, y_far),
                QPointF(right_far, y_far),
                QPointF(right_near, y_near),
                QPointF(left_near, y_near),
            ]))

        painter.restore()

    # -------------------------------------------------------------------------
    def _draw_road_bands(self, painter: QPainter, game: Game) -> None:
        """Dessine les bandes de route en perspective, synchronisées aux segments."""

        if not game.segments or game.SEGMENT_LENGTH <= 0:
            return

        road_path = QPainterPath()
        road_path.addPolygon(self._road_polygon())

        painter.save()
        
        painter.setClipPath(road_path)
        painter.setOpacity(self.BAND_OPACITY)
        length = game.SEGMENT_LENGTH
        # Dessiner une bande par intervalle de segment existant évite tout second
        # compteur temporel et tout reset de phase indépendant du moteur.
        ordered = sorted(game.segments, key=lambda item: item.distance)
        for segment in ordered:
            near_d = max(0.0, segment.distance)
            far_d = min(segment.distance + length, self.SEGMENT_FAR_LIMIT)
            if far_d <= near_d:
                continue

            y_near, y_far = self._project_y(near_d), self._project_y(far_d)
            world_index = round((segment.distance + game.elapsed * game.SCROLL_SPEED) / length)
            color = QColor("#606060" if world_index % 2 == 0 else "#909090")
            painter.setPen(QPen(color, 0.5))
            painter.setBrush(QBrush(color))
            painter.drawPolygon(QPolygonF([QPointF(self._road_left(y_far), y_far), QPointF(self._road_right(y_far), y_far), QPointF(self._road_right(y_near), y_near), QPointF(self._road_left(y_near), y_near)]))

        painter.restore()

        # Lignes pointillées de délimitation des voies
        painter.setPen(QPen(QColor("#D0CFD3"), 2, Qt.PenStyle.DashLine))
        for boundary in (1, 2):
            painter.drawLine(round(self._lane_boundary(boundary, self.ROAD_TOP_Y)), round(self.ROAD_TOP_Y), round(self._lane_boundary(boundary, self.ROAD_BOTTOM_Y)), round(self.ROAD_BOTTOM_Y))

    # -------------------------------------------------------------------------
    def _draw_road(self, painter: QPainter) -> list[float]:

        road = self._road_polygon()
        painter.setPen(QPen(QColor("#c8c0a6"), 2))
        painter.setBrush(QBrush(QColor("#77786e")))
        painter.drawPolygon(road)
        lane_centers = [self._lane_center(lane, self.ROAD_BOTTOM_Y - (self.ROAD_BOTTOM_Y - self.ROAD_TOP_Y) * 0.18) for lane in range(3)]
        return lane_centers

    # -------------------------------------------------------------------------
    def _road_polygon(self) -> QPolygonF:
        return QPolygonF([
            QPointF(self.ROAD_TOP_LEFT_X, self.ROAD_TOP_Y),
            QPointF(self.ROAD_TOP_RIGHT_X, self.ROAD_TOP_Y),
            QPointF(self.ROAD_BOTTOM_RIGHT_X, self.ROAD_BOTTOM_Y),
            QPointF(self.ROAD_BOTTOM_LEFT_X, self.ROAD_BOTTOM_Y),
        ])

    # -------------------------------------------------------------------------
    def _road_edges(self, y: float) -> tuple[float, float]:
        progress = clamp_between((y - self.ROAD_TOP_Y) / (self.ROAD_BOTTOM_Y - self.ROAD_TOP_Y), 0.0, 1.0)
        return (self.ROAD_TOP_LEFT_X + (self.ROAD_BOTTOM_LEFT_X - self.ROAD_TOP_LEFT_X) * progress, self.ROAD_TOP_RIGHT_X + (self.ROAD_BOTTOM_RIGHT_X - self.ROAD_TOP_RIGHT_X) * progress)

    # -------------------------------------------------------------------------
    def _road_left(self, y: float) -> float:
        return self._road_edges(y)[0]

    # -------------------------------------------------------------------------
    def _road_right(self, y: float) -> float:
        return self._road_edges(y)[1]

    # -------------------------------------------------------------------------
    def _lane_boundary(self, boundary: int, y: float) -> float:
        left, right = self._road_edges(y)
        return left + (right - left) * boundary / self.ROAD_LANE_COUNT

    # -------------------------------------------------------------------------
    def _lane_center(self, lane: int, y: float) -> float:
        return (self._lane_boundary(lane, y) + self._lane_boundary(lane + 1, y)) / 2.0

    # -------------------------------------------------------------------------
    def _player_projection_y(self) -> float:
        # Le personnage est en retrait du bord proche : sa position doit utiliser
        # exactement la même projection que les segments à cette hauteur.
        return self.PLAYER_Y

    # -------------------------------------------------------------------------
    def _draw_background(self, painter: QPainter, game: Game) -> None:

        # Ciel, dégradé de couleurs
        sky = QLinearGradient(0, game.HUD_HEIGHT, 0, 315)
        sky.setColorAt(0.0, QColor("#9bd5ee"))
        sky.setColorAt(0.6, QColor("#e2edc0"))
        sky.setColorAt(1.0, QColor("#ff6843"))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(0, game.HUD_HEIGHT, game.WIDTH, game.HEIGHT - game.HUD_HEIGHT, QBrush(sky))

        # Sol, dégradé de couleurs
        ground = QLinearGradient(0, self.ROAD_TOP_Y, 0, game.HEIGHT - game.HUD_HEIGHT)
        ground.setColorAt(0.0, QColor("#448644"))
        ground.setColorAt(1.0, QColor("#243524"))
        painter.fillRect(0, round(self.ROAD_TOP_Y), game.WIDTH, game.HEIGHT - round(self.ROAD_TOP_Y), QBrush(ground))

        # Soleil
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.setBrush(QBrush(QColor("#f5d77a")))
        painter.drawEllipse(780, 105, 58, 58)

        # Nuages
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.setBrush(QBrush(QColor("#eef7fb")))
        for cx, cy in ((145, 115), (390, 82), (675, 132)):
            painter.drawEllipse(cx, cy, 48, 20)
            painter.drawEllipse(cx + 13, cy - 10, 27, 27)
            painter.drawEllipse(cx + 29, cy - 4, 30, 23)

        # Collines et Montagnes
        painter.setBrush(QBrush(QColor("#5fa753")))
        painter.drawEllipse(-100, 215, 440, 135)
        painter.drawEllipse(600, 210, 520, 150)

        painter.drawPolygon(QPolygonF([
            QPointF(-80, 265), QPointF(140, 175), QPointF(330, 265),
            QPointF(430, 185), QPointF(610, 265), QPointF(800, 175),
            QPointF(1000, 265)
        ]))

        # Arbres stylisés au bord du paysage, derrière la route.
        self._draw_trees(painter)

    # -------------------------------------------------------------------------
    def _draw_road_scenery(self, painter: QPainter, game: Game) -> None:

        # Décor de bord de route : chaque objet avance à la vitesse de la route.
        # La projection l'agrandit progressivement en approchant du bas de l'écran.
        for item in sorted(game.scenery, key=lambda obj: obj.distance, reverse=True):
            if item.distance < self.SCENERY_NEAR_LIMIT or item.distance > self.SCENERY_FAR_LIMIT:
                continue

            y = self._project_y(item.distance)
            progress = clamp_between(
                (y - self.ROAD_TOP_Y) / (self.ROAD_BOTTOM_Y - self.ROAD_TOP_Y),
                0.0, 1.25,
            )
            scale = item.size * (0.12 + 1.05 * progress)
            road_edge = self.ROAD_CENTER_X + item.side * (self.ROAD_TOP_WIDTH / 2 + (self.ROAD_BOTTOM_WIDTH - self.ROAD_TOP_WIDTH) / 2 * progress)

            delta_x = item.delta_x * (0.25 + progress * 0.75)
            # Le centre de l’objet reste à l’extérieur du bord, avec une
            # marge visible qui augmente avec la taille apparente.
            x = road_edge + item.side * (game.OBJECTS_DELTA_X + (4.0 + delta_x) * progress)
            painter.setPen(QPen(QColor("#3b5137"), max(1, round(2 * scale))))

            # moving scenery items
            if item.kind == "tree":
                self._draw_road_trees(painter, x, y, scale)
            elif item.kind == "rock":
                self._draw_road_rocks(painter, x, y, scale)
            else:
                self._draw_road_bushes(painter, x, y, scale)

    # -------------------------------------------------------------------------
    def _draw_trees(self, painter: QPainter) -> None:

        painter.setPen(QPen(QColor("#3c6943"), 2))
        for tx, ty, scale in (
            (35, 230, 1.0), (100, 242, .75), (885, 230, 1.0),
            (950, 242, .75), (735, 236, .65)
        ):
            painter.setBrush(QBrush(QColor("#315f3c")))
            painter.drawEllipse(round(tx-17*scale), round(ty-42*scale), round(34*scale), round(43*scale))
            painter.setBrush(QBrush(QColor("#74563a")))
            painter.drawRect(round(tx-3*scale), round(ty-8*scale), round(6*scale), round(19*scale))

    # -------------------------------------------------------------------------
    def _draw_road_trees(
        self,
        painter: QPainter,
        x: float, y: float,
        scale: float
    ) -> None:

        trunk_w = max(2.0, 7.0 * scale)
        trunk_h = 25.0 * scale
        crown_w = 32.0 * scale
        crown_h = 42.0 * scale
        painter.setBrush(QBrush(QColor("#79553a")))
        painter.drawRect(QRectF(x-trunk_w/2,y-trunk_h,trunk_w,trunk_h))
        painter.setBrush(QBrush(QColor("#2d683d")))
        painter.drawEllipse(QRectF(x-crown_w/2,y-trunk_h-crown_h*.78,crown_w,crown_h))

    # -------------------------------------------------------------------------
    def _draw_road_rocks(
        self,
        painter: QPainter,
        x: float, y: float,
        scale: float
    ) -> None:

        painter.setBrush(QBrush(QColor("#777d78")))
        painter.drawPolygon(QPolygonF([
            QPointF(x - 17 * scale, y),
            QPointF(x - 11 * scale, y - 15 * scale),
            QPointF(x + 4 * scale, y - 21 * scale),
            QPointF(x + 18 * scale, y - 8 * scale),
            QPointF(x + 17 * scale, y),
        ]))

    # -------------------------------------------------------------------------
    def _draw_road_bushes(
        self,
        painter: QPainter,
        x: float, y: float,
        scale: float,
    ) -> None:

        radius=12.0*scale
        painter.setPen(QPen(QColor("#654a32"),max(1,round(1.5*scale))))
        painter.setBrush(QBrush(QColor("#79583a")))
        painter.drawRect(QRectF(x-2*scale,y-scale,4*scale,7*scale))
        painter.setPen(QPen(QColor("#315c36"),max(1,round(scale))))
        painter.setBrush(QBrush(QColor("#477d43")))
        painter.drawEllipse(QPointF(x,y-radius*.55),radius,radius*.70)
        painter.drawEllipse(QPointF(x-radius*.55,y-radius*.32),radius*.72,radius*.62)
        painter.drawEllipse(QPointF(x+radius*.55,y-radius*.32),radius*.72,radius*.62)

    # -------------------------------------------------------------------------
    def _draw_runner(
        self,
        painter: QPainter,
        lane_centers: list[float],
        game: Game
    ) -> None:

        lane = game.player_lane if game.player_lane is not None else 1
        player_x = lane_centers[lane]

        run_bounce = 5.0 * math.sin(3.0 * math.pi * game.elapsed * 24.0 / 60.0)
        player_y = self.PLAYER_Y + run_bounce

        painter.setPen(QPen(QColor("#202d36"), 2))
        painter.setBrush(QBrush(QColor("#42d7f5" if game.matching else "#f0bd55")))
        painter.drawRoundedRect(round(player_x - 22), round(player_y - 38), 44, 30, 8, 8)
        painter.setBrush(QBrush(QColor("#d9f7ff")))
        painter.drawEllipse(round(player_x - 14), round(player_y - 54), 28, 23)

    # -------------------------------------------------------------------------
    def _project_y(self, distance: float) -> float:
        progress = clamp_between(1.0 - distance / self.ROAD_DEPTH, 0.0, 1.4)
        return self.ROAD_TOP_Y + (self.ROAD_BOTTOM_Y - self.ROAD_TOP_Y) * progress

"""Rendu rétro en perspective d'un couloir de donjon."""

import math
import time

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QColor, QBrush, QPen,
    QPainter, QPolygonF, QPainterPath,
    QLinearGradient, QRadialGradient,
    QFont,
)

from setup.constants import GAME_FONT
from setup.lang import get_text
from setup.utils import (
    clamp_to_zero, clamp_to_max, clamp_to_min,
    clamp_between, is_between,
    interpolate_color, log_norm
)

from games.game import Game
from games.game_painter import GamePainter
from games.pulsator import Pulsator

# =============================================================================
class DoomWidget(GamePainter):

    PULSATOR: Pulsator = Pulsator(min_radius= 3, max_radius= 22, pen_width= 2, outlined= True)

    CENTER_X: int = 500
    HORIZON_Y: int = 225
    HUD_TOP: int = 570
    WALL_TOP_HALF: int = 78
    WALL_BOTTOM_HALF: int = 465
    WALL_COURSES: int = 4

    # -------------------------------------------------------------------------
    def paint(self, painter: QPainter, game: Game) -> None:

        painter.save()

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self._draw_world(painter, game)
        self._draw_enemy(painter, game)
        self._draw_weapon(painter, game)
        # Doom a son propre HUD, mais en bas (un Heads-Down Display, donc :-) )
        self._draw_bottom_hud(painter, game)
        if game.hit_flash > 0:
            painter.fillRect(
                QRectF(0, 0, game.WIDTH, self.HUD_TOP),
                QColor(180, 20, 20, 48)
            )

        painter.restore()

    # -------------------------------------------------------------------------
    def _draw_world(self, painter: QPainter, game: Game) -> None:

        width = float(game.WIDTH)
        bottom = float(self.HUD_TOP)
        horizon = float(self.HORIZON_Y)
        center = float(self.CENTER_X)
        room_open = game.room_open and game.phase_name == game.GamePhase.EXPLORE
        room_progress = game.room_progress
        room_fade = min(room_progress / 0.22, (1.0 - room_progress) / 0.22, 1.0)
        room_fade = clamp_to_zero(room_fade)
        room_fade = room_fade * room_fade * (3.0 - 2.0 * room_fade)
        room = room_open and room_fade > 0.0
        turn = (
            game.turn_progress
            if game.phase_name == game.GamePhase.EXPLORE
            else 0.0
        )
        turn_direction = game.turn_direction
        world_distance = game.world_distance
        floor_scroll = world_distance * 0.32
        ceiling_scroll = -world_distance * 0.32
        floor_scroll_index = math.floor(floor_scroll)
        ceiling_scroll_index = math.floor(ceiling_scroll)
        floor_scroll_phase = floor_scroll % 1.0
        ceiling_scroll_phase = ceiling_scroll % 1.0
        raw_turn = clamp_between(turn, 0.0, 1.0)
        turn = raw_turn * raw_turn * (3.0 - 2.0 * raw_turn)

        # Grande ouverture rectangulaire au fond du couloir.
        opening_half = 112.0 + (33.0 * room_fade if room else 0.0)
        opening_shift = turn_direction * 125.0 * turn
        opening_left = center - opening_half + opening_shift
        opening_right = center + opening_half + opening_shift
        opening_top = 105.0 + 18.0 * turn
        opening_bottom = horizon + 35.0
        if turn > 0.55:
            opening_left -= 35.0 * (turn - 0.55) / 0.45 * turn_direction
            opening_right -= 35.0 * (turn - 0.55) / 0.45 * turn_direction
        floor_opening_shift = (opening_left + opening_right) * 0.5 - center
        painter.fillRect(QRectF(0, 0, width, game.HEIGHT), QColor("#111319"))

        # Plafond
        painter.setPen(QPen(QColor("#171a20"), 4))
        painter.setBrush(QBrush(QColor("#383b40")))
        painter.drawPolygon(QPolygonF([
            QPointF(0, 0), QPointF(width, 0),
            QPointF(opening_right, opening_top),
            QPointF(opening_left, opening_top),
        ]))

        # Mur gauche et mur droit
        painter.setPen(QPen(QColor("#211f20"), 4))
        painter.setBrush(QBrush(QColor("#75604b")))
        painter.drawPolygon(QPolygonF([
            QPointF(0, 0), QPointF(opening_left, opening_top),
            QPointF(opening_left, opening_bottom), QPointF(0, bottom),
        ]))
        painter.setBrush(QBrush(QColor("#66513f")))
        painter.drawPolygon(QPolygonF([
            QPointF(width, 0), QPointF(opening_right, opening_top),
            QPointF(opening_right, opening_bottom), QPointF(width, bottom),
        ]))

        # Sol
        painter.setPen(QPen(QColor("#1c1b1c"), 4))
        painter.setBrush(QBrush(QColor("#37332e")))
        painter.drawPolygon(QPolygonF([
            QPointF(0, bottom), QPointF(opening_left, opening_bottom),
            QPointF(opening_right, opening_bottom), QPointF(width, bottom),
        ]))

        # Couloir
        painter.setPen(QPen(QColor("#18191d"), 4))
        painter.setBrush(QBrush(QColor("#17191e")))
        painter.drawRect(QRectF(
            opening_left, opening_top,
            opening_right - opening_left, opening_bottom - opening_top,
        ))

        # Murs de pierre
        wall_scroll = world_distance * 0.075
        self._draw_stone_wall(
            painter, side=-1, width=width, bottom=bottom,
            opening_left=opening_left, opening_right=opening_right,
            opening_top=opening_top, opening_bottom=opening_bottom,
            wall_scroll=wall_scroll,
        )
        self._draw_stone_wall(
            painter, side=1, width=width, bottom=bottom,
            opening_left=opening_left, opening_right=opening_right,
            opening_top=opening_top, opening_bottom=opening_bottom,
            wall_scroll=wall_scroll,
        )

        # Texture perspective du plafond
        painter.save()

        ceiling_path = QPainterPath()
        ceiling_path.addPolygon(QPolygonF([
            QPointF(0, 0), QPointF(width, 0),
            QPointF(opening_right, opening_top),
            QPointF(opening_left, opening_top),
        ]))
        painter.setClipPath(ceiling_path)
        ceiling_stones = (QColor("#39352f"), QColor("#302d29"), QColor("#403a32"))
        ceiling_mortar = QColor("#121419")
        painter.setPen(QPen(ceiling_mortar, 1.5))
        rows = 8
        columns = 8
        # Même phase de défilement que les rangées du sol
        for row in range(-1, rows):
            t0_linear = (row + ceiling_scroll_phase) / rows
            t1_linear = (row + 1 + ceiling_scroll_phase) / rows
            if t1_linear <= 0.0 or t0_linear >= 1.0:
                continue
            t0 = clamp_to_min(t0_linear, 0.0) ** 2.0
            t1 = clamp_to_max(t1_linear, 1.0) ** 2.0
            y0 = opening_top * t0
            y1 = opening_top * t1
            half0 = width / 2.0 + (opening_half - width / 2.0) * t0
            half1 = width / 2.0 + (opening_half - width / 2.0) * t1
            shift0 = opening_shift * t0
            shift1 = opening_shift * t1
            for col in range(columns):
                a = col / columns
                b = (col + 1) / columns
                if (row - ceiling_scroll_index) % 2:
                    a = clamp_to_min(a - 0.5 / columns, 0.0)
                    b = clamp_to_max(b - 0.5 / columns, 1.0)
                poly = QPolygonF([
                    QPointF(center - half0 + 2 * half0 * a + shift0, y0),
                    QPointF(center - half0 + 2 * half0 * b + shift0, y0),
                    QPointF(center - half1 + 2 * half1 * b + shift1, y1),
                    QPointF(center - half1 + 2 * half1 * a + shift1, y1),
                ])
                stone_row = row - ceiling_scroll_index
                painter.setBrush(QBrush(ceiling_stones[(stone_row + col) % len(ceiling_stones)]))
                painter.drawPolygon(poly)
 
        painter.restore()

        # Dalles du sol : le clipping empêche les joints de dépasser du polygone,
        # notamment lorsque le couloir tourne et que l'ouverture est décalée.
        painter.save()

        floor_path = QPainterPath()
        floor_path.addPolygon(QPolygonF([
            QPointF(0, bottom), QPointF(opening_left, opening_bottom),
            QPointF(opening_right, opening_bottom), QPointF(width, bottom),
        ]))
        painter.setClipPath(floor_path)

        # Dallage en pierres
        floor_stones = (QColor("#41434a"), QColor("#4a4b50"), QColor("#383a40"))
        floor_rows = 8
        floor_columns = 8
        for row in range(-1, floor_rows):
            t0_linear = (row + floor_scroll_phase) / floor_rows
            t1_linear = (row + 1 + floor_scroll_phase) / floor_rows
            if t1_linear <= 0.0 or t0_linear >= 1.0:
                continue
            t0 = clamp_to_min(t0_linear, 0.0) ** 2
            t1 = clamp_to_max(t1_linear, 1.0) ** 2
            y0 = opening_bottom + (bottom - opening_bottom) * t0
            y1 = opening_bottom + (bottom - opening_bottom) * t1
            half0 = (width / 2.0) * t0 + opening_half * (1.0 - t0)
            half1 = (width / 2.0) * t1 + opening_half * (1.0 - t1)
            shift0 = floor_opening_shift * (1.0 - t0)
            shift1 = floor_opening_shift * (1.0 - t1)
            for col in range(floor_columns):
                a = col / floor_columns
                b = (col + 1) / floor_columns
                if (row - floor_scroll_index) % 2:
                    a = clamp_to_min(a - 0.5 / floor_columns, 0.0)
                    b = clamp_to_min(b - 0.5 / floor_columns, a + 0.001)
                poly = QPolygonF([
                    QPointF(center - half0 + 2 * half0 * a + shift0, y0),
                    QPointF(center - half0 + 2 * half0 * b + shift0, y0),
                    QPointF(center - half1 + 2 * half1 * b + shift1, y1),
                    QPointF(center - half1 + 2 * half1 * a + shift1, y1),
                ])
                painter.setPen(QPen(QColor("#24211e"), 1.2))
                stone_row = row - floor_scroll_index
                painter.setBrush(QBrush(floor_stones[(stone_row + col) % len(floor_stones)]))
                painter.drawPolygon(poly)

        painter.setPen(QPen(QColor("#51483d"), 2))
        for row in range(1, 9):
            t = ((row + floor_scroll_phase) / 8.0) ** 2
            if t >= 1.0:
                continue
            y = opening_bottom + (bottom - opening_bottom) * t
            half = (width / 2.0) * t + opening_half * (1.0 - t)
            shift = floor_opening_shift * (1.0 - t)
            painter.drawLine(
                round(center - half + shift), round(y),
                round(center + half + shift), round(y),
            )

        painter.restore()

        # Taches de sang, lichen et infiltrations sur les dalles
        painter.save()

        painter.setClipPath(floor_path)
        painter.setPen(Qt.PenStyle.NoPen)

        stain_palette = (
            (QColor(91, 25, 27, 125), QColor(66, 17, 21, 105)),   # sang séché
            (QColor(57, 82, 45, 118), QColor(40, 61, 35, 100)),   # lichen
            (QColor(91, 72, 49, 115), QColor(62, 49, 37, 100)),   # terre
            (QColor(61, 65, 69, 125), QColor(39, 42, 56, 105)),   # humidité
            (QColor(104, 91, 61, 105), QColor(75, 64, 45, 90)),   # usure
        )

        def stain_noise(seed: int) -> float:
            # Bruit déterministe : pas de scintillement d'une frame à l'autre.
            value = math.sin(seed * 127.1 + 311.7) * 43758.5453
            return value - math.floor(value)

        for row in range(-1, floor_rows):
            t0 = (row + floor_scroll_phase) / floor_rows
            t1 = (row + 1 + floor_scroll_phase) / floor_rows
            if t1 <= 0.0 or t0 >= 1.0:
                continue
            t = clamp_between((t0 + t1) * 0.5, 0.0, 1.0)
            if t < 0.015:
                continue

            half = (width / 2.0) * t + opening_half * (1.0 - t)
            shift = floor_opening_shift * (1.0 - t)
            world_row = row - floor_scroll_index

            for col in range(floor_columns):
                seed = world_row * 97 + col * 31 + 17
                # Environ une dalle sur trois porte une tache; la distribution
                # est stable mais évite un motif régulier ou uniquement rouge.
                if stain_noise(seed) > 0.36:
                    continue

                jitter = (stain_noise(seed + 5) - 0.5) * 0.36
                fraction = (col + 0.5 - (0.5 if world_row % 2 else 0.0)) / floor_columns
                fraction = clamp_between(fraction + jitter / floor_columns, 0.035, 0.965)
                x = center + shift + (2.0 * fraction - 1.0) * half
                y = opening_bottom + (bottom - opening_bottom) * t

                tile_width = (2.0 * half) / floor_columns
                stain_w = clamp_to_min(tile_width * (0.34 + stain_noise(seed + 9) * 0.42), 10.0)
                stain_h = clamp_to_min(stain_w * (0.44 + stain_noise(seed + 13) * 0.40), 8.0)
                palette = stain_palette[min(len(stain_palette) - 1, int(stain_noise(seed + 21) * len(stain_palette)))]
                angle = (stain_noise(seed + 29) - 0.5) * stain_w * 0.5

                painter.setBrush(QBrush(palette[0]))
                painter.drawEllipse(QRectF(
                    x - stain_w * 0.5, y - stain_h * 0.5,
                    stain_w, stain_h,
                ))
                # Deux petites extensions donnent une silhouette irrégulière
                # sans créer des détails trop géométriques.
                painter.setBrush(QBrush(palette[1]))
                painter.drawEllipse(QRectF(
                    x - stain_w * 0.24 + angle, y - stain_h * 0.16,
                    stain_w * (0.42 + stain_noise(seed + 37) * 0.30),
                    stain_h * 0.72,
                ))
                if stain_noise(seed + 41) > 0.45:
                    painter.drawEllipse(QRectF(
                        x + stain_w * 0.12, y + stain_h * 0.08,
                        stain_w * 0.30, stain_h * 0.42,
                    ))

        painter.restore()

        # Restes des monstres
        self._draw_blood_decals(
            painter, game, center, opening_bottom, bottom, floor_opening_shift
        )

        # Assombrissement en hauteur (torches éclairent le plafond)
        depth_fog = QLinearGradient(0, 0, 0, bottom)
        depth_fog.setColorAt(0.0, QColor(25, 0, 0, 28))
        depth_fog.setColorAt(clamp_to_min(opening_top / bottom, 0.01), QColor(64, 0, 0, 48))
        depth_fog.setColorAt(0.55, QColor(0, 0, 0, 105))
        depth_fog.setColorAt(1.0, QColor(0, 0, 0, 145))
        painter.fillRect(QRectF(0, 0, width, bottom), QBrush(depth_fog))

        # Assombrissement radial : le fond du couloir est plus sombre au centre,
        # tandis que les bords de l'écran restent plus lisibles.
        radial_center_x = center + opening_shift
        radial_center_y = opening_top + 12.0
        radial_radius = math.hypot(width * 0.54, bottom * 0.62)
        radial_fog = QRadialGradient(radial_center_x, radial_center_y, radial_radius)
        radial_fog.setColorAt(0.0, QColor(0, 0, 0, 165))
        radial_fog.setColorAt(0.16, QColor(0, 0, 0, 125))
        radial_fog.setColorAt(0.38, QColor(0, 0, 0, 72))
        radial_fog.setColorAt(0.68, QColor(0, 0, 0, 22))
        radial_fog.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(QRectF(0, 0, width, bottom), QBrush(radial_fog))

        # Torches
        painter.setPen(Qt.PenStyle.NoPen)
        for side in (-1, 1):
            for torch_index in range(3):
                travel = (world_distance * 0.055 + torch_index / 3.0) % 1.0
                # Le retour modulo 1.0 téléportait une torche du premier plan
                # vers le fond. La masquer près des deux extrémités rend la
                # boucle invisible sans modifier la vitesse de déplacement.
                if travel < 0.055 or travel > 0.945:
                    continue

                t = 0.08 + travel * travel * 0.84
                x = opening_left * (1.0 - t) if side < 0 else width - (width - opening_right) * (1.0 - t)
                x += 18 if side < 0 else -18
                y = 125.0 + 12.0 * (1.0 - t) + 8.0 * turn
                scale = (0.55 + t * 0.85) * 1.28
                glow = 17.0 * scale
                painter.setBrush(QBrush(QColor(190, 70, 24, 55)))
                painter.drawEllipse(QRectF(x - glow, y - glow, glow * 2, glow * 2.3))
                painter.setBrush(QBrush(QColor("#8f351c")))
                painter.drawEllipse(QRectF(x - 5 * scale, y - 7 * scale, 10 * scale, 17 * scale))
                painter.setBrush(QBrush(QColor("#ffd06a")))
                painter.drawEllipse(QRectF(x - 2 * scale, y - 8 * scale, 4 * scale, 11 * scale))

        # Chandelier
        chandelier_cycle = int(world_distance // 55.0)
        if chandelier_cycle % 3 == 1:
            chandelier_phase = (world_distance % 55.0) / 55.0
            if chandelier_phase < 0.94:
                approach = chandelier_phase / 0.94
                depth = approach * approach
                # Sur le plafond, un objet qui approche remonte vers le bord
                # supérieur de l'image tout en grossissant.
                chandelier_y = opening_top * (1.0 - depth) - 28.0 * depth
                chandelier_x = center + opening_shift * (1.0 - depth)
                chandelier_scale = (0.38 + 1.65 * depth) * 1.22
                painter.setPen(QPen(QColor("#302b27"), clamp_to_min(round(3 * chandelier_scale), 1)))
                painter.drawLine(round(chandelier_x), 0, round(chandelier_x), round(chandelier_y))
                painter.setBrush(QBrush(QColor("#8b714b")))
                painter.drawEllipse(QRectF(
                    chandelier_x - 24 * chandelier_scale,
                    chandelier_y - 4 * chandelier_scale,
                    48 * chandelier_scale, 9 * chandelier_scale,
                ))
                painter.setBrush(QBrush(QColor("#ffc75b")))
                for candle_side in (-1, 0, 1):
                    candle_x = chandelier_x + candle_side * 13 * chandelier_scale
                    painter.drawEllipse(QRectF(
                        candle_x - 3 * chandelier_scale,
                        chandelier_y - 13 * chandelier_scale,
                        6 * chandelier_scale, 10 * chandelier_scale,
                    ))

    # -------------------------------------------------------------------------
    def _wall_point(
        self, side: int, u: float, v: float, width: float, bottom: float,
        opening_left: float, opening_right: float,
        opening_top: float, opening_bottom: float,
    ) -> QPointF:
        """Projette un point (profondeur u, hauteur v) sur un mur latéral."""

        outer_x = 0.0 if side < 0 else width
        inner_x = opening_left if side < 0 else opening_right
        x = outer_x + (inner_x - outer_x) * u
        top_y = opening_top * u
        bottom_y = bottom + (opening_bottom - bottom) * u
        y = top_y + (bottom_y - top_y) * v

        return QPointF(x, y)

    # -------------------------------------------------------------------------
    def _draw_stone_wall(
        self, painter: QPainter, side: int, width: float, bottom: float,
        opening_left: float, opening_right: float,
        opening_top: float, opening_bottom: float, wall_scroll: float,
    ) -> None:

        courses = clamp_to_min(self.WALL_COURSES, 2)
        rows = [index / courses for index in range(courses + 1)]
        brick_step = 0.235
        mortar = QColor("#493a2e")
        stones = (QColor("#78624d"), QColor("#705a46"), QColor("#806a53"))

        painter.save()

        wall_clip = QPainterPath()
        if side < 0:
            wall_clip.addPolygon(QPolygonF([
                QPointF(0, 0), QPointF(opening_left, opening_top),
                QPointF(opening_left, opening_bottom), QPointF(0, bottom),
            ]))
        else:
            wall_clip.addPolygon(QPolygonF([
                QPointF(width, 0), QPointF(opening_right, opening_top),
                QPointF(opening_right, opening_bottom), QPointF(width, bottom),
            ]))
        painter.setClipPath(wall_clip)
        painter.setPen(QPen(mortar, 1.4))
        for row in range(courses):
            v0, v1 = rows[row], rows[row + 1]
            stagger = 0.5 if row % 2 else 0.0
            phase = (wall_scroll + stagger * brick_step) % brick_step
            joints = [0.0]
            joint = brick_step - phase
            while joint < 1.0:
                if joint > 0.015:
                    joints.append(joint)
                joint += brick_step
            joints.append(1.0)
            for column in range(len(joints) - 1):
                u0, u1 = joints[column], joints[column + 1]
                polygon = QPolygonF([
                    self._wall_point(side, u0, v0, width, bottom, opening_left, opening_right, opening_top, opening_bottom),
                    self._wall_point(side, u1, v0, width, bottom, opening_left, opening_right, opening_top, opening_bottom),
                    self._wall_point(side, u1, v1, width, bottom, opening_left, opening_right, opening_top, opening_bottom),
                    self._wall_point(side, u0, v1, width, bottom, opening_left, opening_right, opening_top, opening_bottom),
                ])

                u_mid = (u0 + u1) * 0.5
                texture_position = u_mid + wall_scroll + stagger * brick_step
                stone_index = math.floor(texture_position / brick_step) + row
                painter.setBrush(QBrush(stones[stone_index % len(stones)]))
                painter.drawPolygon(polygon)

                # Décor attaché aux pierres : il défile avec la texture du mur.
                stain_seed = (stone_index * 13 + row * 7 + (0 if side < 0 else 5)) % 23
                if stain_seed in (2, 7, 13):
                    world_cell = stone_index - row
                    stain_u = (world_cell + 0.5) * brick_step - wall_scroll - stagger * brick_step
                    if 0.08 <= stain_u <= 0.92:
                        stain_v = v0 + (v1 - v0) * (0.34 + (stain_seed % 3) * 0.08)
                        stain_pt = self._wall_point(
                            side, stain_u, stain_v, width, bottom,
                            opening_left, opening_right, opening_top, opening_bottom,
                        )
                        left_pt = self._wall_point(
                            side, clamp_to_min(stain_u - brick_step * 0.19, 0.0), stain_v,
                            width, bottom, opening_left, opening_right, opening_top, opening_bottom,
                        )
                        right_pt = self._wall_point(
                            side, clamp_to_max(stain_u + brick_step * 0.19, 1.0), stain_v,
                            width, bottom, opening_left, opening_right, opening_top, opening_bottom,
                        )
                        stain_w = clamp_to_min(abs(right_pt.x() - left_pt.x()) * 0.5, 4.0)
                        row_height = abs(self._wall_point(
                            side, stain_u, v1, width, bottom, opening_left,
                            opening_right, opening_top, opening_bottom,
                        ).y() - self._wall_point(
                            side, stain_u, v0, width, bottom, opening_left,
                            opening_right, opening_top, opening_bottom,
                        ).y())
                        stain_h = clamp_to_min(row_height * 0.78, 8.0)
                        painter.save()
                        painter.setPen(Qt.PenStyle.NoPen)
                        if stain_seed == 7:
                            # Lichen : plaque irrégulière plus large que haute.
                            painter.setBrush(QBrush(QColor(55, 88, 45, 205)))
                            painter.drawEllipse(QRectF(
                                stain_pt.x() - stain_w * 1.15,
                                stain_pt.y() - stain_h * 0.35,
                                stain_w * 2.3, stain_h * 0.72,
                            ))
                            painter.setBrush(QBrush(QColor(77, 105, 55, 150)))
                            painter.drawEllipse(QRectF(
                                stain_pt.x() - stain_w * 0.55,
                                stain_pt.y() - stain_h * 0.28,
                                stain_w * 0.9, stain_h * 0.32,
                            ))
                        elif stain_seed == 13:
                            # Infiltration : coulure gris-brun, plus haute.
                            painter.setBrush(QBrush(QColor(75, 73, 67, 190)))
                            painter.drawRoundedRect(QRectF(
                                stain_pt.x() - stain_w * 0.75,
                                stain_pt.y() - stain_h * 0.55,
                                stain_w * 1.5, stain_h * 1.1,
                            ), stain_w * 0.45, stain_w * 0.45)
                            painter.drawEllipse(QRectF(
                                stain_pt.x() - stain_w * 0.25,
                                stain_pt.y() + stain_h * 0.25,
                                stain_w * 0.5, stain_h * 0.42,
                            ))
                        else:
                            # Sang séché : grosse tache de peinture irrégulière
                            # et coulures gravitationnelles, sans petits points.
                            painter.setBrush(QBrush(QColor(91, 15, 22, 220)))
                            painter.drawEllipse(QRectF(
                                stain_pt.x() - stain_w * 1.05,
                                stain_pt.y() - stain_h * 0.45,
                                stain_w * 2.1, stain_h * 0.78,
                            ))
                            painter.drawRoundedRect(QRectF(
                                stain_pt.x() - stain_w * 0.52,
                                stain_pt.y() + stain_h * 0.02,
                                stain_w * 0.56, stain_h * 0.72,
                            ), stain_w * 0.22, stain_w * 0.22)
                            painter.drawRoundedRect(QRectF(
                                stain_pt.x() + stain_w * 0.25,
                                stain_pt.y() + stain_h * 0.08,
                                stain_w * 0.36, stain_h * 0.46,
                            ), stain_w * 0.16, stain_w * 0.16)
                        painter.restore()

        painter.restore()

    # -------------------------------------------------------------------------
    def _draw_enemy(self, painter: QPainter, game: Game) -> None:
        """Dessine des silhouettes distinctes : Pinky/Bull Demon et Cyberdemon."""

        # Le moteur retire immédiatement un monstre mort de game.enemies.
        # On conserve sa dernière position dessinée pour afficher l'explosion.
        if not hasattr(self, "_doom_last_kills"):
            self._doom_last_kills = game.kills
            self._doom_last_enemy = None
            self._doom_explosion = None
            self._doom_blood_decals = []

        if game.kills > self._doom_last_kills:
            if self._doom_last_enemy is not None:
                ex, ey, escale, side, approach = self._doom_last_enemy
                now = time.monotonic()
                self._doom_explosion = (ex, ey, escale, now)
                # Ancrer les restes au sol à la profondeur correspondant aux
                # pieds du monstre, pas à son centre ni à une profondeur arbitraire.
                # La perspective du sol va de l'ouverture au bas de la scène.
                floor_opening = float(self.HORIZON_Y + 35)
                floor_bottom = float(self.HUD_TOP)
                feet_y = ey + 59.0 * escale
                floor_t = clamp_between(
                    (feet_y - floor_opening) / clamp_to_min(floor_bottom - floor_opening, 1.0),
                    0.025, 0.88,
                )
                # La trace reste à cette position du monde, défile vers le joueur
                # avec l'avancée du couloir et disparaît une fois dépassée.
                span = clamp_to_min((1.0 - floor_t) * 9.0, 2.5)
                self._doom_blood_decals.append((
                    float(game.world_distance), span,
                    floor_t, side, escale, game.kills * 37 + 11,
                ))
                self._doom_blood_decals = self._doom_blood_decals[-24:]
            self._doom_last_enemy = None
        self._doom_last_kills = game.kills
        self._draw_death_explosion(painter)

        if game.phase_name == game.GamePhase.BOSSFIGHT:
            self._draw_boss(painter, game)

        enemies = game.enemies
        if not enemies:
            return

        enemy = enemies[0]
        approach: float = clamp_between(enemy.approach_progress, 0.0, 1.0)
        breathing = math.sin(game.elapsed * 3.2) * (1.0 + 1.5 * approach)
        is_cyber: bool = (enemy.kind == game.MonsterType.CYBER)
        armored = enemy.armored
        use_old_skin = enemy.old_skin
        x = self.CENTER_X + enemy.side * (18 + 54 * approach)
        y = self.HORIZON_Y + 30 + 107 * approach + breathing
        scale = (0.24 + 0.94 * approach) * (1.34 if is_cyber else 1.12)

        # Mémorise la position du monstre afin de connaitre sa dernière
        # position quand il meurt (pour y générer l'explosion)
        self._doom_last_enemy = (x, y, scale, enemy.side, approach)

        painter.save()

        if is_cyber:
            self._draw_enemy_cyber(painter, game, x, y, scale, armored)
        else:
            if use_old_skin:
                self._draw_enemy_OLD(painter, game, x, y, scale, armored)
            else:
                self._draw_enemy_bull(painter, game, x, y, scale)

        # Les impacts restent sur le haut du corps, jamais sur les yeux.
        painter.setPen(Qt.PenStyle.NoPen)
        blood_spots = clamp_to_max(enemy.blood * 2, 7)
        for i in range(blood_spots):
            painter.setBrush(QBrush(QColor(150, 15, 22, 220)))
            if is_cyber or use_old_skin:
                # Cyberdemon : plastron, sous la tête et au-dessus du ventre.
                spot_x = x - 22*scale + (i % 4)*13*scale
                spot_y = y - 10*scale + (i // 4)*12*scale
            else:
                # Pinky : épaules et partie haute du torse, sous les yeux.
                spot_x = x - 22*scale + (i % 4)*12*scale
                spot_y = y - 34*scale + (i // 4)*11*scale
            painter.drawEllipse(QRectF(spot_x, spot_y, 5*scale, 7*scale))

        painter.restore()

    # -------------------------------------------------------------------------
    def _draw_enemy_bull(
        self,
        painter: QPainter,
        game: Game,
        x: float, y: float,
        scale: float
    ) -> None:

        # Pinky, Bulldemon
        hide = QColor("#9d514f")
        muscle = QColor("#ad564f")
        shadow = QColor("#713a3c")
        outline = QColor("#211a1c")

        painter.setPen(QPen(outline, clamp_to_min(3.0 * scale, 1.0)))
        # Corps
        painter.setBrush(QBrush(hide))
        painter.drawRoundedRect(QRectF(x - 38*scale, y - 43*scale,
                                76*scale, 76*scale), 17*scale, 17*scale)
        painter.setBrush(QBrush(muscle))
        painter.drawRoundedRect(QRectF(x - 32*scale, y - 39*scale,
                                64*scale, 43*scale), 15*scale, 15*scale)
        painter.setBrush(QBrush(shadow))
        painter.drawRoundedRect(QRectF(x - 25*scale, y - 8*scale,
                                50*scale, 34*scale), 10*scale, 10*scale)
        # Bras
        painter.setPen(QPen(muscle, clamp_to_min(15.0*scale, 7.0),
                       Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(round(x-31*scale), round(y-24*scale),
                        round(x-48*scale), round(y+5*scale))
        painter.drawLine(round(x+31*scale), round(y-24*scale),
                        round(x+48*scale), round(y+5*scale))
        painter.setPen(QPen(shadow, clamp_to_min(3.0 * scale, 1.0)))
        painter.setBrush(QBrush(muscle))
        painter.drawEllipse(QRectF(x-52*scale, y-1*scale, 17*scale, 35*scale))
        painter.drawEllipse(QRectF(x+35*scale, y-1*scale, 17*scale, 35*scale))

        # Tête
        head = QRectF(x-24*scale, y-13*scale, 48*scale, 48*scale)
        painter.setPen(QPen(outline, clamp_to_min(2.5*scale, 1.0)))
        painter.setBrush(QBrush(hide))
        painter.drawRoundedRect(head, 10*scale, 10*scale)

        # Cornes
        horn_pen = QPen(QColor("#e0d0ad"), clamp_to_min(6.0*scale, 2.0),
                        Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(horn_pen)
        left_horn = QPainterPath(QPointF(x-15*scale, y-9*scale))
        left_horn.cubicTo(x-35*scale, y-28*scale, x-38*scale, y-7*scale,
                        x-25*scale, y-2*scale)
        right_horn = QPainterPath(QPointF(x+15*scale, y-9*scale))
        right_horn.cubicTo(x+35*scale, y-28*scale, x+38*scale, y-7*scale,
                           x+25*scale, y-2*scale)
        painter.drawPath(left_horn)
        painter.drawPath(right_horn)

        # Yeux, museau et bouche
        painter.setPen(Qt.PenStyle.NoPen)
        eye_color = (
            QColor("#ff2028")
            if game.phase_name == game.GamePhase.COMBAT
            else QColor("#ffd05a")
        )
        painter.setBrush(QBrush(eye_color))
        painter.drawEllipse(QRectF(x-16*scale, y+1*scale, 8*scale, 6*scale))
        painter.drawEllipse(QRectF(x+8*scale, y+1*scale, 8*scale, 6*scale))
        painter.setBrush(QBrush(QColor("#321319")))
        jaw_h = 18 + 5 * (0.5 + 0.5 * math.sin(game.elapsed * 5.0))
        painter.drawRoundedRect(QRectF(x-18*scale, y+12*scale,
                                       36*scale, jaw_h*scale), 5*scale, 5*scale)
        painter.setBrush(QBrush(QColor("#eee0c6")))
        # Crocs
        for tx in (-15, -3, 9):
            painter.drawPolygon(QPolygonF([
                QPointF(x+tx*scale, y+13*scale),
                QPointF(x+(tx+6)*scale, y+13*scale),
                QPointF(x+(tx+3)*scale, y+25*scale),
            ]))
            painter.drawPolygon(QPolygonF([
                QPointF(x+tx*scale, y+12*scale+jaw_h*scale),
                QPointF(x+(tx+6)*scale, y+12*scale+jaw_h*scale),
                QPointF(x+(tx+3)*scale, y+5*scale+jaw_h*scale),
            ]))

        # Jambes
        painter.setPen(QPen(outline, clamp_to_min(2.0*scale, 1.0)))
        painter.setBrush(QBrush(shadow))
        painter.drawRoundedRect(QRectF(x-27*scale, y+29*scale,
                                       22*scale, 30*scale), 6*scale, 5*scale)
        painter.drawRoundedRect(QRectF(x+5*scale, y+29*scale,
                                       22*scale, 30*scale), 6*scale, 5*scale)
        painter.setPen(QPen(QColor("#21191a"), clamp_to_min(2.0*scale, 1.0)))
        painter.drawLine(round(x-26*scale), round(y+55*scale),
                        round(x-7*scale), round(y+55*scale))
        painter.drawLine(round(x+7*scale), round(y+55*scale),
                        round(x+26*scale), round(y+55*scale))

    # -------------------------------------------------------------------------
    def _draw_enemy_cyber(
       self,
        painter: QPainter,
        game: Game,
        x: float, y: float,
        scale: float,
        armored: bool,
    ):

        # Cyberdemon
        skin = QColor("#865447")
        skin_light = QColor("#b47b63")
        metal = QColor("#68747b")
        metal_light = QColor("#b0b9b7")
        outline = QColor("#211a1c")

        painter.setPen(QPen(outline, clamp_to_min(3.0 * scale, 1.0)))
        # Grandes cornes
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#d2c09c"), clamp_to_min(8.0*scale, 2.0),
                            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        left_horn = QPainterPath(QPointF(x-18*scale, y-52*scale))
        left_horn.cubicTo(x-55*scale, y-76*scale, x-53*scale, y-34*scale,
                        x-30*scale, y-34*scale)
        right_horn = QPainterPath(QPointF(x+18*scale, y-52*scale))
        right_horn.cubicTo(x+55*scale, y-76*scale, x+53*scale, y-34*scale,
                           x+30*scale, y-34*scale)
        painter.drawPath(left_horn)
        painter.drawPath(right_horn)
        # Tête et cou.
        painter.setPen(QPen(outline, clamp_to_min(3.0*scale, 1.0)))
        painter.setBrush(QBrush(skin))
        painter.drawEllipse(QRectF(x-22*scale, y-57*scale,
                                   44*scale, 43*scale))
        # Yeux rouges lumineux en combat, ambre hors combat.
        cyber_eye_color = (
            QColor("#ff2028")
            if game.phase_name == game.GamePhase.COMBAT
            else QColor("#e0a04c")
        )
        painter.setBrush(QBrush(cyber_eye_color))
        painter.drawEllipse(QRectF(x-13*scale, y-43*scale, 8*scale, 6*scale))
        painter.drawEllipse(QRectF(x+5*scale, y-43*scale, 8*scale, 6*scale))
        painter.setBrush(QBrush(QColor("#241316")))
        painter.drawRoundedRect(QRectF(x-13*scale, y-29*scale,
                                       26*scale, 10*scale), 3*scale, 3*scale)
        # Torse
        painter.setBrush(QBrush(skin_light))
        painter.drawPolygon(QPolygonF([
            QPointF(x-23*scale, y-22*scale), QPointF(x-43*scale, y-12*scale),
            QPointF(x-37*scale, y+23*scale), QPointF(x-20*scale, y+31*scale),
            QPointF(x+20*scale, y+31*scale), QPointF(x+37*scale, y+23*scale),
            QPointF(x+43*scale, y-12*scale), QPointF(x+23*scale, y-22*scale),
        ]))
        # Shield
        if armored:
            painter.setBrush(QBrush(metal))
            painter.drawPolygon(QPolygonF([
                QPointF(x-25*scale, y-15*scale), QPointF(x, y-25*scale),
                QPointF(x+25*scale, y-15*scale), QPointF(x+21*scale, y+15*scale),
                QPointF(x, y+24*scale), QPointF(x-21*scale, y+15*scale),
            ]))
            painter.setBrush(QBrush(metal_light))
            painter.drawLine(round(x-15*scale), round(y-10*scale),
                            round(x+15*scale), round(y-10*scale))
        # Jambes : gauche organique, droite prothèse.
        painter.setBrush(QBrush(skin))
        painter.drawRoundedRect(QRectF(x-27*scale, y+27*scale,
                                       19*scale, 34*scale), 5*scale, 5*scale)
        painter.setBrush(QBrush(metal))
        painter.drawRoundedRect(QRectF(x+8*scale, y+26*scale,
                                       20*scale, 34*scale), 3*scale, 3*scale)
        painter.setBrush(QBrush(metal_light))
        painter.drawEllipse(QRectF(x+12*scale, y+34*scale, 12*scale, 9*scale))
        painter.setPen(QPen(outline, clamp_to_min(3.0*scale, 1.0)))
        painter.drawLine(round(x-27*scale), round(y+60*scale),
                        round(x-5*scale), round(y+60*scale))
        painter.drawLine(round(x+6*scale), round(y+60*scale),
                        round(x+31*scale), round(y+60*scale))
        # Bras gauche griffu, bras droit terminé par un lance-roquettes.
        painter.setPen(QPen(skin, clamp_to_min(12.0*scale, 4.0),
                            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(round(x-31*scale), round(y-10*scale),
                        round(x-45*scale), round(y+20*scale))
        painter.setPen(QPen(metal, clamp_to_min(13.0*scale, 5.0),
                            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(round(x+31*scale), round(y-10*scale),
                        round(x+48*scale), round(y+8*scale))
        painter.setPen(QPen(outline, clamp_to_min(2.5*scale, 1.0)))
        painter.setBrush(QBrush(metal))
        painter.drawRoundedRect(QRectF(x+38*scale, y+1*scale,
                                       32*scale, 17*scale), 4*scale, 4*scale)
        painter.setBrush(QBrush(QColor("#242a2d")))
        painter.drawEllipse(QRectF(x+61*scale, y+5*scale, 7*scale, 8*scale))
        painter.setBrush(QBrush(QColor("#d05b3f")))
        painter.drawEllipse(QRectF(x+46*scale, y+5*scale, 5*scale, 5*scale))

    # -------------------------------------------------------------------------
    def _draw_death_explosion(self, painter: QPainter) -> None:
        """Éclatement sanglant à la mort du mob"""

        effect = getattr(self, "_doom_explosion", None)
        if effect is None:
            return

        x, y, scale, started = effect
        age = time.monotonic() - started
        duration = 0.95
        if age >= duration:
            self._doom_explosion = None
            return

        progress = clamp_between(age / duration, 0.0, 1.0)
        fade = (1.0 - progress) ** 1.35

        painter.save()

        painter.setPen(Qt.PenStyle.NoPen)

        # Bref nuage rouge sombre au point d'impact.
        radius = (13.0 + 43.0 * progress) * scale * 1.22
        cloud = QRadialGradient(QPointF(x, y), clamp_to_min(radius, 1.0))
        cloud.setColorAt(0.0, QColor(105, 8, 18, int(185 * fade)))
        cloud.setColorAt(0.45, QColor(75, 4, 12, int(130 * fade)))
        cloud.setColorAt(1.0, QColor(48, 0, 5, 0))
        painter.setBrush(QBrush(cloud))
        painter.drawEllipse(QRectF(x - radius, y - radius * 0.8, radius * 2, radius * 1.6))

        # Éclaboussures et fragments projetés avec une trajectoire descendante.
        for i in range(13):
            angle = (2.0 * math.pi * i / 13.0) + 0.23
            speed = (28.0 + (i % 4) * 12.0) * scale * 1.25
            dx = math.cos(angle) * speed * progress
            dy = math.sin(angle) * speed * progress * 1.25 + 33.0 * scale * progress * progress
            size = (4.0 + (i % 3) * 3.0) * scale * (0.75 + 0.25 * fade)
            color = (118, 8 + (i % 3) * 3, 17, int(235 * fade))
            painter.setBrush(QBrush(QColor(*color)))
            if i % 3 == 0:
                painter.drawPolygon(QPolygonF([
                    QPointF(x + dx - size, y + dy - size * 0.4),
                    QPointF(x + dx + size * 1.4, y + dy),
                    QPointF(x + dx - size * 0.2, y + dy + size),
                ]))
            else:
                painter.drawEllipse(QRectF(x + dx - size, y + dy - size * 0.55, size * 2.0, size * 1.1))

        # Quelques gouttes plus fines
        for i in range(9):
            angle = (2.0 * math.pi * i / 9.0) + 0.61
            dist = (40.0 + (i % 3) * 14.0) * scale * progress * 1.18
            dx = math.cos(angle) * dist
            dy = math.sin(angle) * dist + 42.0 * scale * progress * progress
            painter.setBrush(QBrush(QColor(145, 12, 24, int(205 * fade))))
            painter.drawEllipse(QRectF(
                x + dx - 1.7 * scale, y + dy - 2.5 * scale,
                5.0 * scale, 7.5 * scale,
            ))

        painter.restore()

    # -------------------------------------------------------------------------
    def _draw_blood_decals(
        self,
        painter: QPainter,
        game: Game,
        center: float,
        opening_bottom: float,
        bottom: float,
        opening_shift: float,
    ) -> None:
        """Flaques et morceaux résultant de l'explosion du mob!"""

        decals = getattr(self, "_doom_blood_decals", None)
        if not decals:
            return

        current_distance = float(game.world_distance)
        visible = []

        painter.save()

        painter.setPen(Qt.PenStyle.NoPen)
        for born_distance, span, start_t, side, monster_scale, seed in decals:
            travelled = current_distance - born_distance
            remaining = span - travelled
            if remaining <= 0.0:
                continue
            visible.append((born_distance, span, start_t, side, monster_scale, seed))
            if travelled < 0.0:
                continue

            progress = clamp_between(travelled / span, 0.0, 1.0)
            t = start_t + (1.0 - start_t) * progress
            perspective = 0.30 + 1.45 * t
            x = center + side * (10.0 + 148.0 * t) + opening_shift * (1.0 - t)
            y = opening_bottom + (bottom - opening_bottom) * t
            size_factor = clamp_to_min(monster_scale, 0.72)
            w = (20.0 + 48.0 * t) * size_factor
            h = (7.0 + 15.0 * t) * size_factor
            alpha = int(190 * (0.45 + 0.55 * t))

            # Flaque irrégulière, sans flash ni couleur surnaturelle.
            painter.setBrush(QBrush(QColor(48, 5, 9, alpha)))
            painter.drawEllipse(QRectF(x - w * 0.62, y - h * 0.35, w * 1.24, h * 0.82))
            painter.setBrush(QBrush(QColor(112, 8, 17, int(alpha * 0.82))))
            painter.drawEllipse(QRectF(x - w * 0.39, y - h * 0.68, w * 0.73, h * 0.92))
            painter.setBrush(QBrush(QColor(72, 6, 12, int(alpha * 0.9))))
            painter.drawEllipse(QRectF(x + w * 0.18, y - h * 0.28, w * 0.48, h * 0.56))

            # Corps écrasé mais en volume : ombre portée, masse sombre,
            # relief rouge et quelques morceaux épais avec une face éclairée.
            body_w = (15.0 + 29.0 * t) * size_factor
            body_h = (6.0 + 11.0 * t) * size_factor
            painter.setBrush(QBrush(QColor(20, 3, 5, int(alpha * 0.78))))
            painter.drawEllipse(QRectF(x - body_w * 0.72, y - body_h * 0.24,
                                       body_w * 1.44, body_h * 0.94))
            painter.setBrush(QBrush(QColor(36, 24, 25, int(alpha * 0.98))))
            painter.drawEllipse(QRectF(x - body_w * 0.63, y - body_h * 0.58,
                                       body_w * 0.93, body_h * 0.91))
            painter.setBrush(QBrush(QColor(91, 25, 31, int(alpha * 0.98))))
            painter.drawEllipse(QRectF(x - body_w * 0.24, y - body_h * 0.78,
                                       body_w * 0.78, body_h * 0.91))
            painter.setBrush(QBrush(QColor(135, 52, 52, int(alpha * 0.72))))
            painter.drawEllipse(QRectF(x - body_w * 0.10, y - body_h * 0.70,
                                       body_w * 0.33, body_h * 0.31))

            for i in range(5):
                # Pseudo-aléatoire stable : des morceaux irréguliers et épais.
                n = math.sin((seed + i * 19) * 12.9898) * 43758.5453
                r = n - math.floor(n)
                dx = (r - 0.5) * w * 1.45
                dy = (0.10 + ((i * 7) % 5) * 0.12) * h
                chunk = (3.0 + r * 5.8) * perspective * size_factor
                painter.setBrush(QBrush(QColor(38, 7, 10, int(alpha * 0.98))))
                painter.drawEllipse(QRectF(x + dx - chunk * 0.12, y + dy - chunk * 0.18,
                                           chunk * 1.45, chunk * 1.05))
                painter.setBrush(QBrush(QColor(116 + int(r * 30), 20, 28, int(alpha * 0.96))))
                painter.drawEllipse(QRectF(x + dx, y + dy - chunk * 0.30,
                                           chunk * 0.95, chunk * 0.65))

        painter.restore()

        self._doom_blood_decals = visible

    # -------------------------------------------------------------------------
    def _draw_boss(self, painter: QPainter, game: Game) -> None:
        """Draw Boss"""

        approach_duration = clamp_to_min(game.boss_approach_duration, 0.001)
        approach = clamp_between(
            game.boss_approach_elapsed / approach_duration,
            0.0, 1.0,
        )
        approach = approach * approach * (3.0 - 2.0 * approach)
        bob = math.sin(game.elapsed * 2.0) * 9.0 * approach
        cx = self.CENTER_X + math.sin(game.elapsed * 0.65) * 5.0 * approach
        cy = self.HORIZON_Y + 34.0 + 78.0 * approach + bob
        boss_scale = (0.38 + 0.62 * approach) * 1.12

        painter.save()

        painter.translate(cx, cy)
        painter.scale(boss_scale, boss_scale)
        painter.translate(-cx, -cy)

        if game.use_old_boss:
            self._draw_boss_OLD(painter, cx, cy, game)
        else:
            self._draw_boss_caco(painter, cx, cy, game)

        # Ombre au sol qui s'étire légèrement quand le boss monte.
        shadow_width = 112.0 - bob * 1.2
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(10, 8, 14, 100)))
        painter.drawEllipse(QRectF(cx-shadow_width, cy+94, shadow_width*2, 20))

        # Les impacts du fusil laissent des éclaboussures vertes très contrastées
        # sur le Cacodemon rouge, afin qu'ils restent visibles pendant le combat.
        painter.setPen(QPen(QColor("#183d20"), 1.5))
        hit_count = min(
            game.BOSS_HITS_REQUIRED,
            game.boss_hits,
        )
        for hit_index in range(hit_count):
            hit_x = cx - 53 + ((hit_index * 37) % 107)
            hit_y = cy - 35 + ((hit_index * 23) % 82)
            painter.setBrush(QBrush(QColor("#72d447")))
            painter.drawEllipse(QRectF(hit_x, hit_y, 8, 10))
            painter.setPen(QPen(QColor("#72d447"), 2, Qt.PenStyle.SolidLine,
                                Qt.PenCapStyle.RoundCap))
            painter.drawLine(round(hit_x + 4), round(hit_y + 7),
                            round(hit_x + 3), round(hit_y + 13))
            painter.setPen(QPen(QColor("#183d20"), 1.5))

        painter.restore()

    # -------------------------------------------------------------------------
    def _draw_boss_caco(self, painter: QPainter, x: float, y: float, game: Game) -> None:

        # Cacodemon
        cx, cy = x, y
        mouth_open = 1.0 + 0.5 * (0.5 + 0.5 * math.sin(game.elapsed * 4.0))

        # Deux petites cornes qui émergent de la partie supérieure de l'œuf.
        painter.setPen(QPen(QColor("#381a20"), 4, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap))
        painter.setBrush(QBrush(QColor("#e4d4b6")))
        painter.drawPolygon(QPolygonF([
            QPointF(cx-53, cy-47), QPointF(cx-76, cy-89),
            QPointF(cx-67, cy-42), QPointF(cx-45, cy-25),
        ]))
        painter.drawPolygon(QPolygonF([
            QPointF(cx+53, cy-47), QPointF(cx+76, cy-89),
            QPointF(cx+67, cy-42), QPointF(cx+45, cy-25),
        ]))

        # Corps ovoïde rouge, avec reflet pour renforcer l'impression de volume.
        painter.setPen(QPen(QColor("#4a171d"), 5))
        painter.setBrush(QBrush(QColor("#a9323a")))
        painter.drawEllipse(QRectF(cx-86, cy-72, 172, 156))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(235, 94, 76, 100)))
        painter.drawEllipse(QRectF(cx-58, cy-55, 63, 86))
        painter.setBrush(QBrush(QColor("#7c222d")))
        painter.drawEllipse(QRectF(cx+31, cy-42, 34, 62))

        # Un grand œil unique, vert lumineux et pupille verticale.
        painter.setPen(QPen(QColor("#3a1519"), 3))
        painter.setBrush(QBrush(QColor("#d8df79")))
        painter.drawEllipse(QRectF(cx-30, cy-42, 60, 43))
        painter.setBrush(QBrush(QColor("#68bd62")))
        painter.drawEllipse(QRectF(cx-23, cy-36, 46, 31))
        painter.setBrush(QBrush(QColor("#15171a")))
        painter.drawEllipse(QRectF(cx-5, cy-35, 10, 29))
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawEllipse(QRectF(cx-13, cy-32, 7, 7))

        # Bouche sombre ; ouverture animée, dents supérieures et inférieures.
        mouth_h = 30.0 * mouth_open
        mouth = QRectF(cx-45, cy+18, 90, mouth_h)
        painter.setPen(QPen(QColor("#3b111b"), 3))
        painter.setBrush(QBrush(QColor("#211017")))
        painter.drawRoundedRect(mouth, 15, 12)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#f2e4c8")))
        for i in range(6):
            tx = cx - 36 + i*14
            painter.drawPolygon(QPolygonF([
                QPointF(tx, cy+20), QPointF(tx+8, cy+20),
                QPointF(tx+4, cy+20 + clamp_to_max(mouth_h*0.45, 12)),
            ]))
            painter.drawPolygon(QPolygonF([
                QPointF(tx, cy+18+mouth_h), QPointF(tx+8, cy+18+mouth_h),
                QPointF(tx+4, cy+18+mouth_h - clamp_to_max(mouth_h*0.35, 10)),
            ]))
        painter.setBrush(QBrush(QColor("#a52e46")))
        painter.drawEllipse(QRectF(cx-14, cy+mouth_h+8, 28, 7))

    # -------------------------------------------------------------------------
    def _draw_weapon(self, painter: QPainter, game: Game) -> None:

        # Fusil à pompe rétro : crosse, poignée, canon et deux tubes bien distincts.
        recoil = 12.0 if game.shot_flash > 0 else 0.0
        painter.setPen(QPen(QColor("#101116"), 4))
        painter.setBrush(QBrush(QColor("#6b4932")))
        painter.drawPolygon(QPolygonF([
            QPointF(455, 552 + recoil), QPointF(545, 552 + recoil),
            QPointF(559, 625 + recoil), QPointF(441, 625 + recoil),
        ]))
        painter.setBrush(QBrush(QColor("#353b43")))
        painter.drawPolygon(QPolygonF([
            QPointF(461, 524 + recoil), QPointF(539, 524 + recoil),
            QPointF(548, 582 + recoil), QPointF(452, 582 + recoil),
        ]))
        painter.setBrush(QBrush(QColor("#252a31")))
        painter.drawRoundedRect(QRectF(466, 472 + recoil, 68, 95), 7, 7)
        painter.setBrush(QBrush(QColor("#727a82")))
        painter.drawRect(QRectF(474, 448 + recoil, 22, 92))
        painter.drawRect(QRectF(504, 448 + recoil, 22, 92))
        painter.setBrush(QBrush(QColor("#11151a")))
        painter.drawEllipse(QRectF(478, 443 + recoil, 14, 9))
        painter.drawEllipse(QRectF(508, 443 + recoil, 14, 9))
        painter.setPen(QPen(QColor("#a8adb0"), 2))
        painter.drawLine(474, 465 + round(recoil), 496, 465 + round(recoil))
        painter.drawLine(504, 465 + round(recoil), 526, 465 + round(recoil))
        painter.setPen(QPen(QColor("#1a1c20"), 3))
        painter.setBrush(QBrush(QColor("#4d3327")))
        painter.drawRoundedRect(QRectF(482, 558 + recoil, 36, 47), 5, 5)

        if game.shot_flash > 0:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#ffd86b")))
            painter.drawPolygon(QPolygonF([
                QPointF(478, 445 + recoil), QPointF(463, 417 + recoil),
                QPointF(486, 428 + recoil), QPointF(500, 390 + recoil),
                QPointF(514, 428 + recoil), QPointF(537, 417 + recoil),
                QPointF(522, 445 + recoil),
            ]))
            painter.setBrush(QBrush(QColor("#fff2b0")))
            painter.drawEllipse(QRectF(490, 420 + recoil, 20, 18))
            progress = game.bullet_progress
            if game.phase_name == game.GamePhase.BOSSFIGHT:
                approach_duration = clamp_to_min(game.boss_approach_duration, 0.001)
                approach = clamp_between(
                    game.boss_approach_elapsed / approach_duration,
                    0.0, 1.0,
                )
                approach = approach * approach * (3.0 - 2.0 * approach)
                target_x = self.CENTER_X
                target_y = self.HORIZON_Y + 34.0 + 78.0 * approach
                painter.setPen(QPen(QColor("#ffd86b"), 5))
                bullet_x = 500 + (target_x - 500) * progress
                bullet_y = 445 + (target_y - 445) * progress
                painter.drawLine(round(bullet_x), round(bullet_y),
                                round(bullet_x), round(bullet_y - 5))
                if progress > 0.85:
                    painter.setBrush(QBrush(QColor(255, 215, 80, 190)))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(QRectF(target_x-12, target_y-10, 24, 20))
            else:
                enemies = game.enemies
                if enemies:
                    enemy = enemies[0]
                    target_x = self.CENTER_X + (enemy.side * 60)
                    target_y = self.HORIZON_Y + 100
                    bullet_x = 500 + (target_x - 500) * progress
                    bullet_y = 445 + (target_y - 445) * progress
                    painter.setPen(QPen(QColor("#ffd86b"), 5))
                    painter.drawLine(
                        round(bullet_x), round(bullet_y),
                        round(bullet_x + (3 * enemy.side)),
                        round(bullet_y - 4)
                    )

    # -------------------------------------------------------------------------
    def _draw_bottom_hud(self, painter: QPainter, game: Game) -> None:

        # HUD: at the bottom of the game screen
        top = self.HUD_TOP
        painter.fillRect(QRectF(0,top,game.WIDTH,game.HEIGHT-top),QColor("#17191f"))
        painter.setPen(QPen(QColor("#6b6e75"),2))
        painter.drawLine(0,top,game.WIDTH,top)

        # Scores (Kills & injuries)
        painter.setFont(QFont(GAME_FONT,15,QFont.Weight.Bold))
        painter.setPen(QPen(QColor("#e7dfcc")))
        painter.drawText(
            QRectF(24, top+12, 180, 28),
            Qt.AlignmentFlag.AlignLeft,
            get_text("GAME_DOOM_KILLS")
        )
        painter.drawText(
            QRectF(24, top+40, 180, 30),
            Qt.AlignmentFlag.AlignLeft,
            f"{game.kills:03d}"
        )
        painter.drawText(
            QRectF(790, top+12, 185, 28),
            Qt.AlignmentFlag.AlignLeft,
            get_text("GAME_DOOM_INJURIES")
        )
        painter.drawText(
            QRectF(790, top+40, 185, 30),
            Qt.AlignmentFlag.AlignLeft,
            f"{game.injuries:03d}"
        )

        # Visage changeant selon les blessures.
        injuries = game.injuries
        face_color = QColor(interpolate_color(
            color1= "#e0b890",
            color2= "#aa1010",
            ratio= log_norm(clamp_to_max(injuries, game.MAX_INJURIES), game.MAX_INJURIES, 4.0)
        ))
        painter.setPen(QPen(QColor("#08090c"),3))
        painter.setBrush(QBrush(face_color))
        face_x = 470
        painter.drawEllipse(QRectF(face_x, top+7, 60, 60))
        painter.setPen(QPen(QColor("#17191f"),4))
        # Eyes
        if injuries < 2:
            painter.drawLine(face_x+12, top+24, face_x+25, top+31)
            painter.drawLine(face_x+36, top+31, face_x+49, top+24)
        elif injuries < 4:
            painter.drawLine(face_x+12, top+29, face_x+25, top+29)
            painter.drawLine(face_x+36, top+29, face_x+49, top+29)
        else:
            painter.drawLine(face_x+12, top+31, face_x+25, top+24)
            painter.drawLine(face_x+36, top+24, face_x+49, top+31)
        # Mouth
        if is_between(injuries, 1, 2):
            painter.drawLine(face_x+15, top+38 , face_x+45, top+38)
        else:
            painter.drawArc(
                QRectF(face_x+15, top+34, 30, 20),
                20*16,
                -140*16 if injuries < 2 else 140*16
            )

        # Inst. Cadence
        cadence = game.current_spm
        cadence_text = "--" if cadence is None else f"{cadence:.1f}"
        painter.setFont(QFont(GAME_FONT, 18, QFont.Weight.Bold))
        painter.setPen(QPen(QColor("#e7dfcc")))
        painter.drawText(
            QRectF(20, top + 72, 180, 24),
            Qt.AlignmentFlag.AlignLeft,
            f"{get_text('SPM_UNIT')}: {cadence_text}"
        )

        # Phase time
        painter.setFont(QFont(GAME_FONT, 12, QFont.Weight.Bold))
        phase_text = (
            f"{clamp_to_zero(game.explore_remaining):.1f} s"
            if game.phase_name == game.GamePhase.EXPLORE
            else (
                f"{game.boss_hits} / "
                f"{game.BOSS_HITS_REQUIRED} coups · "
                f"{clamp_to_zero(game.boss_remaining):.1f} s"
            )
            if game.phase_name == game.GamePhase.BOSSFIGHT
            else f"{clamp_to_zero(game.combat_remaining):.1f} s"
        )
        painter.drawText(
            QRectF(390, top + 72, 220, 24),
            Qt.AlignmentFlag.AlignCenter,
            phase_text,
        )

        # Remaining Game Time
        painter.setFont(QFont(GAME_FONT, 18, QFont.Weight.Bold))
        painter.drawText(
            QRectF(390, top + 95, 220, 24),
            Qt.AlignmentFlag.AlignCenter,
            game.hud_time_text(),
        )

        # Pendant le boss, les deux Pulses habituels sont remplacés par 34 CPM.
        painter.setFont(QFont(GAME_FONT,14,QFont.Weight.Bold))
        if game.phase_name == game.GamePhase.BOSSFIGHT:
            boss_color = QColor("#c744d9")
            self.PULSATOR.paint(painter, 670, top+40, game.elapsed, game.BOSS_CADENCE,boss_color)
            painter.setPen(QPen(boss_color))
            painter.drawText(640, top + 80, f"{game.BOSS_CADENCE:.0f} {get_text('SPM_UNIT')}")
        # Sinon un Pulse à 24 CPM pour avancer et l'autre à 32 pour tirer
        else:
            move_color = QColor("#3173ee") if game.phase_name != game.GamePhase.COMBAT else QColor("#515255")
            fire_color = QColor("#e6932d") if game.phase_name == game.GamePhase.COMBAT else QColor("#515255")
            self.PULSATOR.paint(painter, 330, top+40, game.elapsed, game.MOVE_CADENCE,move_color)
            self.PULSATOR.paint(painter, 670, top+40, game.elapsed, game.FIRE_CADENCE,fire_color)
            painter.setPen(QPen(move_color))
            painter.drawText(305, top + 80, f"{game.MOVE_CADENCE:.0f} {get_text('SPM_UNIT')}")
            painter.setPen(QPen(fire_color))
            painter.drawText(640, top + 80, f"{game.FIRE_CADENCE:.0f} {get_text('SPM_UNIT')}")

        # Boutton "Règles"
        painter.setPen(QPen(QColor("#d0d0d0"), 1))
        painter.setBrush(QBrush(QColor("#30343b")))
        painter.drawRoundedRect(QRectF(820, top + 88, 160, 30), 5, 5)
        painter.setFont(QFont(GAME_FONT, 10, QFont.Weight.Bold))
        painter.setPen(QPen(QColor("#e7dfcc")))
        painter.drawText(
            QRectF(820, top + 88, 160, 30),
            Qt.AlignmentFlag.AlignCenter,
            get_text("GAME_RULES_BUTTON")
        )

    # -------------------------------------------------------------------------
    def _draw_enemy_OLD(
       self,
        painter: QPainter,
        game: Game,
        x: float, y: float,
        scale: float,
        armored: bool,
    ) -> None:

        hide = QColor("#655b54") if armored else QColor("#71352f")
        body = QColor("#81756d") if armored else QColor("#a54b3c")
        dark = QColor("#292329")

        # Cornes / épaules larges pour une silhouette de démon, pas un simple bonhomme.
        painter.setPen(QPen(dark, 4))
        painter.setBrush(QBrush(hide))
        painter.drawPolygon(QPolygonF([
            QPointF(x - 22 * scale, y - 42 * scale),
            QPointF(x - 39 * scale, y - 66 * scale),
            QPointF(x - 35 * scale, y - 31 * scale),
            QPointF(x - 17 * scale, y - 18 * scale),
        ]))
        painter.drawPolygon(QPolygonF([
            QPointF(x + 22 * scale, y - 42 * scale),
            QPointF(x + 39 * scale, y - 66 * scale),
            QPointF(x + 35 * scale, y - 31 * scale),
            QPointF(x + 17 * scale, y - 18 * scale),
        ]))
        painter.setBrush(QBrush(body))
        painter.drawEllipse(
            QRectF(x - 25 * scale, y - 53 * scale, 50 * scale, 48 * scale)
        )
        painter.drawPolygon(QPolygonF([
            QPointF(x - 34 * scale, y - 13 * scale),
            QPointF(x - 53 * scale, y + 5 * scale),
            QPointF(x - 43 * scale, y + 30 * scale),
            QPointF(x - 22 * scale, y + 23 * scale),
            QPointF(x + 22 * scale, y + 23 * scale),
            QPointF(x + 43 * scale, y + 30 * scale),
            QPointF(x + 53 * scale, y + 5 * scale),
            QPointF(x + 34 * scale, y - 13 * scale),
        ]))
        painter.setBrush(QBrush(hide))
        painter.drawPolygon(QPolygonF([
            QPointF(x - 22 * scale, y + 18 * scale),
            QPointF(x - 18 * scale, y + 56 * scale),
            QPointF(x - 2 * scale, y + 56 * scale),
            QPointF(x, y + 20 * scale),
            QPointF(x + 2 * scale, y + 56 * scale),
            QPointF(x + 18 * scale, y + 56 * scale),
            QPointF(x + 22 * scale, y + 18 * scale),
        ]))

        # Bras et griffes.
        painter.setPen(QPen(dark, 3))
        painter.setBrush(QBrush(hide))
        painter.drawLine(round(x - 34 * scale), round(y - 5 * scale), round(x - 48 * scale), round(y + 25 * scale))
        painter.drawLine(round(x + 34 * scale), round(y - 5 * scale), round(x + 48 * scale), round(y + 25 * scale))
        for claw_side in (-1, 1):
            claw_x = x + claw_side * 49 * scale
            painter.drawLine(round(claw_x), round(y + 23 * scale), round(claw_x + claw_side * 8 * scale), round(y + 35 * scale))
            painter.drawLine(round(claw_x), round(y + 23 * scale), round(claw_x - claw_side * 3 * scale), round(y + 36 * scale))

        # Yeux lumineux et gueule dentée.
        painter.setPen(Qt.PenStyle.NoPen)
        eye_color = (
            QColor("#ff2028")
            if game.phase_name == game.GamePhase.COMBAT
            else QColor("#e0a04c")
        )
        painter.setBrush(QBrush(eye_color))
        painter.drawEllipse(QRectF(x - 15 * scale, y - 36 * scale, 10 * scale, 7 * scale))
        painter.drawEllipse(QRectF(x + 5 * scale, y - 36 * scale, 10 * scale, 7 * scale))
        painter.setBrush(QBrush(QColor("#211619")))
        painter.drawRoundedRect(QRectF(x - 13 * scale, y - 21 * scale, 26 * scale, 13 * scale), 3, 3)
        painter.setBrush(QBrush(QColor("#e8d7bd")))
        for tooth in (-8, -2, 4, 10):
            painter.drawPolygon(QPolygonF([
                QPointF(x + tooth * scale, y - 20 * scale),
                QPointF(x + (tooth + 3) * scale, y - 20 * scale),
                QPointF(x + (tooth + 1.5) * scale, y - 14 * scale),
            ]))

        # Armure et cicatrices pour la variante résistante.
        if armored:
            painter.setPen(QPen(QColor("#c2b5a2"), 3))
            painter.setBrush(QBrush(QColor("#6e747d")))
            painter.drawPolygon(QPolygonF([
                QPointF(x - 30 * scale, y - 12 * scale),
                QPointF(x, y - 24 * scale),
                QPointF(x + 30 * scale, y - 12 * scale),
                QPointF(x + 25 * scale, y + 17 * scale),
                QPointF(x, y + 27 * scale),
                QPointF(x - 25 * scale, y + 17 * scale),
            ]))
            painter.setPen(QPen(QColor("#ffb52e"), 4))
            painter.drawLine(round(x - 10 * scale), round(y - 4 * scale),
                            round(x + 10 * scale), round(y - 4 * scale))

    # -------------------------------------------------------------------------
    def _draw_boss_OLD(self, painter: QPainter, x: float, y: float, game: Game) -> None:
        '''Boss flottant stylisé : chimère sombre, cornes, troisième œil et crocs.'''

        # Chimère
        cx, cy = x, y
        mouth_open = 1.0 + 0.5 * (0.5 + 0.5 * math.sin(game.elapsed * 4.0))

        # Six appendices serpentins derrière le corps.
        for i in range(6):
            side = -1 if i < 3 else 1
            j = i % 3
            sx = cx + side * (54 + j * 12)
            sy = cy + 18 + j * 14
            ex = cx + side * (94 + j * 24)
            ey = cy + 66 + j * 19
            painter.setPen(QPen(QColor("#273b3b"), 12 - j * 2,
                                Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(round(sx), round(sy), round(ex), round(ey))
            painter.setBrush(QBrush(QColor("#405d54")))
            painter.setPen(QPen(QColor("#171d21"), 2))
            painter.drawEllipse(QRectF(ex - 13, ey - 10, 26, 20))
            painter.setBrush(QBrush(QColor("#f4b64c")))
            painter.drawEllipse(QRectF(ex - 5, ey - 2, 4, 4))

        # Cornes ivoire.
        painter.setBrush(QBrush(QColor("#c7b99b")))
        painter.setPen(QPen(QColor("#20151b"), 4))
        painter.drawPolygon(QPolygonF([QPointF(cx-55,cy-47), QPointF(cx-92,cy-105),
                                    QPointF(cx-82,cy-48), QPointF(cx-48,cy-20)]))
        painter.drawPolygon(QPolygonF([QPointF(cx+55,cy-47), QPointF(cx+92,cy-105),
                                    QPointF(cx+82,cy-48), QPointF(cx+48,cy-20)]))

        # Corps massif et tête reptilienne.
        painter.setBrush(QBrush(QColor("#31504b")))
        painter.setPen(QPen(QColor("#151b21"), 5))
        painter.drawEllipse(QRectF(cx-88, cy-67, 176, 148))
        painter.setBrush(QBrush(QColor("#52645a")))
        painter.drawEllipse(QRectF(cx-63, cy-80, 126, 96))
        painter.setBrush(QBrush(QColor("#42635a")))
        painter.drawEllipse(QRectF(cx-55, cy-104, 110, 92))

        # Gueule ouverte et crocs.
        mouth_h = 23.0 * mouth_open
        mouth = QRectF(cx-42, cy-27, 84, mouth_h)
        painter.setBrush(QBrush(QColor("#21151b")))
        painter.drawRoundedRect(mouth, 15, 12)
        painter.setBrush(QBrush(QColor("#8a3030")))
        painter.drawEllipse(QRectF(cx-36, cy-27, 72, mouth_h))
        painter.setBrush(QBrush(QColor("#f1e4c6")))
        for i in range(5):
            tx = cx - 30 + i * 15
            painter.drawPolygon(QPolygonF([
                QPointF(tx, cy-27), QPointF(tx+8, cy-27),
                QPointF(tx+4, cy-27+18
            )]))

        # Deux yeux et un troisième œil frontal.
        painter.setPen(QPen(QColor("#1a1015"), 2))
        for ex, ey, radius in ((cx-28, cy-67, 7), (cx+28, cy-67, 7), (cx, cy-91, 9)):
            painter.setBrush(QBrush(QColor("#f13f31")))
            painter.drawEllipse(QRectF(ex-radius, ey-radius, radius*2, radius*2))
            painter.setBrush(QBrush(QColor("#ffd58a")))
            painter.drawEllipse(QRectF(ex-2, ey-radius/2, 4, radius))

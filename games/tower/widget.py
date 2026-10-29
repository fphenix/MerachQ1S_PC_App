import math

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QBrush, QPen, QPainter, QFont

from setup.constants import GAME_FONT
from setup.lang import get_text
from setup.utils import clamp_to_min

from games.game import Game
from games.game_painter import GamePainter   
from games.pulsator import Pulsator
from games.tower.engine import Tower2Game

# =============================================================================
class TowerWidget(GamePainter):

    PULSATOR = Pulsator(min_radius= 3.0, max_radius= 20.0, pen_width= 2.0, outlined=True)

    STONE_COLORS = ("#b8b9b5", "#999d9e", "#c8c7bf", "#a7aaa7", "#d0cbc0")

    # -------------------------------------------------------------------------
    def paint(self, painter: QPainter, game: Game) -> None:

        painter.save()
        
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Chantier principal.
        painter.fillRect(QRectF(0, game.HUD_HEIGHT, 760, 630), QColor("#dce7e8"))
        camera_y = game.camera_offset_y
        ground_screen_y = game.GROUND_Y - camera_y
        painter.fillRect(QRectF(0, ground_screen_y, 760, max(0.0, 700.0-ground_screen_y)), QColor("#c6b49b"))
        painter.setPen(QPen(QColor("#9a8b78"), 2))
        for x in range(0, 760, 43):
            painter.drawLine(x, round(ground_screen_y + 2), x + 22, 700)

        painter.setPen(QPen(QColor("#655d50"), 4))
        painter.drawLine(0, round(ground_screen_y), 760, round(ground_screen_y))

        # Grue/poutre en acier, avec un crochet suspendu.
        beam_y = game.beam_y - camera_y
        x = game.beam_x
        painter.setPen(QPen(QColor("#3b4d5b"), 2))
        painter.setBrush(QBrush(QColor("#657c8b")))
        painter.drawRect(QRectF(x - 58, beam_y - 9, 116, 18))
        painter.setPen(QPen(QColor("#c4d2d9"), 2))
        painter.drawLine(round(x - 52), round(beam_y - 4), round(x + 52), round(beam_y - 4))
        for lattice_x in range(-60, 46, 15):
            painter.drawLine(round(x + lattice_x), round(beam_y - 8), round(x + lattice_x + 12), round(beam_y + 8))
        painter.setPen(QPen(QColor("#3b4d5b"), 4))
        painter.drawLine(round(x), round(beam_y + 9), round(x), round(beam_y + 30))
        painter.drawArc(QRectF(x - 7, beam_y + 23, 14, 14), 180 * 16, 180 * 16)

        # Bloc porté et aperçu du dépôt à la position horizontale réelle de la grue.
        preview_width, preview_height = game._next_block_size()
        preview_fill = QColor(self.STONE_COLORS[game.block_count % len(self.STONE_COLORS)])
        preview_x = x
        preview_world_y = game.GROUND_Y - preview_height / 2
        preview_y = preview_world_y - camera_y

        if not game.carrying_block:
            pickup_x = game.BEAM_MAX_X if game.pickup_side > 0 else game.BEAM_MIN_X
            painter.setPen(QPen(QColor("#8a8172"), 2))
            painter.setBrush(QBrush(QColor("#a89c88")))
            painter.drawRect(QRectF(pickup_x - preview_width / 2 - 8,
                                    ground_screen_y - 8, preview_width + 16, 8))
            painter.setPen(QPen(QColor("#565c5f"), 2))
            painter.setBrush(QBrush(preview_fill))
            pickup_rect = QRectF(pickup_x - preview_width / 2,
                                ground_screen_y - preview_height,
                                preview_width, preview_height)
            painter.drawRoundedRect(pickup_rect, 3, 3)
            painter.setPen(QPen(preview_fill.lighter(145), 2))
            painter.drawLine(round(pickup_x - preview_width / 2 + 5),
                            round(ground_screen_y - preview_height + 5),
                            round(pickup_x + preview_width / 2 - 5),
                            round(ground_screen_y - preview_height + 5))
            # Flèche discrète vers le bloc que la grue doit aller chercher.
            painter.setPen(QPen(QColor("#9b6330"), 2))
            painter.setBrush(QBrush(QColor("#f3d4a8")))
            arrow_y = ground_screen_y - preview_height - 24
            painter.drawLine(round(pickup_x), round(arrow_y - 14), round(pickup_x), round(arrow_y + 2))
            painter.drawLine(round(pickup_x), round(arrow_y + 2), round(pickup_x - 5), round(arrow_y - 4))
            painter.drawLine(round(pickup_x), round(arrow_y + 2), round(pickup_x + 5), round(arrow_y - 4))
        else:
            carried_y = beam_y + game.CRANE_CARRIED_BLOCK_OFFSET
            painter.setPen(QPen(QColor("#3b4d5b"), 2))
            painter.drawLine(round(x), round(beam_y + 30), round(x), round(carried_y - preview_height / 2))
            painter.setPen(QPen(QColor("#565c5f"), 2))
            painter.setBrush(QBrush(preview_fill))
            carried_rect = QRectF(x - preview_width / 2,
                                carried_y - preview_height / 2,
                                preview_width, preview_height)
            painter.drawRoundedRect(carried_rect, 3, 3)
            painter.setPen(QPen(preview_fill.lighter(145), 2))
            painter.drawLine(round(x - preview_width / 2 + 5),
                            round(carried_y - preview_height / 2 + 5),
                            round(x + preview_width / 2 - 5),
                            round(carried_y - preview_height / 2 + 5))

        # Ligne-guide verticale et fantôme translucide : le dépôt peut se faire
        # à n'importe quelle abscisse, pas uniquement au-dessus de la pile.
        painter.setPen(QPen(QColor("#438b79"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(round(preview_x), round(beam_y + 36), round(preview_x), round(preview_y))
        painter.setPen(QPen(QColor("#438b79"), 1, Qt.PenStyle.DashLine))
        painter.setBrush(QBrush(QColor(67, 139, 121, 65)))
        painter.drawRoundedRect(
            QRectF(preview_x - preview_width / 2, preview_y - preview_height / 2,
                  preview_width, preview_height), 3, 3
        )

        # Blocs rigides avec leur rotation réelle.
        for index, block in enumerate(game.blocks):
            painter.save()

            screen_y = block.y - camera_y
            painter.translate(block.x, screen_y)
            painter.rotate(math.degrees(block.angle))
            rect = QRectF(-block.width / 2, -block.height / 2, block.width, block.height)
            fill = QColor(self.STONE_COLORS[index % len(self.STONE_COLORS)])
            painter.setPen(QPen(QColor("#565c5f"), 2))
            painter.setBrush(QBrush(fill))
            painter.drawRoundedRect(rect, 2, 2)
            painter.setPen(QPen(fill.lighter(135), 2))
            painter.drawLine(round(-block.width / 2 + 5), round(-block.height / 2 + 5), round(block.width / 2 - 5), round(-block.height / 2 + 5))
            painter.setPen(QPen(fill.darker(135), 1))
            painter.drawLine(round(-block.width / 2 + 8), 0, round(block.width / 2 - 8), 0)

            painter.restore()

        # Ligne de hauteur maximale et indicateurs de jeu.
        top_screen_y = game.GROUND_Y - game.max_height_px - camera_y
        painter.setPen(QPen(QColor("#2f7f68"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(18, round(top_screen_y), 742, round(top_screen_y))
        painter.setPen(QPen(QColor("#233746")))
        painter.setFont(QFont(GAME_FONT, 11, QFont.Weight.Bold))
        info_x = 770.0 if isinstance(game, Tower2Game) else 18.0
        info_width = 220.0 if isinstance(game, Tower2Game) else 720.0
        painter.drawText(QRectF(info_x, 78, info_width, 20), Qt.AlignmentFlag.AlignLeft,
                        f"{get_text('GAME_TOWER_BLOCKS')}: {game.block_count}")
        painter.drawText(QRectF(info_x, 98, info_width, 20), Qt.AlignmentFlag.AlignLeft,
                        f"{get_text('GAME_TOWER_MAX')}: {game.max_height_px / 100.0:.2f} m")

        # Vue d'ensemble : échelle dynamique calculée sur tous les blocs,
        # y compris ceux qui sont tombés ou inclinés. Les angles physiques sont conservés.
        overview_rect = QRectF(770.0, 110.0, 220.0, 560.0)
        overview_ground = 655.0
        world_points = [point for block in game.blocks for point in game._vertices(block)]
        # le "*" ci-dessous est un "Unpack"
        world_min_x = min([0.0, *(point[0] for point in world_points)])
        world_max_x = max([game.PLAYFIELD_WIDTH, *(point[0] for point in world_points)])
        world_min_y = min([0.0, *(point[1] for point in world_points)])
        world_max_y = max([game.GROUND_Y, *(point[1] for point in world_points)])

        world_width = clamp_to_min(world_max_x - world_min_x, 1.0)
        world_height = clamp_to_min(world_max_y - world_min_y, 1.0)

        overview_scale = min(overview_rect.width() / world_width,
                            (overview_rect.height() - 20.0) / world_height)
        overview_x = overview_rect.center().x() - (world_min_x + world_max_x) * overview_scale / 2.0
        overview_y = overview_ground - world_max_y * overview_scale

        painter.setPen(QPen(QColor("#b6c4cc"), 2))
        ground_screen_y_overview = overview_y + game.GROUND_Y * overview_scale
        painter.drawLine(770, round(ground_screen_y_overview), 990, round(ground_screen_y_overview))
        painter.setPen(QPen(QColor("#506575"), 1, Qt.PenStyle.DashLine))
        for tick in range(1, 6):
            tick_y = ground_screen_y_overview - tick * 100 * overview_scale
            if overview_rect.top() <= tick_y <= overview_rect.bottom():
                painter.drawLine(770, round(tick_y), 990, round(tick_y))

        for index, block in enumerate(game.blocks):
            painter.save()
            bx = overview_x + block.x * overview_scale
            by = overview_y + block.y * overview_scale
            painter.translate(bx, by)
            painter.rotate(math.degrees(block.angle))
            rect = QRectF(-block.width * overview_scale / 2, -block.height * overview_scale / 2,
                        block.width * overview_scale, block.height * overview_scale)
            painter.setPen(QPen(QColor("#d2d6d6"), 1))
            painter.setBrush(QBrush(QColor(self.STONE_COLORS[index % len(self.STONE_COLORS)])))
            painter.drawRect(rect)
            painter.restore()

        # Trois cibles de cadence : déplacement, maintien et dépôt.
        unit = get_text("SPM_UNIT")
        if isinstance(game, Tower2Game):
            painter.setPen(QPen(QColor("#9b6330")))
            painter.setFont(QFont(GAME_FONT, 9, QFont.Weight.Bold))
            painter.drawText(QRectF(8.0, 120.0, 150.0, 18), Qt.AlignmentFlag.AlignLeft,
                            f"{get_text("GAME_TOWER_PICK")} : {str(int(game.PICKUP_TARGET))} {unit}")
            column_y = 82.0
            column_left = 90.0
            column_width = 160.0
            self.PULSATOR.paint(painter, 40, column_y + 24, game.elapsed, game.PICKUP_TARGET, QColor("#E2666628"))
            for index, target in enumerate(game.COLUMN_TARGETS):
                cx = column_left + index * column_width
                cy = column_y
                pulse_x = cx + (column_width - 8) // 2
                pulse_y = cy + 24
                rect = QRectF(cx, cy, column_width - 8, 48)
                selected = game.column_index == index
                color = QColor(("#f0bd4f", "#62a7e8", "#56bd91", "#d58be8")[index])
                self.PULSATOR.paint(painter, pulse_x, pulse_y, game.elapsed, target, color)
                painter.setPen(QPen(color if selected else QColor("#8a9aa5"), 3 if selected else 1))
                painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 65 if selected else 18)))
                painter.drawRoundedRect(rect, 6, 6)
                painter.setPen(QPen(QColor("#233746")))
                painter.setFont(QFont(GAME_FONT, 11, QFont.Weight.Bold))
                bonus = game.COLUMN_BONUSES[index]
                painter.drawText(rect.adjusted(0, 2, 0, -20), Qt.AlignmentFlag.AlignCenter, f"{target} {unit}")
                painter.setFont(QFont(GAME_FONT, 9, QFont.Weight.Bold))
                painter.drawText(rect.adjusted(0, 23, 0, 0), Qt.AlignmentFlag.AlignCenter, f"+{bonus} pts/bloc")
            # Barre de stabilité visuelle, sans message textuel redondant.
            bar = QRectF(100.0, 140.0, 600.0, 12.0)
            ratio = max(0.0, min(1.0, game.stability_elapsed / game.STABILITY_SECONDS))
            painter.setPen(QPen(QColor("#233746"), 1))
            painter.setBrush(QBrush(QColor("#e8eef0")))
            painter.drawRoundedRect(bar, 4, 4)
            if ratio > 0.0:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor("#35a879")))
                painter.drawRoundedRect(QRectF(bar.x(), bar.y(), bar.width() * ratio, bar.height()), 4, 4)
        else:
            # Trois cibles de cadence historiques : déplacement, maintien et dépôt.
            move_color = QColor("#6377e8")
            hold_color = QColor("#299b83")
            drop_color = QColor("#f19730")
            pulse_y = beam_y + 88.0
            pulse_positions = (
                (max(45.0, x - 145.0), game.MOVE_TARGET, move_color, game.BuildPhase.MOVE.value),
                (x, game.HOLD_TARGET, hold_color, game.BuildPhase.HOLD.value),
                (min(715.0, x + 145.0), game.DROP_TARGET, drop_color, game.BuildPhase.DROP.value),
            )
            for pulse_x, target, color, state in pulse_positions:
                self.PULSATOR.paint(painter, pulse_x, pulse_y, game.elapsed, target, color)
                painter.setPen(QPen(color))
                painter.setFont(QFont(GAME_FONT, 9, QFont.Weight.Bold))
                painter.drawText(QRectF(pulse_x - 42, pulse_y - 38, 84, 20),
                                Qt.AlignmentFlag.AlignCenter, f"{target:.0f} {unit}")
                painter.setPen(QPen(QColor("#233746")))
                painter.setFont(QFont(GAME_FONT, 10, QFont.Weight.Bold))
                state_text = get_text("GAME_TOWER_" + state)
                painter.drawText(QRectF(pulse_x - 42, pulse_y + 24, 84, 20),
                                Qt.AlignmentFlag.AlignCenter, f"{state_text}")

            # L'état courant reste lisible même lorsque la cadence se situe entre cibles.
            state_color = {
                game.BuildPhase.MOVE: move_color,
                game.BuildPhase.HOLD: hold_color,
                game.BuildPhase.DROP: drop_color
            }.get(game.cadence_state, hold_color)
            painter.setPen(QPen(state_color))
            painter.setFont(QFont(GAME_FONT, 10, QFont.Weight.Bold))
            state_txt = get_text(f"GAME_TOWER_{game.cadence_state.value}")
            painter.drawText(
                QRectF(285.0, 80.0, 190.0, 18),
                Qt.AlignmentFlag.AlignCenter,
                f"{state_txt} · {game.current_spm:.1f} {unit}"
                if game.current_spm is not None
                else f"{state_txt} · -- {unit}"
            )

            # Jauge de charge : montée à partir de 16 CPM, décharge sous 16 CPM.
            bar_x, bar_y, bar_w, bar_h = 285.0, 100.0, 190.0, 12.0
            painter.setPen(QPen(QColor("#233746"), 1))
            painter.setBrush(QBrush(QColor("#e8eef0")))
            painter.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 4, 4)
            charge_w = bar_w * max(0.0, min(1.0, game.drop_charge))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#35a879" if game.drop_charge >= game.DROP_CHARGE_MIN else "#63d6e8")))
            if charge_w > 0:
                painter.drawRoundedRect(QRectF(bar_x, bar_y, charge_w, bar_h), 4, 4)
            painter.setPen(QPen(QColor("#233746")))
            painter.setFont(QFont(GAME_FONT, 9, QFont.Weight.Bold))
            painter.drawText(QRectF(bar_x - 20, bar_y + 14, bar_w + 40, 18), Qt.AlignmentFlag.AlignCenter,
                            f"Charge : {game.drop_charge * 100:.0f}%")

        painter.restore()

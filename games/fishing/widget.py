"""Rendu Qt partagé par les variantes Fishing."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush, QFont, QPainter, QPen

from setup.constants import GAME_FONT

from setup.lang import get_text

from games.game import Game
from games.game_painter import GamePainter
from games.pulsator import Pulsator
from games.fishing.engine import Insect

# =============================================================================
class FishingWidget(GamePainter):
    """Objet de rendu, utilisé par GameWidget sans hériter de QWidget."""

    PULSATOR = Pulsator(min_radius= 2.0, max_radius= 16.0, pen_width= 1.5)

    # -------------------------------------------------------------------------
    def paint(self, painter: QPainter, game: Game) -> None:
        """Dessine le terrain dans un repère dont l'origine est le haut du jeu."""

        painter.save()

        painter.translate(0, game.HUD_HEIGHT)

        # Couloirs
        bg_color = QColor("#91c252")
        bg_color_light = [125, 110, 100, 75, 50]
        for lane in range(0, game.LANE_COUNT):
            painter.setPen(QPen(bg_color.lighter(bg_color_light[lane])))
            y = round(lane * game.LANE_HEIGHT)
            painter.fillRect(
                0, y,
                game.WIDTH, game.LANE_HEIGHT,
                bg_color.lighter(bg_color_light[lane])
            )

        # Repères de cadence et pulse
        lane_font = QFont(GAME_FONT, 14, QFont.Weight.Bold)
        painter.setFont(lane_font)
        pulse_time = (
            game.elapsed
            if game.phase == game.PHASE_PLAYING
            else game.phase_elapsed
        )

        # Gameplay A: one pulse per lane
        if game.game_id == "fishing":
            for row, spm in enumerate(reversed(game.CADENCE_LEVELS)):
                center_y = round((row + 0.5) * game.LANE_HEIGHT)
                painter.setPen(QPen(Qt.GlobalColor.black))
                painter.drawText(
                    5, center_y - 3,
                    f"{spm} {get_text('SPM_UNIT')}"
                )
                self.PULSATOR.paint(
                    painter, 36, center_y + 18, pulse_time, spm,
                    QColor(Qt.GlobalColor.black)
                )

        # Gameplay B : trois consignes, sans afficher les niveaux du mode A.
        else:
            pulse_specs = (
                (1, game.CADENCE_UP, "↑"),
                (3, game.CADENCE_STAY, "="),
                (5, game.CADENCE_DOWN, "↓"),
            )

            symbol_font = QFont(GAME_FONT, 20, QFont.Weight.Bold)
            painter.setFont(symbol_font)
            for row_position, spm, symbol in pulse_specs:
                center_y = round((row_position - 0.5) * game.LANE_HEIGHT)
                self.PULSATOR.paint(
                    painter,
                    36, center_y,
                    pulse_time,
                    spm,
                    QColor(Qt.GlobalColor.black)
                )
                painter.setPen(QPen(Qt.GlobalColor.black))
                painter.setFont(symbol_font)
                painter.drawText(
                    55, center_y - 14, 30, 28,
                    Qt.AlignmentFlag.AlignCenter, symbol
                )
                painter.setFont(lane_font)
                painter.drawText(
                    5, center_y + 18, 90, 22,
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                    f"{round(spm)} {get_text('SPM_UNIT')}"
                )

        # Filet stylisé : cadre sombre, maille visible et manche latéral.
        self._draw_net(painter, game)

        # Insectes
        for insect in game.insects:
            self._draw_bug(painter, game, insect)

        painter.restore()

    # -------------------------------------------------------------------------
    def _draw_net(self, canvas: QPainter, game: Game) -> None:
        
        net_x = game.NET_LEFT_MARGIN
        net_y = round(game.net_y)
        canvas.setPen(QPen(QColor("#4b3527"), 5))
        canvas.drawLine(
            net_x + game.NET_WIDTH // 2, net_y + game.NET_HEIGHT - 4,
            net_x - 13, net_y + game.NET_HEIGHT + 15
        )
        canvas.setPen(QPen(QColor("#d7e7e8"), 3))
        canvas.setBrush(QBrush(QColor(210, 237, 240, 65)))
        canvas.drawRoundedRect(
            net_x, net_y,
            game.NET_WIDTH, game.NET_HEIGHT,
            9, 9
        )
        canvas.setPen(QPen(QColor("#8cb9c4"), 1))
        for mesh_x in range(net_x + 10, net_x + game.NET_WIDTH, 10):
            canvas.drawLine(
                mesh_x, net_y + 4,
                mesh_x, net_y + game.NET_HEIGHT - 4
            )
        for mesh_y in range(net_y + 10, net_y + game.NET_HEIGHT, 10):
            canvas.drawLine(
                net_x + 4, mesh_y,
                net_x + game.NET_WIDTH - 4, mesh_y
            )

    # -------------------------------------------------------------------------
    def _draw_bug(self, canvas: QPainter, game: Game, insect: Insect) -> None:
        """Dessine une abeille, un papillon ou un frelon avec quelques formes Qt."""

        canvas.save()

        size = game.INSECTS_DATA[insect.kind]["pxsize"]
        cx = insect.x + size / 2
        cy = insect.y + size / 2
        scale = size / 30.0

        canvas.translate(cx, cy)
        hflip = -1
        canvas.scale(hflip * scale, scale)
        canvas.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        if insect.kind == "butterfly":
            self._draw_butterfly(canvas)
        else:
            is_hornet = insect.kind == "hornet"
            self._draw_bee(canvas, is_hornet)

        canvas.restore()

    # -------------------------------------------------------------------------
    def _draw_bee(self, canvas: QPainter, is_hornet: bool) -> None:
            
        dark_color = QColor("#29252a")
        body_color = QColor("#e9a72f" if is_hornet else "#f58f3b")
        wing_color = QColor(221, 246, 255, 210)
        sting_color = QColor("#c64a2e")

        canvas.setPen(QPen(QColor("#688b94"), 1))
        canvas.setBrush(QBrush(wing_color))
        canvas.drawEllipse(-9, -12, 12, 10)
        canvas.drawEllipse(0, -12, 12, 10)
        canvas.setPen(QPen(dark_color, 1.5))
        canvas.setBrush(QBrush(body_color))
        canvas.drawEllipse(-11, -5, 22, 12)
        # Rayures sombres pour rendre l'abeille et le frelon identifiables.
        canvas.setPen(QPen(dark_color, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        canvas.drawLine(-3, -4, -3, 6)
        canvas.drawLine(3, -4, 3, 6)
        canvas.setBrush(QBrush(dark_color))
        canvas.drawEllipse(8, -4, 7, 7)
        canvas.drawLine(13, -3, 17, -7)
        canvas.drawLine(13, -3, 17, 0)
        canvas.setPen(QPen(dark_color, 1.5))
        canvas.drawLine(-10, 1, -15, 5)
        canvas.drawLine(-5, 6, -8, 11)
        canvas.drawLine(4, 6, 7, 11)

        # Stinger if Hornet
        if is_hornet:
            canvas.setPen(QPen(sting_color, 2))
            canvas.drawLine(-10, 0, -15, 0)

    # -------------------------------------------------------------------------
    def _draw_butterfly(self, canvas: QPainter) -> None:

        # Deux paires d'ailes colorées et un corps fin.
        canvas.setPen(QPen(QColor("#6c3b9c"), 1.5))
        canvas.setBrush(QBrush(QColor("#d8a8ff")))
        canvas.drawEllipse(-14, -10, 13, 14)
        canvas.drawEllipse(1, -10, 13, 14)
        canvas.setBrush(QBrush(QColor("#79d9e8")))
        canvas.drawEllipse(-12, 2, 10, 8)
        canvas.drawEllipse(2, 2, 10, 8)
        # Corps allongé et tête distincte : le papillon ne ressemble plus
        # à deux paires d'ailes sans anatomie centrale.
        canvas.setPen(QPen(QColor("#51305f"), 1))
        canvas.setBrush(QBrush(QColor("#49304f")))
        canvas.drawEllipse(-2.5, -5, 5, 18)
        canvas.setBrush(QBrush(QColor("#f4e8ff")))
        canvas.drawEllipse(-3.5, -10, 7, 7)
        canvas.setPen(QPen(QColor("#29252a"), 1.5))
        canvas.drawLine(-1, -8, -5, -13)
        canvas.drawLine(1, -8, 5, -13)

"""Décor et animation du jeu Real Fishing, dessinés avec QPainter."""

import math

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QColor,
    QBrush,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
)

from setup.constants import GAME_FONT
from setup.lang import get_text

from games.game import Game
from games.game_painter import GamePainter
from games.pulsator import Pulsator
from games.real_fishing.engine import RealFishingGame

# =============================================================================
class RealFishingWidget(GamePainter):

    PULSATOR = Pulsator(min_radius= 2.0, max_radius= 17.0, pen_width= 2.0, outlined=True)

    # enter_x, target_cadence, color
    PULSES_DATA: list[int, float, QColor] = [
        (180, 22.0, QColor("#ff7dff")),
        (395, 26.0, QColor("#0daf4b")),
        (610, 30.0, QColor("#ffad42")),
        (825, 34.0, QColor("#ffea3d")),
    ]

    FISH_COLORS: dict[str, QColor] = {
        "salmon": QColor("#e98a68"),
        "pike": QColor("#839d65"),
        "carp": QColor("#c4a77b"),
        "golden": QColor("#ffd650"),
    }
    
    # -------------------------------------------------------------------------
    def paint(self, painter: QPainter, game: Game) -> None:

        painter.save()

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        self._draw_sky_and_bank(painter, game)
        self._draw_cadence_targets(painter, game)
        self._draw_water(painter, game)
        self._draw_lilypads(painter)
        self._draw_reeds(painter, game)
        self._draw_dragonflies(painter, game)
        self._draw_rod_and_line(painter, game)
        self._draw_bobber(painter, game)
        self._draw_fish(painter, game)
        self._draw_status(painter, game)

        painter.restore()

    # -------------------------------------------------------------------------
    def _draw_cadence_targets(self, painter: QPainter, game: Game) -> None:

        target_cadence = getattr(game, "target_cadence", 26)
        painter.setFont(QFont(GAME_FONT, 13, QFont.Weight.Bold))
        for center_x, cadence, color in self.PULSES_DATA:
            active = (cadence == target_cadence)
            if active:
                # Halo contrasté et pointeur : la cible reste identifiable
                # même si l'on ne distingue pas précisément les couleurs.
                painter.setPen(QPen(QColor("#102f36"), 3))
                painter.setBrush(QBrush(QColor(255, 255, 255, 50)))
                painter.drawEllipse(QRectF(center_x - 28, 82, 55, 55))
                painter.setPen(QPen(QColor("#fffdf0"), 2))
                painter.setBrush(QBrush(QColor("#102f36")))
                painter.drawPolygon(QPolygonF([
                    QPointF(center_x - 8, 82),
                    QPointF(center_x + 8, 82),
                    QPointF(center_x, 92),
                ]))
            self.PULSATOR.paint(
                painter, center_x, 112, game.elapsed, cadence,
                color if active else color.darker(175),
            )
            painter.setPen(QPen(QColor("#102f36"), 3 if active else 1))
            painter.setFont(QFont(GAME_FONT, 13, QFont.Weight.Bold))
            painter.drawText(
                QRectF(center_x - 65, 137, 130, 24),
                Qt.AlignmentFlag.AlignCenter,
                f"{cadence} {get_text('SPM_UNIT')}" + ("  ◀" if active else "")
            )
            if active:
                painter.setPen(QPen(QColor("#102f36")))
                painter.setBrush(QBrush(QColor("#fffdf0")))
                painter.drawRoundedRect(QRectF(center_x - 38, 165, 76, 20), 6, 6)
                painter.setPen(QPen(QColor("#102f36")))
                painter.setFont(QFont(GAME_FONT, 10, QFont.Weight.Bold))
                painter.drawText(QRectF(center_x - 38, 165, 76, 20), Qt.AlignmentFlag.AlignCenter, get_text("GAME_TARGET"))

    # -------------------------------------------------------------------------
    def _draw_sky_and_bank(self, painter: QPainter, game: Game) -> None:

        sky = QLinearGradient(0, game.HUD_HEIGHT, 0, 315)
        sky.setColorAt(0.0, QColor("#9bd5ee"))
        sky.setColorAt(0.5, QColor("#e2edc0"))
        sky.setColorAt(1.0, QColor("#ff6843"))
        painter.fillRect(0, game.HUD_HEIGHT, game.WIDTH, 260, QBrush(sky))

        # Collines boisées lointaines.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#6b9b68")))
        hills = QPainterPath()
        hills.moveTo(0, 260)
        hills.cubicTo(110, 170, 210, 225, 300, 195)
        hills.cubicTo(420, 155, 505, 230, 625, 188)
        hills.cubicTo(760, 155, 850, 220, 1000, 175)
        hills.lineTo(1000, 300)
        hills.lineTo(0, 300)
        hills.closeSubpath()
        painter.drawPath(hills)

        # Trees
        for x, y, size in ((55, 205, 36), (112, 190, 45), (205, 218, 31),
                           (800, 200, 38), (870, 195, 48), (945, 186, 36)):
            self._draw_tree(painter, x, y, size)

        # Berge
        bank = QPainterPath()
        bank.moveTo(0, 250)
        bank.cubicTo(180, 245, 260, 280, 420, 260)
        bank.cubicTo(600, 240, 730, 280, 1000, 230)
        bank.lineTo(1000, 310)
        bank.cubicTo(760, 335, 620, 300, 430, 325)
        bank.cubicTo(250, 345, 120, 300, 0, 318)
        bank.closeSubpath()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#8b7147")))
        painter.drawPath(bank)

        # Touffes d'herbe
        for x, y in ((25, 264), (72, 263), (156, 270), (265, 287), (380, 280),
                     (505, 277), (630, 278), (760, 275), (890, 260), (965, 252)):
            self._draw_grass(painter, x, y)

    # -------------------------------------------------------------------------
    def _draw_tree(self, painter: QPainter, x: int, y: int, size: int) -> None:

        painter.setBrush(QBrush(QColor("#477b50")))
        painter.setPen(QPen(QColor("#76583a"), 6))
        painter.drawLine(x, y + size // 2, x, y + size + 18)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(x - size, y - size / 2, size * 1.5, size * 1.2))
        painter.drawEllipse(QRectF(x - size / 2, y - size, size * 1.6, size * 1.5))

    # -------------------------------------------------------------------------
    def _draw_grass(self, painter: QPainter, x: int, y: int) -> None:
            
        painter.setPen(QPen(QColor("#5b8d45"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(x, y, x + 2, y - 9)
        painter.drawLine(x + 3, y, x + 8, y - 13)
        painter.drawLine(x + 6, y, x + 11, y - 7)

    # -------------------------------------------------------------------------
    def _draw_water(self, painter: QPainter, game: Game) -> None:

        water = QLinearGradient(0, 285, 0, game.HEIGHT)
        water.setColorAt(0.0, QColor("#6ab9c1"))
        water.setColorAt(0.38, QColor("#318c9d"))
        water.setColorAt(1.0, QColor("#155568"))
        painter.fillRect(0, 300, game.WIDTH, game.HEIGHT - 300, QBrush(water))

        # Reflets horizontaux animés.
        painter.setPen(QPen(QColor(207, 244, 232, 75), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        t = game.elapsed
        for i in range(18):
            x = (i * 137 + int(t * (10 + i % 4))) % (game.WIDTH + 130) - 65
            y = 325 + (i * 37) % 330
            length = 25 + (i * 17) % 75
            painter.drawLine(x, y, x + length, y)

    # -------------------------------------------------------------------------
    def _draw_lilypads(self, painter: QPainter) -> None:

        # x, y, radius
        pads = ((160, 385, 30), (260, 500, 24), (405, 350, 27),
                (775, 420, 33), (875, 545, 25), (360, 580, 22))
        
        for x, y, radius in pads:
            painter.setPen(QPen(QColor("#2b6849"), 2))
            painter.setBrush(QBrush(QColor("#4f9a62")))
            painter.drawEllipse(QRectF(x - radius, y - radius * 0.55, radius * 2, radius * 1.1))
            painter.setPen(QPen(QColor("#2b6849"), 2))
            painter.drawLine(x, y, x + radius * 0.55, y - radius * 0.28)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#f6f0d6")))
            painter.drawEllipse(QRectF(x + radius * 0.12, y - radius * 0.62, 7, 7))
            painter.setBrush(QBrush(QColor("#f0b8ca")))
            painter.drawEllipse(QRectF(x + radius * 0.22, y - radius * 0.72, 7, 7))

    # -------------------------------------------------------------------------
    def _draw_reeds(self, painter: QPainter, game: Game) -> None:

        painter.setPen(QPen(QColor("#356d42"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for base_x, base_y, height in ((20, 315, 60), (45, 317, 78), (75, 319, 48),
                                       (930, 290, 62), (960, 284, 82), (985, 282, 50)):
            sway = math.sin(game.elapsed * 1.4 + base_x) * 7
            painter.drawLine(base_x, base_y, base_x + sway, base_y - height)
            painter.drawLine(base_x + 4, base_y - 12, base_x - 10 + sway, base_y - 35)
            painter.setPen(QPen(QColor("#795b36"), 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(base_x + sway, base_y - height, base_x + sway, base_y - height + 12)
            painter.setPen(QPen(QColor("#356d42"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))

    # -------------------------------------------------------------------------
    def _draw_dragonflies(self, painter: QPainter, game: Game) -> None:

        for index, (base_x, base_y) in enumerate(((190, 340), (520, 315), (840, 360))):
            x = base_x + math.sin(game.elapsed * 0.9 + index) * 24
            y = base_y + math.cos(game.elapsed * 1.5 + index) * 12
            flap = math.sin(game.elapsed * 22.0 + index) * 5.0

            painter.save()

            painter.translate(x, y)
            painter.rotate(math.sin(game.elapsed * 1.3 + index) * 12.0)

            # Corps mobile et quatre ailes qui battent rapidement.
            painter.setPen(QPen(QColor("#214c58"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(QPointF(-7, 0), QPointF(7, 0))
            painter.setPen(QPen(QColor(241, 251, 246, 210), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(QPointF(-2, 0), QPointF(-9, -5 - flap))
            painter.drawLine(QPointF(0, 0), QPointF(-6, 5 + flap))
            painter.drawLine(QPointF(2, 0), QPointF(9, -5 - flap))
            painter.drawLine(QPointF(4, 0), QPointF(10, 5 + flap))
            painter.setPen(QPen(QColor("#183f4b"), 2))
            painter.drawPoint(QPointF(7, -1))

            painter.restore()

    # -------------------------------------------------------------------------
    def _draw_rod_and_line(self, painter: QPainter, game: Game) -> None:

        # Canne posée sur la berge à droite, fil allant jusqu'au bouchon.
        painter.setPen(QPen(QColor("#6b4328"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(915, 205), QPointF(745, 268))
        painter.setPen(QPen(QColor("#d7b37a"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(915, 205), QPointF(745, 268))

        bobber_x = 585.0
        bobber_y = 350.0
        if game.bobber_on_bank:
            bobber_x, bobber_y = 760.0, 278.0
        elif game.fishing_state == RealFishingGame.STATE_BITE:
            bobber_y += math.sin(game.elapsed * 18.0) * 9.0
            bobber_x += math.sin(game.elapsed * 13.0) * 5.0
        elif game.fishing_state == RealFishingGame.STATE_REELING:
            progress = min(1.0, game.state_elapsed / max(0.1, game.reel_duration))
            bobber_x += 145.0 * progress
            bobber_y -= 58.0 * progress
            bobber_y += math.sin(game.elapsed * 7.0) * 4.0

        painter.setPen(QPen(QColor("#e7f5e8"), 1))
        painter.drawLine(QPointF(745, 268), QPointF(bobber_x, bobber_y - 5))

    # -------------------------------------------------------------------------
    def _draw_bobber(self, painter: QPainter, game: Game) -> None:

        x, y = 585.0, 350.0
        if game.bobber_on_bank:
            x, y = 760.0, 278.0
        elif game.fishing_state == RealFishingGame.STATE_BITE:
            y += math.sin(game.elapsed * 18.0) * 9.0
            x += math.sin(game.elapsed * 13.0) * 5.0
        elif game.fishing_state == RealFishingGame.STATE_REELING:
            progress = min(1.0, game.state_elapsed / max(0.1, game.reel_duration))
            x += 145.0 * progress
            y -= 58.0 * progress
            y += math.sin(game.elapsed * 7.0) * 4.0

        # Ondes circulaires discrètes autour du bouchon tant qu'il est dans l'eau.
        if not game.bobber_on_bank:
            phase = (game.elapsed * 0.8) % 1.0
            for ring_index in range(2):
                ring_phase = (phase + ring_index * 0.5) % 1.0
                radius_x = 9.0 + ring_phase * 22.0
                radius_y = 3.0 + ring_phase * 6.0
                alpha = int(150 * (1.0 - ring_phase))
                painter.setPen(QPen(QColor(210, 250, 244, alpha), 1.5))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(QRectF(
                    x - radius_x, y + 5 - radius_y,
                    radius_x * 2, radius_y * 2,
                ))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(x - 18, y + 3, 36, 10))

        # Bobber
        painter.setPen(QPen(QColor("#f7f2df"), 2))
        painter.setBrush(QBrush(QColor("#e9eee4")))
        painter.drawEllipse(QRectF(x - 5, y - 7, 10, 15))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#df463d")))
        painter.drawEllipse(QRectF(x - 5, y - 7, 10, 8))
        painter.setPen(QPen(QColor(225, 250, 250, 100), 2))

        # circle around the bobber if moving:
        if game.bobber_moving:
            painter.setPen(QPen(QColor(255, 245, 190, 180), 3))
            painter.drawEllipse(QRectF(x - 26, y - 15, 52, 34))

    # -------------------------------------------------------------------------
    def _draw_fish(self, painter: QPainter, game: Game) -> None:

        if game.current_fish is None:
            return

        fish_visible_phases = (
            RealFishingGame.STATE_BITE,
            RealFishingGame.STATE_REELING,
            RealFishingGame.STATE_UNHOOK
        )
        if game.fishing_state not in fish_visible_phases:
            return

        color = self.FISH_COLORS[game.current_fish]
        x = 580.0
        y = 395.0 + math.sin(game.elapsed * 2.4) * 7.0
        underwater = game.fishing_state != RealFishingGame.STATE_UNHOOK
        if game.fishing_state == RealFishingGame.STATE_REELING:
            progress = min(1.0, game.state_elapsed / max(0.1, game.reel_duration))
            x += 155.0 * progress
            y -= 105.0 * progress
        if game.fishing_state == RealFishingGame.STATE_UNHOOK:
            # Le poisson est désormais sur la berge, au-dessus de la ligne d'eau.
            x = 760.0
            y = 278.0

        painter.save()

        if underwater:
            painter.setOpacity(0.78)

        painter.setPen(QPen(color.darker(160), 2))
        painter.setBrush(QBrush(color))
        body = QPainterPath()
        body.moveTo(x - 35, y)
        body.quadTo(x - 12, y - 18, x + 18, y - 2)
        body.quadTo(x + 28, y + 3, x + 18, y + 9)
        body.quadTo(x - 12, y + 20, x - 35, y)
        painter.drawPath(body)
        # La queue frétille davantage dans l'eau et ralentit pendant le décrochage.
        tail_angle = math.sin(game.elapsed * (12.0 if underwater else 5.0)) * (9.0 if underwater else 4.0)
        painter.drawPolygon(QPolygonF([
            QPointF(x + 15, y),
            QPointF(x + 34, y - 13 + tail_angle),
            QPointF(x + 31, y + 12 - tail_angle),
        ]))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#102f3a")))
        painter.drawEllipse(QRectF(x - 24, y - 3, 4, 4))
        if game.is_golden_fish:
            painter.setPen(QPen(QColor("#fff2a1"), 2))
            painter.drawLine(QPointF(x - 8, y - 9), QPointF(x + 9, y - 9))
            painter.drawLine(QPointF(x - 3, y + 5), QPointF(x + 10, y + 5))

        painter.restore()

    # -------------------------------------------------------------------------
    def _draw_status(self, painter: QPainter, game: Game) -> None:

        key = game.status_key
        if game._last_event == "escaped" and game._event_elapsed < 2.5:
            key = "GAME_REAL_FISHING_ESCAPED"

        text = get_text(key)
        # Compteur de poissons dans la scène, distinct du score HUD.
        painter.setFont(QFont(GAME_FONT, 14, QFont.Weight.Bold))
        painter.setPen(QPen(QColor("#163d45")))
        painter.drawText(
            QRectF(24, 178, 330, 28),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            get_text("GAME_REAL_FISHING_CAUGHT").format(count=game.fish_count),
        )

        painter.setPen(QPen(QColor(12, 43, 48, 180), 1))
        painter.setBrush(QBrush(QColor(12, 43, 48, 185)))
        panel = QRectF(45, 610, 910, 54)
        painter.drawRoundedRect(panel, 12, 12)
        painter.setPen(QPen(QColor("#fff6d6")))
        painter.setFont(QFont(GAME_FONT, 15, QFont.Weight.Bold))
        painter.drawText(
            panel,
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            text,
        )

        if game.current_fish is not None and game.fishing_state in (
            RealFishingGame.STATE_BITE,
            RealFishingGame.STATE_REELING,
            RealFishingGame.STATE_UNHOOK,
        ):
            painter.setFont(QFont(GAME_FONT, 15, QFont.Weight.Bold))
            painter.setPen(QPen(QColor("#f5e276" if game.is_golden_fish else "#f5f5e8")))
            label_rect = (
                QRectF(610, 238, 300, 28)
                if game.fishing_state == RealFishingGame.STATE_UNHOOK
                else QRectF(350, 355, 300, 28)
            )
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, game.fish_label)

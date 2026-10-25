"""Game Widget Qt commun : cycle de vie, HUD et entrées des jeux."""

import json

from pathlib import Path
from time import perf_counter

from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import (
    QPainter, QPen, QFont, QFontMetrics,
    QKeyEvent, QMouseEvent, QPaintEvent,
)
from PySide6.QtWidgets import (
    QWidget,
    QDialog,
    QDialogButtonBox,
    QPlainTextEdit,
    QVBoxLayout,
)

from setup.lang import get_text, get_language
from setup.constants import (
    AVERAGE_FONT_SIZE, MAIN_FONT, GAME_FONT,
    ALLOW_DEBUG_HISCORES,
)
from setup.utils import is_between, clamp_to_max, clamp_to_min

from engine.state import RowState

from games.game import Game
from games.game_painter import GamePainter
from games.game_input import GameInput, resolve_game_cadence, ShortWindowCadenceFilter
from games.game_registry import GAME_CLASSES, GAME_VIEWS, GAME_RULES
from games.highscore import HighScoreManager

# =============================================================================
class GameWidget(QWidget):

    FRAME_MS: int = 33
    MAX_SECONDS_BETWEEN_STROKES: float = 6.0
    DEFAULT_GAME: str = "fishing"

    # -------------------------------------------------------------------------
    def __init__(
        self,
        state: RowState,
        personal_highscore_file: Path,
        common_highscore_file: Path,
        user_id: str = "",
        parent: QWidget | None = None,
    ) -> None:

        super().__init__(parent)

        self.state: RowState = state
        self.user_id: str = user_id
        
        self.highscores = HighScoreManager(
            personal_highscore_file,
            common_highscore_file
        )
        self.personal_highscore_file: Path = personal_highscore_file
        self.personal_hiscore: bool = False
        self.common_hiscore: bool = False

        self.game: Game = GAME_CLASSES[self.DEFAULT_GAME]()
        self.game_view: GamePainter = GAME_VIEWS[self.DEFAULT_GAME]()
        # Au démarrage, Fishing est le jeu sélectionné par défaut dans les Hi-Scores.
        self.last_played_game_id: str = self.DEFAULT_GAME
        
        self._last_time: float | None = None
        self._last_stroke_count: int = 0
        self._manual_stroke_pending: bool = False
        self._debug_input_used: bool = False
        self._last_manual_stroke_time: float | None = None
        self._last_manual_stroke_input_time: float | None = None
        self._manual_spm: float | None = None
        self._last_rower_stroke_time: float | None = None
        self._estimated_rower_spm: float | None = None
        self._game_cadence_filter: ShortWindowCadenceFilter = ShortWindowCadenceFilter()
        
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.rules_btn_rect = QRect(
            self.game.WIDTH // 2 + 20, 12,
            155, 40
        )

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_game)
        self.timer.start(self.FRAME_MS)

    # -------------------------------------------------------------------------
    def set_user_id(self, user_id: str, user_hiscore_file: Path) -> None:
        self.user_id = user_id
        self.set_personal_highscore_file(user_hiscore_file)

    # -------------------------------------------------------------------------
    def set_personal_highscore_file(self, filename: Path) -> None:
        self.personal_highscore_file = filename
        self.highscores.set_personal_filename(filename)

    # -------------------------------------------------------------------------
    def start_game(
        self, game_id: str = DEFAULT_GAME,
        profile_level_norm: float = 0.35
    ) -> None:

        self.game = GAME_CLASSES[game_id]()
        self.game_view = GAME_VIEWS[game_id]()
        if game_id == "doom":
            self.rules_btn_rect = QRect(820, 658, 160, 30)
        else:
            self.rules_btn_rect = QRect(
                self.game.WIDTH // 2 + 20, 12,
                155, 40,
            )

        if hasattr(self.game, "set_profile_level"):
            self.game.set_profile_level(profile_level_norm)

        self.last_played_game_id = game_id

        self.game.start()
        self.timer.start(self.FRAME_MS)
        self._last_time = None
        self._last_stroke_count = self.state.snapshot().rowerdata.stroke_count
        self._manual_stroke_pending = False
        self._debug_input_used = False
        self._last_manual_stroke_time = None
        self._last_manual_stroke_input_time = None
        self._manual_spm = None
        self._last_rower_stroke_time = None
        self._estimated_rower_spm = None
        self._game_cadence_filter.reset()
        self.personal_hiscore = False
        self.common_hiscore = False
        self.setFocus()
        self.update()

    # -------------------------------------------------------------------------
    def stop_game(self) -> None:
        """Arrête la boucle de jeu lorsqu'on quitte l'écran des jeux."""

        self.timer.stop()
        self._manual_stroke_pending = False
        self._last_time = None

    # -------------------------------------------------------------------------
    def register_stroke(self) -> None:
        # Évite qu'un rebond rapide de la barre ESPACE soit interprété comme
        # une cadence absurde (par ex. 1200 SPM pour un intervalle de 50 ms).
        # Une cadence réelle de 30 SPM laisse 2 s entre deux coups.
        current = perf_counter()

        if (
            self._last_manual_stroke_input_time is not None
            and current - self._last_manual_stroke_input_time < 1.0
        ):
            return
        
        self._last_manual_stroke_input_time = current
        self._manual_stroke_pending = True

    # -------------------------------------------------------------------------
    def keyPressEvent(self, event: QKeyEvent) -> None:

        if (
            event.key() == Qt.Key.Key_Space
            and not event.isAutoRepeat()
        ):
            self.register_stroke()
            event.accept()
            return

        super().keyPressEvent(event)

    # -------------------------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent) -> None:

        x = event.position().x() * self.game.WIDTH / clamp_to_min(self.width(), 1)
        y = event.position().y() * self.game.HEIGHT / clamp_to_min(self.height(), 1)

        if self.rules_btn_rect.contains(round(x), round(y)):
            self._show_rules()
            event.accept()
            return
        
        super().mousePressEvent(event)

    # -------------------------------------------------------------------------
    def _show_rules(self) -> None:

        filename = GAME_RULES[self.game.game_id]
        
        try:
            with filename.open("r", encoding="utf-8") as rfile:
                rules = json.load(rfile)
            message = rules.get(get_language(), rules.get("fr", ""))
        
        except (OSError, ValueError, TypeError):
            message = ""
        
        dialog = QDialog(self)
        dialog.setWindowTitle(self.game.title)
        dialog.setMinimumSize(560, 360)
        dialog.setMaximumSize(900, 700)
        dialog.resize(720, 500)

        layout = QVBoxLayout(dialog)
        rules_edit = QPlainTextEdit(dialog)
        rules_edit.setReadOnly(True)
        rules_edit.setFont(
            QFont(MAIN_FONT, AVERAGE_FONT_SIZE)
        )
        rules_edit.setPlainText(message or self.game.title)
        rules_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        layout.addWidget(rules_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close,
            parent=dialog,
        )
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.exec()

    # -------------------------------------------------------------------------
    def _update_game(self) -> None:

        if not self.isVisible():
            return

        current = perf_counter()
        if self._last_time is None:
            self._last_time = current
            return

        dt = clamp_to_max(current - self._last_time, 0.1)
        self._last_time = current

        data = self.state.snapshot().rowerdata
        stroke_count = data.stroke_count
        stroke_delta = stroke_count - self._last_stroke_count

        if stroke_delta < 0:  # nouvelle session ou compteur remis à zéro
            stroke_delta = 0
            self._game_cadence_filter.reset()
        self._last_stroke_count = stroke_count

        # Le calculateur du rameur attend plusieurs coups avant de fournir
        # une cadence lissée. En secours, on estime la cadence entre deux
        # changements du compteur de coups (utile notamment vers 18 SPM).
        if stroke_delta > 0:
            # Un coup réel reprend la main sur une éventuelle simulation ESPACE.
            self._last_manual_stroke_time = None
            self._manual_spm = None
            if self._last_rower_stroke_time is not None:
                interval = current - self._last_rower_stroke_time
                # Une estimation par intervalle n'est fiable que si un seul
                # coup a été ajouté. Si plusieurs coups arrivent dans le même
                # paquet, intervalle = délai entre paquets, pas entre coups.
                if stroke_delta == 1 and is_between(interval, 1.0, 6.0):
                    estimated_spm = 60.0 / interval
                    self._estimated_rower_spm = (
                        estimated_spm if is_between(estimated_spm, 8.0, 50.0)
                        else None
                    )
                else:
                    self._estimated_rower_spm = None
            self._last_rower_stroke_time = current

        manual_stroke = self._manual_stroke_pending and stroke_delta == 0
        if manual_stroke:
            if self._last_manual_stroke_time is not None:
                interval = current - self._last_manual_stroke_time
                if 0.0 < interval <= self.MAX_SECONDS_BETWEEN_STROKES:
                    self._manual_spm = 60.0 / interval
                else:
                    self._manual_spm = None
            self._last_manual_stroke_time = current

        if (
            self._last_manual_stroke_time is None
            or current - self._last_manual_stroke_time > self.MAX_SECONDS_BETWEEN_STROKES
        ):
            self._manual_spm = None

        if manual_stroke:
            stroke_delta = 1
            self._debug_input_used = True
        stroke_event = stroke_delta > 0

        manual_spm = self._manual_spm or 0.0

        estimated_spm = (
            (self._estimated_rower_spm or 0.0)
            if self._last_rower_stroke_time is not None
            and current - self._last_rower_stroke_time <= 5.0
            else 0.0
        )
        measured_spm = data.cadence or 0.0
        raw_spm = data.raw_stroke_rate or 0.0
        filtered_raw_spm = self._game_cadence_filter.update(
            raw_spm,
            (
                data.raw_elapsed_time,
                data.raw_stroke_count,
                raw_spm,
            ),
        )
        # Une série de frappes ESPACE doit utiliser sa propre cadence, même si
        # une valeur Q1S ancienne est encore présente dans le snapshot.
        manual_input_active = (
            self._last_manual_stroke_time is not None
            and current - self._last_manual_stroke_time <= self.MAX_SECONDS_BETWEEN_STROKES
        )
       
        # elapsed_time du Q1S a une résolution d'une seconde. La cadence
        # calculée sur ces horodatages est donc quantifiée (typiquement 20/30
        # CPM autour d'une vraie cadence de 24 CPM). Pour les jeux, l'intervalle
        # perf_counter entre changements du compteur de coups est plus précis.
        # La cadence calculée/raw reste un secours si l'estimation n'est pas
        # encore disponible ou si le compteur a avancé de plusieurs coups.
        if manual_input_active:
            effective_spm = manual_spm
            effective_raw_spm = manual_spm
        else:
            # La sélection commune privilégie la mesure FTMS, sans appliquer
            # de facteur correctif dépendant de la cible ou du jeu.
            effective_spm = resolve_game_cadence(
                raw_spm,
                measured_spm,
                estimated_spm,
                filtered_raw_spm,
            )
            effective_raw_spm = (
                raw_spm if raw_spm > 0.0
                else measured_spm if measured_spm > 0.0
                else estimated_spm if estimated_spm > 0.0
                else 0.0
            )

        if manual_input_active:
            cadence_age = (
                current - self._last_manual_stroke_time
                if manual_spm is not None else float("inf")
            )
        elif self._last_rower_stroke_time is not None:
            cadence_age = current - self._last_rower_stroke_time
        else:
            cadence_age = float("inf")

        game_input = GameInput(
            spm= effective_spm,
            raw_spm= effective_raw_spm,
            elapsed= data.elapsed_time,
            stroke_event= stroke_event,
            stroke_count= stroke_count,
            stroke_delta= stroke_delta,
            cadence_age= cadence_age,
        )
        self._manual_stroke_pending = False

        was_finished = self.game.finished
        self.game.update(dt, game_input)

        if was_finished and not self.game.finished:
            self.personal_hiscore = False
            self.common_hiscore = False

        record_hiscore = (
            self.game.records_score()
            and (ALLOW_DEBUG_HISCORES or not self._debug_input_used)
        )
        if self.game.finished and not was_finished and record_hiscore:
            self.personal_hiscore = self.highscores.add_hiscore(
                self.game.game_id,
                self.game.score,
                tie_break_score=getattr(self.game, "injuries", None),
            )
            self.common_hiscore = self.highscores.add_hiscore(
                self.game.game_id,
                self.game.score,
                common= True,
                user_id= self.user_id,
                tie_break_score=getattr(self.game, "injuries", None),
            )

        self.update()

    # -------------------------------------------------------------------------
    def paintEvent(self, event: QPaintEvent) -> None:

        del event

        painter = QPainter(self)

        if not painter.isActive():
            return
        
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.fillRect(self.rect(), Qt.GlobalColor.black)
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.scale(self.width() / self.game.WIDTH, self.height() / self.game.HEIGHT)

        if self.game.game_id != "doom":
            painter.drawLine(0, self.game.HUD_HEIGHT, self.game.WIDTH, self.game.HUD_HEIGHT)
            painter.drawLine(
                self.game.WIDTH // 2, 0,
                self.game.WIDTH // 2, self.game.HUD_HEIGHT,
            )

            # Bouton "Regles" dessiné dans le HUD commun.
            painter.drawRect(self.rules_btn_rect)
            painter.setFont(QFont(GAME_FONT, 16))
            painter.drawText(
                self.game.WIDTH // 2 + 40, 38,
                get_text("GAME_RULES_BUTTON")
            )

            # HUD commun : score, CPM et temps.
            painter.setFont(QFont(GAME_FONT, 20))
            painter.drawText(20, 40, self.game.hud_score_text())
            painter.drawText(790, 40, self.game.hud_time_text())

            current_spm = self.game.current_spm
            spm_text = "--" if current_spm is None else f"{current_spm:.1f}"
            painter.drawText(
                300, 40,
                f"{get_text('SPM_UNIT')}: {spm_text}",
            )

        # Rendu spécifique quan un jeu est actif.
        if self.game.phase == self.game.Phase.PLAYING:
            self.game_view.paint(painter, self.game)

        # Avant jeu actif: Messages
        if self.game.phase == self.game.Phase.WAITING:
            if self.game.phase_elapsed >= self.game.START_DELAY_SECONDS:
                # Doom has its own separated HUD
                if self.game.game_id == "doom":
                    painter.setFont(QFont(GAME_FONT, 30, QFont.Weight.Bold))
                    self.paint_hcentered_text(
                        painter, y=300, text=self.game.title
                    )
                    painter.setFont(QFont(GAME_FONT, 22, QFont.Weight.Bold))
                    self.paint_hcentered_text(
                        painter, y=360, text=get_text("GAME_WAIT_FOR_STROKE")
                    )
                # HUD, all games but Doom
                else:
                    self.paint_hcentered_text(
                        painter, y=300, text=self.game.title
                    )
                    self.paint_hcentered_text(
                        painter, y=360, text=get_text("GAME_WAIT_FOR_STROKE")
                    )

        # Après jeu: Game Over, Hi-Score
        elif self.game.phase == self.game.Phase.FINISHED:
            painter.setFont(QFont(GAME_FONT, 34, QFont.Weight.Bold))
            self.paint_hcentered_text(
                painter, y=280, text=self.game.title
            )
            result_text = self.game.hud_result_text()
            result_lines = (
                result_text.splitlines()
                if result_text
                else [get_text("GAME_OVER")]
            )
            has_score_line = len(result_lines) > 1

            painter.setFont(QFont(GAME_FONT, 26, QFont.Weight.Bold))
            for line_index, line in enumerate(result_lines):
                self.paint_hcentered_text(
                    painter,
                    y=335 + line_index * 38,
                    text=line,
                )

            hiscore_y = 410 if has_score_line else 385
            restart_y = 455 if has_score_line else 430

            if self.personal_hiscore or self.common_hiscore:
                painter.setFont(QFont(GAME_FONT, 22, QFont.Weight.Bold))
                self.paint_hcentered_text(
                    painter,
                    y=hiscore_y,
                    text=get_text("GAME_NEW_HISCORE"),
                )

            if self.game.phase_elapsed >= self.game.RESTART_DELAY_SECONDS:
                 painter.setFont(QFont(GAME_FONT, 20, QFont.Weight.Bold))
                 self.paint_hcentered_text(
                    painter,
                    y=restart_y,
                    text=get_text("GAME_WAIT_FOR_STROKE"),
                )


    # -------------------------------------------------------------------------
    def paint_hcentered_text(
        self, canvas: QPainter,
        y: int,
        text: str
    ) -> None:

        fm = QFontMetrics(canvas.font())
        text_width: int = fm.horizontalAdvance(text)

        canvas.drawText(
            (self.game.WIDTH - text_width) // 2, y,
            text
        )

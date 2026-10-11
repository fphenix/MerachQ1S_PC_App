"""Game Widget Qt commun : cycle de vie, HUD et entrées des jeux."""

import json

from pathlib import Path
from time import perf_counter

from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QPainter, QPen, QFont, QFontMetrics
from PySide6.QtWidgets import (
    QWidget,
    QDialog,
    QDialogButtonBox,
    QPlainTextEdit,
    QVBoxLayout,
)

from setup.lang import get_text, get_language
from setup.utils import format_duration

from engine.state import RowState

from games.game_input import GameInput
from games.game_registry import GAME_CLASSES, GAME_VIEWS, GAME_RULES
from games.highscore import HighScoreManager

# =============================================================================
class GameWidget(QWidget):

    FRAME_MS: int = 33

    # -------------------------------------------------------------------------
    def __init__(
        self,
        state: RowState,
        personal_highscore_file: Path,
        common_highscore_file: Path,
        user_id: str = "",
        parent= None,
    ) -> None:

        super().__init__(parent)

        self.state = state
        self.user_id = user_id
        
        self.highscores = HighScoreManager(
            personal_highscore_file,
            common_highscore_file
        )
        self.personal_highscore_file = personal_highscore_file
        self.personal_hiscore = False
        self.common_hiscore = False

        self.game = GAME_CLASSES["fishing"]()
        self.game_view = GAME_VIEWS["fishing"]()
        # Au démarrage, Fishing est le jeu sélectionné par défaut dans les Hi-Scores.
        self.last_played_game_id = "fishing"
        
        self._last_time: float | None = None
        self._last_stroke_count = 0
        self._manual_stroke_pending = False
        
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
    def start_game(self, game_id: str = "fishing") -> None:

        self.game = GAME_CLASSES[game_id]()
        self.game_view = GAME_VIEWS[game_id]()
        self.last_played_game_id = game_id

        self.game.start()
        self._last_time = None
        self._last_stroke_count = self.state.snapshot().rowerdata.stroke_count
        self._manual_stroke_pending = False
        self.personal_hiscore = False
        self.common_hiscore = False
        self.setFocus()
        self.update()

    # -------------------------------------------------------------------------
    def register_stroke(self) -> None:
        self._manual_stroke_pending = True

    # -------------------------------------------------------------------------
    def keyPressEvent(self, event) -> None:

        if (
            event.key() == Qt.Key.Key_Space
            and not event.isAutoRepeat()
        ):
            self.register_stroke()
            event.accept()
            return

        super().keyPressEvent(event)

    # -------------------------------------------------------------------------
    def mousePressEvent(self, event) -> None:

        x = event.position().x() * self.game.WIDTH / max(1, self.width())
        y = event.position().y() * self.game.HEIGHT / max(1, self.height())

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

        dt = min(0.1, current - self._last_time)
        self._last_time = current

        data = self.state.snapshot().rowerdata
        stroke_count = data.stroke_count
        stroke_delta = stroke_count - self._last_stroke_count
        if stroke_delta < 0:  # nouvelle session ou compteur remis à zéro
            stroke_delta = 0
        self._last_stroke_count = stroke_count
        if self._manual_stroke_pending and stroke_delta == 0:
            stroke_delta = 1
        stroke_event = stroke_delta > 0

        game_input = GameInput(
            spm= data.cadence,
            raw_spm= data.raw_stroke_rate,
            elapsed= data.elapsed_time,
            stroke_event= stroke_event,
            stroke_count= stroke_count,
            stroke_delta= stroke_delta,
        )
        self._manual_stroke_pending = False

        was_finished = self.game.finished
        self.game.update(dt, game_input)

        if was_finished and not self.game.finished:
            self.personal_hiscore = False
            self.common_hiscore = False

        if self.game.finished and not was_finished:
            self.personal_hiscore = self.highscores.add_hiscore(
                self.game.game_id,
                self.game.score
            )
            self.common_hiscore = self.highscores.add_hiscore(
                self.game.game_id,
                self.game.score,
                common= True,
                user_id= self.user_id
            )

        self.update()

    # -------------------------------------------------------------------------
    def paintEvent(self, event) -> None:
        del event

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.fillRect(self.rect(), Qt.GlobalColor.black)
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.scale(self.width() / self.game.WIDTH, self.height() / self.game.HEIGHT)

        painter.drawLine(0, self.game.HUD_HEIGHT, self.game.WIDTH, self.game.HUD_HEIGHT)
        painter.drawLine(self.game.WIDTH // 2, 0, self.game.WIDTH // 2, self.game.HUD_HEIGHT)

        # Bouton "Regles" dessiné dans le HUD pour éviter de dépendre d'un jeu précis.
        painter.drawRect(self.rules_btn_rect)
        painter.setFont(QFont("Courier New", 16))
        painter.drawText(
            self.game.WIDTH // 2 + 40, 38,
            get_text("GAME_RULES_BUTTON")
        )

        # HUD : Score, CPM, Time
        painter.setFont(QFont("Courier New", 20))
        painter.drawText(
            20, 40,
            f"{get_text("SCORE")}: {self.game.score:05d}"
        )
        painter.drawText(
            790, 40,
            f"{get_text("TIME")}: {format_duration(self.game.remaining())}"
        )
        current_spm = self.game.current_spm
        spm_text = "--" if current_spm is None else f"{current_spm:.1f}"
        painter.drawText(300, 40, f"{get_text("SPM_UNIT")}: {spm_text}")

        # Rendu spécifique quan un jeu est actif.
        if self.game.phase != self.game.PHASE_FINISHED:
            self.game_view.paint(painter, self.game)

        # Hors jeu actif: Messages (Game Over, Hi-Score, ...)
        if self.game.phase == self.game.PHASE_WAITING:
            if self.game.phase_elapsed >= self.game.START_DELAY_SECONDS:
                self.paint_hcentered_text(
                    painter,
                    y= 360,
                    text= get_text("GAME_WAIT_FOR_STROKE")
                )

        elif self.game.phase == self.game.PHASE_FINISHED:
            self.paint_hcentered_text(
                painter,
                y= 330,
                text= get_text("GAME_OVER")
            )

            if self.personal_hiscore or self.common_hiscore:
                self.paint_hcentered_text(
                    painter,
                    y= 370,
                    text= get_text("GAME_NEW_HISCORE")
                )

            if self.game.phase_elapsed >= self.game.RESTART_DELAY_SECONDS:
                 self.paint_hcentered_text(
                    painter,
                    y= 410,
                    text= get_text("GAME_WAIT_FOR_STROKE")
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

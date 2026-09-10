import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QFrame,
)

from setup.constants import (
    DELAY_SECONDS,
    FPS,
    BAR_HEIGHT,
    LIST_FONT_SIZE,
    LIST_WIDTH,
    WINDOW_BACKGROUND,
    LIST_BACKGROUND,
    MENU_SEL_BACKGROUND,
    BAR_BORDER,
    BAR_BACKGROUND,
    BAR_COLOR,
    TEXT_COLOR, LISTTEXT_COLOR,
    TITLE_FONT_SIZE,
    BIG_FONT_SIZE,
    MAIN_FONT,
    WORKOUTS_DIR,
)

from workout.workout import Workout
from setup.utils import load_workout, format_time

# =============================================================================
class WorkoutWidget(QFrame):

    def __init__(
        self,
        metronome_bar: QProgressBar,
        parent=None,
    ):
        super().__init__(parent)

        self.metronome_bar = metronome_bar

        self.setStyleSheet(
            f"""
            WorkoutWidget {{
                background-color: {WINDOW_BACKGROUND};
            }}
            """
        )

        self.workout = Workout()

        self.current_step = 0

        self.countdown_active = False
        self.running = False
        self.replay_mode = False

        self.countdown_remaining = 0.0
        self.total_remaining = 0.0
        self.total_time = 0.0
        self.step_remaining = 0.0

        self.started = False
        self.workout_elapsed = 0.0

        self.beat_phase = 0.0
        self.last_elapsed = 0.0
        self.last_tick = time.perf_counter()

        self._create_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(
            self.update_timer
        )

    # ------------------------------------------------------------------
    def _create_ui(self):

        self.setFrameShape(QFrame.Box)
        self.setLineWidth(2)
        
        main_layout = QHBoxLayout(self)

        main_layout.setContentsMargins(
            10,
            10,
            10,
            10,
        )

        main_layout.setSpacing(15)

        #
        # Partie principale Workout
        #

        layout = QVBoxLayout()

        layout.setSpacing(12)
        layout.setContentsMargins(
            10,
            5,
            10,
            5,
        )

        main_layout.addLayout(
            layout,
            1,
        )

        self.title_label = QLabel(
            "Workout"
        )

        self.field_label = QLabel(
            "Field"
        )

        self.state_label = QLabel(
            "Aucun workout chargé"
        )

        self.total_label = QLabel(
            "Temps total : 00:00"
        )

        self.exercise_label = QLabel(
            "Exercice : --"
        )

        self.rate_label = QLabel(
            "Cadence : -- CPM"
        )

        self.intensity_label = QLabel(
            "Intensité : --"
        )

        self.title_label.setAlignment(
            Qt.AlignCenter
        )

        self.field_label.setAlignment(
            Qt.AlignCenter
        )

        for label in (
            self.title_label,
        ):
            label.setStyleSheet(
                f"""
                QLabel {{
                    border: 2px solid black;
                    color: {TEXT_COLOR};
                    background-color: transparent;
                    font: bold {TITLE_FONT_SIZE}px
                    {MAIN_FONT};
                }}
                """
            )

        self.state_label.setAlignment(
            Qt.AlignCenter
        )

        for label in (
            self.field_label,
            self.total_label,
            self.state_label,
            self.exercise_label,
            self.rate_label,
            self.intensity_label,
        ):

            label.setAlignment(
                Qt.AlignCenter
            )

            color = (
                f"color: {TEXT_COLOR};"
                if label is not self.intensity_label
                else ""
            )

            bgcolor = (
                "transparent"
                if label is not self.intensity_label
                else LIST_BACKGROUND
            )

            label.setStyleSheet(
                f"""
                QLabel {{
                    {color}
                    background-color: {bgcolor};
                    font: bold {BIG_FONT_SIZE}px
                    {MAIN_FONT};
                }}
                """
            )

        layout.addWidget(
            self.title_label
        )

        layout.addWidget(
            self.field_label
        )

        layout.addWidget(
            self.state_label
        )

        layout.addWidget(
            self.total_label
        )

        layout.addWidget(
            self.exercise_label
        )

        layout.addWidget(
            self.rate_label
        )

        layout.addWidget(
            self.intensity_label
        )

        #
        # Liste des étapes à droite
        #

        self.step_list = QListWidget()

        self.step_list.setMinimumWidth(
            LIST_WIDTH
        )

        self.step_list.setMaximumWidth(
            LIST_WIDTH
        )

        self.step_list.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Expanding,
        )

        self.step_list.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {LIST_BACKGROUND};
                color: {TEXT_COLOR};
                border: 1px solid {MENU_SEL_BACKGROUND};
                font: {LIST_FONT_SIZE}px {MAIN_FONT};
            }}

            QListWidget::item {{
                padding: 3px;
                border: 1px solid transparent;
            }}

            QListWidget::item:selected {{
                background-color: transparent;
                color: {LISTTEXT_COLOR};
                border: 2px solid {BAR_COLOR};
            }}
            """
        )

        main_layout.addWidget(
            self.step_list
        )

        #
        # Barre métronome fournie par MainWindow
        #

        self._configure_metronome_bar()

    # ------------------------------------------------------------------
    def _configure_metronome_bar(self):

        bar = self.metronome_bar

        bar.setRange(
            0,
            1000,
        )

        bar.setValue(0)

        bar.setTextVisible(False)

        bar.setFixedHeight(
            BAR_HEIGHT
        )

        bar.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        bar.setStyleSheet(
            f"""
            QProgressBar {{
                border: 1px solid {BAR_BORDER};
                border-radius: 4px;
                background: {BAR_BACKGROUND};
            }}

            QProgressBar::chunk {{
                background: {BAR_COLOR};
            }}
            """
        )

    # ------------------------------------------------------------------
    # By default filename is None so the PopUp will show to load os file.
    # Else if a filename is give, then we auto load it.
    def open_setup(
        self,
        filename=None,
        replay_mode: bool = False,
    ) -> bool:

        if filename is None:

            default_dir = WORKOUTS_DIR

            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Choisir un workout",
                str(default_dir),
                "Workout (*.wo);;Tous les fichiers (*)",
            )

            if not filename:
                return False

        try:

            workout = load_workout(
                filename
            )

        except Exception as exc:

            QMessageBox.warning(
                self,
                "Erreur",
                str(exc),
            )

            return False

        self.workout = workout

        self.step_list.clear()

        for i, step in enumerate(
            workout.steps,
            start=1,
        ):

            self.step_list.addItem(
                f"{i:2d}. "
                f"{step.duration_seconds:>3}s   "
                f"{step.cpm:>3} CPM   "
                f"{step.intensity_text}"
            )

        self.replay_mode = replay_mode

        self.current_step = -1 if replay_mode else 0

        self.countdown_active = not replay_mode

        self.running = False
        self.started = False

        self.workout_elapsed = 0.0

        self.countdown_remaining = (
            DELAY_SECONDS
            if not replay_mode
            else 0.0
        )

        self.total_remaining = self.total_time

        self.total_time = workout.total_seconds

        self.step_remaining = 0.0
        self.step_elapsed = 0.0

        self.metronome_bar.setValue(0)

        self.title_label.setText(workout.title)

        self.field_label.setText(workout.field)

        self.state_label.setText(
            f"Démarrage dans "
            f"{format_time(self.countdown_remaining)}"
        )

        self.total_label.setText(
            f"Temps total : "
            f"{format_time(self.total_remaining)}"
        )

        self.exercise_label.setText(
            "Préparation..."
        )

        self.rate_label.setText(
            "Cadence : -- CPM"
        )

        self.intensity_label.setText(
            "Intensité : --"
        )

        self.last_tick = time.perf_counter()

        if not self.replay_mode:
            self.timer.start(
                int(1000 / FPS)
            )

        return True

    # ------------------------------------------------------------------
    def update_timer(self):

        now = time.perf_counter()

        elapsed = (
            now - self.last_tick
        )

        self.last_elapsed = elapsed

        if elapsed > 1.0:
            elapsed = 1.0

        self.last_tick = now

        #
        # Délai
        #

        if self.countdown_active:

            self.countdown_remaining -= (
                elapsed
            )

            if self.countdown_remaining <= 0:

                self.countdown_active = False

                self.start_step()

            else:

                self.state_label.setText(
                    f"Démarrage dans "
                    f"{format_time(self.countdown_remaining)}"
                )

            return

        #
        # Workout
        #

        if self.running:

            self.workout_elapsed += elapsed

            self.workout_elapsed = min(
                self.workout_elapsed,
                self.total_time,
            )

            self.total_remaining -= elapsed
            self.step_remaining -= elapsed

            if self.total_remaining < 0:
                self.total_remaining = 0

            if self.step_remaining <= 0:
                self.next_step()
            else:
                self.update_progress()

            self.update_labels()

    # ------------------------------------------------------------------
    def start_step(self):

        if self.current_step >= len(
            self.workout.steps
        ):
            self.finish_workout()
            return

        step = self.workout.steps[
            self.current_step
        ]

        self.step_remaining = (
            step.duration_seconds
        )

        self.step_list.setCurrentRow(
            self.current_step
        )

        self._update_current_step_visuals()

        self.step_list.scrollToItem(
            self.step_list.currentItem(),
            QListWidget.ScrollHint.PositionAtCenter,
        )

        self.beat_phase = 0.0

        self.running = True

        self.metronome_bar.setValue(0)

        self.state_label.setText(
            "Workout en cours"
        )

        self.update_labels()

    # ------------------------------------------------------------------
    def next_step(self):

        self.current_step += 1

        if self.current_step >= len(
            self.workout.steps
        ):
            self.finish_workout()
            return

        self.start_step()

    # ------------------------------------------------------------------
    def update_progress(self):

        if not self.running:
            return

        step = self.workout.steps[
            self.current_step
        ]

        cycle = 60.0 / step.cpm

        self.beat_phase += (
            self.last_elapsed
        )

        if self.beat_phase >= cycle:
            self.beat_phase -= cycle

        progress = (
            self.beat_phase / cycle
        )

        self.metronome_bar.setValue(
            int(progress * 1000)
        )

    # ------------------------------------------------------------------
    def update_labels(self):

        if not self.running:
            return

        step = self.workout.steps[
            self.current_step
        ]

        self.total_label.setText(
            "Temps total : "
            + format_time(
                self.total_remaining
            )
            + " sur "
            + format_time(
                self.total_time
            )
        )

        self.exercise_label.setText(
            f"Exercice "
            f"{self.current_step + 1}/"
            f"{len(self.workout.steps)}  -  "
            f"Temps : "
            f"{format_time(self.step_remaining)}"
        )

        self.rate_label.setText(
            f"Cadence : {step.cpm} CPM"
        )

        self.intensity_label.setText(
            f"Intensité : "
            f"{step.intensity_text}"
        )

        palette = (
            self.intensity_label.palette()
        )

        palette.setColor(
            QPalette.WindowText,
            step.intensity_color,
        )

        self.intensity_label.setPalette(
            palette
        )

    # ------------------------------------------------------------------
    def finish_workout(self):

        self.running = False
        self.timer.stop()

        self.metronome_bar.setValue(
            1000
        )

        self.state_label.setText(
            "Workout terminé !"
        )

        self.exercise_label.setText("")
        self.rate_label.setText("")
        self.intensity_label.setText("")

    # ------------------------------------------------------------------
    def set_replay_mode(
        self,
        enabled: bool,
    ) -> None:

        self.replay_mode = enabled

        if enabled:
            self.timer.stop()

    # ------------------------------------------------------------------
    def update_replay_time(
        self,
        elapsed_time: float,
    ) -> None:

        if not self.replay_mode:
            return

        if not self.workout.steps:
            return

        self.workout_elapsed = min(
            max(0.0, elapsed_time),
            self.total_time,
        )

        remaining = self.workout_elapsed

        last_index = (
            len(self.workout.steps) - 1
        )

        for index, step in enumerate(
            self.workout.steps
        ):

            duration = step.duration_seconds

            if (
                remaining < duration
                or index == last_index
            ):

                new_step = index
                step_elapsed = remaining

                break

            remaining -= duration

        step = self.workout.steps[new_step]

        # Nouveau step
        if new_step != self.current_step:

            self.current_step = new_step

            self._update_current_step_visuals()

            self.step_list.setCurrentRow(
                new_step
            )

            self.step_list.scrollToItem(
                self.step_list.currentItem(),
                QListWidget.ScrollHint.PositionAtCenter,
            )

            self.beat_phase = 0.0

        self.step_elapsed = min(
            step_elapsed,
            step.duration_seconds,
        )

        self.step_remaining = max(
            0.0,
            step.duration_seconds
            - self.step_elapsed,
        )

        self.total_remaining = (
            self.total_time
            - self.workout_elapsed
        )

        self.started = True

        self.running = (
            self.workout_elapsed
            < self.total_time
        )

        # Pas de métronome en Replay.
        self.metronome_bar.setValue(0)

        if self.running:

            self.state_label.setText(
                "Workout en cours"
            )

            self.update_labels()

        else:

            self.state_label.setText(
                "Workout terminé"
            )

    # ------------------------------------------------------------------
    def _update_current_step_visuals(self) -> None:

        if (
            self.current_step is None
            or not self.workout.steps
            or not (
                0 <= self.current_step
                < len(self.workout.steps)
            )
        ):
            return

        color = self.workout.steps[self.current_step].intensity_color

        # --------------------------------------------------------------
        # Bordure de l'étape courante
        # --------------------------------------------------------------

        self.step_list.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {LIST_BACKGROUND};
                color: {TEXT_COLOR};
                border: 1px solid {MENU_SEL_BACKGROUND};
                font: {LIST_FONT_SIZE}px {MAIN_FONT};
            }}

            QListWidget::item {{
                padding: 3px;
                border: 1px solid transparent;
            }}

            QListWidget::item:selected {{
                background-color: transparent;
                color: {TEXT_COLOR};
                border: 2px solid {color};
            }}
            """
        )

        # --------------------------------------------------------------
        # Couleur du métronome
        # --------------------------------------------------------------

        self.metronome_bar.setStyleSheet(
            f"""
            QProgressBar {{
                border: 1px solid {BAR_BORDER};
                border-radius: 4px;
                background: {BAR_BACKGROUND};
            }}

            QProgressBar::chunk {{
                background: {color};
            }}
            """
        )

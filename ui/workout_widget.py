import time

from PySide6.QtCore import Qt, QTimer, Signal
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

from setup.lang import get_text
from setup.utils import (
    load_workout,
    format_time,
    format_duration,
    clamp_to_zero,
    clamp_between,
)
from engine.calc import calc_deltatime
from setup.settings import Settings
from setup.constants import (
    WORKOUT_TIMER_MS,
    BAR_HEIGHT,
    WORKOUT_LIST_FONT_SIZE,
    LIST_WIDTH,
    WINDOW_BACKGROUND,
    LIST_BACKGROUND,
    MENU_SEL_BACKGROUND,
    BAR_BORDER,
    BAR_BACKGROUND,
    BAR_COLOR,
    TEXT_COLOR, LISTTEXT_COLOR,
    WORKOUT_TITLE_FONT_SIZE,
    BIG_FONT_SIZE,
    WORKOUT_INFO_FONT_SIZE,
    MAIN_FONT,
    WORKOUTS_DIR,
)

from workout.workout import Workout

# =============================================================================
class WorkoutWidget(QFrame):

    workout_started = Signal()

    # ------------------------------------------------------------------
    def __init__(
        self,
        settings: Settings,
        metronome_bar: QProgressBar,
        parent=None,
    ) -> None:

        super().__init__(parent)

        self.settings: Settings = settings
        
        self.metronome_bar: QProgressBar = metronome_bar

        self.workout: Workout = Workout()

        self.current_step: int = 0

        self.countdown_active: bool = False
        self.running: bool = False
        self.replay_mode: bool = False

        self.countdown_remaining: float = 0.0
        self.total_remaining_time: float = 0.0
        self.total_time: float = 0.0
        self.step_remaining_time: float = 0.0

        self.started: bool = False
        self.workout_elapsed: float = 0.0

        self.beat_phase: float = 0.0
        self.last_elapsed: float = 0.0
        self.last_tick: float = time.perf_counter()

        self._create_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(
            self.update_timer
        )
        self.model_start_elapsed: float | None = None

    # ------------------------------------------------------------------
    def reset(self) -> None:

        self.timer.stop()

        self.workout = Workout()

        self.current_step = 0

        self.countdown_active = False
        self.running = False
        self.replay_mode = False

        self.countdown_remaining = 0.0
        self.total_remaining_time = 0.0
        self.total_time = 0.0
        self.step_remaining_time = 0.0
        self.step_elapsed = 0.0

        self.started = False
        self.workout_elapsed = 0.0

        self.beat_phase = 0.0
        self.last_elapsed = 0.0
        self.last_tick = time.perf_counter()

        self.step_list.clear()

        self.metronome_bar.setValue(0)

        self._default_label_text()

        palette = self.intensity_label.palette()
        palette.setColor(
            QPalette.WindowText,
            TEXT_COLOR,
        )
        self.intensity_label.setPalette(palette)

        self.info_label.clear()

    # ------------------------------------------------------------------
    def _default_label_text(self) -> None:

        self.title_label.setText(get_text("WORKOUT"))

        self.field_label.setText(get_text("FIELD"))

        self.state_label.setText(get_text("WORKOUT_NONE_LOADED"))

        self.total_label.setText(
            f"{get_text("TOTAL_TIME")} : 00:00"
        )

        self.exercise_label.setText(
            f"{get_text("WORKOUT")} : --"
        )

        self.rate_label.setText(
            f"{get_text("CADENCE")} : -- {get_text("SPM_UNIT")}"
        )

        self.intensity_label.setText(
            f"{get_text("INTENSITY")} : --"
        )

        self.info_label.setText("--")

    # ------------------------------------------------------------------
    def _create_ui(self) -> None:

        self.setStyleSheet(
            f"""
            WorkoutWidget {{
                background-color: {WINDOW_BACKGROUND};
            }}
            """
        )

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

        layout.setSpacing(8)
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

        self.title_label = QLabel()
        self.field_label = QLabel()
        self.state_label = QLabel()
        self.total_label = QLabel()
        self.exercise_label = QLabel()
        self.rate_label = QLabel()
        self.intensity_label = QLabel()
        self.info_label = QLabel()

        self._default_label_text()

        self.info_label.setWordWrap(True)

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
                    font: bold {WORKOUT_TITLE_FONT_SIZE}px
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
            self.info_label,
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

            font = (
                BIG_FONT_SIZE
                if label is not self.info_label
                else WORKOUT_INFO_FONT_SIZE
            )

            label.setStyleSheet(
                f"""
                QLabel {{
                    {color}
                    background-color: {bgcolor};
                    font: bold {font}px {MAIN_FONT};
                }}
                """
            )

        for label in (
            self.title_label,
            self.field_label,
            self.state_label,
            self.total_label,
            self.exercise_label,
            self.rate_label,
            self.intensity_label,
            self.info_label,
        ):

            layout.addWidget(
                label
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
                font: {WORKOUT_LIST_FONT_SIZE}px {MAIN_FONT};
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
    def _configure_metronome_bar(self) -> None:

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
        filename: str | None = None,
        replay_mode: bool = False,
    ) -> bool:

        if filename is None:

            default_dir = WORKOUTS_DIR

            filename, _ = QFileDialog.getOpenFileName(
                self,
                get_text("WORKOUT_FILE_SELECT"),
                str(default_dir),
                get_text("WORKOUT_FILE_EXT"),
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
                get_text("ERROR"),
                str(exc),
            )

            return False

        self.workout = workout

        self.model_start_elapsed = None

        self.step_list.clear()

        for i, step in enumerate(
            workout.steps,
            start=1,
        ):

            formatted_duration = format_duration(step.duration_seconds)

            self.step_list.addItem(
                f"{i:2d}. "
                f"{formatted_duration}   "
                f"{step.spm:>3} {get_text("SPM_UNIT")}   "
                f"{step.intensity_text}"
            )

        self.replay_mode = replay_mode

        self.current_step = -1 if replay_mode else 0

        self.countdown_active = not replay_mode

        self.running = False
        self.started = False

        self.workout_elapsed = 0.0

        self.countdown_remaining = (
            self.settings.delay_seconds
            if not replay_mode
            else 0.0
        )

        self.total_time = workout.total_seconds
        self.total_remaining_time = self.total_time

        self.step_remaining_time = 0.0
        self.step_elapsed = 0.0

        self.metronome_bar.setValue(0)

        self.title_label.setText(workout.title)

        self.field_label.setText(workout.field)

        self.state_label.setText(
            f"{get_text("WORKOUT_STARTS_IN")} "
            f"{format_time(self.countdown_remaining)}"
        )

        self.total_label.setText(
            f"{get_text("TOTAL_TIME")} : "
            f"{format_time(self.total_remaining_time)}"
        )

        self.exercise_label.setText(
            get_text("WORKOUT_PREPARING")
        )

        self.rate_label.setText(
            f"{get_text("CADENCE")} : -- {get_text("SPM_UNIT")}"
        )

        self.intensity_label.setText(
            f"{get_text("INTENSITY")} : --"
        )

        self.info_label.clear()

        self.last_tick = time.perf_counter()

        if not self.replay_mode:
            self.timer.start(int(WORKOUT_TIMER_MS))

        return True

    # ------------------------------------------------------------------
    def update_timer(self) -> None:

        now = time.perf_counter()

        elapsed = calc_deltatime(now, self.last_tick)

        self.last_elapsed = elapsed

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
                    f"{get_text("WORKOUT_STARTS_IN")}"
                    f" {format_time(self.countdown_remaining)}"
                )

            return

        #
        # Workout
        #

        if self.running:

            # Le temps du workout est piloté par le modèle
            # (Q1S ou Replay), pas par le QTimer du GUI.
            # Le timer ne sert ici qu'au compte à rebours et au
            # rafraîchissement de l'affichage.

            if self.model_start_elapsed is not None:
                self._update_from_model_elapsed(
                    self.model_start_elapsed + self.workout_elapsed
                )

    # ------------------------------------------------------------------
    def start_step(self) -> None:

        if self.current_step >= len(self.workout.steps):
            self.finish_workout()
            return

        step = self.workout.steps[
            self.current_step
        ]

        self.step_remaining_time = (
            step.duration_seconds
        )

        self._select_step(
            self.current_step
        )

        self.running = True
        self.started = True

        self.metronome_bar.setValue(0)

        self.state_label.setText(
            get_text("WORKOUT_RUNNING")
        )

        self.update_labels()

    # ------------------------------------------------------------------
    def update_progress(self) -> None:

        if not self.running:
            return

        step = self.workout.steps[
            self.current_step
        ]

        cycle = 60.0 / step.spm

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
    def update_labels(self) -> None:

        if not self.running:
            return

        step = self.workout.steps[
            self.current_step
        ]

        self.total_label.setText(
            f"{get_text("TOTAL_TIME")} : "
            + format_time(
                self.total_remaining_time
            )
            + get_text("TOTAL_TIME_OF")
            + format_time(
                self.total_time
            )
        )

        self.exercise_label.setText(
            f"{get_text("WORKOUT")} "
            f"{self.current_step + 1}/"
            f"{len(self.workout.steps)}  -  "
            f"{get_text("TIME")} : "
            f"{format_time(self.step_remaining_time)}"
        )

        self.rate_label.setText(
            f"{get_text("CADENCE")} : "
            f"{step.spm} {get_text("SPM_UNIT")}"
        )

        self.intensity_label.setText(
            f"{get_text("INTENSITY")} : "
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

        if step.info:
            self.info_label.setText(
                step.info
            )
        else:
            self.info_label.clear()

    # ------------------------------------------------------------------
    def finish_workout(self) -> None:

        self.running = False
        self.started = False
        self.timer.stop()

        self.metronome_bar.setValue(
            1000
            if not self.replay_mode
            else 0
        )

        self.state_label.setText(
            f"{get_text("WORKOUT_COMPLETE")} !"
        )

        self.exercise_label.clear()
        self.rate_label.clear()
        self.intensity_label.clear()
        self.info_label.clear()

    # ------------------------------------------------------------------
    def _update_from_model_elapsed(
        self,
        elapsed_time: float,
    ) -> None:

        if not self.running and not self.replay_mode:
            return

        if self.model_start_elapsed is None:
            self.model_start_elapsed = clamp_to_zero(
                float(elapsed_time)
            )
            self.workout_started.emit()

        self.workout_elapsed = clamp_between(
            calc_deltatime(
                float(elapsed_time),
                self.model_start_elapsed
            ),
            0.0,
            self.total_time,
        )

        if self.workout_elapsed >= self.total_time:
            self.finish_workout()
            return

        step_info = self.workout.find_step(
            self.workout_elapsed
        )

        if step_info is None:
            return

        new_step, step_elapsed = step_info

        if new_step != self.current_step:
            self._select_step(new_step)

        step = self.workout.steps[new_step]

        self.step_elapsed = min(
            step.duration_seconds,
            step_elapsed,
        )

        self.step_remaining_time = clamp_to_zero(
            calc_deltatime(
                step.duration_seconds,
                self.step_elapsed,
            )
        )

        self.total_remaining_time = clamp_to_zero(
            calc_deltatime(
                self.total_time,
                self.workout_elapsed,
            )
        )

        self.running = True
        self.started = True

        self.update_progress()
        self.update_labels()

    # ------------------------------------------------------------------
    def update_model_time(
        self,
        elapsed_time: float,
    ) -> None:

        if not self.workout.steps:
            return

        if self.replay_mode:
            self.model_start_elapsed = 0.0

        self._update_from_model_elapsed(elapsed_time)

    # ------------------------------------------------------------------
    def _select_step(self, step_index: int) -> None:

        self.current_step = step_index

        self._update_current_step_visuals()

        self.step_list.setCurrentRow(
            step_index
        )

        self.step_list.scrollToItem(
            self.step_list.currentItem(),
            QListWidget.ScrollHint.PositionAtCenter,
        )

        self.beat_phase = 0.0

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
                font: {WORKOUT_LIST_FONT_SIZE}px {MAIN_FONT};
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

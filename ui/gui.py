"""
gui.py

Fenêtre principale.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QGridLayout,
    QMainWindow,
    QWidget,
    QPushButton,
    QButtonGroup,
    QRadioButton,
    QVBoxLayout,
    QHBoxLayout,
    QProgressBar,
    QLabel,
    QSizePolicy,
    QFileDialog,
    QMessageBox,
    QDialog,
)

from setup.lang import get_text
from setup.utils import (
    format_pace,
    format_time,
    load_workout,
)
from setup.settings_utils import save_settings
from setup.constants import (
    GUI_REFRESH_MS,
    WINDOW_WIDTH, WINDOW_HEIGHT,
    WORKOUT_WIDTH, WORKOUT_HEIGHT,
    METRONOME_MARGIN,
    SPLIT_MODES,
    USE_REPLAY, USE_REPLAY_WORKOUT,
    REPLAY_WORKOUT_FILE,
    LOGS_DIR, WORKOUTS_DIR,
)
from setup.cnx_enum import CnxState

from ui.status_widget import StatusWidget
from ui.widgets import MetricWidget
from ui.split_widget import SplitListWidget
from ui.progbar_widget import GradientGauge
from ui.workout_widget import WorkoutWidget
from ui.settings_dialog import SettingsDialog
from ui.workout_editor import WorkoutEditorDialog

from workout.split import WorkoutSplitCalculator

from tools.analyzer import AnalyzerWindow
from tools.plot_wo import WorkoutPlotWindow

# =============================================================================
class MainWindow(QMainWindow):

    def __init__(self, state, settings) -> None:

        super().__init__()

        self.state = state
        self.settings = settings

        self._workout_editor_paused = False

        self._create_ui()

        #
        # Rafraîchissement
        #

        self._apply_split_mode_preference()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(GUI_REFRESH_MS)

        self.refresh()

    # ------------------------------------------------------------------
    def _create_ui(self) -> None:
        self.setWindowTitle(f"{get_text("WINDOW_TITLE")} : {self.state.rower.NAME}")

        self.create_menu()

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(
            10, 10, 10, 10
        )
        main_layout.setSpacing(10)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)

        main_layout.addLayout(
            top_layout
        )

        rower_panel = QWidget()

        rower_panel.setFixedSize(
            WINDOW_WIDTH,
            WINDOW_HEIGHT,
        )

        grid = QGridLayout(rower_panel)

        grid.setContentsMargins(15, 15, 15, 15)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        top_layout.addWidget(
            rower_panel,
            0,
        )

        #
        # Ligne 0 : Etat Bluetooth
        #

        self.connectionWidget = StatusWidget()

        grid.addWidget(
            self.connectionWidget,
            0, # row
            0, # column
            1, # rowSpan
            3, # columnSpan
        )

        #
        # Widgets
        #

        self.timeWidget = MetricWidget(
            title= get_text("TIME"),
            unit= "h:mm:ss",
        )

        self.distanceWidget = MetricWidget(
            title= get_text("DISTANCE"),
            unit= "m",
        )

        self.speedWidget = MetricWidget(
            title= get_text("SPEED"),
            unit= f"m/s  /  {get_text("AVG")}",
            gauge= GradientGauge(
                zones=[0, 2, 4, 6, 8], # 2 à 6 m/s est plus réaliste pour femme-débutante à homme-très-confirmé
            ),
        )

        self.strokeWidget = MetricWidget(
            title= f"{get_text("STROKE")}s",
        )

        self.distStrokeWidget = MetricWidget(
            title= get_text("DPS"),
            unit= f"m/{get_text("STROKE").lower()}  /  {get_text("AVG")}",
            gauge= GradientGauge(
                zones=[0, 5, 10, 15, 20], # 6 à 15 m/coup est plus réaliste pour femme-débutante à homme-très-confirmé
            ),
        )

        self.powerWidget = MetricWidget(
            title= get_text("POWER"),
            unit= f"W  /  W {get_text("AVG")}",
            gauge= GradientGauge(
                zones=[0, 100, 200, 300, 400], # 60 à 350 W est plus réaliste pour femme-débutante à homme-très-confirmé
            ),
        )

        self.cadenceWidget = MetricWidget(
            title= get_text("CADENCE"),
            unit= f"{get_text("SPM_UNIT")}  /  {get_text("AVG")}",
            gauge= GradientGauge(
                zones=[10, 20, 24, 30, 40], # 18 à 34 est plus réaliste pour h/f-débutant à h/f-très-confirmé
            ),
        )

        self.splitWidget = MetricWidget(
            title= get_text("SPLIT"),
            unit= f"mm:ss/500m  /  {get_text("AVG")}",
            gauge= GradientGauge(
                zones=[80, 100, 130, 160, 200], # en sec/500m ; 2:55 à 1:45 mm:ss/500m est plus réaliste pour femme-débutante à homme-très-confirmé
                inverted= True,
            ),
        )

        self.splitListWidget = SplitListWidget(
            settings= self.settings,
        )

        # Split selector : radiobutton

        splitMode_label   = QLabel(get_text("SPLIT_MODE_TITLE"))

        self.splitModeNormal  = QRadioButton("Normal")
        self.splitMode500m    = QRadioButton("500m")
        self.splitModeWorkout = QRadioButton("Workout")

        split_mode_list = [self.splitModeNormal, self.splitMode500m, self.splitModeWorkout]

        for modebtn in split_mode_list:
            modebtn.setEnabled(True)

        self.splitModeWorkout.setEnabled(False) # disabled until a workout is loaded

        self.splitModeNormal.setChecked(True) # default mode

        self.splitModeGroup = QButtonGroup(self)

        self.splitModeGroup.addButton(
            self.splitModeNormal,
            0,
        )

        self.splitModeGroup.addButton(
            self.splitMode500m,
            1,
        )

        self.splitModeGroup.addButton(
            self.splitModeWorkout,
            2,
        )

        self.splitModeGroup.idClicked.connect(
            self.set_split_mode
        )

        # split widget

        splitContainer = QWidget()
        splitLayout = QVBoxLayout(splitContainer)
        splitLayout.setContentsMargins(0, 0, 0, 0)
        splitLayout.setSpacing(4)

        splitLayout.addWidget(self.splitWidget)
        splitLayout.addWidget(self.splitListWidget)

        self.splitListWidget.setVisible(False)

        self.caloriesWidget = MetricWidget(
            title= get_text("CALORIES"),
            unit= "kcal/s  /  kcal",
        )

        #
        # Ligne 1
        #

        grid.addWidget(self.timeWidget,       1, 0) # row, column
        grid.addWidget(self.distanceWidget,   1, 1) # row, column
        grid.addWidget(self.speedWidget,      1, 2) # row, column

        #
        # Ligne 2
        #

        grid.addWidget(self.strokeWidget,     2, 0) # row, column
        grid.addWidget(self.distStrokeWidget, 2, 1) # row, column
        grid.addWidget(self.powerWidget,      2, 2) # row, column

        #
        # Ligne 3
        # Note: splitWidget and the container for SplitList is on the some
        # cell of the grid and we will display on or the other by clicking
        # the splitModeCheck button
        #

        grid.addWidget(self.cadenceWidget,     3, 0) # row, column
        grid.addWidget(splitContainer,         3, 1) # row, column
        grid.addWidget(self.caloriesWidget,    3, 2) # row, column

        #
        # Ligne 4 : Bouton Reset (new session) et radiobutton pour le Splut widget
        #

        self.resetButton = QPushButton(
            get_text("NEW_SESSION")
        )

        self.resetButton.clicked.connect(
            self.new_session
        )

        self.splitModeLayout = QHBoxLayout()

        self.splitModeLayout.setContentsMargins(
            0, 0, 0, 0
        )

        self.splitModeLayout.addStretch()

        self.splitModeLayout.addWidget(splitMode_label)
        for modebtn in split_mode_list:
            self.splitModeLayout.addWidget(modebtn)

        self.splitModeLayout.addStretch()

        grid.addWidget(self.resetButton,      4, 0) # row, column
        grid.addLayout(self.splitModeLayout,  4, 1) # row, column

        #
        # Workout
        #

        self.workout_bar = QProgressBar()

        self.workoutWidget = WorkoutWidget(
            settings= self.settings,
            metronome_bar=self.workout_bar,
        )

        self.workoutWidget.setMinimumWidth(
            WORKOUT_WIDTH
        )

        self.workoutWidget.setMaximumWidth(
            WORKOUT_HEIGHT
        )

        self.workoutWidget.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Expanding,
        )

        self.workoutWidget.setVisible(
            False
        )

        self.workoutWidget.workout_started.connect(
            self._workout_started
        )

        top_layout.addWidget(
            self.workoutWidget,
            1,
        )

        self.workoutSplitCalculator = WorkoutSplitCalculator(
            self.settings
        )

        #
        # Workout : Metronome
        #

        self.metronome_container = QWidget()

        metronome_layout = QHBoxLayout(
            self.metronome_container
        )

        metronome_layout.setContentsMargins(
            0, 0, 0, 0
        )

        metronome_layout.addSpacing(
            METRONOME_MARGIN
        )

        self.metronome_label = QLabel("CPM")

        self.metronome_label.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter
        )

        metronome_layout.addWidget(
            self.metronome_label
        )

        metronome_layout.addWidget(
            self.workout_bar,
            1,
        )

        metronome_layout.addSpacing(
            METRONOME_MARGIN
        )

        main_layout.addWidget(
            self.metronome_container
        )

        self.metronome_container.setVisible(False)

    # -------------------------------------------------------------------------
    def create_menu(self) -> None:

        #
        # Workout >
        #   Ouvrir un .wo
        #   Créer un .wo
        #   Editer un .wo
        #

        workout_menu = self.menuBar().addMenu(
            get_text("MENU_WORKOUT")
        )

        open_workout_action = workout_menu.addAction(
            get_text("MENU_WORKOUT_OPEN")
        )
        open_workout_action.triggered.connect(self.open_workout_file)

        create_workout_action = workout_menu.addAction(
            get_text("MENU_WORKOUT_CREATE")
        )
        create_workout_action.triggered.connect(self.create_workout)

        edit_workout_action = workout_menu.addAction(
            get_text("MENU_WORKOUT_EDIT")
        )
        edit_workout_action.triggered.connect(self.edit_workout)

        #
        # Tools >
        #   Analyser un log
        #   Visualiser un .wo
        #

        tools_menu = self.menuBar().addMenu(
            get_text("MENU_TOOLS")
        )

        analyzer_action = tools_menu.addAction(
            get_text("MENU_TOOLS_ANALYZER")
        )

        analyzer_action.triggered.connect(
            self.open_analyzer
        )

        plot_wo_action = tools_menu.addAction(
            get_text("MENU_TOOLS_PLOT")
        )

        plot_wo_action.triggered.connect(
            self.open_plot_wo
        )

        #
        # Réglages >
        #   Paramètres...
        #

        settings_menu = self.menuBar().addMenu(
            get_text("MENU_SETTINGS")
        )

        settings_action = settings_menu.addAction(
            f"{get_text("SETTINGS")}..."
        )

        settings_action.triggered.connect(
            self.open_settings
        )

        #Desactive le Réglage des Paramètres en Replay"
        settings_action.setEnabled(
            not USE_REPLAY
        )

    # -------------------------------------------------------------------------
    def _workout_started(self) -> None:

        rowerdata = self.state.snapshot().rowerdata

        self.workoutSplitCalculator.start(
            distance=rowerdata.distance,
        )

    # -------------------------------------------------------------------------
    def set_split_mode(
        self,
        mode: int,
    ) -> None:

        if mode == 0: # NORMAL

            self.splitWidget.setVisible(True)
            self.splitListWidget.setVisible(False)

        else:

            self.splitWidget.setVisible(False)
            self.splitListWidget.setVisible(True)

            rowerdata = (
                self.state.snapshot().rowerdata
            )

            if mode == 1: # SPLIT_500m

                self.splitListWidget.set_splits(
                    rowerdata.splits
                )

            elif mode == 2: # SPLIT_WORKOUT

                self.splitListWidget.set_workout_splits(
                    self.workoutWidget.workout,
                    self.workoutSplitCalculator.splits,
                    self.workoutSplitCalculator.current_step,
                )

    # -------------------------------------------------------------------------
    def new_session(self) -> None:

        logger = self.state.logger

        if logger is not None:
            logger.flush()
            logger.stop()

        # --------------------------------------------------------------
        # Ferme le workout courant.
        # --------------------------------------------------------------

        self.close_workout()

        # --------------------------------------------------------------
        # Mode Replay
        # --------------------------------------------------------------

        if USE_REPLAY:

            if USE_REPLAY_WORKOUT:

                self.load_workout_file(
                    filename=REPLAY_WORKOUT_FILE,
                    replay_mode=True,
                )

            self.state.reset_session()

            if logger is not None:
                logger.start()
                self.state.set_logger(logger)

            self.state.source.restart()

        # --------------------------------------------------------------
        # Mode réel
        # --------------------------------------------------------------

        else:

            QMessageBox.information(
                self,
                get_text("NEW_SESSION"),
                get_text("MSG_RESET_ROWER"),
            )

            # Reset du modèle/calculateur local.
            self.state.rower.reset()

            # La prochaine trame Bluetooth devient
            # la nouvelle référence de séance.
            self.state.reset_session()

            if logger is not None:
                logger.start()
                self.state.set_logger(logger)

        self.refresh()

    # -------------------------------------------------------------------------
    def refresh(self) -> None:
        
        snapshot = self.state.snapshot()

        rowerdata = snapshot.rowerdata

        #
        # Bluetooth
        #

        if self._workout_editor_paused:
            self.connectionWidget.set_status(CnxState.PAUSE)
        else:
            self.connectionWidget.set_status(rowerdata.connection)

        #
        # Temps
        #

        self.timeWidget.setValue(
            textvalue= format_time(rowerdata.elapsed_time)
        )

        #
        # Distance
        #

        self.distanceWidget.setValue(
            textvalue= f"{rowerdata.distance:.0f}"
        )

        #
        # Vitesse et Vmoy
        # + Gauge
        #

        self.speedWidget.setValue(
            textvalue= f"{rowerdata.speed:.2f} / {rowerdata.speed_avg:.2f}",
            gaugevalue= rowerdata.speed
        )

        #
        # Coups
        #

        self.strokeWidget.setValue(
            textvalue= rowerdata.stroke_count
        )

        #
        # Distance/coup et DpS moyenne
        # + Gauge
        #

        self.distStrokeWidget.setValue(
            textvalue= f"{rowerdata.distance_per_stroke:.2f} / {rowerdata.dist_per_stroke_avg:.2f}",
            gaugevalue= rowerdata.distance_per_stroke
        )

        #
        # Puissance (recalibrée) et P moyenne
        # + Gauge
        #

        self.powerWidget.setValue(
            textvalue= f"{rowerdata.power:.0f} / {rowerdata.power_avg:.0f}",
            gaugevalue=rowerdata.power
        )

        #
        # Cadence et SPM moyen
        # + Gauge
        #

        self.cadenceWidget.setValue(
            textvalue= f"{rowerdata.cadence:.1f} / {rowerdata.cadence_avg:.1f}",
            gaugevalue= rowerdata.cadence
        )

        #
        # Split et Split Moyen
        # + Gauge
        #

        self.splitWidget.setValue(
            textvalue= f"{format_pace(rowerdata.split_inst)} / {format_pace(rowerdata.split_avg)}",
            gaugevalue= rowerdata.split_inst
        )

        if (
            USE_REPLAY
            and self.workoutWidget.replay_mode
        ):
            self.workoutWidget.update_replay_time(
                rowerdata.elapsed_time
            )

        if self.workoutWidget.started:

            self.workoutSplitCalculator.update(
                workout_elapsed=(
                    self.workoutWidget.workout_elapsed
                ),
                distance=rowerdata.distance,
            )

        if self.splitMode500m.isChecked():
            self.splitListWidget.set_splits(
                rowerdata.splits
            )

        elif self.splitModeWorkout.isChecked():

            self.splitListWidget.set_workout_splits(
                self.workoutWidget.workout,
                self.workoutSplitCalculator.splits,
                self.workoutSplitCalculator.current_step,
            )

        #
        # Calories Rate et Calories Totales
        #
        self.caloriesWidget.setValue(
            textvalue= f"{rowerdata.calories_rate:.3f} / {rowerdata.calories:.1f}"
        )

    # -------------------------------------------------------------------------
    def _edit_workout_dialog(self, workout= None) -> None:
        # Pas d'édition pendant une séance.
        if self.workoutWidget.started:
            QMessageBox.warning(
                self,
                get_text("WARNING"),
                get_text("WARN_CANT_EDIT_WO"),
            )
            return

        source = self.state.source

        self._workout_editor_paused = True

        if source is not None:
            source.stop()

        try:
            dialog = WorkoutEditorDialog(
                workout=workout,
                parent=self,
            )
            dialog.exec()

        finally:
            self._workout_editor_paused = False

            if source is not None:
                source.start()

    # -------------------------------------------------------------------------
    def create_workout(self) -> None:
        self._edit_workout_dialog()

    # -------------------------------------------------------------------------
    def edit_workout(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            get_text("WO_EDIT_TITLE"),
            str(WORKOUTS_DIR),
            "Workout (*.wo)",
        )

        if not filename:
            return

        workout = load_workout(filename)

        self._edit_workout_dialog(workout)

    # -------------------------------------------------------------------------
    def open_workout_file(self) -> None:

        self.load_workout_file(
            filename=None,
            replay_mode=False,
        )

    # -------------------------------------------------------------------------
    def load_workout_file(
        self,
        filename=None,
        replay_mode: bool = False,
    ) -> bool:

        if not self.workoutWidget.open_setup(
            filename=filename,
            replay_mode=replay_mode,
        ):
            return False

        logger = self.state.logger

        if logger is not None:
            logger.set_workout_file(
                self.workoutWidget.workout.filename
            )

        self.workoutSplitCalculator.reset(
            self.workoutWidget.workout
        )

        self.splitModeWorkout.setEnabled(True)

        self.workoutWidget.setVisible(True)
        self.metronome_container.setVisible(True)

        self._apply_split_mode_preference()

        return True

    # -------------------------------------------------------------------------
    def open_analyzer(self) -> None:

        filename, _ = QFileDialog.getOpenFileName(
            self,
            get_text("LOG_FILE_SELECT"),
            str(LOGS_DIR),
            get_text("LOG_FILE_EXT"),
        )

        if not filename:
            return

        self.analyzer_window = AnalyzerWindow(
            filename,
        )

        self.analyzer_window.show()

    # -------------------------------------------------------------------------
    def open_plot_wo(self) -> None:

        filename, _ = QFileDialog.getOpenFileName(
            self,
            get_text("WORKOUT_FILE_SELECT"),
            str(WORKOUTS_DIR),
            get_text("WORKOUT_FILE_EXT"),
        )

        if not filename:
            return

        try:

            self.plot_workout_window = (
                WorkoutPlotWindow(
                    filename,
                )
            )

            self.plot_workout_window.show()

        except Exception as exc:

            QMessageBox.warning(
                self,
                get_text("ERROR"),
                f"{get_text("ERR_LOAD_WORKOUT")}\n{exc}",
            )

    # -------------------------------------------------------------------------
    def closeEvent(self, event) -> None:
        # Arrête le moteur principal.
        if self.state.source is not None:
            self.state.source.stop()

        # Ferme les fenêtres outils.
        for window in (
            getattr(self, "analyzer_window", None),
            getattr(self, "plot_workout_window", None),
        ):
            if window is not None:
                window.close()

        event.accept()

    # -------------------------------------------------------------------------
    def close_workout(self) -> None:

        self.workoutWidget.reset()

        self.workoutSplitCalculator.reset()

        self.workoutWidget.setVisible(False)
        self.metronome_container.setVisible(False)

        self.splitModeWorkout.setChecked(False)
        self.splitModeWorkout.setEnabled(False)

        logger = self.state.logger

        if logger is not None:
            logger.set_workout_file(None)

        self._apply_split_mode_preference()

        self.centralWidget().adjustSize()
        self.resize(
            self.sizeHint()
        )

    # -------------------------------------------------------------------------
    def open_settings(self) -> None:

        # On évite de modifier SPLIT_LENGTH en plein milieu
        # d'une session active.
        rowerdata = self.state.snapshot().rowerdata

        if rowerdata.elapsed_time > 0.0:
            QMessageBox.information(
                self,
                get_text("SETTINGS"),
                get_text("WARN_NO_SETTINGS"),
            )
            return

        old_language_setting = self.settings.language

        dialog = SettingsDialog(
            self.settings,
            self,
        )

        if dialog.exec() != QDialog.Accepted:
            return

        dialog.apply_to(
            self.settings
        )

        save_settings(
            self.settings
        )

        if self.settings.language != old_language_setting:
            QMessageBox.information(
                self,
                get_text("SETTINGS"),
                get_text("LANGUAGE_RESTART_REQUIRED"),
            )

    # -------------------------------------------------------------------------
    def _apply_split_mode_preference(self) -> None:

        mode = self.settings.split_mode

        # Si le choix par défaut de l'utilisateur est "Workout"
        # alors on force à "Normal" si aucun Workout n'est chargé
        # mais on applique Split Mode = "Workout" si un .wo est chargé.
        # Note: Si un .wo est chargé, alors workoutWidget est visible.
        # Si le choix par défaut est "Workout", on ne peut l'utiliser
        # que lorsqu'un Workout est effectivement chargé.
        if (
            mode == "workout"
            and not self.splitModeWorkout.isEnabled()
        ):
            mode = "normal"

        mode_index = SPLIT_MODES.index(mode)

        button = self.splitModeGroup.button(mode_index)

        if button is not None:
            button.setChecked(True)

        self.set_split_mode(mode_index)
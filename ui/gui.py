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

from setup.constants import (
    GUI_REFRESH_MS,
    WINDOW_TITLE,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WORKOUT_WIDTH,
    METRONOME_MARGIN,
    SPLIT_MODES,
    USE_REPLAY, USE_REPLAY_WORKOUT,
    REPLAY_WORKOUT_FILE,
    LOGS_DIR, WORKOUTS_DIR,
    ANALYZER_WIDTH, ANALYZER_HEIGHT,
)

from setup.utils import (
    format_pace,
    format_time,
)

from ui.status_widget import StatusWidget
from ui.widgets import MetricWidget, SplitListWidget
from ui.progbar_widget import GradientGauge
from ui.workout_widget import WorkoutWidget
from ui.settings_dialog import SettingsDialog
from ui.plot_wo import WorkoutPlotWindow

from workout.split import WorkoutSplitCalculator
from analyzer.analyzer import AnalyzerWindow
from setup.settings import save_settings

# =============================================================================
class MainWindow(QMainWindow):

    # -------------------------------------------------------------------------
    def __init__(self, state, settings):

        super().__init__()

        self.state = state
        self.settings = settings

        self.setWindowTitle(f"{WINDOW_TITLE} : {self.state.rower.NAME}")

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
            title= "Temps",
            unit= "h:mm:ss",
        )

        self.distanceWidget = MetricWidget(
            title= "Distance",
            unit= "m",
        )

        self.speedWidget = MetricWidget(
            title= "Vitesse",
            unit= "m/s  /  moy",
            gauge= GradientGauge(
                zones=[0, 2, 4, 6, 8], # 2 à 6 m/s est plus réaliste pour femme-débutante à homme-très-confirmé
            ),
        )

        self.strokeWidget = MetricWidget(
            title= "Coups",
        )

        self.distStrokeWidget = MetricWidget(
            title= "Dist/Coup",
            unit= "m/coup  /  moy",
            gauge= GradientGauge(
                zones=[0, 5, 10, 15, 20], # 6 à 15 m/coup est plus réaliste pour femme-débutante à homme-très-confirmé
            ),
        )

        self.powerWidget = MetricWidget(
            title= "Puissance",
            unit= "W  /  W moy",
            gauge= GradientGauge(
                zones=[0, 100, 200, 300, 400], # 60 à 350 W est plus réaliste pour femme-débutante à homme-très-confirmé
            ),
        )

        self.cadenceWidget = MetricWidget(
            title= "Cadence",
            unit= "cpm  /  cpm moy",
            gauge= GradientGauge(
                zones=[10, 20, 24, 30, 40], # 18 à 34 est plus réaliste pour h/f-débutant à h/f-très-confirmé
            ),
        )

        self.splitWidget = MetricWidget(
            title= "Split",
            unit= "mm:ss/500m  /  moy",
            gauge= GradientGauge(
                zones=[80, 100, 130, 160, 200], # en sec/500m ; 2:55 à 1:45 mm:ss/500m est plus réaliste pour femme-débutante à homme-très-confirmé
                inverted= True,
            ),
        )

        self.splitListWidget = SplitListWidget(
            settings= self.settings,
        )

        # Split selector : radiobutton

        splitMode_label   = QLabel("Split Mode:")

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
            title= "Calories",
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
            "Nouvelle séance"
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
            700
        )

        self.workoutWidget.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Expanding,
        )

        self.workoutWidget.setVisible(
            False
        )

        self.workout_bar.setVisible(
            False
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

        metronome_layout = QHBoxLayout()

        metronome_layout.addSpacing(METRONOME_MARGIN)

        metronome_label = QLabel("CPM")

        metronome_label.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter
        )

        metronome_layout.addWidget(
            metronome_label
        )

        metronome_layout.addWidget(
            self.workout_bar,
            1,
        )

        metronome_layout.addSpacing(METRONOME_MARGIN)

        main_layout.addLayout(
            metronome_layout
        )

        self.workout_bar.setVisible(False)

        #
        # Rafraîchissement
        #

        self._apply_split_mode_preference()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(GUI_REFRESH_MS)

        self.refresh()

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
        # Réinitialisation / préparation du Workout
        # --------------------------------------------------------------

        if USE_REPLAY and USE_REPLAY_WORKOUT:

            # On repart du même workout que celui configuré
            # pour le replay.
            self.close_workout()

            self.load_workout_file(
                filename=REPLAY_WORKOUT_FILE,
                replay_mode=True,
            )

        else:

            # En mode réel, un nouveau workout doit être choisi.
            self.close_workout()

        # --------------------------------------------------------------
        # Nouvelle session Q1S
        # --------------------------------------------------------------

        self.state.reset_session()

        # --------------------------------------------------------------
        # Nouveau logger
        # Le workout éventuel est déjà défini à ce stade.
        # --------------------------------------------------------------

        if logger is not None:
            logger.start()
            self.state.set_logger(logger)

        # --------------------------------------------------------------
        # Nouvelle source
        # --------------------------------------------------------------

        if USE_REPLAY:
            self.state.source.restart()
        else:
            self.state.rower.reset()

        self.refresh()


    # -------------------------------------------------------------------------
    def refresh(self):
        
        snapshot = self.state.snapshot()

        rowerdata = snapshot.rowerdata

        #
        # Bluetooth
        #

        self.connectionWidget.set_status(
            rowerdata.connection
        )

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
    def create_menu(self):

        #
        # File >
        #   Ouvrir un .wo
        #

        file_menu = self.menuBar().addMenu(
            "Fichier"
        )

        workout_action = file_menu.addAction(
            "Ouvrir un workout..."
        )

        workout_action.triggered.connect(
            self.open_workout
        )

        #
        # Tools >
        #   Analyser un log
        #   Visualiser un .wo
        #

        tools_menu = self.menuBar().addMenu(
            "Outils"
        )

        analyzer_action = tools_menu.addAction(
            "Analyser un log..."
        )

        analyzer_action.triggered.connect(
            self.open_analyzer
        )

        plot_wo_action = tools_menu.addAction(
            "Visualiser un .wo..."
        )

        plot_wo_action.triggered.connect(
            self.open_plot_wo
        )

        #
        # Réglages >
        #   Paramètres...
        #

        settings_menu = self.menuBar().addMenu(
            "Réglages"
        )

        settings_action = settings_menu.addAction(
            "Paramètres..."
        )

        settings_action.triggered.connect(
            self.open_settings
        )

        #Desactive le Réglage des Paramètres en Replay"
        settings_action.setEnabled(
            not USE_REPLAY
        )

    # -------------------------------------------------------------------------
    def open_workout(self):

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
        self.workout_bar.setVisible(True)

        self._apply_split_mode_preference()

        return True

    # -------------------------------------------------------------------------
    def open_analyzer(self):

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir un log",
            str(LOGS_DIR),
            "Logs (*.csv *.zip);;Tous les fichiers (*)",
        )

        if not filename:
            return

        self.analyzer_window = AnalyzerWindow(
            filename,
        )

        self.analyzer_window.resize(
            ANALYZER_WIDTH,
            ANALYZER_HEIGHT,
        )

        self.analyzer_window.show()

    # -------------------------------------------------------------------------
    def open_plot_wo(self):

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir un workout",
            str(WORKOUTS_DIR),
            "Workout (*.wo);;Tous les fichiers (*)",
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
                "Erreur",
                f"Impossible de charger le workout.\n\n{exc}",
            )

    # -------------------------------------------------------------------------
    def closeEvent(self, event):
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

        self.workoutWidget.timer.stop()

        self.workoutWidget.setVisible(False)
        self.workout_bar.setVisible(False)

        self.workoutSplitCalculator.reset()

        self.splitModeWorkout.setChecked(False)
        self.splitModeWorkout.setEnabled(False)

        logger = self.state.logger

        if logger is not None:
            logger.set_workout_file(None)

    # -------------------------------------------------------------------------
    def open_settings(self):

        # On évite de modifier SPLIT_LENGTH en plein milieu
        # d'une session active.
        rowerdata = self.state.snapshot().rowerdata

        if rowerdata.elapsed_time > 0.0:
            QMessageBox.information(
                self,
                "Paramètres",
                "Les paramètres peuvent être modifiés "
                "entre deux séances.",
            )
            return

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

    # -------------------------------------------------------------------------
    def _apply_split_mode_preference(self) -> None:

        mode = self.settings.split_mode

        # Si le choix par défaut de l'utilisateur est "Workout"
        # alors on force à "Normal" si aucun Workout n'est chargé
        # mais on applique Split Mode = "Workout" si un .wo est chargé.
        # Note: Si un .wo est chargé, alors workoutWidget est visible.
        if (
            mode == "workout"
            and not self.workoutWidget.isVisible()
        ):
            mode = "normal"

        mode_index = SPLIT_MODES.index(mode)

        button = self.splitModeGroup.button(mode_index)

        if button is not None:
            button.setChecked(True)

        self.set_split_mode(mode_index)
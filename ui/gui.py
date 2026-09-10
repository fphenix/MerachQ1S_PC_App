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
)

from setup.constants import (
    GUI_REFRESH_MS,
    WINDOW_TITLE,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WORKOUT_WIDTH,
    METRONOME_MARGIN,
    USE_REPLAY,
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

from workout.split import WorkoutSplitCalculator
from analyzer.analyzer import AnalyzerWindow
from ui.plot_wo import WorkoutPlotWindow

# =============================================================================
class MainWindow(QMainWindow):

    # -------------------------------------------------------------------------
    def __init__(self, state):

        super().__init__()

        self.state = state

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

        self.splitListWidget = SplitListWidget()

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

        self.workoutSplitCalculator = WorkoutSplitCalculator()

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
    def new_session(self):

        logger = self.state.logger

        if logger is not None:
            logger.flush()
            logger.stop()
            logger.start()

            self.state.set_logger(logger)

        # Remise à zéro de l'état de la nouvelle session.
        self.state.reset_session()

        if USE_REPLAY:
            # En Replay: Stoppe le thread, remet le modèle à zéro,
            # puis recommence le fichier depuis le début.
            self.state.source.restart()
        else:
            # Mode rameur réel. ou Replay
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

    # -------------------------------------------------------------------------
    def open_workout(self):

        if self.load_workout_file(
            filename=None,
            replay_mode=False,
        ):
            return

    # -------------------------------------------------------------------------
    def load_workout_file(
        self,
        filename=None,
        replay_mode: bool = False,
    ) -> bool:

        if filename is None:

            return_value = (
                self.workoutWidget.open_setup(
                    replay_mode=replay_mode,
                )
            )

        else:

            return_value = (
                self.workoutWidget.open_setup(
                    filename=filename,
                    replay_mode=replay_mode,
                )
            )

        if not return_value:
            return False

        self.workoutSplitCalculator.reset(
            self.workoutWidget.workout
        )

        self.splitModeWorkout.setEnabled(
            True
        )

        self.workoutWidget.setVisible(
            True
        )

        self.workout_bar.setVisible(
            True
        )

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
            parent=self,
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
                    parent=self,
                )
            )

            self.plot_workout_window.show()

        except Exception as exc:

            QMessageBox.warning(
                self,
                "Erreur",
                f"Impossible de charger le workout.\n\n{exc}",
            )

"""
gui.py

Fenêtre principale.
"""

from status_widget import StatusWidget
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QGridLayout,
    QMainWindow,
    QWidget,
    QPushButton,
)

from constants import (
    GUI_REFRESH_MS,
    WINDOW_TITLE,
)

from utils import (
    format_pace,
    format_time,
    debug,
)

from widgets import MetricWidget


# =============================================================================
class MainWindow(QMainWindow):

    # -------------------------------------------------------------------------
    def __init__(self, state):

        super().__init__()

        self.state = state

        self.setWindowTitle(f"{WINDOW_TITLE} : {self.state.rower.NAME}")

        central = QWidget()
        self.setCentralWidget(central)

        grid = QGridLayout(central)

        grid.setContentsMargins(15, 15, 15, 15)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        #
        # Ligne 0 : Etat Bluetooth
        #

        self.connectionWidget = StatusWidget()

        grid.addWidget(
            self.connectionWidget,
            0,
            0,
            1,
            3,
        )

        #
        # Widgets
        #

        self.timeWidget = MetricWidget(
            "Temps",
            "h:mm:ss"
        )

        self.distanceWidget = MetricWidget(
            "Distance",
            "m",
        )

        self.speedWidget = MetricWidget(
            "Vitesse",
            "m/s  /  avg",
        )

        self.strokeWidget = MetricWidget(
            "Coups",
        )

        self.distStrokeWidget = MetricWidget(
            "Dist/Coup",
            "m/coup",
        )

        self.powerWidget = MetricWidget(
            "Puissance",
            "W  /  Wavg",
        )

        self.cadenceWidget = MetricWidget(
            "Cadence",
            "spm  /  spm avg",
        )

        self.splitWidget = MetricWidget(
            "Split",
            "min/500m  /  avg",
        )

        self.caloriesWidget = MetricWidget(
            "Calories",
            "kcal/s  /  kcal",
        )

        #
        # Ligne 1
        #

        grid.addWidget(self.timeWidget,       1, 0)
        grid.addWidget(self.distanceWidget,   1, 1)
        grid.addWidget(self.speedWidget,      1, 2)

        #
        # Ligne 2
        #

        grid.addWidget(self.strokeWidget,     2, 0)
        grid.addWidget(self.distStrokeWidget, 2, 1)
        grid.addWidget(self.powerWidget,      2, 2)

        #
        # Ligne 3
        #

        grid.addWidget(self.cadenceWidget,    3, 0)
        grid.addWidget(self.splitWidget,      3, 1)
        grid.addWidget(self.caloriesWidget,   3, 2)

        #
        # Ligne 4 : Bouton Reset
        #

        self.resetButton = QPushButton(
            "Nouvelle séance"
        )

        self.resetButton.clicked.connect(
            self.new_session
        )

        grid.addWidget(
            self.resetButton,
            4,
            0,
            1,
            3,
        )

        #
        # Rafraîchissement
        #

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(GUI_REFRESH_MS)

        self.refresh()


    # -------------------------------------------------------------------------
    def new_session(self):

        logger = self.state.logger

        if logger is not None:
            logger.flush()
            logger.close()
            logger.open()

            self.state.set_logger(logger)

        self.state.reset_session()

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
            format_time(rowerdata.elapsed_time)
        )

        #
        # Distance
        #

        self.distanceWidget.setValue(
            f"{rowerdata.distance:.0f}"
        )

        #
        # Vitesse
        #

        self.speedWidget.setValue(
            f"{rowerdata.speed:.2f} / {rowerdata.speed_avg:.2f}"
        )

        #
        # Coups
        #

        self.strokeWidget.setValue(
            rowerdata.stroke_count
        )

        #
        # Distance / coup
        #

        self.distStrokeWidget.setValue(
            f"{rowerdata.distance_per_stroke:.2f}"
        )

        #
        # Puissance
        #

        self.powerWidget.setValue(
            f"{rowerdata.raw_power:.0f} / {rowerdata.power_avg:.0f}"
        )

        #
        # Cadence
        #

        self.cadenceWidget.setValue(
            f"{rowerdata.cadence:.1f} / {rowerdata.cadence_avg:.1f}"
        )

        #
        # Split
        #

        self.splitWidget.setValue(
            f"{format_pace(rowerdata.split_inst)} / {format_pace(rowerdata.split_avg)}"
        )

        #
        # Calories
        #
        self.caloriesWidget.setValue(
            f"{rowerdata.calories_rate:.3f} / {rowerdata.calories:.1f}"
        )

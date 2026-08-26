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
from progbar_widget import GradientGauge


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
            "m/s  /  moy",
            gauge=GradientGauge(
                zones=[0, 3, 5, 7, 15],
            ),
        )

        self.strokeWidget = MetricWidget(
            "Coups",
        )

        self.distStrokeWidget = MetricWidget(
            "Dist/Coup",
            "m/coup  /  moy",
            gauge=GradientGauge(
                zones=[0, 5, 10, 20, 30],
            ),
        )

        self.powerWidget = MetricWidget(
            "Puissance",
            "W  /  W moy",
            gauge=GradientGauge(
                zones=[0, 75, 150, 225, 300],
            ),
        )

        self.cadenceWidget = MetricWidget(
            "Cadence",
            "cpm  /  cpm moy",
            gauge=GradientGauge(
                zones=[15, 22, 25, 28, 45],
            ),
        )

        self.splitWidget = MetricWidget(
            "Split",
            "mm:ss/500m  /  moy",
            gauge=GradientGauge(
                zones=[60, 100, 140, 220, 300],
            ),
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
            logger.stop()
            logger.start()

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
        # Vitesse et Vmoy
        # + Gauge
        #

        self.speedWidget.setValue(
            f"{rowerdata.speed:.2f} / {rowerdata.speed_avg:.2f}",
            rowerdata.speed
        )

        #
        # Coups
        #

        self.strokeWidget.setValue(
            rowerdata.stroke_count
        )

        #
        # Distance/coup et DpS moyenne
        # + Gauge
        #

        self.distStrokeWidget.setValue(
            f"{rowerdata.distance_per_stroke:.2f} / {rowerdata.dist_per_stroke_avg:.2f}",
            rowerdata.distance_per_stroke
        )

        #
        # Puissance (recalibrée) et P moyenne
        # + Gauge
        #

        self.powerWidget.setValue(
            f"{rowerdata.power:.0f} / {rowerdata.power_avg:.0f}",
            rowerdata.power
        )

        #
        # Cadence et SPM moyen
        # + Gauge
        #

        self.cadenceWidget.setValue(
            f"{rowerdata.cadence:.1f} / {rowerdata.cadence_avg:.1f}",
            rowerdata.cadence
        )

        #
        # Split et Split Moyen
        # + Gauge
        #

        self.splitWidget.setValue(
            f"{format_pace(rowerdata.split_inst)} / {format_pace(rowerdata.split_avg)}",
            rowerdata.split_inst
        )

        #
        # Calories Rate et Calories Totales
        #
        self.caloriesWidget.setValue(
            f"{rowerdata.calories_rate:.3f} / {rowerdata.calories:.1f}"
        )

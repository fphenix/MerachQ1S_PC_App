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

        self.caloriesWidget = MetricWidget(
            title= "Calories",
            unit= "kcal/s  /  kcal",
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

        #
        # Calories Rate et Calories Totales
        #
        self.caloriesWidget.setValue(
            textvalue= f"{rowerdata.calories_rate:.3f} / {rowerdata.calories:.1f}"
        )

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


class MainWindow(QMainWindow):

    def __init__(self, state):
        super().__init__()

        self.state = state

        self.setWindowTitle(WINDOW_TITLE)

        central = QWidget()
        self.setCentralWidget(central)

        grid = QGridLayout(central)

        grid.setContentsMargins(15, 15, 15, 15)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        #
        # Etat Bluetooth
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

        self.kcalWidget = MetricWidget(
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
        grid.addWidget(self.kcalWidget,       3, 2)

        #
        # Bouton Reset
        #

        self.resetButton = QPushButton(
            "Nouvelle séance"
        )

        self.resetButton.clicked.connect(
            self.state.reset_session
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

    def refresh(self):
        snapshot = self.state.snapshot()

        ftms = snapshot.ftms
        session = snapshot.session

        #
        # Bluetooth
        #

        self.connectionWidget.set_status(
            ftms.connection
        )

        #
        # Temps
        #

        self.timeWidget.setValue(
            format_time(ftms.elapsed_time)
        )

        #
        # Distance
        #

        self.distanceWidget.setValue(
            f"{session.distance:.0f}"
        )

        #
        # Vitesse
        #

        self.speedWidget.setValue(
            f"{session.speed:.2f} / {session.speed_avg:.2f}"
        )

        #
        # Coups
        #

        self.strokeWidget.setValue(
            ftms.stroke_count
        )

        #
        # Distance / coup
        #

        self.distStrokeWidget.setValue(
            f"{session.distance_per_stroke:.2f}"
        )

        #
        # Puissance
        #

        self.powerWidget.setValue(
            f"{ftms.power:.0f} / {ftms.power_avg:.0f}"
        )

        #
        # Cadence
        #

        self.cadenceWidget.setValue(
            f"{session.cadence:.1f} / {session.cadence_avg:.1f}"
        )

        #
        # Split
        #

        self.splitWidget.setValue(
            f"{format_pace(session.split)} / {format_pace(session.split_avg)}"
        )

        #
        # Calories
        #

        self.kcalWidget.setValue(
            f"{session.calories_rate:.3f} / {session.calories:.1f}"
        )
        
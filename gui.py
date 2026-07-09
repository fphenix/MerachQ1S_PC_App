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
            2,
        )

        #
        # Widgets
        #

        self.timeWidget = MetricWidget("Temps")

        self.distanceWidget = MetricWidget(
            "Distance",
            "m",
        )

        self.spmWidget = MetricWidget(
            "Cadence",
            "spm",
        )

        self.avgSpmWidget = MetricWidget(
            "Cadence moyenne",
            "spm",
        )

        self.strokeWidget = MetricWidget(
            "Coups",
        )

        self.powerWidget = MetricWidget(
            "Puissance",
            "W / Wavg",
        )

        self.paceWidget = MetricWidget(
            "Allure",
            "/500 m",
        )

        self.kcalWidget = MetricWidget(
            "Calories",
            "kcal",
        )

        widgets = [

            self.timeWidget,
            self.distanceWidget,

            self.spmWidget,
            self.avgSpmWidget,

            self.strokeWidget,
            self.powerWidget,

            self.paceWidget,
            self.kcalWidget,
        ]

        for i, widget in enumerate(widgets):

            row = (i // 2) + 1
            col = i % 2

            grid.addWidget(widget, row, col)

        #
        # Bouton Reset
        #

        self.resetButton = QPushButton("Nouvelle séance")

        self.resetButton.clicked.connect(
            self.state.reset_session
        )

        grid.addWidget(
            self.resetButton,
            5,
            0,
            1,
            2,
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
        # Distance calculée
        #

        self.distanceWidget.setValue(
            f"{session.corrected_distance:.0f}"
        )

        #
        # Cadence
        #

        self.spmWidget.setValue(
            f"{ftms.stroke_rate:.1f}"
        )

        self.avgSpmWidget.setValue(
            f"{ftms.stroke_rate_avg:.1f}"
        )

        #
        # Coups
        #

        self.strokeWidget.setValue(
            ftms.stroke_count
        )

        #
        # Puissance
        #

        self.powerWidget.setValue(
            f"{ftms.power:.0f} / {ftms.power_avg:.0f}"
        )

        #
        # Allure moyenne
        #

        self.paceWidget.setValue(
            format_pace(ftms.split_avg)
        )

        #
        # Calories
        #

        self.kcalWidget.setValue(
            f"{ftms.kcal:.0f}"
        )

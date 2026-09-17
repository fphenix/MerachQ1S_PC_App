from typing import Any
from io import BytesIO
from pathlib import Path
import zipfile

import pandas as pd

from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas,
)
from matplotlib.backends.backend_qtagg import (
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
from matplotlib.widgets import CheckButtons

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPlainTextEdit,
)

from setup.lang import get_text
from setup.utils import format_time
from setup.constants import (
    MAIN_FONT,
    ANALYZER_STATS_FONT_SIZE,
    ANALYZER_STATS_MIN_WIDTH,
    ANALYZER_STATS_MAX_WIDTH,
)

from engine.calc import calc_stats

# =============================================================================
class AnalyzerWindow(QMainWindow):

    def __init__(
        self,
        filename: str | Path,
        parent=None,
    ) -> None:

        super().__init__(parent)

        self.filename = Path(filename)

        self.setWindowTitle(
            f"{get_text("ANALYZER_TITLE")} - {self.filename.name}"
        )

        self.df = self.load_log(
            self.filename
        )

        self.expanded_plot = None

        self.ax: list = []
        self.line_calc = None
        self.line_avg = None
        self.line_rower = None
        self.line_rower_avg = None
        self.rax = None
        self.check = None

        # === ui ===================

        self.figure = Figure(
            figsize=(12, 12)
        )

        self.canvas = FigureCanvas(
            self.figure
        )

        self.toolbar = NavigationToolbar(
            self.canvas,
            self,
        )

        main_layout = QHBoxLayout()

        plot_layout = QVBoxLayout()

        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(
            self.canvas,
            1,
        )

        main_layout.addLayout(
            plot_layout,
            1,
        )

        self.stats_widget = QPlainTextEdit()
        self.stats_widget.setReadOnly(True)
        self.stats_widget.setFont(
            QFont(MAIN_FONT, ANALYZER_STATS_FONT_SIZE)
        )
        self.stats_widget.setMinimumWidth(ANALYZER_STATS_MIN_WIDTH)
        self.stats_widget.setMaximumWidth(ANALYZER_STATS_MAX_WIDTH)

        main_layout.addWidget(
            self.stats_widget,
            0,
        )

        center = QWidget()

        self.setCentralWidget(
            center
        )

        self.centralWidget().setLayout(
            main_layout
        )

        # ==========================

        self.canvas.mpl_connect(
            "button_press_event",
            self.plot_click,
        )

        self.plots = self.create_plot_definitions()

        self.draw_all_plots()

        self.stats_widget.setPlainText(
            self.build_stats_text()
        )

    # -------------------------------------------------------------------------
    def load_log(
        self,
        filename: str | Path,
    ) -> pd.DataFrame:

        path = Path(filename)

        if not path.exists():
            raise FileNotFoundError(
                f"{get_text("ERR_LOGFILE_NOT_FOUND")} : {path}"
            )

        suffix = path.suffix.lower()

        if suffix == ".csv":

            return pd.read_csv(
                path,
                skiprows=2,
            )

        if suffix == ".zip":

            with zipfile.ZipFile(
                path,
                "r",
            ) as archive:

                csv_files = [
                    name
                    for name in archive.namelist()
                    if (
                        name.lower().endswith(".csv")
                        and not name.endswith("/")
                    )
                ]

                if len(csv_files) != 1:
                    raise ValueError(
                        f"{path.name} {get_text("ERR_ZIP_ONLY_1_FILE")}"
                    )

                csv_data = archive.read(
                    csv_files[0]
                )

            return pd.read_csv(
                BytesIO(csv_data),
                skiprows=2,
            )

        raise ValueError(
            f"{get_text("ERR_WRONG_LOG_FORMAT")} : {suffix}"
        )

    # -------------------------------------------------------------------------
    def create_plot_definitions(self) -> list[dict[str, Any]]:

        t = self.df["Elapsed"]

        return [
            {
                "id": 0,
                "title": [f"{get_text("POWER")} ({get_text("PLOT_POWER_RECAL")})", get_text('PLOT_AVERAGE')],
                "x": t,
                "y": ["Power_Recalibrated", "Power_Avg"],
                "xlabel": get_text("PLOT_X_AXIS_TIME"),
                "ylabel": "W",
            },
            {
                "id": 1,
                "title": [get_text("SPEED"), get_text('PLOT_AVERAGE'), get_text("DPS_AVG")],
                "x": t,
                "y": ["Speed", "Speed_Avg", "Dist_Per_Stroke_Avg"],
                "xlabel": get_text("PLOT_X_AXIS_TIME"),
                "ylabel": "m/s",
            },
            {
                "id": 2,
                "title": [get_text("CADENCE"), get_text('PLOT_AVERAGE')],
                "x": t,
                "y": ["Cadence", "Cadence_Avg"],
                "xlabel": get_text("PLOT_X_AXIS_TIME"),
                "ylabel": get_text("PLOT_SPM_UNIT"),
            },
            {
                "id": 3,
                "title": [get_text('DISTANCE')],
                "x": t,
                "y": ["Distance"],
                "xlabel": get_text("PLOT_X_AXIS_TIME"),
                "ylabel": "m",
            },
            {
                "id": 4,
                "title": [
                    get_text('SPLIT_CALC'),
                    get_text('PLOT_AVERAGE'),
                    get_text('SPLIT_RAW_INST'),
                    get_text('SPLIT_RAW_AVG'),
                ],
                "x": t,
                "y": [
                    "Split",
                    "Split_Avg",
                    "Raw_Split_Instant",
                    "Raw_Split_Avg",
                ],
                "xlabel": get_text("PLOT_X_AXIS_TIME"),
                "ylabel": "s/500m",
                "linewidth": [2, 2, 1, 1],
                "linestyle": [
                    "solid",
                    "solid",
                    "dashed",
                    "dashdot",
                ],
            },
            {
                "id": 5,
                "title": [get_text("CALORIES")],
                "x": t,
                "y": ["Calories"],
                "xlabel": get_text("PLOT_X_AXIS_TIME"),
                "ylabel": "kcal",
            },
        ]

    # -------------------------------------------------------------------------
    def toggle(self, label) -> None:

        if (
            label == "Rower Instant"
            and self.line_rower is not None
        ):
            self.line_rower.set_visible(
                not self.line_rower.get_visible()
            )

        elif (
            label == "Rower Average"
            and self.line_rower_avg is not None
        ):
            self.line_rower_avg.set_visible(
                not self.line_rower_avg.get_visible()
            )

        self.canvas.draw_idle()

    # -------------------------------------------------------------------------
    def create_checkbuttons(self) -> None:

        self.rax = self.figure.add_axes(
            [0.82, 0.80, 0.16, 0.12]
        )

        labels: list = []
        states: list = []

        if self.line_rower is not None:
            labels.append("Rower Instant")
            states.append(
                self.line_rower.get_visible()
            )

        if self.line_rower_avg is not None:
            labels.append("Rower Average")
            states.append(
                self.line_rower_avg.get_visible()
            )

        if labels:

            self.check = CheckButtons(
                self.rax,
                labels,
                states,
            )

            self.check.on_clicked(
                self.toggle
            )

        else:

            self.check = None

    # -------------------------------------------------------------------------
    def draw_plot(self, plot, axis) -> list:

        lines: list = []

        title = plot["title"]
        x = plot["x"]
        y = plot["y"]

        for j in range(len(title)):

            linestyle = (
                plot["linestyle"][j]
                if "linestyle" in plot
                else "solid"
            )

            linewidth = (
                plot["linewidth"][j]
                if "linewidth" in plot
                else 1
            )

            line, = axis.plot(
                x,
                self.df[y[j]],
                label=title[j],
                linewidth=linewidth,
                linestyle=linestyle,
            )

            lines.append((y[j], line))

        axis.set_xlabel(plot["xlabel"])
        axis.set_ylabel(plot["ylabel"])
        axis.grid(True)
        axis.legend()

        return lines
    
    # -------------------------------------------------------------------------
    def draw_all_plots(self) -> None:

        self.figure.clear()

        self.ax = list(
            self.figure.subplots(
                nrows=6,
                ncols=1,
                sharex=True,
                gridspec_kw={
                    "height_ratios": [
                        2, 2, 2, 3, 2, 1
                    ],
                },
            )
        )

        self.line_calc = None
        self.line_avg = None
        self.line_rower = None
        self.line_rower_avg = None
        self.rax = None
        self.check = None

        for plot in self.plots:

            plot_id = plot["id"]

            lines = self.draw_plot(
                plot,
                self.ax[plot_id],
            )

            for field_name, line in lines:

                if field_name == "Split":
                    self.line_calc = line

                elif field_name == "Split_Avg":
                    self.line_avg = line

                elif field_name == "Raw_Split_Instant":
                    self.line_rower = line

                elif field_name == "Raw_Split_Avg":
                    self.line_rower_avg = line

        self.create_checkbuttons()

        self.figure.subplots_adjust(
            left=0.08,
            right=0.78,
            top=0.95,
            bottom=0.06,
            hspace=0.35,
        )

        self.canvas.draw_idle()

    # -------------------------------------------------------------------------
    def draw_single_plot(self, plot_id) -> None:

        self.figure.clear()

        self.ax = [
            self.figure.add_subplot(111)
        ]

        self.line_calc = None
        self.line_avg = None
        self.line_rower = None
        self.line_rower_avg = None

        self.rax = None
        self.check = None

        plot = self.plots[plot_id]

        lines = self.draw_plot(
            plot,
            self.ax[0],
        )

        for field_name, line in lines:

            if field_name == "Split":
                self.line_calc = line

            elif field_name == "Split_Avg":
                self.line_avg = line

            elif field_name == "Raw_Split_Instant":
                self.line_rower = line

            elif field_name == "Raw_Split_Avg":
                self.line_rower_avg = line

        self.figure.subplots_adjust(
            left=0.08,
            right=0.95,
            top=0.92,
            bottom=0.08,
        )

        self.canvas.draw_idle()

    # -------------------------------------------------------------------------
    def plot_click(self, event) -> None:

        if event.inaxes is None:
            return

        if self.expanded_plot is not None:

            self.expanded_plot = None
            self.draw_all_plots()
            return

        for plot in self.plots:

            plot_id = plot["id"]

            if event.inaxes is self.ax[plot_id]:

                self.expanded_plot = plot_id
                self.draw_single_plot(plot_id)

                return
            
    # -------------------------------------------------------------------------
    def build_stats_text(self) -> str:

        df = self.df

        lines = [
            "========== SESSION ==========",
            f"{get_text("STATS_DURATION")} : {format_time(df['Elapsed'].iloc[-1])}",
            f"{get_text("STATS_DISTANCE")} : {df['Distance'].iloc[-1]:.1f} m",
            f"{get_text("STATS_STROKES")} : {int(df['Stroke_Count'].iloc[-1])}",
            f"{get_text("STATS_CALORIES")} : {df['Calories'].iloc[-1]:.1f} kcal",
            f"{get_text("STATS_WORK")} : {df['Work_J'].iloc[-1] / 1000:.1f} kJ",
            f"{get_text("STATS_AVG_POWER")} : {df['Power_Avg'].iloc[-1]:.1f} W",
            f"{get_text("STATS_AVG_SPEED")} : {df['Speed_Avg'].iloc[-1]:.2f} m/s",
            f"{get_text("STATS_AVG_CADENCE")} : {df['Cadence_Avg'].iloc[-1]:.1f} spm",
            "=============================",
            "",
        ]

        power_stats = calc_stats(
            df["Power_Recalibrated"].tolist(),
            minimum=1,
        )

        cadence_stats = calc_stats(
            df["Cadence"].tolist(),
            minimum=1,
        )

        dps_stats = calc_stats(
            df["Distance_Per_Stroke"].tolist(),
            minimum=0.1,
        )

        for stats, title in (
            (power_stats, get_text("POWER")),
            (cadence_stats, get_text("CADENCE")),
            (dps_stats, f"{get_text("DISTANCE")}/{get_text("STROKE")}"),
        ):

            lines.extend([
                title,
                "-----------",
                f"mean  : {stats['mean']:.2f}",
                f"stdev : {stats['stdev']:.2f}",
                f"min   : {stats['min']:.2f}",
                f"max   : {stats['max']:.2f}",
                "",
            ])

        return "\n".join(lines)

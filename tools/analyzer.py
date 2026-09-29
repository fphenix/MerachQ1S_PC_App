from typing import Any
import csv
from io import BytesIO
from pathlib import Path
import zipfile

import pandas as pd

from matplotlib.axes._axes import Axes
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
    ANALYZER_WIDTH, ANALYZER_HEIGHT,
    ANALYZER_STATS_FONT_SIZE,
    ANALYZER_STATS_MIN_WIDTH,
    ANALYZER_STATS_MAX_WIDTH,
    LOGGER_FORMAT_CSV,
    LOGGER_FORMAT_ZIP,
    ANALYZER_SHOW_CHECKBUTTONS,
    FILE_ENCODING_BOM,
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

        self.filename: Path = Path(filename)

        self.workout_filename: str | None = None

        self.df: pd.DataFrame = self._load_log(
            self.filename
        )

        self.expanded_plot: int | None = None

        self.ax: list = []
        self.line_split_calc: list | None = None
        self.line_split_avg: list | None = None
        self.line_raw_split: list | None = None
        self.line_raw_split_avg: list | None = None

        self.rax: Axes | None = None
        self.checkbtn: CheckButtons | None = None

        self._create_ui()

        self.plots: list = self._create_plot_definitions()

        self._draw_all_plots()

        self.stats_widget.setPlainText(
            self._build_stats_text()
        )

    # -------------------------------------------------------------------------
    def _create_ui(self) -> None:

        self.setWindowTitle(
            f"{get_text("ANALYZER_TITLE")} - {self.filename.name}"
        )

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

        self.stats_widget = QPlainTextEdit()
        self.stats_widget.setReadOnly(True)
        self.stats_widget.setFont(
            QFont(MAIN_FONT, ANALYZER_STATS_FONT_SIZE)
        )
        self.stats_widget.setMinimumWidth(ANALYZER_STATS_MIN_WIDTH)
        self.stats_widget.setMaximumWidth(ANALYZER_STATS_MAX_WIDTH)

        main_layout.addLayout(
            plot_layout,
            1,
        )

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

        self.resize(
            ANALYZER_WIDTH,
            ANALYZER_HEIGHT,
        )

        self.canvas.mpl_connect(
            "button_press_event",
            self._callback_plot_click,
        )

    # -------------------------------------------------------------------------
    def _load_log(
        self,
        filename: str | Path,
    ) -> pd.DataFrame:

        path = Path(filename)

        if not path.exists():
            raise FileNotFoundError(
                f"{get_text("ERR_LOGFILE_NOT_FOUND")} : {path}"
            )

        suffix = path.suffix.lower()[1:]

        csv_ret_data = None
        csv_data = None

        if suffix == LOGGER_FORMAT_CSV:

            csv_data = path.read_bytes()

        elif suffix == LOGGER_FORMAT_ZIP:

            with zipfile.ZipFile(
                path,
                "r",
            ) as archive:

                csv_ext = f".{LOGGER_FORMAT_CSV}"
                csv_files = [
                    name
                    for name in archive.namelist()
                    if (
                        name.lower().endswith(csv_ext)
                        and not name.endswith("/")
                    )
                ]

                if len(csv_files) != 1:
                    raise ValueError(
                        f"{path.name} {get_text("ERR_ZIP_ONLY_1_FILE")}"
                    )

                csv_data = archive.read(csv_files[0])

        if csv_data is not None:

            # La 2e ligne du csv Log contient par exemple :
            # Workout,"None Loaded" ou Workout,"workouts/filename.wo"
            lines = csv_data.decode(FILE_ENCODING_BOM).splitlines()

            self.workout_filename = None

            if len(lines) >= 2:

                row = next(csv.reader([lines[1]]), [])

                if len(row) >= 2 and row[0] == "Workout":
                    workout_value = row[1]

                    if workout_value != "None Loaded":
                        self.workout_filename = Path(workout_value).name

            csv_ret_data = pd.read_csv(
                BytesIO(csv_data),
                skiprows=2,
            )

        if csv_ret_data is not None:
            return csv_ret_data

        raise ValueError(
            f"{get_text("ERR_WRONG_LOG_FORMAT")} : {suffix}"
        )

    # -------------------------------------------------------------------------
    def _create_plot_definitions(self) -> list[dict[str, Any]]:

        t = self.df["Elapsed"] / 60.0 # convert in minutes

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
            label == f"{get_text("SPLIT")} {get_text("PLOT_INST")}"
            and self.line_raw_split is not None
        ):
            self.line_raw_split.set_visible(
                not self.line_raw_split.get_visible()
            )

        elif (
            label == f"{get_text("SPLIT")} {get_text("PLOT_AVERAGE")}"
            and self.line_raw_split_avg is not None
        ):
            self.line_raw_split_avg.set_visible(
                not self.line_raw_split_avg.get_visible()
            )

        self.canvas.draw_idle()

    # -------------------------------------------------------------------------
    def _create_checkbuttons(self) -> None:

        if not ANALYZER_SHOW_CHECKBUTTONS:
            self.rax = None
            self.check = None
            return

        self.rax = self.figure.add_axes(
            [0.82, 0.80, 0.16, 0.12]
        )

        labels: list = []
        states: list = []

        if self.line_raw_split is not None:
            labels.append(f"{get_text("SPLIT")} {get_text("PLOT_INST")}")
            states.append(
                self.line_raw_split.get_visible()
            )

        if self.line_raw_split_avg is not None:
            labels.append(f"{get_text("SPLIT")} {get_text("PLOT_AVERAGE")}")
            states.append(
                self.line_raw_split_avg.get_visible()
            )

        if labels:

            self.checkbtn = CheckButtons(
                self.rax,
                labels,
                states,
            )

            self.checkbtn.on_clicked(
                self.toggle
            )

        else:

            self.checkbtn = None

    # -------------------------------------------------------------------------
    def _draw_plot(self, plot, axis) -> list:

        lines: list = []

        title = plot["title"]
        x = plot["x"]
        y = plot["y"]

        for j in range(len(title)):

            if y[j] not in self.df.columns:
                print(f"{get_text("WARN_ANALYZER_COL_NOT_FOUND")}: {y[j]}")
                continue

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
    def _draw_all_plots(self) -> None:

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

        self.line_split_calc = None
        self.line_split_avg = None
        self.line_raw_split = None
        self.line_raw_split_avg = None

        self.rax = None
        self.checkbtn = None

        for plot in self.plots:

            plot_id = plot["id"]

            lines = self._draw_plot(
                plot,
                self.ax[plot_id],
            )

            for field_name, line in lines:

                if field_name == "Split":
                    self.line_split_calc = line

                elif field_name == "Split_Avg":
                    self.line_split_avg = line

                elif field_name == "Raw_Split_Instant":
                    self.line_raw_split = line

                elif field_name == "Raw_Split_Avg":
                    self.line_raw_split_avg = line

        self._create_checkbuttons()

        self.figure.subplots_adjust(
            left=0.08,
            right=(
                0.78
                if ANALYZER_SHOW_CHECKBUTTONS
                else 0.95
            ),
            top=0.95,
            bottom=0.06,
            hspace=0.35,
        )

        self.canvas.draw_idle()

    # -------------------------------------------------------------------------
    def _draw_single_plot(self, plot_id) -> None:

        self.figure.clear()

        self.ax = [
            self.figure.add_subplot(111)
        ]

        self.line_split_calc = None
        self.line_split_avg = None
        self.line_raw_split = None
        self.line_raw_split_avg = None

        self.rax = None
        self.checkbtn = None

        plot = self.plots[plot_id]

        lines = self._draw_plot(
            plot,
            self.ax[0],
        )

        for field_name, line in lines:

            if field_name == "Split":
                self.line_split_calc = line

            elif field_name == "Split_Avg":
                self.line_split_avg = line

            elif field_name == "Raw_Split_Instant":
                self.line_raw_split = line

            elif field_name == "Raw_Split_Avg":
                self.line_raw_split_avg = line

        self.figure.subplots_adjust(
            left=0.08,
            right=0.95,
            top=0.92,
            bottom=0.08,
        )

        self.canvas.draw_idle()

    # -------------------------------------------------------------------------
    def _callback_plot_click(self, event) -> None:

        if event.inaxes is None:
            return

        if self.expanded_plot is not None:

            self.expanded_plot = None
            self._draw_all_plots()
            return

        for plot in self.plots:

            plot_id = plot["id"]

            if event.inaxes is self.ax[plot_id]:

                self.expanded_plot = plot_id
                self._draw_single_plot(plot_id)

                return
            
    # -------------------------------------------------------------------------
    def _build_stats_text(self) -> str:

        df = self.df

        lines = [
            "========== SESSION ==========",
        ]

        if self.workout_filename is not None:
            lines.extend([
                f"Workout : {self.workout_filename}",
                "",
            ])

        lines.extend([
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
        ])

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

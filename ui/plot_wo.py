from pathlib import Path

from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas,
)
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator

from PySide6.QtWidgets import (
    QMainWindow,
)

from setup.constants import (
    INTENSITY_COLORS,
    PLOTWO_WIDTH, PLOTWO_HEIGHT,
)
from setup.utils import (
    load_workout,
)


# =============================================================================
class WorkoutPlotWidget(FigureCanvas):

    VERTICAL_STYLE = "none"

    LINE_WIDTH = 4

    Y_MIN = 14
    Y_MAX = 40

    def __init__(
        self,
        parent=None,
    ):
        self.current_workout = None

        figure = Figure(
            figsize=(10, 5)
        )

        super().__init__(
            figure
        )

        self.axes = figure.add_subplot(
            111
        )

    # -------------------------------------------------------------------------
    def clear(self):

        self.current_workout = None

        self.axes.clear()

        self.axes.set_xlim(
            0,
            60,
        )

        self.axes.set_ylim(
            self.Y_MIN,
            self.Y_MAX,
        )

        self.axes.set_xlabel(
            "Temps (minutes)"
        )

        self.axes.set_ylabel(
            "Cadence (spm)"
        )

        self.axes.grid(
            True
        )

        self.figure.tight_layout()

        self.draw()

    # -------------------------------------------------------------------------
    def set_vertical_style(
        self,
        style: str,
    ) -> None:

        self.VERTICAL_STYLE = style

        if self.current_workout is not None:
            self.plot_workout(
                self.current_workout
            )

    # -------------------------------------------------------------------------
    def plot_workout(
        self,
        workout,
    ) -> None:

        self.current_workout = workout

        ax = self.axes

        ax.clear()

        total_minutes = (
            workout.total_seconds
            / 60.0
        )

        xmax = max(
            1.0,
            total_minutes,
        )

        ax.set_xlim(
            0,
            xmax,
        )

        ax.set_ylim(
            self.Y_MIN,
            self.Y_MAX,
        )

        ax.xaxis.set_major_locator(
            MultipleLocator(5)
        )

        ax.xaxis.set_minor_locator(
            MultipleLocator(1)
        )

        ax.yaxis.set_major_locator(
            MultipleLocator(2)
        )

        ax.yaxis.set_minor_locator(
            MultipleLocator(1)
        )

        ax.grid(
            True,
            which="major",
            axis="both",
            linewidth=1.0,
        )

        ax.grid(
            True,
            which="minor",
            axis="both",
            linewidth=0.5,
        )

        ax.set_xlabel(
            "Temps (minutes)"
        )

        ax.set_ylabel(
            "Cadence (spm)"
        )

        ax.set_facecolor(
            "white"
        )

        current_time = 0.0
        previous_spm = None

        for step in workout.steps:

            duration = (
                step.duration_minutes
            )

            x0 = current_time
            x1 = (
                current_time
                + duration
            )

            color = INTENSITY_COLORS.get(
                step.intensity,
                "black",
            )

            ax.plot(
                [x0, x1],
                [step.cpm, step.cpm],
                color=color,
                linewidth=self.LINE_WIDTH,
                solid_capstyle="round",
                zorder=2,
            )

            if previous_spm is not None:

                if self.VERTICAL_STYLE == "gray":
                    vcolor = "lightgray"
                    vwidth = 1

                elif self.VERTICAL_STYLE == "color":
                    vcolor = color
                    vwidth = self.LINE_WIDTH

                else:
                    vcolor = None
                    vwidth = 0

                if vcolor is not None:

                    ax.plot(
                        [x0, x0],
                        [
                            previous_spm,
                            step.cpm,
                        ],
                        color=vcolor,
                        linewidth=vwidth,
                        solid_capstyle="round",
                        zorder=1,
                    )

            previous_spm = step.cpm

            current_time = x1

        self.figure.suptitle(
            workout.title,
            fontsize=16,
            fontweight="bold",
        )

        if workout.field:

            ax.set_title(
                workout.field,
                fontsize=11,
                pad=10,
            )

        legend = [
            Line2D(
                [0],
                [0],
                color=INTENSITY_COLORS["M"],
                lw=4,
                label="M",
            ),
            Line2D(
                [0],
                [0],
                color=INTENSITY_COLORS["F"],
                lw=4,
                label="F",
            ),
            Line2D(
                [0],
                [0],
                color=INTENSITY_COLORS["N"],
                lw=4,
                label="N",
            ),
            Line2D(
                [0],
                [0],
                color=INTENSITY_COLORS["E"],
                lw=4,
                label="E",
            ),
            Line2D(
                [0],
                [0],
                color=INTENSITY_COLORS["R"],
                lw=4,
                label="R",
            ),
        ]

        ax.legend(
            handles=legend,
            loc="upper right",
            title="Zones",
        )

        self.figure.tight_layout(
            rect=[0, 0, 1, 0.93]
        )

        self.draw()


# =============================================================================
class WorkoutPlotWindow(QMainWindow):

    def __init__(
        self,
        filename: str | Path,
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.filename = Path(
            filename
        )

        self.setWindowTitle(
            "Workout Viewer"
        )

        self.plot = WorkoutPlotWidget(
            self
        )

        self.setCentralWidget(
            self.plot
        )

        self.resize(
            PLOTWO_WIDTH,
            PLOTWO_HEIGHT,
        )

        self.load_file()

    # -------------------------------------------------------------------------
    def load_file(self) -> None:

        workout = load_workout(
            self.filename
        )

        self.plot.plot_workout(
            workout
        )

        self.setWindowTitle(
            "Workout Viewer - "
            + self.filename.name
        )
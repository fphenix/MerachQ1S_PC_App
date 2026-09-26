from matplotlib import pyplot
from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas,
)
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator

from setup.constants import (
    INTENSITY_COLORS,
)

from setup.lang import get_text

# =============================================================================
class WorkoutPlotWidget(FigureCanvas):

    VERTICAL_STYLE = "none"

    LINE_WIDTH = 4

    Y_MIN = 14
    Y_MAX = 40

    # ------------------------------------------------------------------
    def __init__(
        self,
        parent=None,
    ) -> None:

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
    def clear(self) -> None:

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
            f"{get_text("TIME")} ({get_text("MINUTE_UNIT_FULL")})"
        )

        self.axes.set_ylabel(
            f"{get_text("CADENCE")} ({get_text("SPM_UNIT")})"
        )

        self.axes.grid(
            True
        )

        self.figure.tight_layout()

        self.draw()

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
            f"{get_text("TIME")} ({get_text("MINUTE_UNIT_FULL")})"
        )

        ax.set_ylabel(
            f"{get_text("CADENCE")} ({get_text("SPM_UNIT")})"
        )

        ax.set_facecolor(
            "white"
        )

        current_time = 0.0
        previous_spm = None
        parts_set: set[str] = set()

        for step in workout.steps:

            duration_minutes = step.duration_seconds / 60.0

            x0 = current_time
            x1 = current_time + duration_minutes

            color = INTENSITY_COLORS.get(
                step.intensity,
                "black",
            )

            ax.plot(
                [x0, x1],
                [step.spm, step.spm],
                color=color,
                linewidth=self.LINE_WIDTH,
                solid_capstyle="round",
                zorder=2,
            )

            if step.part:
                parts_set.add(step.part)

                ax.annotate(
                    step.part,  # get_text(f"PART_DICT_{step.part}"),
                    xy=(
                        (x0 + x1) / 2.0,
                        step.spm,
                    ),
                    xytext=(0, 6),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    zorder=3,
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
                            step.spm,
                        ],
                        color=vcolor,
                        linewidth=vwidth,
                        solid_capstyle="round",
                        zorder=1,
                    )

            previous_spm = step.spm

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

        handle_intensity = [
            Line2D(
                [0], [0],
                color=color, lw=4,
                label=label,
            ) for intensity, color in INTENSITY_COLORS.items()
            if (label := get_text(f"INTENSITY_DICT_{intensity}"))
        ]

        intensity_legend = ax.legend(
            handles=handle_intensity,
            loc="upper right",
            title=get_text("INTENSITY"),
        )

        ax.add_artist(intensity_legend)

        if parts_set:
            handle_part = [
                Line2D(
                    [], [],
                    color="none",
                    marker="", linestyle="",
                    label=f"{part.upper()} : {get_text(f"PART_DICT_{part.upper()}")}",
                ) for part in sorted(parts_set)
            ]

            ax.legend(
                handles=handle_part,
                loc="upper center",
                title=get_text("BODY_PART"),
            )

        self.figure.tight_layout(
            rect=[0, 0, 1, 0.93]
        )

        self.draw()

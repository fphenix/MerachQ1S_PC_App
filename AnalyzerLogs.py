import io
import zipfile
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons
from tkinter import Tk, filedialog
import os
from calc import calc_stats


# -----------------------------------------------------------------------------
def load_log(filename: str | Path) -> pd.DataFrame:
    path = Path(filename)

    if not path.exists():
        raise FileNotFoundError(
            f"Fichier de log introuvable : {path}"
        )

    suffix = path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(
            path,
            skiprows=2,
        )

    if suffix == ".zip":
        with zipfile.ZipFile(path, "r") as archive:

            csv_files = [
                name
                for name in archive.namelist()
                if name.lower().endswith(".csv")
                and not name.endswith("/")
            ]

            if len(csv_files) != 1:
                raise ValueError(
                    f"{path.name} doit contenir exactement "
                    f"un fichier CSV."
                )

            csv_data = archive.read(csv_files[0])

        return pd.read_csv(
            io.BytesIO(csv_data),
            skiprows=2,
        )

    raise ValueError(
        f"Format de log non supporté : {suffix}"
    )


# -----------------------------------------------------------------------------
def toggle(label):
    global line_rower
    global line_rower_avg

    if label == "Rower Instant" and line_rower is not None:
        line_rower.set_visible(
            not line_rower.get_visible()
        )

    elif label == "Rower Average" and line_rower_avg is not None:
        line_rower_avg.set_visible(
            not line_rower_avg.get_visible()
        )

    fig.canvas.draw_idle()


# -----------------------------------------------------------------------------
def draw_plot(plot, axis):
    """
    Dessine un graphe à partir de sa définition dans 'plot'.

    Retourne les lignes créées pour permettre de les gérer ensuite.
    """
    lines = []

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
            df[y[j]],
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


# -----------------------------------------------------------------------------
def create_checkbuttons():
    """
    Crée les cases à cocher utilisées pour les courbes Split raw.
    """

    global rax
    global check
    global line_rower
    global line_rower_avg

    rax = plt.axes([0.82, 0.80, 0.16, 0.12])

    labels = []
    states = []

    if line_rower is not None:
        labels.append("Rower Instant")
        states.append(line_rower.get_visible())

    if line_rower_avg is not None:
        labels.append("Rower Average")
        states.append(line_rower_avg.get_visible())

    if labels:
        check = CheckButtons(
            rax,
            labels,
            states,
        )

        check.on_clicked(toggle)
    else:
        check = None


# -----------------------------------------------------------------------------
def draw_all_plots():
    """
    Affiche les six graphes.
    """

    global ax
    global line_calc
    global line_avg
    global line_rower
    global line_rower_avg

    fig.clear()

    ax = fig.subplots(
        nrows=6,
        ncols=1,
        sharex=True,
        gridspec_kw={
            "height_ratios": [2, 2, 2, 3, 2, 1],
        },
    )

    if not isinstance(ax, (list, tuple)):
        ax = list(ax)

    line_calc = None
    line_avg = None
    line_rower = None
    line_rower_avg = None

    for plot in plots:

        plot_id = plot["id"]

        lines = draw_plot(
            plot,
            ax[plot_id],
        )

        for field_name, line in lines:

            if field_name == "Split":
                line_calc = line

            elif field_name == "Split_Avg":
                line_avg = line

            elif field_name == "Raw_Split_Instant":
                line_rower = line

            elif field_name == "Raw_Split_Avg":
                line_rower_avg = line

    create_checkbuttons()

    fig.subplots_adjust(
        left=0.08,
        right=0.78,
        top=0.95,
        bottom=0.06,
        hspace=0.35,
    )

    fig.canvas.draw_idle()


# -----------------------------------------------------------------------------
def draw_single_plot(plot_id):
    """
    Affiche un seul graphe en plein cadre.
    """

    global ax
    global line_calc
    global line_avg
    global line_rower
    global line_rower_avg
    global rax
    global check

    fig.clear()

    ax = [fig.add_subplot(111)]

    line_calc = None
    line_avg = None
    line_rower = None
    line_rower_avg = None

    plot = plots[plot_id]

    lines = draw_plot(
        plot,
        ax[0],
    )

    for field_name, line in lines:

        if field_name == "Split":
            line_calc = line

        elif field_name == "Split_Avg":
            line_avg = line

        elif field_name == "Raw_Split_Instant":
            line_rower = line

        elif field_name == "Raw_Split_Avg":
            line_rower_avg = line

    # Pas de CheckButtons en mode plein écran.
    rax = None
    check = None

    fig.subplots_adjust(
        left=0.08,
        right=0.95,
        top=0.92,
        bottom=0.08,
    )

    fig.canvas.draw_idle()


# -----------------------------------------------------------------------------
def plot_click(event):
    """
    Premier clic sur un graphe :
        → agrandit ce graphe.

    Clic suivant :
        → retour aux six graphes.
    """

    global expanded_plot

    if event.inaxes is None:
        return

    # Si un graphe est déjà agrandi :
    # n'importe quel clic dans celui-ci revient à la vue globale.
    if expanded_plot is not None:
        expanded_plot = None
        draw_all_plots()
        return

    # Sinon, chercher quel graphe a été cliqué.
    for plot in plots:

        plot_id = plot["id"]

        if event.inaxes is ax[plot_id]:
            expanded_plot = plot_id
            draw_single_plot(plot_id)
            return


# =============================================================================
#
# Choix du fichier
#

Tk().withdraw()

filename = filedialog.askopenfilename(
    title="Choisir un fichier de log",
    filetypes=[
        ("All Files", "*.*"),
        ("CSV", "*.csv"),
        ("Zipped CSV", "*.zip"),
    ],
)

if filename == "":
    raise SystemExit

#
# Lecture du fichier
#

df = load_log(filename)

file_basename = os.path.basename(filename)
file_corename = os.path.splitext(file_basename)[0]


# =============================================================================
#
# Résumé
#

print()
print("========== SESSION ==========")
print(f"Durée       : {df['Elapsed'].iloc[-1]:.1f} s")
print(f"Distance    : {df['Distance'].iloc[-1]:.1f} m")
print(f"Coups       : {int(df['Stroke_Count'].iloc[-1])}")
print(f"Calories    : {df['Calories'].iloc[-1]:.1f} kcal")
print(f"Travail     : {df['Work_J'].iloc[-1] / 1000:.1f} kJ")
print(f"Puiss. moy. : {df['Power_Avg'].iloc[-1]:.1f} W")
print(f"Vit. moy.   : {df['Speed_Avg'].iloc[-1]:.2f} m/s")
print(f"Cad. moy.   : {df['Cadence_Avg'].iloc[-1]:.1f} spm")
print("=============================\n")


# =============================================================================
#
# Stats
#

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

stats_path = Path(
    f"./Logs/stats/stats_{file_corename}.txt"
)

stats_path.parent.mkdir(
    parents=True,
    exist_ok=True,
)

with stats_path.open(
    "w",
    encoding="utf-8",
) as fw:

    for t_stats, title in [
        (power_stats, "Power_Recalibrated"),
        (cadence_stats, "Cadence"),
        (dps_stats, "Distance/Stroke"),
    ]:

        fw.write(
            f"{title}\n"
            "-----------\n"
        )

        for key in [
            "mean",
            "stdev",
            "min",
            "max",
        ]:
            fw.write(
                f"{key}\t: {t_stats[key]}\n"
            )

        fw.write("\n")


# =============================================================================
#
# Temps
#

t = df["Elapsed"]


# =============================================================================
#
# Plots
#

line_calc = None
line_avg = None
line_rower = None
line_rower_avg = None

expanded_plot = None

plots = [
    {
        "id": 0,
        "title": ["Power", "Average"],
        "x": t,
        "y": ["Power_Recalibrated", "Power_Avg"],
        "xlabel": "Temps (s)",
        "ylabel": "W",
    },
    {
        "id": 1,
        "title": ["Speed", "Average", "DPSavg (m/coup)"],
        "x": t,
        "y": ["Speed", "Speed_Avg", "Dist_Per_Stroke_Avg"],
        "xlabel": "Temps (s)",
        "ylabel": "m/s",
    },
    {
        "id": 2,
        "title": ["Cadence", "Average"],
        "x": t,
        "y": ["Cadence", "Cadence_Avg"],
        "xlabel": "Temps (s)",
        "ylabel": "spm",
    },
    {
        "id": 3,
        "title": ["Distance"],
        "x": t,
        "y": ["Distance"],
        "xlabel": "Temps (s)",
        "ylabel": "m",
    },
    {
        "id": 4,
        "title": [
            "Split Calculated",
            "Average",
            "Raw Inst",
            "Raw Avg",
        ],
        "x": t,
        "y": [
            "Split",
            "Split_Avg",
            "Raw_Split_Instant",
            "Raw_Split_Avg",
        ],
        "xlabel": "Temps (s)",
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
        "title": ["Calories"],
        "x": t,
        "y": ["Calories"],
        "xlabel": "Temps (s)",
        "ylabel": "kcal",
    },
]


# =============================================================================
#
# Figure
#

fig, ax = plt.subplots(
    nrows=6,
    ncols=1,
    figsize=(12, 12),
    sharex=True,
    gridspec_kw={
        "height_ratios": [2, 2, 2, 3, 2, 1],
    },
)

fig.canvas.manager.set_window_title(
    "Merach Q1S Logger Analyzer"
)

fig.suptitle(file_basename)

fig.canvas.mpl_connect(
    "button_press_event",
    plot_click,
)

draw_all_plots()

plt.show()
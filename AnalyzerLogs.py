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
def toggle(label):
    global line_rower, line_rower_avg

    if label == "Rower Instant":
        line_rower.set_visible(
            not line_rower.get_visible()
        )

    elif label == "Rower Average":
        line_rower_avg.set_visible(
            not line_rower_avg.get_visible()
        )

    fig.canvas.draw_idle()

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


# =============================================================================

#
# Choix du fichier
#

Tk().withdraw()

filename = filedialog.askopenfilename(
    title="Choisir un fichier CSV",
    filetypes=[("CSV", "*.csv"),("Zipped CSV", "*.zip")]
)

if filename == "":
    raise SystemExit

#
# Lecture du fichier
#

df = load_log(filename)

# needd "import os"
file_basename = os.path.basename(filename)
file_corename = os.path.splitext(file_basename)[0]
# Alt : needs "from pathlib import Path"
# file_basename = Path(filename).stem

#
# Résumé
#

#print(df.keys())

print()
print("========== SESSION ==========")
print(f"Durée       : {df['Elapsed'].iloc[-1]:.1f} s")
print(f"Distance    : {df['Distance'].iloc[-1]:.1f} m")
print(f"Coups       : {int(df['Stroke_Count'].iloc[-1])}")
print(f"Calories    : {df['Calories'].iloc[-1]:.1f} kcal")
print(f"Travail     : {df['Work_J'].iloc[-1]/1000:.1f} kJ")
print(f"Puiss. moy. : {df['Power_Avg'].iloc[-1]:.1f} W")
print(f"Vit. moy.   : {df['Speed_Avg'].iloc[-1]:.2f} m/s")
print(f"Cad. moy.   : {df['Cadence_Avg'].iloc[-1]:.1f} spm")
print("=============================\n")

#
# Stats
#

power_stats = calc_stats(df["Power_Recalibrated"].tolist(), minimum=1)
cadence_stats = calc_stats(df["Cadence"].tolist(), minimum=1)
dps_stats = calc_stats(
    df["Distance_Per_Stroke"].tolist(),
    minimum=0.1,
)

"""
speed_stats = calc_stats(df["Speed"].tolist())

split_stats = calc_stats(df["Split"].tolist())

wps_stats = calc_stats(df["Work_J"].diff().fillna(0).tolist())
"""

with open(f"./Logs/stats/stats_{file_corename}.txt", "w", encoding="utf-8") as fw:
    for t, title in [
        (power_stats, "Power_Recalibrated"),
        (cadence_stats, "Cadence"),
        (dps_stats, "Distance/Stroke"),
    ]:
        fw.write(f"{title}\n-----------\n")
        for k in ["mean", "stdev", "min", "max"]:
            fw.write(f"{k}\t: {t[k]}\n")
        fw.write('\n')

# =============================================================================

#
# Temps
#

t = df["Elapsed"]

#
# Plots
# * Graph 1 : Puissance
# * Graph 2 : Vitesse
# * Graph 3 : Cadence
# * Graph 4 : Distance
# * Graph 5 : Split
# * Graph 6 : Calories
#

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
        "title": ["Speed", "Average"],
        "x": t,
        "y": ["Speed", "Speed_Avg"],
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
        "title": ["Split Calculated", "Average", "Raw Inst", "Raw Avg"],
        "x": t,
        "y": ["Split", "Split_Avg", "Raw_Split_Instant", "Raw_Split_Avg"],
        "xlabel": "Temps (s)",
        "ylabel": "s/500m",
        "linewidth": [2, 2, 1, 1],
        "linestyle": ["solid", "solid", "dashed", "dashdot"],
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

#
# Figure
#

fig, ax = plt.subplots(
    nrows= 6,
    ncols= 1,
    figsize=(12, 12),
    sharex=True
)

fig.canvas.manager.set_window_title("Merach Q1S Logger Analyzer")
fig.suptitle(file_basename)

#
# Graphs
#

for c_plot in plots:

    id = c_plot["id"]
    title=c_plot["title"] # list
    x = c_plot["x"]
    y = c_plot["y"] # list
    xlabel = c_plot["xlabel"]
    ylabel = c_plot["ylabel"]

    for j, _ in enumerate(title):

        if "linestyle" in c_plot.keys():
            linestyle = c_plot["linestyle"][j]
        else:
            linestyle = "solid"

        if "linewidth" in c_plot.keys():
            linewidth = c_plot["linewidth"][j]
        else:
            linewidth = 1

        line, = ax[id].plot(
            x, 
            df[y[j]], 
            label=title[j], 
            linewidth= linewidth, 
            linestyle=linestyle
        )

        match y[j]:
            case "Split":
                line_calc = line
            case "Split_Avg":
                line_avg = line
            case "Raw_Split_Instant":
                line_rower = line
            case "Raw_Split_Avg":
                line_rower_avg = line
        
    ax[id].set_xlabel(xlabel)
    ax[id].set_ylabel(ylabel)
    ax[id].grid(True)
    ax[id].legend()

#
# Cases à cocher
#

rax = plt.axes([0.82, 0.80, 0.16, 0.12])

labels = []
states = []

if line_rower is not None:
    labels.append("Rower Instant")
    states.append(True)

if line_rower_avg is not None:
    labels.append("Rower Average")
    states.append(True)

check = CheckButtons(rax, labels, states) 

check.on_clicked(toggle)

#plt.tight_layout(rect=[0, 0, 0.80, 1])
fig.subplots_adjust(
    left=0.08,
    right=0.78,
    top=0.95,
    bottom=0.06,
    hspace=0.35,
)

plt.show()

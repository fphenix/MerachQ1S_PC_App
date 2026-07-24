import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons
from tkinter import Tk, filedialog
import os

#
# Choix du fichier
#

Tk().withdraw()

filename = filedialog.askopenfilename(
    title="Choisir un fichier CSV",
    filetypes=[("CSV", "*.csv")]
)

if filename == "":
    raise SystemExit

#
# Lecture du fichier
#

df = pd.read_csv(
    filename,
    skiprows=2
)

#
# Résumé
#

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
print("=============================")

#
# Temps
#

t = df["Elapsed"]

#
# Figure
#

fig, ax = plt.subplots(6, 1, figsize=(12, 12), sharex=True)

fig.canvas.manager.set_window_title("Merach Logger")
fig.suptitle(os.path.basename(filename))

#
# Puissance
#

ax[0].plot(t, df["Power"], label="Power")
ax[0].plot(t, df["Power_Avg"], label="Average")
ax[0].set_ylabel("W")
ax[0].grid(True)
ax[0].legend()

#
# Vitesse
#

ax[1].plot(t, df["Speed"], label="Speed")
ax[1].plot(t, df["Speed_Avg"], label="Average")
ax[1].set_ylabel("m/s")
ax[1].grid(True)
ax[1].legend()

#
# Cadence
#

ax[2].plot(t, df["Cadence"], label="Cadence")
ax[2].plot(t, df["Cadence_Avg"], label="Average")
ax[2].set_ylabel("spm")
ax[2].grid(True)
ax[2].legend()

#
# Distance
#

ax[3].plot(t, df["Distance"])
ax[3].set_ylabel("m")
ax[3].grid(True)

#
# Split
#

line_calc, = ax[4].plot(
    t,
    df["Split"],
    label="Calculated",
    linewidth=2,
)

line_avg, = ax[4].plot(
    t,
    df["Split_Avg"],
    label="Average",
    linewidth=2,
)

line_ftms = None
line_ftms_avg = None

if "FTMS_Split_Instant" in df.columns:
    line_ftms, = ax[4].plot(
        t,
        df["FTMS_Split_Instant"],
        label="FTMS Instant",
        linestyle="--",
    )

if "FTMS_Split_Avg" in df.columns:
    line_ftms_avg, = ax[4].plot(
        t,
        df["FTMS_Split_Avg"],
        label="FTMS Average",
        linestyle=":",
    )

ax[4].set_ylabel("s/500m")
ax[4].grid(True)
ax[4].legend()

#
# Calories
#

ax[5].plot(t, df["Calories"])
ax[5].set_ylabel("kcal")
ax[5].set_xlabel("Temps (s)")
ax[5].grid(True)

#
# Cases à cocher
#

rax = plt.axes([0.82, 0.80, 0.16, 0.12])

labels = []
states = []

if line_ftms is not None:
    labels.append("FTMS Instant")
    states.append(True)

if line_ftms_avg is not None:
    labels.append("FTMS Average")
    states.append(False)

check = CheckButtons(rax, labels, states)

#
# Masque les courbes décochées
#

if line_ftms_avg is not None:
    line_ftms_avg.set_visible(False)


def toggle(label):

    if label == "FTMS Instant":
        line_ftms.set_visible(
            not line_ftms.get_visible()
        )

    elif label == "FTMS Average":
        line_ftms_avg.set_visible(
            not line_ftms_avg.get_visible()
        )

    fig.canvas.draw_idle()


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

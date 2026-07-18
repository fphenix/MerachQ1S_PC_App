import pandas as pd
import matplotlib.pyplot as plt
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
    skiprows=2      # titre + ligne vide
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

ax[4].plot(t, df["Split"], label="Split")
ax[4].plot(t, df["Split_Avg"], label="Average")
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


plt.tight_layout()

plt.show()

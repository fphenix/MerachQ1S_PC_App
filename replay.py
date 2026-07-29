"""
replay.py

Replay un Log pour émuler une Communication Bluetooth FTMS.

"""

import pandas as pd
from pathlib import Path

# =============================================================================
class ReplayFTMS:

    # -------------------------------------------------------------------------
    def __init__(self,
                 filename,
                 state,
                 speed=1.0):

        self.filename = filename
        self.state = state
        self.speed = speed


    # -------------------------------------------------------------------------
    def csv_value(self, row, *columns, default=0):
        for col in columns:

            if col in row.index:

                value = row[col]

                if value == value:      # pas NaN
                    return value

        return default


    # -------------------------------------------------------------------------
    def start(self):

        if not Path(self.filename).exists():
            raise FileNotFoundError(
                f"Replay : fichier Replay introuvable : {self.filename}"
            )
        
        self.df = pd.read_csv(
            self.filename,
            skiprows=2
        )

        first_packet = self.df.iloc[0] 

        #
        # Le premier paquet du CSV est déjà un paquet "calculable".
        # On restaure donc l'état interne précédant ce paquet afin
        # que delta_elapsed soit identique à celui de la séance réelle.
        #

        self.state.initialize_replay(
            elapsed = first_packet["Elapsed"], 
            delta_elapsed = first_packet["Delta_Elapsed"]
        )

        for _, row in self.df.iterrows():

            packet = {
                "time_elapsed": float(self.csv_value(row, "Elapsed")),

                "stroke_count": int(self.csv_value(row, "Stroke_Count")),
                "stroke_rate_instant": float(self.csv_value(row, "FTMS_SPM")),
                "stroke_rate_average": float(self.csv_value(row, "FTMS_SPM_Avg")),

                "power_instant": float(self.csv_value(row, "Power")),
                "power_average": float(self.csv_value(row, "Power_Avg")),

                "distance_total": float(self.csv_value(row, "FTMS_Distance")),

                "split_time_instant": float(self.csv_value(row, "FTMS_Split_Instant", "Split")),
                "split_time_average": float(self.csv_value(row, "FTMS_Split_Avg", "Silt_Avg")),

                "energy_total": float(self.csv_value(row, "FTMS_Energy", "Calories")),
                "energy_per_hour": float(self.csv_value(row, "FTMS_Energy_Per_Hour")),
                "energy_per_minute": float(self.csv_value(row, "FTMS_Energy_Per_Minute")),

                "resistance_level": float(self.csv_value(row, "FTMS_Resistance")),
                "training_status": int(self.csv_value(row, "FTMS_Training_Status")),
                "heart_rate": float(self.csv_value(row, "FTMS_Heart_Rate")),
            }

            self.state.update_ftms(packet)

            #break

    # -------------------------------------------------------------------------
    def stop(self):
        pass

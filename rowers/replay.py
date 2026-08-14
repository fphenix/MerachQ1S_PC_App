"""
replay.py

Replay un Log pour émuler une Communication Bluetooth FTMS.

"""

import pandas as pd
from pathlib import Path

from .data import RowerData
from .rower import RowerClient

# =============================================================================
class ReplayRower(RowerClient):

    NAME = 'Replay'

    # -------------------------------------------------------------------------
    def __init__(self,
                 filename,
                 state,
                 speed=1.0):

        super().__init__("REPLAY", state)

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

            rower_data = RowerData(
                elapsed_time=float(self.csv_value(row, "Elapsed")),
                delta_strokes=int(self.csv_value(row, "Delta_Strokes")),
                stroke_event=bool(int(self.csv_value(row, "Stroke_Event"))),

                stroke_count=int(self.csv_value(row, "Stroke_Count")),
                stroke_rate=float(self.csv_value(row, "FTMS_SPM")),
                stroke_rate_avg=float(self.csv_value(row, "FTMS_SPM_Avg")),

                cadence_raw=float(self.csv_value(row, "Cadence")),
                #cadence_avg=float(self.csv_value(row, "Cadence_Avg")),
                cadence=float(self.csv_value(row, "Cadence")),

                power=float(self.csv_value(row, "Power")),
                power_avg=float(self.csv_value(row, "Power_Avg")),

                speed=float(self.csv_value(row, "Speed")),
                speed_avg=float(self.csv_value(row, "Speed_Avg")),

                distance=float(self.csv_value(row, "Distance")),
                distance_per_stroke=float(self.csv_value(row, "Distance_Per_Stroke")),

                split_inst=float(self.csv_value(row, "Split")),
                split_avg=float(self.csv_value(row, "Split_Avg")),

                kcal=float(self.csv_value(
                        row,
                        "Calories",
                        "FTMS_Energy",
                    )
                ),

                energy_hour=float(self.csv_value(row, "FTMS_Energy_Per_Hour")),
                energy_minute=float(self.csv_value(row, "FTMS_Energy_Per_Minute")),

                work_j=float(self.csv_value(row, "Work_J")),
                work_per_stroke=(
                    float(self.csv_value(row, "Work_J"))
                    / int(self.csv_value(row, "Stroke_Count"))
                    if int(self.csv_value(row, "Stroke_Count")) > 0
                    else 0.0
                ),

                resistance_level=int(self.csv_value(row, "FTMS_Resistance")),

                training_status=int(self.csv_value(row, "FTMS_Training_Status")),

                heart_rate=int(self.csv_value(row, "FTMS_Heart_Rate")),
            )

            self.state.update(rower_data)

            #break

    # -------------------------------------------------------------------------
    def stop(self):
        pass

   # -------------------------------------------------------------------------
    def process(
        self,
        rowerdata: RowerData,
        delta_elapsed: float,
    ) -> RowerData:
        
        return rowerdata
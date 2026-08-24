"""
replay.py

Replay un Log pour émuler une Communication Bluetooth venant d'un Rameur.

"""
import time
import threading

import pandas as pd
from pathlib import Path

from .data import RowerData
from .rower import RowerClient

from calc import calc_work_per_stroke

# =============================================================================
class ReplayRower(RowerClient):

    NAME = 'Replay'

    # -------------------------------------------------------------------------
    def __init__(self, filename, state, speed=1.0):

        super().__init__("REPLAY", state)

        self.filename = filename
        self.state = state
        self.speed = speed

        self.reset()

    # -------------------------------------------------------------------------
    def reset(self):

        self._thread = None
        self._running = False

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

        if self._running:
            return

        self._running = True

        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
        )

        self._thread.start()

    # -------------------------------------------------------------------------
    def _run(self):

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
            elapsed = first_packet["Raw_Elapsed"], 
            delta_elapsed = first_packet["Delta_Elapsed"]
        )

        firstPacket = True
        prev_calories = None

        for _, row in self.df.iterrows():

            self.state.set_connection("Replay")

            power = float(self.csv_value(row, "Raw_Power"))
            stroke_count = int(self.csv_value(row, "Raw_Stroke_Count"))
            work_j = float(self.csv_value(row, "Work_J"))

            # Speed of the Replay
            delta_elapsed = float(
                self.csv_value(row, "Delta_Elapsed")
            )

            if "Calories_Rate" in self.df.columns:
                calories_rate = float(self.csv_value(row, "Calories_Rate"))
            else:
                if prev_calories is not None and delta_elapsed > 0:
                    calories_rate = (
                        float(self.csv_value(row, "Calories")) - prev_calories
                    ) / delta_elapsed
                else:
                    calories_rate = 0.0

            prev_calories = float(
                self.csv_value(row, "Calories")
            )

            if "Work_Per_Stroke" in self.df.columns:
                work_per_stroke = float(
                    self.csv_value(row, "Work_Per_Stroke")
                )
            else:
                work_per_stroke = calc_work_per_stroke(
                    work= work_j,
                    stroke_count= stroke_count
                )

            rower_data = RowerData(
                delta_strokes= int(self.csv_value(row, "Delta_Strokes")),
                stroke_event= bool(int(self.csv_value(row, "Stroke_Event"))),
                elapsed_time= float(self.csv_value(row, "Elapsed", "Raw_Elapsed")),
                stroke_count= stroke_count,
                
                distance= float(self.csv_value(row, "Distance")),
                distance_per_stroke= float(self.csv_value(row, "Distance_Per_Stroke")),

                power_avg= float(self.csv_value(row, "Power_Avg", "Raw_Power_Avg")),

                speed= float(self.csv_value(row, "Speed")),
                speed_avg= float(self.csv_value(row, "Speed_Avg")),

                cadence_inst= float(self.csv_value(row, "Cadence_Inst")),
                cadence= float(self.csv_value(row, "Cadence")),

                split_inst= float(self.csv_value(row, "Split")),
                split_avg= float(self.csv_value(row, "Split_Avg")),

                calories_rate= calories_rate,
                calories= float(self.csv_value(row, "Calories", "Raw_Energy")),

                calories_hour= float(self.csv_value(row, "Raw_Energy_Hour")),
                calories_minute= float(self.csv_value(row, "Raw_Energy_Minute")),

                work_j= work_j,
                work_per_stroke= work_per_stroke,

                raw_elapsed_time= float(self.csv_value(row, "Raw_Elapsed")),
                raw_stroke_count= stroke_count,

                raw_distance= float(self.csv_value(row, "Raw_Distance")),

                raw_stroke_rate= float(self.csv_value(row, "Raw_Stroke_Rate")),
                raw_stroke_rate_avg= float(self.csv_value(row, "Raw_Stroke_Rate_Avg")),

                raw_power= power,
                raw_power_avg= float(self.csv_value(row, "Raw_Power_Avg", "Power_Avg")),

                raw_split_inst= float(self.csv_value(row, "Raw_Split_Instant")),
                raw_split_avg= float(self.csv_value(row, "Raw_Split_Avg")),

                raw_calories= float(self.csv_value(row, "Raw_Energy")),
                raw_calories_hour= float(self.csv_value(row, "Raw_Energy_Hour")),
                raw_calories_minute= float(self.csv_value(row, "Raw_Energy_Minute")),

                raw_resistance= int(self.csv_value(row, "Raw_Resistance")),
                raw_training_status= int(self.csv_value(row, "Raw_Training_Status")),
                raw_heart_rate= int(self.csv_value(row, "Raw_Heart_Rate")),
            )

            if not firstPacket and self.speed > 0:
                time.sleep(delta_elapsed / self.speed)

            # Update State
            self.state.update(rower_data)

            firstPacket = False

            #break

    # -------------------------------------------------------------------------
    def stop(self):

        self._running = False

        if self._thread is not None:
            self._thread.join(timeout=5)

   # -------------------------------------------------------------------------
    def process(
        self,
        rowerdata: RowerData,
        delta_elapsed: float
    ) -> RowerData:
        
        return rowerdata

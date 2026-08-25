"""
replay_q1s.py

Rejoue les données brutes d'un log Q1S.

Le Replay ne calcule aucune métrique et ne remplace pas MerachRower.
Il injecte des données raw dans le même pipeline que le Bluetooth :

    ReplayQ1S -> MerachRower + MerachQ1SCalc -> RowerData -> RowState
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pandas as pd

from rowers.merach_q1s import MerachRower
from replays.replay_source import ReplaySource

from utils import echoerr

# =============================================================================
class ReplayQ1S(ReplaySource):
    """Source de replay pour le pipeline Merach Q1S."""

    NAME = "Replay Q1S"

    # -------------------------------------------------------------------------
    def __init__(
        self,
        filename: str,
        state,
        speed: float = 1.0,
    ) -> None:

        super().__init__(filename, speed)

        self.state = state

        # Le vrai modèle Q1S est utilisé pendant le replay.
        self.rower = MerachRower(state)

    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Réinitialise le modèle Q1S sans arrêter le thread de replay."""

        self.rower.reset()

    # ------------------------------------------------------------------
    # Abstracted in parent class
    def start(self) -> None:

        if self._running:
            return

        self._running = True

        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
        )

        self._thread.start()

    # ------------------------------------------------------------------
    # Abstracted in parent class
    def stop(self) -> None:

        self._running = False

        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    # ------------------------------------------------------------------
    @staticmethod
    def csv_value(
        row: pd.Series,
        *columns: str,
        default: float = 0.0,
    ) -> float:

        for column in columns:

            if column not in row.index:
                continue

            value = row[column]

            if pd.notna(value):
                return float(value)

        return default

    # ------------------------------------------------------------------
    def _raw_event_from_row(self, row: pd.Series) -> dict:

        return {
            # Données natives Q1S / FTMS
            "time_elapsed": self.csv_value(
                row, "Raw_Elapsed"
            ),

            "stroke_count": int(
                self.csv_value(row, "Raw_Stroke_Count")
            ),

            "power_instant": self.csv_value(
                row, "Raw_Power"
            ),

            "power_average": self.csv_value(
                row, "Raw_Power_Avg"
            ),

            "distance_total": self.csv_value(
                row, "Raw_Distance"
            ),

            "stroke_rate_instant": self.csv_value(
                row, "Raw_Stroke_Rate"
            ),

            "stroke_rate_average": self.csv_value(
                row, "Raw_Stroke_Rate_Avg"
            ),

            "split_time_instant": self.csv_value(
                row, "Raw_Split_Instant"
            ),

            "split_time_average": self.csv_value(
                row, "Raw_Split_Avg"
            ),

            "energy_total": self.csv_value(
                row, "Raw_Energy"
            ),

            "energy_per_hour": self.csv_value(
                row, "Raw_Energy_Hour"
            ),

            "energy_per_minute": self.csv_value(
                row, "Raw_Energy_Minute"
            ),

            "resistance_level": int(
                self.csv_value(row, "Raw_Resistance")
            ),

            "training_status": int(
                self.csv_value(row, "Raw_Training_Status")
            ),

            "heart_rate": int(
                self.csv_value(row, "Raw_Heart_Rate")
            ),
        }

    # ------------------------------------------------------------------
    # Abstracted in parent class
    def _run(self) -> None:

        path = Path(self.filename)

        if not path.exists():
            self._running = False

            raise FileNotFoundError(
                f"Replay Q1S : fichier introuvable : {path}"
            )

        try:

            df = pd.read_csv(
                path,
                skiprows=2, # 2 first lines are skipped to point on table
            )

            if df.empty:
                self._running = False

                raise FileNotFoundError(
                    f"Replay Q1S : fichier vide : {path}"
                )

            self.state.set_connection("Replay")

            # Le premier paquet passe dans exactement le même
            # pipeline que les paquets Bluetooth.
            first_packet = True

            for _, row in df.iterrows():

                if not self._running:
                    break

                raw_event = self._raw_event_from_row(row)

                # Le temps utilisé pour accélérer le replay est celui
                # enregistré dans le log, pas un recalcul.
                delta_elapsed = self.csv_value(
                    row,
                    "Delta_Elapsed",
                )

                self.rower.feed_raw_data(raw_event)

                if not first_packet and self.speed > 0.0:
                    time.sleep(
                        max(0.0, delta_elapsed / self.speed)
                    )

                first_packet = False

        except Exception as exc:

            echoerr(
                f"Erreur Replay Q1S : {exc}"
            )

        finally:

            self._running = False
            self.state.set_connection("Arrêt")

    # ------------------------------------------------------------------
    @property
    def running(self) -> bool:
        return self._running

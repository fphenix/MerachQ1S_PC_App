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

from rowers.merach_q1s import MerachRower
from replays.replay_source import ReplaySource

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
    def _raw_event_from_row(self, row: dict[str, str]) -> dict:

        return {
            # Données natives Q1S / FTMS
            "time_elapsed": self.csv_value(row, "Raw_Elapsed"),
            "stroke_count": int(self.csv_value(row, "Raw_Stroke_Count")),

            "distance_total": self.csv_value(row, "Raw_Distance"),

            "split_time_instant": self.csv_value(row, "Raw_Split_Instant"),
            "split_time_average": self.csv_value(row, "Raw_Split_Avg"),

            "power_instant": self.csv_value(row, "Raw_Power"),
            "power_average": self.csv_value(row, "Raw_Power_Avg"),

            "stroke_rate_instant": self.csv_value(row, "Raw_Stroke_Rate"),
            "stroke_rate_average": self.csv_value(row, "Raw_Stroke_Rate_Avg"),

            "energy_total": self.csv_value(row, "Raw_Energy"),
            "energy_per_hour": self.csv_value(row, "Raw_Energy_Hour"),
            "energy_per_minute": self.csv_value(row, "Raw_Energy_Minute"),

            "resistance_level": int(self.csv_value(row, "Raw_Resistance")),
            "training_status": int(self.csv_value(row, "Raw_Training_Status")),
            "heart_rate": int(self.csv_value(row, "Raw_Heart_Rate")),
        }

    # ------------------------------------------------------------------
    # Abstracted in parent class
    def _run(self) -> None:

        try:
            self.state.set_connection("Replay")

            first_row = True

            for row in self.iter_rows():

                if not self._running:
                    break

                raw_event = self._raw_event_from_row(row)

                if not first_row:
                    delta_elapsed = self.csv_value(
                        row,
                        "Delta_Elapsed",
                        0.0,
                    )

                    if self.speed > 0.0:
                        time.sleep(
                            max(
                                0.0,
                                delta_elapsed / self.speed,
                            )
                        )

                self.rower.feed_raw_data(raw_event)

                first_row = False

        except Exception as exc:
            self._running = False

            raise Exception(f"Replay Q1S : {exc}")

        finally:
            self._running = False
            self.state.set_connection("Arrêt")

    # ------------------------------------------------------------------
    @property
    def running(self) -> bool:
        return self._running

from dataclasses import dataclass
from threading import Lock
from copy import deepcopy
from collections import deque

from logger import CsvLogger
from logrecord import LogRecord
import time

from constants import DRAG_FACTOR, CALORIE_OFFSET, CADENCE_WINDOW

@dataclass(slots=True)
class FtmsData:
    connection: str = "Recherche..."

    elapsed_time: float = 0

    distance: float = 0

    power: float = 0
    power_avg: float = 0

    stroke_rate: float = 0
    stroke_rate_avg: float = 0

    stroke_count: int = 0

    split_avg: float = 0

    kcal: float = 0


@dataclass(slots=True)
class SessionData:
    # énergie développée
    work_j: float = 0.0

    # distance calculée par intégration
    distance: float = 0.0

    # vitesse
    speed: float = 0.0
    speed_avg: float = 0.0

    # cadence
    cadence: float = 0.0
    cadence_avg: float = 0.0

    # split
    split: float = 0.0
    split_avg: float = 0.0

    # distance/coup
    distance_per_stroke: float = 0.0

    # calories calculées
    calories: float = 0.0
    calories_rate: float = 0.0

    # valeurs précédentes (pour calcul cadence instantanée)
    last_elapsed: float = 0.0
    last_strokes: int = 0

    stroke_times: deque = None
    stroke_numbers: deque = None

@dataclass(slots=True)
class Snapshot:
    ftms: FtmsData
    session: SessionData


class RowState:
    def __init__(self):

        self._lock = Lock()

        self.ftms = FtmsData()

        self.session = SessionData()

        self.session.stroke_times = deque(maxlen=CADENCE_WINDOW)
        self.session.stroke_numbers = deque(maxlen=CADENCE_WINDOW)

        self._last_time = None

        self.logger = None


    def reset_session(self):
        """
        Remet à zéro les statistiques de séance.
        Les données FTMS restent inchangées.
        """

        with self._lock:
            self.session = SessionData()

            self.session.stroke_times = deque(maxlen=CADENCE_WINDOW)
            self.session.stroke_numbers = deque(maxlen=CADENCE_WINDOW)

            self._last_time = self.ftms.elapsed_time


    def set_connection(self, status: str):
        with self._lock:
            self.ftms.connection = status


    def set_logger(self, logger: CsvLogger):
        self.logger = logger


    def update_ftms(self, data: dict):
        with self._lock:
            #
            # Temps écoulé
            #

            delta_elapsed = 0.0

            if "time_elapsed" in data:
                t = float(data["time_elapsed"])

                delta_elapsed = 0 if self._last_time is None else max(0.0, t - self._last_time)

                self._last_time = t
                self.ftms.elapsed_time = t

            #
            # Copie des données FTMS
            #

            mapping = {
                "distance_total": "distance",
                "power_instant": "power",
                "power_average": "power_avg",
                "stroke_rate_instant": "stroke_rate",
                "stroke_rate_average": "stroke_rate_avg",
                "stroke_count": "stroke_count",
                "split_time_average": "split_avg",
                "energy_total": "kcal",
            }

            for k, a in mapping.items():
                if k in data:
                    setattr(self.ftms, a, data[k])

            #
            # Aucun calcul au premier paquet
            #

            if delta_elapsed <= 0:
                return

            #
            # Travail mécanique
            #

            self.session.work_j += self.ftms.power * delta_elapsed

            #
            # Vitesse instantanée
            #

            if self.ftms.power > 0:
                self.session.speed = (self.ftms.power / DRAG_FACTOR) ** (1.0 / 3.0)

            else:
                self.session.speed = 0.0

            #
            # Vitesse moyenne
            #

            if self.ftms.power_avg > 0:
                self.session.speed_avg = (self.ftms.power_avg / DRAG_FACTOR) ** (1.0 / 3.0)

            else:
                self.session.speed_avg = 0.0

            #
            # Distance intégrée
            #

            self.session.distance += self.session.speed * delta_elapsed

            #
            # Split
            #

            if self.session.speed > 0:
                self.session.split = 500.0 / self.session.speed

            else:
                self.session.split = 0.0

            if self.session.speed_avg > 0:
                self.session.split_avg = 500.0 / self.session.speed_avg

            else:
                self.session.split_avg = 0.0

            #
            # Calories  instantanées (kcal/s)
            # Calories cumulées (kcal)
            #

            self.session.calories_rate = (4.0 * self.ftms.power + CALORIE_OFFSET) / 3600.0

            self.session.calories += self.session.calories_rate * delta_elapsed

            #
            # Cadence moyenne
            #

            if self.ftms.elapsed_time > 0:
                self.session.cadence_avg = (
                    60.0
                    * self.ftms.stroke_count
                    / self.ftms.elapsed_time
                )

            else:
                self.session.cadence_avg = 0.0

            #
            # Cadence instantanée
            #

            delta_strokes = (
                self.ftms.stroke_count
                - self.session.last_strokes
            )

            stroke_event = delta_strokes > 0

            if stroke_event:

                #
                # mémorise chaque nouveau coup
                #

                for i in range(delta_strokes):

                    self.session.stroke_times.append(
                        self.ftms.elapsed_time
                    )

                    self.session.stroke_numbers.append(
                        self.ftms.stroke_count
                        - delta_strokes
                        + i
                        + 1
                    )

                #
                # cadence sur les derniers coups
                #

                if len(self.session.stroke_times) >= 2:

                    dt = (
                        self.session.stroke_times[-1]
                        - self.session.stroke_times[0]
                    )

                    dn = (
                        self.session.stroke_numbers[-1]
                        - self.session.stroke_numbers[0]
                    )

                    if dt > 0 and dn > 0:

                        self.session.cadence = (
                            60.0
                            * dn
                            / dt
                        )

                self.session.last_elapsed = (
                    self.ftms.elapsed_time
                )

                self.session.last_strokes = (
                    self.ftms.stroke_count
                )

            #
            # Distance par coup
            #

            if self.session.cadence > 0:
                self.session.distance_per_stroke = (
                    60.0
                    * self.session.speed
                    / self.session.cadence
                )

            #
            # Logger
            #

            if self.logger is not None:

                if stroke_event:
                    self.logger.stroke_detected()

                self.logger.check_end_session()

                packet, pc_time, delta_pc = self.logger.next_packet()

                record = LogRecord(

                    packet=packet,

                    pc_time=pc_time,
                    delta_pc=delta_pc,

                    elapsed=self.ftms.elapsed_time,
                    delta_elapsed=delta_elapsed,

                    power=self.ftms.power,
                    power_avg=self.ftms.power_avg,

                    stroke_count=self.ftms.stroke_count,
                    delta_strokes=delta_strokes,
                    stroke_event=stroke_event,

                    speed=self.session.speed,
                    speed_avg=self.session.speed_avg,

                    distance=self.session.distance,

                    cadence=self.session.cadence,
                    cadence_avg=self.session.cadence_avg,

                    split=self.session.split,
                    split_avg=self.session.split_avg,

                    distance_per_stroke=self.session.distance_per_stroke,

                    calories=self.session.calories,

                    #
                    # FTMS bruts
                    #

                    ftms_distance=self.ftms.distance,

                    ftms_spm=self.ftms.stroke_rate,

                    ftms_spm_avg=self.ftms.stroke_rate_avg,

                    ftms_split_avg=self.ftms.split_avg,

                    ftms_energy=self.ftms.kcal,

                )

                self.logger.log(record)


    def snapshot(self):
        with self._lock:
            return Snapshot(
                deepcopy(self.ftms),
                deepcopy(self.session),
            )
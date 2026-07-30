from dataclasses import dataclass
from threading import Lock
from copy import deepcopy
from collections import deque

from logger import CsvLogger
from logrecord import LogRecord

from constants import (
    CADENCE_WINDOW, CADENCE_SMOOTHING,
)

from calc import (
    calc_delta,
    calc_speed,
    calc_split,
    calc_kcal_rate,
    calc_dist,
    calc_work,
    calc_kcal,
    calc_cadence_avg,
    calc_cadence_inst,
    calc_dist_per_stroke,
)

# =============================================================================
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

    split_inst: float = 0
    split_avg: float = 0

    kcal: float = 0

    energy_hour: float = 0
    energy_minute: float = 0

    resistance_level: int = 0

    training_status: int = 0

    heart_rate: int = 0


# =============================================================================
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
    cadence_raw: float = 0.0
    cadence_avg: float = 0.0
    cadence_history: deque = None

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


# =============================================================================
@dataclass(slots=True)
class Snapshot:
    ftms: FtmsData
    session: SessionData


# =============================================================================
class RowState:

    # -------------------------------------------------------------------------
    def __init__(self):

        self._lock = Lock()

        self.ftms = FtmsData()

        self.session = SessionData()

        self.session.stroke_times = deque(maxlen=CADENCE_WINDOW)

        self.session.cadence_history = deque(maxlen=CADENCE_SMOOTHING)

        self._last_time = None

        self.logger = None


    # -------------------------------------------------------------------------
    def reset_session(self):
        """
        Remet à zéro les statistiques de séance.
        Les données FTMS restent inchangées.
        """

        with self._lock:
            self.session = SessionData()

            self.session.stroke_times = deque(maxlen=CADENCE_WINDOW)

            self.session.cadence_history = deque(maxlen=CADENCE_SMOOTHING)

            self._last_time = self.ftms.elapsed_time


    # -------------------------------------------------------------------------
    def initialize_replay(self, elapsed, delta_elapsed):
        self._last_time = calc_delta(elapsed, delta_elapsed)


    # -------------------------------------------------------------------------
    def set_connection(self, status: str):
        with self._lock:
            self.ftms.connection = status


    # -------------------------------------------------------------------------
    def set_logger(self, logger: CsvLogger):
        self.logger = logger


    # -------------------------------------------------------------------------
    def update_ftms(self, data: dict):
        with self._lock:
            #
            # Temps écoulé
            #

            delta_elapsed = 0.0

            if "time_elapsed" in data:
                t = float(data["time_elapsed"])

                delta_elapsed = 0.0 if self._last_time is None else max(0.0, calc_delta(t, self._last_time))

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

                "split_time_instant": "split_inst",
                "split_time_average": "split_avg",

                "energy_total": "kcal",
                "energy_per_hour": "energy_hour",
                "energy_per_minute": "energy_minute",

                "resistance_level": "resistance_level",

                "training_status": "training_status",

                "heart_rate": "heart_rate",
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

            self.session.work_j += calc_work(self.ftms.power, delta_elapsed)

            #
            # Vitesse instantanée
            #

            self.session.speed = calc_speed(self.ftms.power)

            #
            # Vitesse moyenne
            #

            self.session.speed_avg = calc_speed(self.ftms.power_avg)

            #
            # Distance intégrée
            #

            self.session.distance += calc_dist(self.session.speed, delta_elapsed)

            #
            # Split
            #

            self.session.split = calc_split(self.session.speed)

            self.session.split_avg = calc_split(self.session.speed_avg)

            #
            # Calories  instantanées (kcal/s)
            # Calories cumulées (kcal)
            #

            self.session.calories_rate = calc_kcal_rate(self.ftms.power)

            self.session.calories += calc_kcal(self.session.calories_rate, delta_elapsed)

            #
            # Cadence moyenne
            #

            self.session.cadence_avg = calc_cadence_avg(
                    self.ftms.stroke_count, 
                    self.ftms.elapsed_time
                )

            #
            # Cadence instantanée
            #

            delta_strokes = calc_delta(
                self.ftms.stroke_count,
                self.session.last_strokes
            )

            stroke_event = delta_strokes > 0

            if stroke_event:

                #
                # Répartition des coups dans le temps.
                #
                # Si plusieurs coups sont reçus dans un même paquet BLE,
                # on suppose qu'ils sont répartis uniformément entre
                # l'échantillon précédent et l'échantillon courant.
                #

                if delta_strokes == 1:

                    self.session.stroke_times.append(
                        self.ftms.elapsed_time
                    )

                else:

                    step = delta_elapsed / delta_strokes

                    first_time = (
                        calc_delta(self.ftms.elapsed_time, delta_elapsed)
                        + step
                    )

                    first_stroke = (
                        calc_delta(self.ftms.stroke_count, delta_strokes)
                        + 1
                    )

                    for i in range(delta_strokes):

                        self.session.stroke_times.append(
                            first_time + i * step
                        )

                #
                # Cadence calculée sur les derniers coups
                #

                self.session.cadence_raw, self.session.cadence = (
                    calc_cadence_inst(
                        self.session.stroke_times,
                        self.session.cadence_history,
                    )
                )

                #
                # Mémorisation pour le prochain calcul
                #

                self.session.last_elapsed = (
                    self.ftms.elapsed_time
                )

                self.session.last_strokes = (
                    self.ftms.stroke_count
                )

            #
            # Distance par coup
            #

            self.session.distance_per_stroke = calc_dist_per_stroke(
                self.session.speed,
                self.session.cadence
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

                    cadence=self.session.cadence_raw,
                    cadence_avg=self.session.cadence_avg,

                    split=self.session.split,
                    split_avg=self.session.split_avg,

                    distance_per_stroke=self.session.distance_per_stroke,

                    calories=self.session.calories,
                    work_j=self.session.work_j,

                    #
                    # FTMS bruts
                    #

                    ftms_distance=self.ftms.distance,

                    ftms_spm=self.ftms.stroke_rate,

                    ftms_spm_avg=self.ftms.stroke_rate_avg,

                    ftms_split_inst=self.ftms.split_inst,
                    ftms_split_avg=self.ftms.split_avg,

                    ftms_energy=self.ftms.kcal,
                    ftms_energy_hour=self.ftms.energy_hour,
                    ftms_energy_minute=self.ftms.energy_minute,

                    ftms_resistance=self.ftms.resistance_level,

                    ftms_training_status=self.ftms.training_status,

                    ftms_heart_rate=self.ftms.heart_rate,

                )

                self.logger.log(record)


    # -------------------------------------------------------------------------
    def snapshot(self):
        with self._lock:
            return Snapshot(
                deepcopy(self.ftms),
                deepcopy(self.session),
            )

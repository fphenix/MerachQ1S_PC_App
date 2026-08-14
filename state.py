from threading import Lock
from copy import deepcopy

from logger import CsvLogger
from logrecord import LogRecord

from rowers.data import RowerData

from session import SessionData
from snapshot import Snapshot

from calc import (
    calc_delta,
    calc_cadence_from_strokes,
    calc_dist_per_stroke,
)

# =============================================================================
class RowState:

    # -------------------------------------------------------------------------
    def __init__(self):

        self._lock = Lock()

        self.rower = None

        self.rowerdata = RowerData()
        self.session = SessionData()

        self._last_time = None
        self.delta_strokes = 0
        self.stroke_event = False

        self.logger = None


    # -------------------------------------------------------------------------
    def reset_session(self):
        """
        Remet à zéro les statistiques de séance.
        Les données restent inchangées.
        """

        with self._lock:
            self.session = SessionData()

            self._last_time = self.rowerdata.elapsed_time


    # -------------------------------------------------------------------------
    def initialize_replay(self, elapsed, delta_elapsed):
        self._last_time = calc_delta(elapsed, delta_elapsed)


    # -------------------------------------------------------------------------
    def set_connection(self, status: str):
        with self._lock:
            self.rowerdata.connection = status


    # -------------------------------------------------------------------------
    def set_logger(self, logger: CsvLogger):
        self.logger = logger


    # -------------------------------------------------------------------------
    def update(self, rowerdata: RowerData):

        with self._lock:

            #
            # Temps écoulé
            #

            delta_elapsed = 0.0

            t = float(rowerdata.elapsed_time)

            if self._last_time is not None:
                delta_elapsed = max(
                    0.0,
                    calc_delta(t, self._last_time),
                )

            self._last_time = t
            self.rowerdata = rowerdata

            if self.rower is not None:
                self.rowerdata = self.rower.process(
                    self.rowerdata,
                    delta_elapsed,
                )

            self.delta_strokes = self.rowerdata.delta_strokes
            self.stroke_event = self.rowerdata.stroke_event

            #
            # Aucun calcul au premier paquet
            #

            if delta_elapsed <= 0:
                return

            #
            # Cadence
            #

            self.session.cadence_raw = self.rowerdata.cadence_raw
            self.session.cadence = self.rowerdata.cadence
            self.session.cadence_avg = calc_cadence_from_strokes(self.rowerdata.stroke_count, self.rowerdata.elapsed_time)

            #
            # Travail mécanique
            #

            self.session.work_j = self.rowerdata.work_j
            self.session.work_per_stroke = self.rowerdata.work_per_stroke

            #
            # Vitesse instantanée
            #

            self.session.speed = self.rowerdata.speed

            #
            # Vitesse moyenne
            #

            self.session.speed_avg = self.rowerdata.speed_avg

            #
            # Distance intégrée
            #

            self.session.distance = self.rowerdata.distance

            #
            # Split
            #

            self.session.split = self.rowerdata.split_inst

            self.session.split_avg = self.rowerdata.split_avg

            #
            # Calories instantanées (kcal/s)
            # Calories cumulées (kcal)
            #
            self.session.calories_rate = self.rowerdata.kcal_rate
            self.session.calories = self.rowerdata.kcal

            #
            # Distance par coup
            #

            self.session.distance_per_stroke = calc_dist_per_stroke(
                self.session.speed,
                self.session.cadence,
            )

            #
            # Logger
            #

            if self.logger is not None:

                if self.stroke_event:
                    self.logger.stroke_detected()

                self.logger.check_end_session()

                packet, pc_time, delta_pc = self.logger.next_packet()

                record = LogRecord(

                    packet=packet,

                    pc_time=pc_time,
                    delta_pc=delta_pc,

                    elapsed=self.rowerdata.elapsed_time,
                    delta_elapsed=delta_elapsed,

                    power=self.rowerdata.power,
                    power_avg=self.rowerdata.power_avg,

                    stroke_count=self.rowerdata.stroke_count,
                    delta_strokes=self.delta_strokes,
                    stroke_event=self.stroke_event,

                    speed=self.session.speed,
                    speed_avg=self.session.speed_avg,

                    distance=self.session.distance,

                    cadence_raw=self.session.cadence_raw,   # cadence instantanée non lissée
                    cadence_avg=self.session.cadence_avg,   # cadence moyenne sur la séance

                    split=self.session.split,
                    split_avg=self.session.split_avg,

                    distance_per_stroke=self.session.distance_per_stroke,

                    calories=self.session.calories,
                    work_j=self.session.work_j,

                    #
                    # FTMS bruts
                    #

                    raw_distance=self.rowerdata.distance,

                    raw_stroke_rate=self.rowerdata.stroke_rate,

                    raw_stroke_rate_avg=self.rowerdata.stroke_rate_avg,

                    raw_split_inst=self.rowerdata.split_inst,
                    raw_split_avg=self.rowerdata.split_avg,

                    raw_energy=self.rowerdata.kcal,
                    raw_energy_hour=self.rowerdata.energy_hour,
                    raw_energy_minute=self.rowerdata.energy_minute,

                    raw_resistance=self.rowerdata.resistance_level,

                    raw_training_status=self.rowerdata.training_status,

                    raw_heart_rate=self.rowerdata.heart_rate,
                )

                self.logger.log(record)


    # -------------------------------------------------------------------------
    def snapshot(self):
        with self._lock:
            return Snapshot(
                deepcopy(self.rowerdata),
                deepcopy(self.session),
            )

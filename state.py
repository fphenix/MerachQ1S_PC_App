from threading import Lock
from copy import deepcopy

from logger import CsvLogger
from logrecord import LogRecord

from rowers.data import RowerData

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

        self._last_time = None
        self._elapsed_offset = 0.0
        self._stroke_offset = 0
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
            self._elapsed_offset = self.rowerdata.elapsed_time
            self._stroke_offset = self.rowerdata.stroke_count

            self._last_time = 0.0

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

            rowerdata.elapsed_time = max(0.0, rowerdata.elapsed_time - self._elapsed_offset)
            rowerdata.stroke_count = max(0, rowerdata.stroke_count - self._stroke_offset)

            temp = float(rowerdata.elapsed_time)

            if self._last_time is not None:
                delta_elapsed = max(
                    0.0,
                    calc_delta(temp, self._last_time),
                )

            self._last_time = temp

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
            # Cadence moyenne (strokes per minute) : calculée
            #

            self.rowerdata.cadence_avg = calc_cadence_from_strokes(
                self.rowerdata.stroke_count, 
                self.rowerdata.elapsed_time
            )

            #
            # Distance par coup (m/stroke) : calculé
            #

            self.rowerdata.distance_per_stroke = calc_dist_per_stroke(
                self.rowerdata.speed,
                self.rowerdata.cadence,
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

                    speed=self.rowerdata.speed,
                    speed_avg=self.rowerdata.speed_avg,

                    distance=self.rowerdata.distance,

                    cadence_raw=self.rowerdata.cadence_raw,   # "Cadence" : cadence instantanée brute calculée sur la fenêtre
                    cadence=self.rowerdata.cadence,           # "Cadence_Inst": cadence instantanée lissée
                    cadence_avg=self.rowerdata.cadence_avg,   # "Cadence_Avg": cadence moyenne sur la séance

                    split=self.rowerdata.split_inst,
                    split_avg=self.rowerdata.split_avg,

                    distance_per_stroke=self.rowerdata.distance_per_stroke,

                    calories_rate= self.rowerdata.calories_rate,
                    calories=self.rowerdata.calories,

                    work_j=self.rowerdata.work_j,
                    work_per_stroke=self.rowerdata.work_per_stroke,

                    #
                    # FTMS bruts
                    #

                    raw_distance=self.rowerdata.raw_distance,

                    raw_stroke_rate=self.rowerdata.raw_stroke_rate,
                    raw_stroke_rate_avg=self.rowerdata.raw_stroke_rate_avg,

                    raw_split_inst=self.rowerdata.raw_split_inst,
                    raw_split_avg=self.rowerdata.raw_split_avg,

                    raw_calories=self.rowerdata.raw_calories,
                    raw_calories_hour=self.rowerdata.raw_calories_hour,
                    raw_calories_minute=self.rowerdata.raw_calories_minute,

                    raw_resistance=self.rowerdata.raw_resistance,
                    raw_training_status=self.rowerdata.raw_training_status,
                    raw_heart_rate=self.rowerdata.raw_heart_rate,
                )

                self.logger.log(record)


    # -------------------------------------------------------------------------
    def snapshot(self):
        
        with self._lock:
            return Snapshot(
                deepcopy(self.rowerdata),
            )

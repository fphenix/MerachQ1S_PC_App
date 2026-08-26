from threading import Lock
from copy import deepcopy

from logger import CsvLogger
from logrecord import LogRecord

from rowers.data import RowerData

from snapshot import Snapshot

from calc import calc_delta

from utils import debug

# =============================================================================
class RowState:

    # -------------------------------------------------------------------------
    def __init__(self):

        self._lock = Lock()

        self.rower = None

        self.curr_rowerdata = RowerData()

        self._last_time = None
        self._elapsed_offset = 0.0
        self._stroke_offset = 0

        self.delta_strokes = 0
        self.stroke_event = False

        self.logger = None

    # -------------------------------------------------------------------------
    def reset_session(self):
        """
        Remet à zéro les données de séance sans arrêter le rameur.
        La connexion et les compteurs raw de la machine sont conservés
        via les offsets de session.
        """

        with self._lock:
            connection = self.curr_rowerdata.connection

            self._elapsed_offset = self.curr_rowerdata.raw_elapsed_time
            self._stroke_offset = self.curr_rowerdata.raw_stroke_count

            self._last_time = None

            self.curr_rowerdata = RowerData(
                connection=connection,
            )

    # -------------------------------------------------------------------------
    def initialize_replay(self, elapsed, delta_elapsed):

        self._last_time = calc_delta(elapsed, delta_elapsed)


    # -------------------------------------------------------------------------
    def set_connection(self, status: str):

        with self._lock:
            self.curr_rowerdata.connection = status


    # -------------------------------------------------------------------------
    def set_logger(self, logger: CsvLogger):

        self.logger = logger


    # -------------------------------------------------------------------------
    def update(self, new_rowerdata: RowerData):

        with self._lock:

            #
            # Temps écoulé
            #

            delta_elapsed = 0.0

            # for elapsed_time and stroke_count we want the value
            # minus the "New Session" offset (offset is 0 for first
            # session). We also clamp is to 0 if it ever goes negative.
            elapsed_time = max(
                0.0, 
                calc_delta(
                    new_rowerdata.raw_elapsed_time, 
                    self._elapsed_offset
                )
            )

            stroke_count = max(
                0, 
                calc_delta(
                    new_rowerdata.raw_stroke_count,
                    self._stroke_offset
                )
            )

            if self._last_time is None: # first packet
                delta_elapsed = 0.0
            else:
                delta_elapsed = max(
                    0.0,
                    calc_delta(elapsed_time, self._last_time),
                )

            self._last_time = elapsed_time

            self.curr_rowerdata = new_rowerdata

            self.curr_rowerdata.elapsed_time = elapsed_time
            self.curr_rowerdata.stroke_count = stroke_count

            #
            # Process the data with the machine model
            #

            if self.rower is not None:
                self.curr_rowerdata = self.rower.process(
                    self.curr_rowerdata,
                    delta_elapsed
                )

            self.delta_strokes = self.curr_rowerdata.delta_strokes
            self.stroke_event = self.curr_rowerdata.stroke_event

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

                    elapsed_time=elapsed_time,
                    delta_elapsed=delta_elapsed,

                    power=self.curr_rowerdata.power,
                    power_avg=self.curr_rowerdata.power_avg,

                    stroke_count=stroke_count,
                    delta_strokes=self.delta_strokes,
                    stroke_event=self.stroke_event,

                    speed=self.curr_rowerdata.speed,
                    speed_avg=self.curr_rowerdata.speed_avg,

                    distance=self.curr_rowerdata.distance,

                    cadence_inst=self.curr_rowerdata.cadence_inst,   # "Cadence_Inst" : cadence instantanée brute
                    cadence=self.curr_rowerdata.cadence,             # "Cadence": cadence instantanée lissée
                    cadence_avg=self.curr_rowerdata.cadence_avg,     # "Cadence_Avg": cadence moyenne sur la séance

                    split=self.curr_rowerdata.split_inst,
                    split_avg=self.curr_rowerdata.split_avg,

                    distance_per_stroke=self.curr_rowerdata.distance_per_stroke,
                    dist_per_stroke_avg=self.curr_rowerdata.dist_per_stroke_avg,

                    calories_rate= self.curr_rowerdata.calories_rate,
                    calories=self.curr_rowerdata.calories,

                    work_j=self.curr_rowerdata.work_j,
                    work_per_stroke=self.curr_rowerdata.work_per_stroke,

                    #
                    # Autres valeurs venant diretement du Rameur
                    #

                    raw_elapsed_time=new_rowerdata.raw_elapsed_time,
                    raw_distance=self.curr_rowerdata.raw_distance,

                    raw_stroke_count=new_rowerdata.raw_stroke_count,

                    raw_stroke_rate=self.curr_rowerdata.raw_stroke_rate,
                    raw_stroke_rate_avg=self.curr_rowerdata.raw_stroke_rate_avg,

                    raw_power=self.curr_rowerdata.raw_power,
                    raw_power_avg=self.curr_rowerdata.raw_power_avg,

                    raw_split_inst=self.curr_rowerdata.raw_split_inst,
                    raw_split_avg=self.curr_rowerdata.raw_split_avg,

                    raw_calories=self.curr_rowerdata.raw_calories,
                    raw_calories_hour=self.curr_rowerdata.raw_calories_hour,
                    raw_calories_minute=self.curr_rowerdata.raw_calories_minute,

                    raw_resistance=self.curr_rowerdata.raw_resistance,
                    raw_training_status=self.curr_rowerdata.raw_training_status,
                    raw_heart_rate=self.curr_rowerdata.raw_heart_rate,
                )

                self.logger.log(record)

    # -------------------------------------------------------------------------
    def snapshot(self):
        
        with self._lock:
            return Snapshot(
                deepcopy(self.curr_rowerdata),
            )

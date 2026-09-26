from threading import Lock
from collections import deque
from copy import deepcopy

from engine.snapshot import Snapshot

from engine.calc import calc_delta, calc_deltatime
from setup.utils import clamp_to_zero

from rowers.data import RowerData

from logger.logger import CsvLogger
from logger.logrecord import LogRecord

# =============================================================================
class RowState:

    def __init__(self) -> None:

        self._lock = Lock()

        self.source = None # MerachRower | ReplayQ1S | None
        self.rower = None # MerachRower | None

        self.curr_rowerdata = RowerData()

        self._last_time: float | None = None
        self._elapsed_offset: float = 0.0
        self._stroke_offset: int = 0

        self.delta_strokes: int = 0
        self.stroke_event: bool = False

        self.logger: CsvLogger | None = None

        self._session_rebase_pending: bool = False

        self._distance_history = deque(maxlen=10000)
        self._distance_history_index: int = 0

    # -------------------------------------------------------------------------
    def set_source(self, source):
        self.source = source

    # -------------------------------------------------------------------------
    def set_rower(self, rower):
        self.rower = rower

    # -------------------------------------------------------------------------
    def reset_session(self) -> None:
        """
        Remet à zéro les données de séance sans arrêter le rameur.
        La prochaine trame reçue devient la nouvelle référence des
        compteurs raw de la machine.
        """

        with self._lock:
            connection = self.curr_rowerdata.connection

            self._elapsed_offset = 0.0
            self._stroke_offset = 0

            self._last_time = None
            self._session_rebase_pending = True
            self._distance_history.clear()
            self._distance_history_index = 0

            self.curr_rowerdata = RowerData(
                connection=connection,
            )

    # -------------------------------------------------------------------------
    def set_cnx_status(self, status) -> None:

        with self._lock:
            self.curr_rowerdata.connection = status

    # -------------------------------------------------------------------------
    def set_logger(self, logger: CsvLogger) -> None:

        self.logger = logger

    # -------------------------------------------------------------------------
    def update(self, new_rowerdata: RowerData) -> None:

        with self._lock:

            if self._session_rebase_pending:
                self._elapsed_offset = new_rowerdata.raw_elapsed_time
                self._stroke_offset = new_rowerdata.raw_stroke_count

                self._last_time = None
                self._session_rebase_pending = False

            #
            # Temps écoulé
            #

            delta_elapsed = 0.0

            # for elapsed_time and stroke_count we want the value
            # minus the "New Session" offset (offset is 0 for first
            # session). We also clamp it to 0 if it ever goes negative.
            elapsed_time = clamp_to_zero(
                calc_deltatime(
                    new_rowerdata.raw_elapsed_time, 
                    self._elapsed_offset
                )
            )

            stroke_count = clamp_to_zero(
                calc_delta(
                    new_rowerdata.raw_stroke_count,
                    self._stroke_offset
                )
            )

            if self._last_time is None: # first packet
                delta_elapsed = 0.0

            else:
                delta_elapsed = clamp_to_zero(
                    calc_deltatime(elapsed_time, self._last_time)
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

            self._distance_history_index += 1
            self._distance_history.append(
                (
                    self._distance_history_index,
                    elapsed_time,
                    self.curr_rowerdata.distance,
                )
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

                    #
                    # Power Calibration
                    #

                    calib_machine_power= self.curr_rowerdata.calibration_machine_power,
                    calib_profile_factor= self.curr_rowerdata.calibration_profile_factor,
                    calib_level_factor= self.curr_rowerdata.calibration_level_factor,
                    calib_workout_factor= self.curr_rowerdata.calibration_workout_factor,
                    calib_spm_factor= self.curr_rowerdata.calibration_spm_factor,
                    calib_duration_factor= self.curr_rowerdata.calibration_duration_factor,
                    calib_final_factor= self.curr_rowerdata.calibration_final_factor,
                )

                self.logger.log(record)

    # -------------------------------------------------------------------------
    def distance_samples_since(
        self,
        index: int = 0,
    ) -> list[tuple[int, float, float]]:

        with self._lock:
            return [
                sample
                for sample in self._distance_history
                if sample[0] > index
            ]

    # -------------------------------------------------------------------------
    def snapshot(self) -> Snapshot:
        
        with self._lock:
            return Snapshot(
                deepcopy(self.curr_rowerdata),
            )

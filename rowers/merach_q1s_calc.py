# Merach Q1S specific recalculations
#
# The Q1S has untrustable data figures. For instance the distance
# is nothing more than "5 * strokes" in meters and the Calories
# roughly are "0.1428 * strokes" kcal. Hence we will try to
# calculate the data to approach a bit more "real" figures.
# The data that we will trust/use from the Merach Q1S are:
# the time, the number of strokes and the powers (instantaneous
# and average). The powers are not perfect either, certainly not
# generated from a sensor of strength on the handle, but we
# need to base our calculations on something... In fact we will
# only use the inst power, not the average.

# Coefficient Concept2 est 2.8.
# Peut être ajusté expérimentalement pour le Merach Q1S.
DRAG_FACTOR  = 2.5

CADENCE_WINDOW = 4      # nombre de coups utilisés pour le calcul brut (ou plus précisément la taille de la fenêtre utilisée pour calculer la cadence brute)
CADENCE_SMOOTHING = 3   # nombre de cadences calculées utilisées pour le lissage
CALORIE_OFFSET = 300.0

from calc import calc_delta, calc_average, calc_speed_avg
from collections import deque

# -------------------------------------------------------------------------
class MerachQ1SCalc:

    # -------------------------------------------------------------------------
    def __init__(self):

        self.stroke_times = deque(maxlen=CADENCE_WINDOW)
        self.cadence_history = deque(maxlen=CADENCE_SMOOTHING)

        self.reset()

    # -------------------------------------------------------------------------
    def reset(self):

        self.distance = 0.0
        self.calories = 0.0
        self.work_j = 0.0
        self.work_per_stroke = 0.0

        self.stroke_times.clear()
        self.cadence_history.clear()

        self.last_strokes = 0

    # -------------------------------------------------------------------------
    def process(self, data: dict, delta_elapsed: float) -> dict:

        elapsed_time = float(data.get("elapsed_time", 0.0))

        #
        # Power : venant du Q1S
        #

        power = float(data.get("power", 0.0))

        #
        # Vitesse : recalculé à partir de power
        #

        speed = self.calc_speed(power)

        # NOTE: Power's values (raw data from the Q1S machine) are weird:
        # Raw_Power is about half of Raw_Power_Avg. Hence using Raw_Power_Avg
        # to calculate values produces the same behaviour 
        # between speed and speed_avg, and between split_abg and split.
        #
        # We will recalculate speed_avg from the distance (thus from
        # speed) instead.
        # Old behaviour for speed_avg was: speed_avg = self.calc_speed(power_avg)

        #
        # Distance : recalculée à partir de Vitesse et delta temps
        #

        self.distance += self.calc_dist(speed, delta_elapsed)

        #
        # Speed average : New speed_avg recalculée à partir de
        #                 distance et temps, see NOTE above.
        #

        speed_avg = calc_speed_avg(self.distance, elapsed_time)

        #
        # Split : recalculé à partir de speed
        # Split Average : recalculé à partir de speed_avg
        #

        split = self.calc_split(speed)
        split_avg = self.calc_split(speed_avg)

        #
        # Calories inst: recalculé à partir de power
        #

        calories_rate = self.calc_calories_rate(power)
        self.calories += self.calc_calories(calories_rate, delta_elapsed)

        #
        # Cadences (Strokes per minute)
        #

        delta_strokes, cadence_inst, cadence = self.calc_cadence_inst(
            stroke_count=int(data.get("stroke_count", 0)),
            elapsed_time=elapsed_time,
            delta_elapsed=delta_elapsed,
        )

        #
        # Work (J) : recalculés
        #

        self.work_j += self.calc_work(
            power,
            delta_elapsed,
        )
        self.work_per_stroke = self.calc_work_per_stroke(
            int(data.get("stroke_count", 0)),
            self.work_j,
        )

        #
        # Valeurs calculées ajoutées/remplacées
        #

        data["delta_strokes"] = delta_strokes
        data["stroke_event"] = (delta_strokes > 0)

        data["speed"] = speed
        data["speed_avg"] = speed_avg

        data["distance"] = self.distance

        data["split_inst"] = split
        data["split_avg"] = split_avg

        data["calories_rate"] = calories_rate
        data["calories"] = self.calories

        data["cadence_inst"] = cadence_inst
        data["cadence"] = cadence

        data["work_j"] = self.work_j
        data["work_per_stroke"] = self.work_per_stroke

        return data

    # -----------------------------------------------------------------------------
    # cadence instantaneous
    # Calcule la cadence instantanée à partir des quelques derniers coups
    # et applique un lissage sur les dernières valeurs.
    # on va faire la moyenne des dernières valeurs instantanées pour lisser les valeurs
    # inputs: list of times and list of cadences inst
    # outputs : delta_strokes, cadence_inst, cadence lissée
    def calc_cadence_inst(
        self,
        stroke_count: int,
        elapsed_time: float,
        delta_elapsed: float,
    ) -> tuple[float, float, float]: 

        delta_strokes = calc_delta(stroke_count, self.last_strokes)

        if delta_strokes <= 0:

            if not self.cadence_history:
                return 0.0, 0.0, 0.0

            cadence_inst = self.cadence_history[-1]
            cadence = calc_average(self.cadence_history)

            return 0.0, cadence_inst, cadence

        if delta_strokes == 1:

            self.stroke_times.append(elapsed_time)

        else:

            step = delta_elapsed / delta_strokes

            first_time = calc_delta(elapsed_time, delta_elapsed) + step

            for i in range(delta_strokes):
                self.stroke_times.append(
                    first_time + i * step
                )

        self.last_strokes = stroke_count

        if len(self.stroke_times) < CADENCE_WINDOW:
            return delta_strokes, 0.0, 0.0

        delta_time = calc_delta(
            self.stroke_times[-1],
            self.stroke_times[-CADENCE_WINDOW],
        )

        if delta_time <= 0:
            return delta_strokes, 0.0, 0.0

        cadence_inst = self.calc_cadence_window(
            CADENCE_WINDOW - 1,
            delta_time,
        )

        self.cadence_history.append(cadence_inst)

        cadence = calc_average(self.cadence_history)

        return delta_strokes, cadence_inst, cadence


    # =========================================================================
    # Below are calculation method that are specific to Q1S, hence in here
    # rather than in calc.py
    # =========================================================================


    # -----------------------------------------------------------------------------
    # Works for speed instantaneous (using power inst
    # (could also work for speed_avg based on power avg, but since
    # Raw_Power_Avg from the Q1S can't be trusted, we will recalculate
    # speed_avg separately)
    # speed (m/s) = (power / drag_factor)^(1/3)
    # power in Watts
    @staticmethod
    def calc_speed(power: float) -> float:
        
        return (
            (power / DRAG_FACTOR) ** (1.0 / 3.0)
            if power > 0.0
            else 0.0
        )

    # -----------------------------------------------------------------------------
    # Works for split instantaneous (pace) or split average (using respectively speed instantaneous or speed average)
    # split (min/500m) = 500 / speed
    # speed in m/s
    @staticmethod
    def calc_split(speed: float) -> float:
        return (500.0 / speed) if speed > 0.0 else 0.0

    # -----------------------------------------------------------------------------
    # calories inst
    # calories_per_second (kcal/s) = (4 * power + 300) / 3600
    # power in Watts
    @staticmethod
    def calc_calories_rate(power: float) -> float:
        return ((4.0 * power) + CALORIE_OFFSET) / 3600.0

    # -----------------------------------------------------------------------------
    # calories total
    # calories (kcal) = calories_per_second * time
    # or calories = SUM from k=1 to max Samples of [ ( 4 * Pik + 300) * delta_tk) / 3600]
    # calories_rate in kcal/s, delta_t in s
    @staticmethod
    def calc_calories(calories_rate: float, delta_t:float) -> float:
        return calories_rate * delta_t

    # -----------------------------------------------------------------------------
    # distance (m) = time * speed
    # or distance = SUM from k=1 to max Samples of [ Pik / 2,8 ]1/3 * delta_tk
    # speed in m/s, delta_t in s
    @staticmethod
    def calc_dist(speed: float, delta_t: float) -> float:
        return speed * delta_t

    # -----------------------------------------------------------------------------
    # Cadence (strokes per minute)
    # It works for cadence instantaneous (but see calc_cadence_inst for a
    # smoothed calculation) or cadence average (using respectively delta_N and 
    # delta_t or N and time)
    # cadence (spm, number_of_strokes_per_minute) = 60 * nb_strokes / time
    # stroke_count a number, delta_t in s
    @staticmethod
    def calc_cadence_window(stroke_count: int, delta_t:float) -> float:
        return (60.0 * stroke_count) / delta_t if delta_t > 0 else 0.0

    # -----------------------------------------------------------------------------
    # Work (J) = power * time
    # power in Watts, delta_t in s
    @staticmethod
    def calc_work(power:float, delta_t: float) -> float:
        return power * delta_t

    # -----------------------------------------------------------------------------
    # Work (J) per stroke
    @staticmethod
    def calc_work_per_stroke(stroke_count: int, work_j: float) -> float:
        return (
            work_j / stroke_count
            if stroke_count > 0
            else 0.0
        )

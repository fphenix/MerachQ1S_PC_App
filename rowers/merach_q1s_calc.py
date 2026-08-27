# Merach Q1S specific recalculations
#
# The Q1S has untrustable data figures. For instance the distance
# is nothing more than "5 * strokes" in meters and the Calories
# roughly are "0.1428 * strokes" kcal. Hence we will try to
# calculate the data to approach a bit more "real" figures.
# The data that we will trust/use from the Merach Q1S are:
# the time, the number of strokes and the instantaneous power.
# The powers are not perfect either, certainly not generated
# from a sensor of strength on the handle, but we need to base
# our calculations on something... We will only use the inst power
# (not the raw average).

# Frottements : Coefficient Concept2 est 2.8.
# Peut être ajusté expérimentalement pour le Merach Q1S.
DRAG_FACTOR  = 2.8

# Power : le raw_power venant du Q1S semble beaucoup trop bas (30-35 au lieu de 90-120W!)
# On va le calibrer grâce à cette valeur:
POWER_SCALE = 3.6

# Candence : lissage
CADENCE_WINDOW = 4      # nombre de coups utilisés pour le calcul brut (ou plus précisément la taille de la fenêtre utilisée pour calculer la cadence brute)
CADENCE_SMOOTHING = 3   # nombre de cadences calculées utilisées pour le lissage

# Calories
USE_C2_CALORIES = False
CALORIE_OFFSET = 300.0
CALORIES_CALIB = 1.1639
CALORIES_PER_WATT = 3.4

from calc import (
    calc_delta,
    calc_average,
    calc_speed_avg,
    calc_power_avg,
    calc_cadence_from_strokes,
    calc_split500,
    calc_dist,
    calc_dist_per_stroke,
    calc_dist_per_stroke_avg,
    calc_calories,
    calc_work,
    calc_work_per_stroke,
)
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

        self.cadence_avg = 0.0
        self.distance_per_stroke = 0.0
        self.dist_per_stroke_avg = 0.0

        self.last_strokes = 0

    # -------------------------------------------------------------------------
    def process(self, data: dict, delta_elapsed: float) -> dict:

        elapsed_time = float(data.get("elapsed_time", 0.0))

        #
        # Power : venant du Q1S
        #         Note: la raw power venant du Q1S est trop basse, nous devons la recalibrer
        #

        raw_power = float(data.get("raw_power", 0.0))
        power = raw_power * POWER_SCALE

        #
        # Vitesse : recalculé à partir de power
        #

        speed = self.q1s_calc_speed(power)

        # NOTE: Power's values (raw data from the Q1S machine) are weird:
        # Raw_Power is about half of Raw_Power_Avg. Hence using Raw_Power_Avg
        # to calculate values produces the same behaviour 
        # between speed and speed_avg, and between split_abg and split.
        #
        # We will recalculate speed_avg from the distance (thus from
        # speed) instead.
        # Old behaviour for speed_avg was: speed_avg = calc_speed(power_avg)

        #
        # Distance : recalculée à partir de Vitesse et delta temps
        #

        self.distance += calc_dist(speed, delta_elapsed)

        #
        # Speed average : New speed_avg recalculée à partir de
        #                 distance et temps, see NOTE above.
        #

        speed_avg = calc_speed_avg(self.distance, elapsed_time)

        #
        # Split (temps (s) aux 500m) : recalculé à partir de speed
        # Split Average : recalculé à partir de speed_avg
        #

        split = calc_split500(speed)
        split_avg = calc_split500(speed_avg)

        #
        # Calories inst: recalculé à partir de power
        #

        calories_rate = self.q1s_calc_calories_rate(power)
        self.calories += calc_calories(calories_rate, delta_elapsed)

        #
        # Cadences (Strokes per minute) : Delta, Inst et Inst lissée
        #

        stroke_count=int(data.get("stroke_count", 0))

        delta_strokes, cadence_inst, cadence = self.q1s_calc_cadence_inst(
            stroke_count=stroke_count,
            elapsed_time=elapsed_time,
            delta_elapsed=delta_elapsed,
        )

        #
        # Cadence average : recalculée
        #

        if elapsed_time > 0.0:
            self.cadence_avg = calc_cadence_from_strokes(
                stroke_count= stroke_count,
                elapsed_time= elapsed_time,
            )

        #
        # Distance per stroke : recalculée
        # Distance per stroke Moyenne
        #

        if delta_elapsed > 0.0 and cadence > 0.0:
            self.distance_per_stroke = calc_dist_per_stroke(
                speed=speed,
                cadence=cadence,
            )

        self.dist_per_stroke_avg = calc_dist_per_stroke_avg(
            distance= self.distance,
            stroke_count= stroke_count
        )

        #
        # Work (J) : recalculé
        #

        self.work_j += calc_work(
            power,
            delta_elapsed,
        )

        self.work_per_stroke = calc_work_per_stroke(
            work= self.work_j,
            stroke_count= stroke_count
        )

        #
        # Power average (recalculée)
        #

        power_avg = calc_power_avg(
            work= self.work_j, 
            total_time= elapsed_time
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
        data["cadence_avg"] = self.cadence_avg

        data["distance_per_stroke"] = self.distance_per_stroke
        data["dist_per_stroke_avg"] = self.dist_per_stroke_avg

        data["work_j"] = self.work_j
        data["work_per_stroke"] = self.work_per_stroke

        data["power"] = power
        data["power_avg"] = power_avg

        return data

    # -----------------------------------------------------------------------------
    # cadence instantaneous
    # Calcule la cadence instantanée à partir des quelques derniers coups
    # et applique un lissage sur les dernières valeurs.
    # on va faire la moyenne des dernières valeurs instantanées pour lisser les valeurs
    # outputs : delta_strokes, cadence_inst, cadence inst lissée sur la fenêtre
    def q1s_calc_cadence_inst(
        self,
        stroke_count: int,
        elapsed_time: float,
        delta_elapsed: float,
    ) -> tuple[int, float, float]:

        delta_strokes = calc_delta(stroke_count, self.last_strokes)

        # Update the reference BEFORE any early return.
        self.last_strokes = stroke_count

        # No new stroke.
        # Keep the last known cadence instead of returning zero
        # once a cadence has already been established.
        if delta_strokes <= 0:

            if not self.cadence_history:
                return 0, 0.0, 0.0

            cadence_inst = self.cadence_history[-1]
            cadence = calc_average(self.cadence_history)

            return 0, cadence_inst, cadence

        if delta_strokes == 1:

            self.stroke_times.append(elapsed_time)

        else:

            step = delta_elapsed / float(delta_strokes)

            first_time = calc_delta(elapsed_time, delta_elapsed) + step

            for i in range(delta_strokes):
                self.stroke_times.append(
                    first_time + i * step
                )

        if len(self.stroke_times) < CADENCE_WINDOW:
            return delta_strokes, 0.0, 0.0

        delta_time = calc_delta(
            self.stroke_times[-1],
            self.stroke_times[-CADENCE_WINDOW],
        )

        if delta_time <= 0:
            return delta_strokes, 0.0, 0.0

        cadence_inst = self.q1s_calc_cadence_window(
            CADENCE_WINDOW - 1,
            delta_time,
        )

        self.cadence_history.append(cadence_inst)
            
        cadence = calc_average(self.cadence_history)

        return delta_strokes, cadence_inst, cadence


    # =========================================================================
    # Below are calculation methods that are specific to the Q1S, hence in here
    # rather than in calc.py
    # =========================================================================

    # -----------------------------------------------------------------------------
    # speed (m/s) = (power / drag_factor)^(1/3)
    # power in Watts
    # Works for speed instantaneous (using power inst).
    # (It could also work for speed_avg based on power_avg, but since
    # Raw_Power_Avg from the Q1S can't be trusted, we will recalculate
    # speed_avg separately)
    @staticmethod
    def q1s_calc_speed(power: float) -> float:
        
        return (
            (power / DRAG_FACTOR) ** (1.0 / 3.0)
            if power > 0.0
            else 0.0
        )

    # -----------------------------------------------------------------------------
    # calories inst
    # Formule Concept2:
    # calories_per_second (kcal/s) = ((4 * power / 1.1639) + offset) / 3600
    # power in Watts
    # Note : due to the offset, the resulting value is non-null even when
    #        power is 0. You may want to rework that formulae to sort this out.
    @staticmethod
    def q1s_calc_calories_rate(power: float) -> float:
        if USE_C2_CALORIES:
            return ((4.0 * power / CALORIES_CALIB) + CALORIE_OFFSET) / 3600.0
        else:
            return (CALORIES_PER_WATT * power) / 3600.0

    # -----------------------------------------------------------------------------
    # Cadence (strokes per minute) = 60 * nb_strokes / time
    # stroke_count is a number, delta_t in s and "*60" to get minutes
    # Here is is used to get the smoothed cadence inst on a filtering window (last
    # few values (a mini average to filter the noisy real inst cadence)
    # It works for a "real" cadence instantaneous (but see q1s_calc_cadence_inst for
    # a smoothed calculation) or for cadence average (using respectively delta_N 
    # and delta_t OR N and time)
    @staticmethod
    def q1s_calc_cadence_window(stroke_count: int, delta_t:float) -> float:
        return calc_cadence_from_strokes(stroke_count, delta_t)

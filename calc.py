from collections import deque
from statistics import mean, stdev

# -----------------------------------------------
# Universal calc functions
# -----------------------------------------------

# -----------------------------------------------------------------------------
# return the average in a deque
# both values must be in the same unit
def calc_average(values: deque) -> float:
    return sum(values) / len(values)

# -----------------------------------------------------------------------------
# delta = curr - prev
# both values must be in the same unit
def calc_delta(curr: int|float, prev: int|float) -> int|float:
    return curr - prev

# -----------------------------------------------------------------------------
# generic metric average : metric / per_unit
# returns 0.0 if the per_unit is negative or null
def calc_metric_avg(metric: float, per_unit: int|float) -> float:
    return (
            metric / float(per_unit)
            if float(per_unit) > 0.0
            else 0.0
        )

# --------------------------------------------------------
# Metrics
# --------------------------------------------------------

# -----------------------------------------------------------------------------
# calories total (kcal) = calories_rate * time
# calories_rate in kcal/s, delta_t in s
# Note: we could also calculate calories like so:
#   calories = SUM from k=1 to max Samples of [ ( 4 * Pik + 300) * delta_tk) / 3600]
def calc_calories(calories_rate: float, delta_t:float) -> float:
    return calories_rate * delta_t

# -----------------------------------------------------------------------------
# Work (J) = power * time
# power in Watts, delta_t in s
def calc_work(power:float, delta_t: float) -> float:
    return power * delta_t

# -----------------------------------------------------------------------------
# split (s/distance_m) = distance (m) / speed (m/s)
# Works for split instantaneous (pace) or split average (using respectively 
# speed instantaneous or speed average)
def calc_split(dist:float, speed: float) -> float:
    return calc_metric_avg(dist, speed)

# -----------------------------------------------------------------------------
# split (s/500m) = 500 (m) / speed (m/s)
# Works for split instantaneous (pace) or split average (using respectively
# speed instantaneous or speed average)
def calc_split500(speed: float) -> float:
    return calc_split(500.0, speed)

# -----------------------------------------------------------------------------
# distance (m) = time * speed
# speed in m/s, delta_t in s
# Note: we could also calculate the distance like so:
#     distance = SUM from k=1 to max Samples of [ Pik / 2,8 ]1/3 * delta_tk
def calc_dist(speed: float, delta_t: float) -> float:
    return speed * delta_t
    
# -----------------------------------------------------------------------------
# distance_per_stroke (m/stroke) = 60 * speed / strokes_per_minute
# speed in m/s (mult by 60 to get in m/min),
# cadence in spm (number of strokes per minutes)
def calc_dist_per_stroke(speed: float, cadence: float) -> float:
    return calc_metric_avg((60.0 * speed), cadence)

# -----------------------------------------------------------------------------
# distance_per_stroke_avg (m/stroke) = distance (m) / strokes_total (number)
def calc_dist_per_stroke_avg(distance: float, stroke_count: int) -> float:
    return calc_metric_avg(distance, stroke_count)

# -----------------------------------------------------------------------------
# average cadence (strokes per minute) from 
# the number of strokes and
# the time (s) (divided by 60 to get in minutes, which is the same as
# multiplying stroke_count by 60)
def calc_cadence_from_strokes(stroke_count: int, elapsed_time:float) -> float:
    return calc_metric_avg((60.0 * stroke_count), elapsed_time)

# -----------------------------------------------------------------------------
# speed (m/s) from distance (m) and time (s)
def calc_speed_avg(distance: float, total_time: float) -> float:
    return calc_metric_avg(distance, total_time)

# -----------------------------------------------------------------------------
# power average (W) from work (J) and time (s)
def calc_power_avg(work: float, total_time: float) -> float:
    return calc_metric_avg(work, total_time)

# -----------------------------------------------------------------------------
# work per stroke (J/stroke) from work (J) and number of strokes
def calc_work_per_stroke(work: float, stroke_count: int) -> float:
    return calc_metric_avg(work, float(stroke_count))

# --------------------------------------------------------
# Stats
# --------------------------------------------------------

def calc_stats(values: list[float], minimum=None) -> dict[str, float]:

    # if empty list, set results to 0
    if not values:
        return {
            "mean": 0.0,
            "min": 0.0,
            "max": 0.0,
            "stdev": 0.0,
        }

    # If desired, filter out values below a certain threshold
    # (useful to get rid of 0s)
    if minimum is not None:
        values = [v for v in values if v > minimum]

        #in case all values were filtered out we need to redo:
        if not values:
                return {
                    "mean": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "stdev": 0.0,
                }


    if len(values) == 1:
        return {
            "mean": values[0],
            "min": values[0],
            "max": values[0],
            "stdev": 0.0,
        }

    return {
        "mean": mean(values),
        "min": min(values),
        "max": max(values),
        "stdev": stdev(values),
    }

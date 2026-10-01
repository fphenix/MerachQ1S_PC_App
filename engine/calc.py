from statistics import mean, stdev

from setup.utils import calc_metric_avg

# --------------------------------------------------------
# Metrics
# --------------------------------------------------------

# -----------------------------------------------------------------------------
# calories total (kcal) = calories_rate * time
# calories_rate in kcal/s, delta_t in s
# Note: we could also calculate calories like so:
#   calories = SUM from k=1 to max Samples of [ ( 4 * Pik + 300) * delta_tk) / 3600]
def calc_calories(calories_rate: float, delta_t: float) -> float:
    return calories_rate * delta_t

# -----------------------------------------------------------------------------
# Work (J) = power * time
# power in Watts, delta_t in s
def calc_work(power: float, delta_t: float) -> float:
    return power * delta_t

# -----------------------------------------------------------------------------
# split (s/distance_m) = distance (m) / speed (m/s)
# Works for split instantaneous or split average (using respectively 
# speed instantaneous or speed average)
def calc_split(distance: float, speed: float) -> float:
    return calc_metric_avg(distance, speed)

# -----------------------------------------------------------------------------
# split (s/500m) = 500 (m) / speed (m/s)
# Works for split instantaneous or split average (using respectively
# speed instantaneous or speed average)
def calc_split500(speed: float, split_length: float) -> float:
    return calc_split(split_length, speed)

# -----------------------------------------------------------------------------
# Split (s/split_length_m) = (temps (s) / distance (m)) * split_length (m)
# Par exemple pour des splits de 500m ou ramené à 500m:
# Split (s/500m) = (temps / distance) * 500
# Si distance = split_length alors split = temps
# Mais si par exemple distance = 250m alors 
# split = temps / 250 * 500 soit split = 2 * temps
# ce qui est bien le temps ramené à 500m
def calc_full_split(distance: float, time: float, split_length: float) -> float:
    return calc_metric_avg(time, distance) * split_length

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
# pace (s/m) from distance and time OR from speed
# If dist_or_speed is distance (m) and time_or_1 is time (s), pace is time/distance (s/m)
# If dist_or_speed is speed (m/s) and time_or_1 is 1.0 (no unit), pace is 1/speed (s/m)
def calc_pace(dist_or_speed: float, time_or_1: float = 1.0) -> float:
    return calc_metric_avg(time_or_1, dist_or_speed)

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

def calc_stats(
    values: list[float],
    minimum: float|None = None
) -> dict[str, float]:

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

from collections import deque
from statistics import mean, stdev

# -----------------------------------------------------------------------------
# return the average in a deque
# both values must be in the same unit
def calc_average(values: deque) -> float:
    return sum(values) / len(values)


# -----------------------------------------------------------------------------
# delta = curr - prev
# both values must be in the same unit
def calc_delta(curr: float, prev: float) -> float:
    return curr - prev

   
# -----------------------------------------------------------------------------
# distance_per_stroke (m/stroke) = 60 * speed / strokes_per_minute
# speed in m/s, cadence in spm (number of strokes per minutes)
def calc_dist_per_stroke(speed: float, cadence: float) -> float:
    return (60.0 * speed) / cadence if cadence > 0 else 0.0


# -----------------------------------------------------------------------------
def calc_cadence_from_strokes(stroke_count: int, delta_t:float) -> float:
    return (60.0 * stroke_count) / delta_t if delta_t > 0 else 0.0


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
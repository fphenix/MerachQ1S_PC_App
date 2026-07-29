from constants import DRAG_FACTOR, CALORIE_OFFSET

# -----------------------------------------------------------------------------
# delta = curr - prev
# both values must be in the same unit
def calc_delta(curr: float, prev: float):
    return curr - prev

# -----------------------------------------------------------------------------
# Works for speed instantaneous or speed average (using respectively power inst or power avg)
# speed (m/s) = (power / drag_factor)^(1/3)
# power in Watts
def calc_speed(power: float):
    return (power / DRAG_FACTOR) ** (1.0 / 3.0) if power > 0.0 else 0.0

# -----------------------------------------------------------------------------
# Works for split instantaneous (pace) or split average (using respectively speed instantaneous or speed average)
# split (min/500m) = 500 / speed
# speed in m/s
def calc_split(speed: float):
    return (500.0 / speed) if speed > 0.0 else 0.0

# -----------------------------------------------------------------------------
# calories inst
# calories_per_second (kcal/s) = (4 * power + 300) / 3600
# power in Watts
def calc_kcal_rate(power: float):
    return ((4.0 * power) + CALORIE_OFFSET) / 3600.0

# -----------------------------------------------------------------------------
# calories total
# calories (kcal) = calories_per_second * time
# or calories = SUM from k=1 to max Samples of [ ( 4 * Pik + 300) * delta_tk) / 3600]
# kcal_rate in kcal/s, delta_t in s
def calc_kcal(kcal_rate: float, delta_t:float):
    return kcal_rate * delta_t

# -----------------------------------------------------------------------------
# distance (m) = time * speed
# or distance = SUM from k=1 to max Samples of [ Pik / 2,8 ]1/3 * delta_tk
# speed in m/s, delta_t in s
def calc_dist(speed: float, delta_t: float):
    return speed * delta_t

# -----------------------------------------------------------------------------
# work (J) = power * time
# power in Watts, delta_t in s
def calc_work(power:float, delta_t: float):
    return power * delta_t

# -----------------------------------------------------------------------------
# Works for cadence instantaneous or cadence average (using respectively delta_N and delta_t or N and time)
# cadence (spm, number_of_strokes_per_minute) = 60 * nb_strokes / time
# stroke_count a number, delta_t in s
def calc_cadence_avg(stroke_count: int, delta_t:float):
    return (60.0 * stroke_count) / delta_t if delta_t > 0 else 0.0

# -----------------------------------------------------------------------------
# distance_per_stroke (m/stroke) = 60 * speed / strokes_per_minute
# speed in m/s, cadence in spm (number of strokes per minutes)
def calc_dist_per_stroke(speed: float, cadence: float):
    return (60.0 * speed) / cadence if cadence > 0 else 0.0

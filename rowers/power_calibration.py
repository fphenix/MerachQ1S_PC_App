from setup.utils import clamp_between, interpolate
from setup.constants import (
    MIN_PROFILE_WEIGHT, MAX_PROFILE_WEIGHT,
    MIN_PROFILE_HEIGHT, MAX_PROFILE_HEIGHT,
)

from rowers.power_calib_data import PowerCalibrationContext

# ==============================================================================
class WorkoutPowerCalibration:
    """Converts Q1S machine power into a workout/profile-aware power."""

    # Power : le raw_power venant du Q1S semble beaucoup trop bas (30-35 au lieu de 90-120W!)
    # On va le calibrer grâce à cette valeur:
    POWER_SCALE:float = 3.6

    # -----------------------------------------------------------------------------
    # Evidence-backed reference points used by the first version of the model.
    #
    # Jensen/World Rowing reports mean power ratios relative to 2k power for elite
    # rowers: ~76% (60 min), ~85% (6k), 100% (2k), ~153% (60 s), ~173% (10 s).
    # These are deliberately kept here, in one place, so the model can be tuned
    # without touching the Q1S calculator.
    # -----------------------------------------------------------------------------
    DURATION_POWER_RATIOS = (
        (10.0, 1.73),
        (60.0, 1.53),
        (120.0, 1.30),
        (300.0, 1.10),
        (600.0, 1.00),
        (3600.0, 0.76),
    )

    # Workout intensity is interpreted as the intended effort relative to the
    # duration-based reference power.  R/E are recovery/easy work, N is the
    # reference effort, F is hard work and M is maximal/very hard work.
    # These are deliberately modest multipliers: the duration model supplies the
    # physiological scale, while the workout intensity moves around it.
    INTENSITY_FACTORS = {
        "R": 0.50,
        "E": 0.65,
        "N": 1.00,
        "F": 1.10,
        "M": 1.15,
    }

    MAX_RECALIBRATION_FACTOR = 2.00

    def __init__(self, machine_scale: float = POWER_SCALE) -> None:
        self.machine_scale = machine_scale

    # ------------------------------------------------------------------
    def calibrate(
        self,
        raw_power: float,
        context: PowerCalibrationContext,
    ) -> float:
        machine_power = max(0.0, float(raw_power)) * self.machine_scale

        if machine_power <= 0.0:
            return 0.0

        factor = 1.0

        if context.profile_enabled:
            factor *= self.profile_factor(context)

        if context.workout_enabled and context.intensity is not None:
            factor *= self.workout_factor(context)

        factor = max(0.0, min(self.MAX_RECALIBRATION_FACTOR, factor))

        return machine_power * factor

    # ------------------------------------------------------------------
    @staticmethod
    def duration_reference_ratio(duration_seconds: float) -> float:
        """Return expected power relative to 2k power for a given duration."""

        duration = max(10.0, float(duration_seconds))

        points = WorkoutPowerCalibration.DURATION_POWER_RATIOS

        if duration <= points[0][0]:
            return points[0][1]

        for (t0, r0), (t1, r1) in zip(points, points[1:]):
            if duration <= t1:
                # Interpolate in log(duration), which gives a smooth power-
                # duration transition without arbitrary discontinuities.
                x0 = 0.0 if t0 <= 0 else __import__("math").log(t0)
                x1 = __import__("math").log(t1)
                x = __import__("math").log(duration)
                return r0 + (r1 - r0) * ((x - x0) / (x1 - x0))

        return points[-1][1]

    # ------------------------------------------------------------------
    @staticmethod
    def workout_factor(context: PowerCalibrationContext) -> float:
        intensity_factor = WorkoutPowerCalibration.INTENSITY_FACTORS.get(
            context.intensity or "N",
            1.0,
        )

        duration_ratio = WorkoutPowerCalibration.duration_reference_ratio(
            context.duration_seconds
        )

        # N is normalized to the duration-specific reference.  R/E/F/M then
        # shift the intended effort around that reference.
        return duration_ratio * intensity_factor

    # ------------------------------------------------------------------
    # OLD CALCULATION WAS:
    #    # Age: Seiler et al. reported approximately 3% power loss per decade
    #    # from 24-50 and ~7% per decade from 50-74 in indoor-rowing data.
    #    age = max(18.0, float(context.age))
    #    if age > 24.0:
    #        if age <= 50.0:
    #            factor *= pow(0.97, (age - 24.0) / 10.0)
    #        else:
    #            factor *= pow(0.97, 2.6) * pow(0.93, (age - 50.0) / 10.0)
    # NEW CALCULATION IS:
    @staticmethod
    def age_factor(age: float) -> float:

        age = clamp_between(float(age), 24.0, 90.0)

        # Points issus de la relation observée dans Seiler et al.
        # Le modèle reste continu entre les points.
        anchors = (
            (24.0, 1.000),
            (50.0, 0.923),
            (74.0, 0.776),
        )

        for (a0, f0), (a1, f1) in zip(anchors, anchors[1:]):
            if age <= a1:
                return interpolate(age, a0, f0, a1, f1)

        return anchors[-1][1]

    # ------------------------------------------------------------------
    @staticmethod
    def height_factor(height_cm: float) -> float:

        height = clamp_between(float(height_cm), MIN_PROFILE_HEIGHT, MAX_PROFILE_HEIGHT)

        # Référence = 180 cm.
        #
        # Coefficient volontairement conservateur dans cette V1 :
        # les études démontrent l'association taille/performance,
        # mais ne fournissent pas une loi adulte universelle
        # "watts = f(taille)" utilisable telle quelle.
        exponent = 0.35

        return (height / 180.0) ** exponent

    # ------------------------------------------------------------------
    # Body-mass scaling: rowing-ergometer performance has been modelled
    # with a mass exponent around 0.23. Keep it normalized to 75 kg.
    @staticmethod
    def weight_factor(weight_kg: float) -> float:

        weight = clamp_between(float(weight_kg), MIN_PROFILE_WEIGHT, MAX_PROFILE_WEIGHT)

        return (weight / 75.0) ** 0.23

    # ------------------------------------------------------------------
    # OLD CALCULATION WAS:    
    #    # Sex: the 2003 rowing study found roughly a 9-10% slower 2k time for
    #    # women at similar height/mass. Convert speed ratio to power ratio:
    #    # power is approximately proportional to speed^3.
    #    if context.sex.upper() == "F":
    #        factor *= 0.73
    # NEW CALCULATION IS:
    @staticmethod
    def sex_factor(is_male: bool) -> float:

        return 1.00 if is_male else 0.90

    # ------------------------------------------------------------------
    # The application level is retained in the context, but is not yet
    # converted into a fixed power multiplier. British Rowing uses
    # beginner/intermediate/advanced mainly to describe training status,
    # not universal wattage classes. A fixed multiplier here would be an
    # arbitrary assumption.
    @staticmethod
    def level_factor(level: float) -> float:

        level = clamp_between(float(level), 0.0, 1.0)

        # Référence : intermédiaire = 0.33
        # Valeurs provisoires, à calibrer ensuite sur les benchmarks.
        return 0.85 + 0.45 * level

    # ------------------------------------------------------------------
    @staticmethod
    def profile_factor(context: PowerCalibrationContext) -> float:
        """Conservative profile correction, normalized to the default profile.

        Age and sex have direct evidence in adult rowing-performance studies.
        Body mass is applied with the established rowing allometric exponent
        0.23. Height is intentionally not used as a second independent power
        multiplier yet: available studies show an association, but no robust
        adult coefficient suitable for this application.
        """

        factor_age = WorkoutPowerCalibration.age_factor(float(context.age))
        factor_height = WorkoutPowerCalibration.height_factor(float(context.height_cm))
        factor_weight = WorkoutPowerCalibration.weight_factor(float(context.weight_kg))
        factor_sex = WorkoutPowerCalibration.sex_factor(is_male= (context.sex.upper() == "M"))
        factor_level = WorkoutPowerCalibration.level_factor(float(context.level_norm))

        profile_factor = (
            factor_age
            * factor_height
            * factor_weight
            * factor_sex
            * factor_level
        )

        return clamp_between(profile_factor, 0.65, 1.35)


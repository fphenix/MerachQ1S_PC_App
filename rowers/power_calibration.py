import math

from setup.utils import clamp_between, clamp_to_zero
from engine.calc import interpolate
from setup.constants import (
    MIN_PROFILE_WEIGHT, MAX_PROFILE_WEIGHT,
    MIN_PROFILE_HEIGHT, MAX_PROFILE_HEIGHT,
    DEFAULT_PROFILE_NORM_LEVEL,
)

from rowers.power_calib_data import (
    PowerCalibrationContext,
    PowerCalibrationResult
)

# ==============================================================================
class WorkoutPowerCalibration:
    """Converts Q1S machine power into a workout/profile-aware power."""

    # Power : le raw_power venant du Q1S semble beaucoup trop bas (30-35 au lieu
    # de 90-120W!). On va le calibrer grâce à cette valeur:
    POWER_SCALE:float = 3.6

    # -----------------------------------------------------------------------------
    # Evidence-backed reference points used by the first version of the model.
    #
    # Jensen/World Rowing reports mean power ratios relative to 2k power for elite
    # rowers: ~76% (60 min), ~85% (6k), 100% (2k), ~153% (60 s), ~173% (10 s).
    # These are deliberately kept here, in one place, so the model can be tuned
    # without touching the Q1S calculator.
    '''
    DURATION_POWER_RATIOS = (
        (10.0, 1.73),
        (60.0, 1.53),
        (120.0, 1.30),
        (300.0, 1.10),
        (600.0, 1.00),
        (3600.0, 0.76),
    )

    DURATION_INTENSITY_EXPONENTS = {
        "R": 0.0,
        "E": 0.0,
        "N": 0.0,
        "F": 0.5,
        "M": 1.0,
    }
    '''

    # -----------------------------------------------------------------------------
    # Points issus de la relation observée dans Seiler et al. pour le paramètre age.
    # Le modèle reste continu entre les points.
    AGE_RATIOS = (
        (24.0, 1.000),
        (50.0, 0.923),
        (74.0, 0.776),
    )

    # -----------------------------------------------------------------------------
    # Workout intensity is interpreted as the intended effort relative to the
    # duration-based reference power.  R/E are recovery/easy work, N is the
    # reference effort, F is hard work and M is maximal/very hard work.
    # These are deliberately modest multipliers: the duration model supplies the
    # physiological scale, while the workout intensity moves around it.
    INTENSITY_FACTORS = {
        "R": 0.30,
        "E": 0.50,
        "N": 1.00, # ref
        "F": 1.50,
        "M": 1.70,
    }

    MAX_RECALIBRATION_FACTOR = 2.00

    REFERENCE_SPM = 24.0
    SPM_FACTOR_EXPONENT = 0.30

    # ------------------------------------------------------------------
    def __init__(self, machine_scale: float = POWER_SCALE) -> None:

        self.machine_scale: float = machine_scale

    # ------------------------------------------------------------------
    def calibrate(
        self,
        raw_power: float,
        context: PowerCalibrationContext,
    ) -> float:

        return self.calibrate_details(
            raw_power,
            context,
        ).power

    # ------------------------------------------------------------------
    def calibrate_details(
        self,
        raw_power: float,
        context: PowerCalibrationContext,
    ) -> PowerCalibrationResult:

        rawpower = clamp_to_zero(float(raw_power))

        if raw_power == 0.0:
            return PowerCalibrationResult(
                machine_power=0.0,
                profile_factor=1.0,
                level_factor=1.0,
                workout_factor=1.0,
                spm_factor=1.0,
                duration_factor=1.0,
                final_factor=1.0,
                power=0.0,
            )

        # Suppression de l'effet SPM artificiel du Q1S
        if (
            context.workout_enabled
            and context.spm_correction_enabled
        ):
            rawpower = self.remove_q1s_spm_effect(
                raw_power=rawpower,
                spm=context.spm,
            )
        
        machine_power = rawpower * self.machine_scale

        factor_profile = 1.0
        factor_level = 1.0
        factor_workout = 1.0
        factor_spm = 1.0
        factor_duration = 1.0

        # If selected (settings), calibrate the power based on the Profile info.
        if context.profile_enabled:
            
            factor_profile = self.profile_factor(context)
            factor_level = self.level_factor(context.level_norm)

        # Correction based on Cadence
        if context.spm_correction_enabled:

            factor_spm = self.spm_factor(context.spm)

        # If selected (settings), calibrate the power based on the Workout phases.
        if (
            context.workout_enabled
            and context.intensity is not None
        ):
            factor_workout = self.workout_factor(context)

            if context.duration_correction_enabled:

               factor_duration = self.duration_factor(
                    context.duration_seconds,
                    context.intensity,
                )

        factor = (
            factor_profile
            * factor_level
            * factor_spm
            * factor_workout
            * factor_duration
        )

        factor = clamp_between(
            factor,
            0.0,
            self.MAX_RECALIBRATION_FACTOR
        )
 
        power = machine_power * factor

        return PowerCalibrationResult(
            machine_power=machine_power,
            profile_factor=factor_profile,
            level_factor=factor_level,
            workout_factor=factor_workout,
            spm_factor=factor_spm,
            duration_factor=factor_duration,
            final_factor=factor,
            power=power,
        )

    # ------------------------------------------------------------------
    @staticmethod
    def duration_factor(
        duration_seconds: float,
        intensity: str | None,
    ) -> float:
        """
        Nous allons neutraliser ce facteur pour le moment car
        il semble surestimer la puissance.
        """
        return 1.0

        '''
        """
        Facteur de durée dépendant de l'intensité du workout.

        La durée correspond au temps déjà écoulé dans l'étape.

        R/E/N : pas de correction.
        F     : correction intermédiaire.
        M     : correction complète.
        """

        if intensity is None:
            return 1.0

        intensity = intensity.upper()

        exponent = (
            WorkoutPowerCalibration
            .DURATION_INTENSITY_EXPONENTS
            .get(intensity, 0.0)
        )

        if exponent == 0.0:
            return 1.0

        duration_ratio = (
            WorkoutPowerCalibration.duration_reference_ratio(
                duration_seconds
            )
        )

        return duration_ratio ** exponent
        '''
    '''
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

                return interpolate(x, x0, r0, x1, r1)

        return points[-1][1]
    '''

    # ------------------------------------------------------------------
    @staticmethod
    def workout_factor(context: PowerCalibrationContext) -> float:
        """
        Facteur de calibration lié à l'intensité demandée
        par l'étape courante du workout.

        La durée et le SPM ne sont pas utilisés ici.
        """

        if (
            (not context.workout_enabled) 
            or (context.intensity is None)
        ):
            return 1.0

        intensity = context.intensity.upper()

        return WorkoutPowerCalibration.INTENSITY_FACTORS.get(
            intensity,
            1.0,
        )

    # ------------------------------------------------------------------
    @staticmethod
    def remove_q1s_spm_effect(
        raw_power: float,
        spm: float,
    ) -> float:
        """
        Supprime la dépendance artificielle du RawPower Q1S
        vis-à-vis de la cadence.

        Le Q1S produit expérimentalement une puissance presque
        proportionnelle au SPM. On ramène donc la puissance à
        une cadence de référence de 24 SPM.

        La correction physiologique liée au SPM sera appliquée
        séparément plus tard.
        """

        rawpower = clamp_to_zero(float(raw_power))
        spm = float(spm)

        if rawpower <= 0.0 or spm <= 0.0:
            return rawpower

        return rawpower * (
            WorkoutPowerCalibration.REFERENCE_SPM / spm
        )

    # ------------------------------------------------------------------
    @staticmethod
    def spm_factor(spm: float) -> float:
        """
        Correction physiologique liée à la cadence.

        Le Q1S ayant déjà été corrigé de sa dépendance artificielle
        RawPower <-> SPM, cette correction représente uniquement
        l'effet physiologique de la cadence sur l'effort.

        La référence est 24 SPM.
        """

        spm = float(spm)

        if spm <= 0.0:
            return 1.0

        return (
            spm / WorkoutPowerCalibration.REFERENCE_SPM
        ) ** WorkoutPowerCalibration.SPM_FACTOR_EXPONENT

    # ------------------------------------------------------------------
    # PROFILE
    #
    # The profile describes physical potential, not training status.
    #
    # Reference profile:
    #   age    = 40 years
    #   height = 180 cm
    #   weight = 75 kg
    #   sex    = male
    #
    # Height and body mass are associated with rowing performance in
    # anthropometric studies. The exponents below are deliberately
    # conservative because those studies do not provide a universal
    # adult "watts = f(height, weight)" equation.
    #
    # BMI is calculated from height and weight, but is NOT given a second
    # independent multiplier: doing so would double-count information
    # already present in height and weight.
    #
    # Sex factor is also deliberately moderate. Differences observed
    # between men and women are substantially reduced when comparing
    # athletes with similar fat-free mass / aerobic capacity.
    # ------------------------------------------------------------------

    PROFILE_REFERENCE_AGE = 40.0
    PROFILE_REFERENCE_HEIGHT = 180.0
    PROFILE_REFERENCE_WEIGHT = 75.0

    HEIGHT_EXPONENT = 0.35
    WEIGHT_EXPONENT = 0.23

    FEMALE_FACTOR = 0.90

    PROFILE_FACTOR_MIN = 0.55
    PROFILE_FACTOR_MAX = 1.30

    # ------------------------------------------------------------------
    # OLDDER CALCULATION WAS:
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

        for (a0, f0), (a1, f1) in zip(
            WorkoutPowerCalibration.AGE_RATIOS,
            WorkoutPowerCalibration.AGE_RATIOS[1:]
        ):
            if age <= a1:
                return interpolate(age, a0, f0, a1, f1)

        return WorkoutPowerCalibration.AGE_RATIOS[-1][1]

    # ------------------------------------------------------------------
    # Coefficient volontairement conservateur dans cette V1 :
    # les études démontrent l'association taille/performance,
    # mais ne fournissent pas une loi adulte universelle
    # "watts = f(taille)" utilisable telle quelle. Référence = 180 cm.
    @staticmethod
    def height_factor(height_cm: float) -> float:

        height = clamp_between(
            float(height_cm),
            MIN_PROFILE_HEIGHT,
            MAX_PROFILE_HEIGHT
        )

        reference: float = WorkoutPowerCalibration.PROFILE_REFERENCE_HEIGHT # cm
        exponent: float = WorkoutPowerCalibration.HEIGHT_EXPONENT

        return (height / reference) ** exponent

    # ------------------------------------------------------------------
    # Body-mass scaling: rowing-ergometer performance has been modelled
    # with a mass exponent around 0.23. Keep it normalized to 75 kg.
    @staticmethod
    def weight_factor(weight_kg: float) -> float:

        weight = clamp_between(
            float(weight_kg),
            MIN_PROFILE_WEIGHT,
            MAX_PROFILE_WEIGHT
        )

        reference: float = WorkoutPowerCalibration.PROFILE_REFERENCE_WEIGHT # kg
        exponent: float = WorkoutPowerCalibration.WEIGHT_EXPONENT

        return (weight / reference) ** exponent

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

        return 1.00 if is_male else WorkoutPowerCalibration.FEMALE_FACTOR

    # ------------------------------------------------------------------
    @staticmethod
    def profile_factor(context: PowerCalibrationContext) -> float:
        """
        Physical potential associated with the user profile.

        The result is normalized to 1.0 for the reference profile:
            40 years / 180 cm / 75 kg / male.

        Training level is deliberately NOT included here.
        """

        factor_age = WorkoutPowerCalibration.age_factor(
            float(context.age)
        )
        age_reference = WorkoutPowerCalibration.age_factor(
            WorkoutPowerCalibration.PROFILE_REFERENCE_AGE
        )

        factor_height = WorkoutPowerCalibration.height_factor(
            float(context.height_cm)
        )
        height_reference = WorkoutPowerCalibration.height_factor(
            WorkoutPowerCalibration.PROFILE_REFERENCE_HEIGHT
        )

        factor_weight = WorkoutPowerCalibration.weight_factor(
            float(context.weight_kg)
        )
        weight_reference = WorkoutPowerCalibration.weight_factor(
            WorkoutPowerCalibration.PROFILE_REFERENCE_WEIGHT
        )

        factor_sex = WorkoutPowerCalibration.sex_factor(
            is_male= (context.sex.upper() == "M")
        )
 
        profile_factor = (
            (factor_age / age_reference)
            * (factor_height / height_reference)
            * (factor_weight / weight_reference)
            * factor_sex
        )

        return clamp_between(
            profile_factor,
            WorkoutPowerCalibration.PROFILE_FACTOR_MIN,
            WorkoutPowerCalibration.PROFILE_FACTOR_MAX
        )

    # ------------------------------------------------------------------
    # TRAINING LEVEL
    #
    # Unlike age/height/weight/sex, there is no universal published
    # conversion from "beginner/intermediate/advanced" to watts.
    #
    # We therefore use a smooth sigmoid rather than arbitrary linear
    # steps. The values below are V1 tuning parameters and are expected
    # to be refined against real users / C2 reference data.
    #
    # The curve deliberately has:
    #   - little change at very low levels,
    #   - its strongest progression in the middle,
    #   - diminishing returns at high levels.
    # ------------------------------------------------------------------

    LEVEL_SIGMOID_LOW = 0.72
    LEVEL_SIGMOID_HIGH = 1.28
    LEVEL_SIGMOID_CENTER = 0.50
    LEVEL_SIGMOID_STEEPNESS = 6.0

    # ------------------------------------------------------------------
    @staticmethod
    def sigmoid(value: float) -> float:

        sigmoid_low = WorkoutPowerCalibration.LEVEL_SIGMOID_LOW
        sigmoid_high = WorkoutPowerCalibration.LEVEL_SIGMOID_HIGH
        sigmoid_steep = WorkoutPowerCalibration.LEVEL_SIGMOID_STEEPNESS
        sigmoid_center = WorkoutPowerCalibration.LEVEL_SIGMOID_CENTER

        return (
            sigmoid_low 
            + (
                ( sigmoid_high - sigmoid_low )
                / (
                    1.0
                    + math.exp(
                        -sigmoid_steep * ( value - sigmoid_center )
                    )
                )
            )
        )

    # ------------------------------------------------------------------
    # The application level is retained in the context, but is not yet
    # converted into a fixed power multiplier. British Rowing uses
    # beginner/intermediate/advanced mainly to describe training status,
    # not universal wattage classes. A fixed multiplier here would be an
    # arbitrary assumption.
    @staticmethod
    def level_factor(level: float) -> float:

        level = clamp_between(float(level), 0.0, 1.0)

        # The application's reference level is 0.33.
        # Normalize it to exactly 1.0.
        reference = WorkoutPowerCalibration.sigmoid(
            DEFAULT_PROFILE_NORM_LEVEL
        )

        return WorkoutPowerCalibration.sigmoid(level) / reference

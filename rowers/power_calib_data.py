from dataclasses import dataclass

from setup.constants import (
    DEFAULT_PROFILE_AGE,
    DEFAULT_PROFILE_WEIGHT,
    DEFAULT_PROFILE_HEIGHT,
    DEFAULT_PROFILE_SEX,
    DEFAULT_PROFILE_LEVEL,
    DEFAULT_PROFILE_NORM_LEVEL,
)

# =============================================================================
@dataclass(frozen=True)
class PowerCalibrationContext:

    # Power calibration base on Profile and/or Workout:
    profile_enabled: bool = False
    workout_enabled: bool = False
    spm_correction_enabled: bool = False
    duration_correction_enabled: bool = False

    # Profile:
    age: float = float(DEFAULT_PROFILE_AGE) # years
    weight_kg: float = DEFAULT_PROFILE_WEIGHT # kg
    height_cm: float = DEFAULT_PROFILE_HEIGHT # cm
    sex: str = DEFAULT_PROFILE_SEX # "M" : Male, "F" : "Female"

    # Valeur continue utilisée par les formules : [0; 1].
    # 0.0 = débutant; 0.33 = Internédiare; 0.66 = confirmé;  1.0 = Advanced
    level_norm: float = DEFAULT_PROFILE_NORM_LEVEL

    intensity: str | None = None # "R", "E", "N", "F" or "M"
    duration_seconds: float = 0.0 # seconds
    step_elapsed_seconds: float = 0.0 # seconds
    spm: float = 0.0 # strokes per minutes

    # TODO: Maybe to remove later:
    level: str = DEFAULT_PROFILE_LEVEL

# ==============================================================================
from dataclasses import dataclass
@dataclass
class PowerCalibrationResult:
    machine_power: float
    profile_factor: float
    level_factor: float
    workout_factor: float
    spm_factor: float
    duration_factor: float
    final_factor: float
    power: float

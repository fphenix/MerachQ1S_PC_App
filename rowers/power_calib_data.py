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

    profile_enabled: bool = False
    workout_enabled: bool = False

    age: float = float(DEFAULT_PROFILE_AGE) # years
    weight_kg: float = DEFAULT_PROFILE_WEIGHT # kg
    height_cm: float = DEFAULT_PROFILE_HEIGHT # cm
    sex: str = DEFAULT_PROFILE_SEX # "M" : Male, "F" : "Female"

    # Valeur continue utilisée par les formules : [0; 1].
    # 0.0 = débutant; 0.33 = Internédiare; 0.66 = confirmé;  1.0 = Advanced
    level_norm: float = DEFAULT_PROFILE_NORM_LEVEL

    intensity: str | None = None # "R", "E", "N", "F" or "M"
    duration_seconds: float = 0.0 # seconds

    # TODO: Maybe to remove later:
    level: str = DEFAULT_PROFILE_LEVEL
    spm: float = 0.0 # strokes per minutes

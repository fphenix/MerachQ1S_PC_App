from dataclasses import dataclass

from setup.constants import (
    DEFAULT_DELAY_SECONDS,
    DEFAULT_SPLIT_LENGTH,
    DEFAULT_SPLIT_MODE,
    DEFAULT_LANGUAGE,
    DEFAULT_PROFILE_AGE,
    DEFAULT_PROFILE_WEIGHT,
    DEFAULT_PROFILE_HEIGHT,
    DEFAULT_PROFILE_LEVEL,
    DEFAULT_PROFILE_SEX,
    DEFAULT_PROFILE_NORM_LEVEL,
)

# =============================================================================
@dataclass
class Settings:

    language: str = DEFAULT_LANGUAGE
    delay_seconds: int = DEFAULT_DELAY_SECONDS
    split_length: float = DEFAULT_SPLIT_LENGTH
    split_mode: str = DEFAULT_SPLIT_MODE

    power_recalibration_profile_enabled: bool = False
    power_recalibration_workout_enabled: bool = False
    power_recalibration_spm_enabled: bool = False
    power_recalibration_duration_enabled: bool = False

    profile_age: float = DEFAULT_PROFILE_AGE
    profile_weight_kg: float = DEFAULT_PROFILE_WEIGHT
    profile_height_cm: float = DEFAULT_PROFILE_HEIGHT
    profile_sex: str = DEFAULT_PROFILE_SEX

    profile_level_norm: float = DEFAULT_PROFILE_NORM_LEVEL
    profile_level: str = DEFAULT_PROFILE_LEVEL
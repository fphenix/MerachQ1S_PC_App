from pathlib import Path
import json
from typing import Any
from dataclasses import asdict

from setup.utils import clamp_between
from setup.constants import (
    DEFAULT_LANGUAGE,
    LANGUAGES,
    DEFAULT_DELAY_SECONDS,
    DEFAULT_SPLIT_LENGTH,
    DELAY_SECONDS_STEP,
    MAX_DELAY_SECONDS,
    MAX_SPLIT_LENGTH,
    MIN_DELAY_SECONDS,
    MIN_SPLIT_LENGTH,
    SPLIT_LENGTH_STEP,
    DEFAULT_SPLIT_MODE,
    SPLIT_MODES,
    FILE_ENCODING,
    PROFILE_LEVELS_KEYS,
    PROFILE_LEVELS_THRESHOLDS,
    DEFAULT_PROFILE_LEVEL,
    DEFAULT_PROFILE_NORM_LEVEL,
    MIN_PROFILE_AGE, MAX_PROFILE_AGE, DEFAULT_PROFILE_AGE,
    MIN_PROFILE_WEIGHT, MAX_PROFILE_WEIGHT, DEFAULT_PROFILE_WEIGHT,
    MIN_PROFILE_HEIGHT, MAX_PROFILE_HEIGHT, DEFAULT_PROFILE_HEIGHT,
    DEFAULT_PROFILE_SEX,
)

from setup.settings import Settings

# =============================================================================
def profile_level_norm_from_key(level: str) -> float:
    """Return the normalized level associated with a level key."""

    return PROFILE_LEVELS_THRESHOLDS.get(
        level,
        DEFAULT_PROFILE_NORM_LEVEL,
    )

# =============================================================================
def profile_level_key_from_norm(level_norm: float) -> str:
    """Return the display level key for a normalized level."""

    value = clamp_between(float(level_norm), 0.0, 1.0)

    if value < PROFILE_LEVELS_THRESHOLDS["I"]:
        return PROFILE_LEVELS_KEYS[0]
    if value < PROFILE_LEVELS_THRESHOLDS["C"]:
        return PROFILE_LEVELS_KEYS[1]
    if value < PROFILE_LEVELS_THRESHOLDS["A"]:
        return PROFILE_LEVELS_KEYS[2]
    return PROFILE_LEVELS_KEYS[3]

# =============================================================================
def clamp_step(
    value,
    minimum,
    maximum,
    step,
) -> Any:

    value = max(
        minimum,
        min(maximum, value),
    )

    return round(
        value / step
    ) * step

# =============================================================================
def load_settings(settings_file: Path) -> Settings:

    if not settings_file.exists():
        return Settings()

    try:

        with settings_file.open(
            "r",
            encoding=FILE_ENCODING,
        ) as jrfile:

            data = json.load(jrfile)

        language = data.get(
            "language",
            DEFAULT_LANGUAGE,
        )

        if language not in LANGUAGES:
            language = DEFAULT_LANGUAGE

        delay_seconds = clamp_step(
            int(data.get(
                "delay_seconds",
                DEFAULT_DELAY_SECONDS,
            )),
            MIN_DELAY_SECONDS,
            MAX_DELAY_SECONDS,
            DELAY_SECONDS_STEP,
        )

        split_length = clamp_step(
            float(data.get(
                "split_length",
                DEFAULT_SPLIT_LENGTH,
            )),
            MIN_SPLIT_LENGTH,
            MAX_SPLIT_LENGTH,
            SPLIT_LENGTH_STEP,
        )

        split_mode = data.get(
            "split_mode",
            DEFAULT_SPLIT_MODE,
        )

        if split_mode not in SPLIT_MODES:
            split_mode = DEFAULT_SPLIT_MODE

        profile_sex = data.get("profile_sex", DEFAULT_PROFILE_SEX)
        if profile_sex not in ("M", "F"):
            profile_sex = DEFAULT_PROFILE_SEX


        # newer config settings
        if "profile_level_norm" in data:
            profile_level_norm = float(data["profile_level_norm"])
        # support old config settings
        else:
            legacy_level = data.get("profile_level", DEFAULT_PROFILE_LEVEL)
            if legacy_level not in PROFILE_LEVELS_KEYS:
                legacy_level = DEFAULT_PROFILE_LEVEL
            profile_level_norm = profile_level_norm_from_key(legacy_level)

        profile_level_norm = clamp_between(
            profile_level_norm,
            0.0,
            1.0,
        )
        profile_level = profile_level_key_from_norm(profile_level_norm)

        profile_age = float(data.get("profile_age", DEFAULT_PROFILE_AGE))
        profile_age = clamp_between(profile_age, MIN_PROFILE_AGE, MAX_PROFILE_AGE)

        profile_weight_kg = float(data.get("profile_weight_kg", DEFAULT_PROFILE_WEIGHT))
        profile_weight_kg = clamp_between(profile_weight_kg, MIN_PROFILE_WEIGHT, MAX_PROFILE_WEIGHT)

        profile_height_cm = float(data.get("profile_height_cm", DEFAULT_PROFILE_HEIGHT))
        profile_height_cm = clamp_between(profile_height_cm, MIN_PROFILE_HEIGHT, MAX_PROFILE_HEIGHT)

        return Settings(
            language= language,
            delay_seconds= delay_seconds,
            split_length= split_length,
            split_mode= split_mode,
            power_recalibration_profile_enabled=bool(
                data.get("power_recalibration_profile_enabled", False)
            ),
            power_recalibration_workout_enabled=bool(
                data.get("power_recalibration_workout_enabled", False)
            ),
            profile_age= profile_age,
            profile_weight_kg=profile_weight_kg,
            profile_height_cm=profile_height_cm,
            profile_sex=profile_sex,
            profile_level_norm=profile_level_norm,
            profile_level=profile_level,
        )

    except (
        OSError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ):

        return Settings()

# =============================================================================
def save_settings(
    settings: Settings,
    settings_file: Path,
) -> None:

    settings_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with settings_file.open(
        "w",
        encoding=FILE_ENCODING,
    ) as wfile:

        json.dump(
            asdict(settings),
            wfile,
            indent=4,
        )

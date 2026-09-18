import json
from typing import Any
from dataclasses import asdict

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
    SETTINGS_FILE,
    SPLIT_LENGTH_STEP,
    DEFAULT_SPLIT_MODE,
    SPLIT_MODES,
    FILE_ENCODING,
)

from setup.settings import Settings

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
def load_settings() -> Settings:

    if not SETTINGS_FILE.exists():
        return Settings()

    try:

        with SETTINGS_FILE.open(
            "r",
            encoding=FILE_ENCODING,
        ) as jfile:

            data = json.load(jfile)

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

        return Settings(
            language= language,
            delay_seconds= delay_seconds,
            split_length= split_length,
            split_mode= split_mode,
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
) -> None:

    with SETTINGS_FILE.open(
        "w",
        encoding=FILE_ENCODING,
    ) as file:

        json.dump(
            asdict(settings),
            file,
            indent=4,
        )

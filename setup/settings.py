import json
from dataclasses import asdict, dataclass

from setup.constants import (
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
)


@dataclass
class Settings:

    delay_seconds: int = DEFAULT_DELAY_SECONDS
    split_length: float = DEFAULT_SPLIT_LENGTH
    split_mode: str = DEFAULT_SPLIT_MODE


# =============================================================================
def _clamp_step(
    value,
    minimum,
    maximum,
    step,
):
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
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        delay_seconds = _clamp_step(
            int(data.get(
                "delay_seconds",
                DEFAULT_DELAY_SECONDS,
            )),
            MIN_DELAY_SECONDS,
            MAX_DELAY_SECONDS,
            DELAY_SECONDS_STEP,
        )

        split_length = _clamp_step(
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
            delay_seconds=delay_seconds,
            split_length=split_length,
            split_mode=split_mode,
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
        encoding="utf-8",
    ) as file:

        json.dump(
            asdict(settings),
            file,
            indent=4,
        )
from dataclasses import dataclass

from setup.constants import (
    DEFAULT_DELAY_SECONDS,
    DEFAULT_SPLIT_LENGTH,
    DEFAULT_SPLIT_MODE,
    DEFAULT_LANGUAGE,
)

# =============================================================================
@dataclass
class Settings:

    language: str = DEFAULT_LANGUAGE
    delay_seconds: int = DEFAULT_DELAY_SECONDS
    split_length: float = DEFAULT_SPLIT_LENGTH
    split_mode: str = DEFAULT_SPLIT_MODE

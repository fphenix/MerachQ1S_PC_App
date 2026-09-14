from dataclasses import dataclass

from setup.constants import (
    INTENSITY_DICT,
    INTENSITY_COLORS,
    PART_DICT,
)

# =============================================================================
@dataclass
class WorkoutStep:

    duration_seconds: float
    cpm: int
    intensity: str
    part: str | None
    info: str | None
    comment: str | None

    # -------------------------------------------------------------------------
    @property
    def intensity_text(self):
        part_txt = (
            ""
            if self.part is None
            else f" ({PART_DICT[self.part]})"
        )

        return (
            f"{INTENSITY_DICT[self.intensity]}"
            f"{part_txt}"
        )

    # -------------------------------------------------------------------------
    @property
    def intensity_color(self):
        return INTENSITY_COLORS[self.intensity]

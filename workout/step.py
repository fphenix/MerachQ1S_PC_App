from dataclasses import dataclass

from setup.lang import get_text
from setup.constants import (
    INTENSITY_COLORS,
)

# =============================================================================
@dataclass
class WorkoutStep:

    duration_seconds: float
    spm: int
    intensity: str
    part: str | None
    info: str | None
    comment: str | None

    # -------------------------------------------------------------------------
    @property
    def intensity_text(self) -> str:
        
        part_txt = (
            ""
            if self.part is None
            else f" ({get_text(f"PART_DICT_{self.part}")})"
        )

        return (
            f"{get_text(f"INTENSITY_DICT_{self.intensity}")}"
            f"{part_txt}"
        )

    # -------------------------------------------------------------------------
    @property
    def intensity_color(self) -> str:
        return INTENSITY_COLORS[self.intensity]

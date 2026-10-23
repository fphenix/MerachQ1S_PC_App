"""Moteur de Slow N'Go : suivre des cibles de cadence imprévisibles."""

import random

from setup.lang import get_text
from setup.utils import is_within, clamp_to_zero

from games.game import Game
from games.game_input import GameInput, input_cadence

# =============================================================================
class SlowNGoGame(Game):

    WIDTH: int = 1000
    HEIGHT: int = 700
    HUD_HEIGHT: int = 70
    DURATION_SECONDS: float = 240.0

    STINT_MIN_SECONDS: float = 20.0
    STINT_MAX_SECONDS: float = 50.0
    CADENCE_HOLD_SECONDS: float = 2.0
    SCORE_PER_SECOND: float = 1.0
    PERFECT_TOLERANCE: float = 1.5

    CADENCE_TARGETS: dict[str, float] = {"slow": 18.0, "medium": 24.0, "fast": 30.0}
    CADENCE_MARGIN: float = 2.0

    # -------------------------------------------------------------------------
    def __init__(self) -> None:

        super().__init__("slowngo", get_text("MENU_GAMES_SLOWNGO"), self.DURATION_SECONDS)

        self.reset()

    # -------------------------------------------------------------------------
    def reset(self) -> None:

        self.current_spm: float | None = None
        self._last_valid_spm: float | None = None
        self._cadence_hold_remaining: float = 0.0
        self.target_band: str = "medium"
        self.target_spm: float = self.CADENCE_TARGETS[self.target_band]
        self.stint_remaining: float = random.uniform(self.STINT_MIN_SECONDS, self.STINT_MAX_SECONDS)
        self.match_quality: float = 0.0
        self._score_fraction: float = 0.0
        self._last_band: str | None = None
        
        self._choose_target(initial=True)

    # -------------------------------------------------------------------------
    def update_game(self, dt: float, game_input: GameInput) -> None:

        measured_spm = input_cadence(game_input)

        if measured_spm is not None:
            self._last_valid_spm = measured_spm
            self._cadence_hold_remaining = self.CADENCE_HOLD_SECONDS
            self.current_spm = measured_spm
        else:
            self._cadence_hold_remaining = clamp_to_zero(self._cadence_hold_remaining - dt)
            self.current_spm = (
                self._last_valid_spm
                if self._cadence_hold_remaining > 0.0
                else None
            )

        self.stint_remaining -= dt
        if self.stint_remaining <= 0.0:
            self._choose_target()
            self.stint_remaining = random.uniform(self.STINT_MIN_SECONDS, self.STINT_MAX_SECONDS)

        target_spm = self.CADENCE_TARGETS[self.target_band]
        difference = abs(self.current_spm - target_spm) if self.current_spm is not None else 99.0
        if difference <= self.PERFECT_TOLERANCE:
            self.match_quality = 1.0
        elif (
            self.current_spm is not None
            and is_within(self.current_spm, target_spm, self.CADENCE_MARGIN)
        ):
            self.match_quality = 0.55
        else:
            self.match_quality = 0.0
        self._score_fraction += self.match_quality * self.SCORE_PER_SECOND * dt
        points = int(self._score_fraction)
        if points:
            self.add_score(points)
            self._score_fraction -= points

    # -------------------------------------------------------------------------
    def _choose_target(self, initial: bool = False) -> None:

        bands = list(self.CADENCE_TARGETS)
        if not initial and self._last_band in bands and len(bands) > 1:
            bands.remove(self._last_band)
        self.target_band = random.choice(bands)
        self._last_band = self.target_band
        self.target_spm = self.CADENCE_TARGETS[self.target_band]

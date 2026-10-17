"""Moteur de Ballade : suivre un parcours visible en changeant de cadence."""

from dataclasses import dataclass

import random

from setup.lang import get_text
from setup.utils import is_within

from games.game import Game
from games.game_input import GameInput
from games.cadence import input_cadence

# =============================================================================
@dataclass(slots=True)
class PathSegment:
    distance: float
    lane: int

# =============================================================================
class PathGame(Game):

    WIDTH = 1000
    HEIGHT = 700
    HUD_HEIGHT = 70
    DURATION_SECONDS = 240.0
    PLAYER_Y = 620.0
    SCROLL_SPEED = 105.0
    SEGMENT_LENGTH = 330.0
    POINTS_PER_SECOND = 1.0

    CADENCE_LEFT: float = 18.0
    CADENCE_MIDDLE: float = 24.0
    CADENCE_RIGHT: float = 30.0
    CADENCE_TARGETS = (CADENCE_LEFT, CADENCE_MIDDLE, CADENCE_RIGHT)
    CADENCE_MARGIN = 2.0

    # -------------------------------------------------------------------------
    def __init__(self) -> None:

        super().__init__("path", get_text("MENU_GAMES_PATH"), self.DURATION_SECONDS)

        self.current_spm: float | None = None
        self.player_lane: int | None = 1
        self.segments: list[PathSegment] = []
        self.matching = False
        self._score_fraction = 0.0
        self._stint_lane: int | None = None
        self._stint_tiles_remaining = 0

    # -------------------------------------------------------------------------
    def reset(self) -> None:

        self.current_spm = None
        self.player_lane = 1
        self.segments = []
        self.matching = False
        self._score_fraction = 0.0
        distance = 0.0
        self._stint_lane = random.randrange(3)
        self._stint_tiles_remaining = 0
        while len(self.segments) < 7:
            lane = self._next_stint_lane()
            self.segments.append(PathSegment(distance, lane))
            distance += self.SEGMENT_LENGTH

    # -------------------------------------------------------------------------
    def update_game(self, dt: float, game_input: GameInput) -> None:
        
        self.current_spm = input_cadence(game_input)
        self.player_lane = self._cadence_lane(self.current_spm)
        self.matching = bool(
            self.segments
            and self.player_lane is not None
            and self.player_lane == self.segments[0].lane
        )
        if self.matching:
            self._score_fraction += dt * self.POINTS_PER_SECOND
            points = int(self._score_fraction)
            if points:
                self.add_score(points)
                self._score_fraction -= points
        for segment in self.segments:
            segment.distance -= self.SCROLL_SPEED * dt
        while self.segments and self.segments[0].distance <= -self.SEGMENT_LENGTH:
            self.segments.pop(0)
        while len(self.segments) < 7:
            last = self.segments[-1] if self.segments else PathSegment(0.0, 1)
            lane = self._next_stint_lane()
            self.segments.append(PathSegment(
                last.distance + self.SEGMENT_LENGTH,
                lane,
            ))

    # -------------------------------------------------------------------------
    @classmethod
    def _cadence_lane(cls, cadence: float | None) -> int | None:
        """Convertit la cadence en voie : gauche=0, centre=1, droite=2."""

        if cadence is None:
            return None
        
        for lane, target in enumerate(cls.CADENCE_TARGETS):
            if is_within(cadence, target, cls.CADENCE_MARGIN):
                return lane

        return None

    # -------------------------------------------------------------------------
    def _next_stint_lane(self) -> int:
        """Maintient chaque voie 5 à 7 tuiles avant de changer de voie."""

        if self._stint_tiles_remaining <= 0:
            previous = self._stint_lane if self._stint_lane is not None else 1
            choices = [lane for lane in range(3) if lane != previous]
            self._stint_lane = random.choice(choices)
            self._stint_tiles_remaining = random.randint(5, 7)

        self._stint_tiles_remaining -= 1
        return self._stint_lane if self._stint_lane is not None else 1

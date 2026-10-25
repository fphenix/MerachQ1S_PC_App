"""Moteur de Ballade : suivre un parcours visible en changeant de cadence."""

from dataclasses import dataclass

import random

from setup.lang import get_text
from setup.utils import is_within

from games.game import Game
from games.game_input import GameInput, input_cadence

# =============================================================================
@dataclass(slots=True)
class PathSegment:
    
    distance: float
    lane: int

# =============================================================================
@dataclass(slots=True)
class PathScenery:
    """Objet décoratif dont la distance diminue comme les segments de route."""

    distance: float
    side: int
    kind: str
    size: float
    delta_x: float

# =============================================================================
class PathGame(Game):

    GAME_ID: str = "path"

    WIDTH: int = 1000
    HEIGHT: int = 700
    HUD_HEIGHT: int = 70
    DURATION_SECONDS: float = 240.0

    SCROLL_SPEED: float = 105.0
    SEGMENT_LENGTH: float = 330.0
    POINTS_PER_SECOND: float = 1.0

    CADENCE_LEFT: float = 18.0
    CADENCE_MIDDLE: float = 24.0
    CADENCE_RIGHT: float = 30.0
    CADENCE_MARGIN: float = 3.0

    OBJECTS_DELTA_X: float = 32.0

    # -------------------------------------------------------------------------
    def __init__(self) -> None:

        super().__init__(
            game_id= self.GAME_ID,
            title= get_text("MENU_GAMES_PATH"),
            duration= self.DURATION_SECONDS
        )

        self.reset()

    # -------------------------------------------------------------------------
    def reset(self) -> None:

        self.current_spm: float | None = None
        self.player_lane: int | None = 1
        self.segments: list[PathSegment] = []
        self.scenery: list[PathScenery] = []
        self.matching: bool = False
        self._score_fraction: float = 0.0
        self._stint_lane: int = random.randrange(3)
        self._stint_tiles_remaining: int = 0

        distance: float = 0.0
        while len(self.segments) < 7:
            lane = self._next_stint_lane()
            self.segments.append(PathSegment(distance, lane))
            distance += self.SEGMENT_LENGTH

        # Les objets de décor sont placés sur les bas-côtés, à des profondeurs variées.
        scenery_distance = 180.0
        while scenery_distance < 1900.0:
            self._add_scenery(scenery_distance)
            scenery_distance += random.uniform(150.0, 310.0)

    # -------------------------------------------------------------------------
    def update_game(self, dt: float, game_input: GameInput) -> None:
        
        self.current_spm = input_cadence(game_input)
        target_lane = self._cadence_lane(self.current_spm)
        if target_lane is not None:
            self.player_lane = target_lane
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
        for item in self.scenery:
            item.distance -= self.SCROLL_SPEED * dt
        self.scenery = [item for item in self.scenery if item.distance > -180.0]
        farthest_scenery = max((item.distance for item in self.scenery), default=0.0)
        while farthest_scenery < 1700.0:
            farthest_scenery += random.uniform(150.0, 310.0)
            self._add_scenery(farthest_scenery)
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
    def _add_scenery(self, distance: float) -> None:
        self.scenery.append(PathScenery(
            distance= distance,
            side= random.choice((-1, 1)),
            kind= random.choice(("bush", "rock", "tree")),
            size= random.uniform(0.75, 1.25),
            delta_x= random.uniform(-self.OBJECTS_DELTA_X, self.OBJECTS_DELTA_X),
        ))

    # -------------------------------------------------------------------------
    @classmethod
    def _cadence_lane(cls, cadence: float | None) -> int | None:
        """Convertit la cadence en voie : gauche=0, centre=1, droite=2."""

        if cadence is None:
            return None

        if is_within(cadence, cls.CADENCE_MIDDLE, cls.CADENCE_MARGIN):
            return 1
        elif cadence > (cls.CADENCE_RIGHT - cls.CADENCE_MARGIN):
            return 2
        else:
            return 0

    # -------------------------------------------------------------------------
    def _next_stint_lane(self) -> int:
        """Maintient chaque voie 5 à 7 tuiles avant de changer de voie."""

        if self._stint_tiles_remaining <= 0:
            previous = self._stint_lane
            choices = [lane for lane in range(3) if lane != previous]
            self._stint_lane = random.choice(choices)
            self._stint_tiles_remaining = random.randint(5, 7)

        self._stint_tiles_remaining -= 1
        return self._stint_lane

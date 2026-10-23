""" Jeu Attrape-insectes.

    Appelé "Fishing" en interne car il est basé sur le jeu "Fishing" du Concept2!
"""
from dataclasses import dataclass

import random
import math

from setup.lang import get_text
from setup.utils import is_between, clamp_to_zero, clamp_to_max
from setup.utils import debug

from games.game import Game
from games.game_input import GameInput, input_cadence

# =============================================================================
@dataclass(slots=True)
class Insect:

    x: float
    y: float
    speed: float
    kind: str
    lane_index: int

# =============================================================================
class FishingGame(Game):

    WIDTH: int = 1000
    HEIGHT: int = 700
    HUD_HEIGHT: int = 70
    DURATION_SECONDS: float = 240.0

    PLAYFIELD_HEIGHT: int = HEIGHT - HUD_HEIGHT

    NET_HEIGHT: int = 90
    NET_WIDTH: int = 55
    NET_RETURN_SPEED: float = 90.0
    NET_SPEED: float = 60.0
    NET_GRAVITY_SPEED: float = 20.0
    NET_LERP_SPEED: float = 3.0
    NET_LEFT_MARGIN: int = 90
    
    SPAWN_MIN: float = 0.65
    SPAWN_MAX: float = 1.20

    INSECTS_DATA: dict[str, dict[str, int|float]] = {
        "bee":       {"pxsize": 35, "speed":  70.0, "points":  60, "freq": 55.0},
        "butterfly": {"pxsize": 40, "speed":  50.0, "points":  30, "freq": 25.0},
        "hornet":    {"pxsize": 50, "speed": 100.0, "points": -45, "freq": 20.0},
    }

    CADENCE_LEVELS: tuple[int] = (16, 20, 24, 28, 32)

    MIN_VALID_CADENCE: float = 10.0
    MAX_VALID_CADENCE: float = 40.0

    LANE_COUNT: int = len(CADENCE_LEVELS)
    LANE_HEIGHT: float = PLAYFIELD_HEIGHT / LANE_COUNT

    # -------------------------------------------------------------------------
    def __init__(self) -> None:

        super().__init__(
            game_id= "fishing",
            title= get_text("MENU_GAMES_FISHING"),
            duration= self.DURATION_SECONDS,
        )

        self.reset()

    # -------------------------------------------------------------------------
    def reset(self) -> None:

        self._game_time: float = 0.0
        self._rest_offset: float = 0.0
        self._last_stroke_time: float | None = None

        self.current_spm: float | None = None
        self.lane_index: int = 2

        self.net_y: float = self._net_y_for_lane(self.lane_index)
        self._target_net_y: float = self.net_y

        self.insects: list[Insect] = []
        self._spawn_remaining: float = 0.5

    # -------------------------------------------------------------------------
    def _net_y_for_lane(self, lane_index: int) -> float:

        lane_center = self.PLAYFIELD_HEIGHT - (
            lane_index + 0.5
        ) * self.LANE_HEIGHT

        return lane_center - self.NET_HEIGHT / 2
    
    # -------------------------------------------------------------------------
    @classmethod
    def _lane_for_spm(cls, spm: float) -> int:
        """Return the unique lane for a cadence, using midpoint boundaries."""

        for lane_index in range(cls.LANE_COUNT - 1):
            threshold = (
                cls.CADENCE_LEVELS[lane_index]
                + cls.CADENCE_LEVELS[lane_index + 1]
            ) / 2
            if spm < threshold:
                return lane_index
            
        return cls.LANE_COUNT - 1

    # -------------------------------------------------------------------------
    def _update_lane_from_spm(self, spm: float) -> None:

        self.lane_index = self._lane_for_spm(spm)
        self._target_net_y = self._net_y_for_lane(self.lane_index)

    # -------------------------------------------------------------------------
    def update_game(self, dt: float, game_input: GameInput) -> None:

        self._game_time += dt
        stroke_delta = clamp_to_zero(getattr(game_input, "stroke_delta", 0))
        if game_input.stroke_event and stroke_delta == 0:
            stroke_delta = 1

        if stroke_delta:
            # When a packet reports multiple strokes, use the machine cadence
            # if available; the exact individual stroke times are unknowable.
            if stroke_delta > 1:
                interval = (
                    self._game_time - self._last_stroke_time
                    if self._last_stroke_time is not None else 0.0
                )
                measured_spm = input_cadence(game_input)
                interval_spm = (
                    60.0 * stroke_delta / interval
                    if interval > 0.0
                    else None
                )

                if self._is_valid_cadence(measured_spm):
                    candidate_spm = measured_spm
                elif self._is_valid_cadence(interval_spm):
                    candidate_spm = interval_spm
                else:
                    candidate_spm = None

                if candidate_spm is not None:
                    self.current_spm = candidate_spm

                if self.current_spm is not None:
                    for _ in range(stroke_delta):
                        self._update_lane_from_spm(self.current_spm)
            else:
                if self._last_stroke_time is not None:
                    interval = self._game_time - self._last_stroke_time
                    # After a long pause, the first stroke establishes a new
                    # timing baseline; do not treat the pause as a real cadence.
                    if is_between(interval, 0.01, 60.0 / self.CADENCE_LEVELS[0]):
                        # Priorité à la mesure effective commune fournie par
                        # GameWidget ; le chronométrage local reste un secours.
                        measured_spm = input_cadence(game_input)
                        interval_spm = 60.0 / interval
                        if self._is_valid_cadence(measured_spm):
                            candidate_spm = measured_spm
                        elif self._is_valid_cadence(interval_spm):
                            candidate_spm = interval_spm
                        else:
                            candidate_spm = None

                        if candidate_spm is not None:
                            self.current_spm = candidate_spm
                            self._update_lane_from_spm(self.current_spm)

            self._last_stroke_time = self._game_time
            self._rest_offset = 0.0

        # Keep the selected lane stable between strokes. The instantaneous
        # value 60 / elapsed_time is only a prediction of the *next* stroke,
        # not the cadence actually held by the rower; using it to select a lane
        # makes the net jump to the fastest lane immediately after every stroke.
        # Only begin a small downward drift when the next stroke is noticeably
        # late. A real stroke resets this offset above.
        if self._last_stroke_time is not None and not stroke_delta:
            interval = self._game_time - self._last_stroke_time
            if self.current_spm is not None and self.current_spm > 0.0:
                expected_interval = 60.0 / self.current_spm
                grace_interval = expected_interval * 1.35
                if interval > grace_interval:
                    max_offset = self.LANE_HEIGHT * 0.40
                    excess_time = interval - grace_interval
                    self._rest_offset = clamp_to_max(
                        max_offset * excess_time / 2.0,
                        max_offset,
                    )

        target_y = self._net_y_for_lane(self.lane_index) + self._rest_offset
        alpha = 1.0 - math.exp(-self.NET_LERP_SPEED * dt)
        self.net_y += (target_y - self.net_y) * alpha

        # Spawn, move, collide, then remove insects that left the screen.
        self._spawn_remaining -= dt
        if self._spawn_remaining <= 0.0:
            self._spawn()
            self._spawn_remaining = random.uniform(self.SPAWN_MIN, self.SPAWN_MAX)

        for insect in self.insects:
            insect.x -= insect.speed * dt

        self._check_collisions()
        self.insects = [
            insect for insect in self.insects
            if insect.x + self.INSECTS_DATA[insect.kind]["pxsize"] > 0.0
        ]

    # -------------------------------------------------------------------------
    @classmethod
    def _is_valid_cadence(cls, spm: float | None) -> bool:
        """Écarte les valeurs aberrantes avant qu'elles changent de couloir."""

        return spm is not None and is_between(
            spm, cls.MIN_VALID_CADENCE, cls.MAX_VALID_CADENCE
        )

    # -------------------------------------------------------------------------
    def _spawn(self) -> None:

        insects = ("bee", "butterfly", "hornet")
        
        insects_freq: list[int] = []
        for insect in insects:
            insects_freq.append(self.INSECTS_DATA[insect]["freq"])

        kind = random.choices(
            insects,
            weights= insects_freq,
            k= 1,
        )[0]

        insect_data = self.INSECTS_DATA[kind]
        size = insect_data["pxsize"]

        lane_index = random.randrange(self.LANE_COUNT)
        lane_center = self.PLAYFIELD_HEIGHT - (
            lane_index + 0.5
        ) * self.LANE_HEIGHT

        self.insects.append(
            Insect(
                x=float(self.WIDTH),
                y=lane_center - size / 2,
                speed=insect_data["speed"],
                kind=kind,
                lane_index=lane_index,
            )
        )

    # -------------------------------------------------------------------------
    def _check_collisions(self) -> None:

        net_left = self.NET_LEFT_MARGIN
        net_right = net_left + self.NET_WIDTH
        remaining = []
        resting = (
            self.lane_index == 0
            and self.net_y - self._net_y_for_lane(0) >= self.LANE_HEIGHT * 0.30
        )

        for insect in self.insects:
            # Discrete lanes make vertical rectangle tests unnecessary.
            same_lane = insect.lane_index == self.lane_index
            overlaps_horizontally = (
                net_left < insect.x + self.INSECTS_DATA[insect.kind]["pxsize"]
                and net_right > insect.x
            )
            # At the bottom rest position, the net is deliberately inactive.
            collision = same_lane and overlaps_horizontally and not resting

            if collision:
                self.add_score(self.INSECTS_DATA[insect.kind]["points"])
            else:
                remaining.append(insect)

        self.insects = remaining

    # -------------------------------------------------------------------------
    # Cette méthode pourrait être utilisée si ne filet pouvait
    # bouger plus librement, même verticalement. Dans cette version
    # du jeu, la mécanique de couloirs fait que les hauteurs du filet
    # sont des valeurs discrètes et prédéfinies donc une colission
    # plus simple est suffisante.
    def _check_collisions_rect(self) -> None:

        net_left = self.NET_LEFT_MARGIN
        net_right = net_left + self.NET_WIDTH
        net_top = self.net_y
        net_bottom = net_top + self.NET_HEIGHT

        remaining = []

        for insect in self.insects:
            size = self.INSECTS_DATA[insect.kind]["pxsize"]

            insect_left = insect.x
            insect_right = insect.x + size
            insect_top = insect.y
            insect_bottom = insect.y + size

            collision = (
                net_left < insect_right
                and net_right > insect_left
                and net_top < insect_bottom
                and net_bottom > insect_top
            )

            if collision:
                self.add_score(
                    self.INSECTS_DATA[insect.kind]["points"]
                )
            else:
                remaining.append(insect)

        self.insects = remaining

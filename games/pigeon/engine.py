"""Jeu de tir automatique au pigeon."""

from dataclasses import dataclass

import math
import random

from setup.lang import get_text
from setup.utils import is_between, is_within

from games.game import Game
from games.game_input import GameInput, input_cadence

# =============================================================================
@dataclass(slots=True)
class Pigeon:
    x: float
    y: float
    base_y: float
    speed: float
    direction: int
    phase: float

# =============================================================================
@dataclass(slots=True)
class Bullet:
    x: float
    y: float
    speed: float

# =============================================================================
class PigeonGame(Game):

    WIDTH = 1000
    HEIGHT = 700
    HUD_HEIGHT = 70
    DURATION_SECONDS = 240.0

    OPENING_MIN = 20.0
    OPENING_MAX = 45.0
    SHOOTING_MIN = 20.0
    SHOOTING_MAX = 40.0
    BULLET_SPEED = 620.0
    BULLET_INTERVAL_LOW = 0.50  # 2 balles/s à 28 CPM
    BULLET_INTERVAL_HIGH = 0.22  # environ 4,5 balles/s à 32 CPM
    PIGEON_SIZE = 26

    CADENCE_OPEN = 24.0
    CADENCE_SHOOT = 30.0
    CADENCE_MARGIN = 2.0

    # -------------------------------------------------------------------------
    def __init__(self) -> None:

        super().__init__(
            game_id="pigeon",
            title=get_text("MENU_GAMES_PIGEON"),
            duration=self.DURATION_SECONDS,
        )
        
        self.current_spm: float | None = None
        self.phase_name = "opening"
        self.phase_duration = 0.0
        self._phase_remaining = 0.0
        self._spawn_remaining = 0.0
        self._bullet_remaining = 0.0
        self.pigeons: list[Pigeon] = []
        self.bullets: list[Bullet] = []
        self.shots_fired = 0

    # -------------------------------------------------------------------------
    def reset(self) -> None:

        self.current_spm = None
        self.phase_name = "opening"
        self.phase_duration = random.uniform(self.OPENING_MIN, self.OPENING_MAX)
        self._phase_remaining = self.phase_duration
        self._spawn_remaining = 0.0
        self._bullet_remaining = 0.0
        self.pigeons.clear()
        self.bullets.clear()
        self.shots_fired = 0

    # -------------------------------------------------------------------------
    @property
    def cages_open(self) -> bool:
        
        return (
            self.current_spm is not None
            and is_within(self.current_spm, self.CADENCE_OPEN, self.CADENCE_MARGIN)
        )

    # -------------------------------------------------------------------------
    def hud_score_text(self) -> str:
        return f"{get_text('GAME_SCORE')}: {self.score:05d}"

    # -------------------------------------------------------------------------
    def update_game(self, dt: float, game_input: GameInput) -> None:

        self.current_spm = input_cadence(game_input)

        # Les phases ne sont plus chronométrées : le rameur choisit lui-même
        # quand ouvrir les cages (22–26 CPM) et quand tirer (28 CPM ou plus).
        self.phase_name = (
            "opening"
            if self.cages_open
            else "shooting"
        )

        if self.cages_open:
            self._spawn_remaining -= dt
            if self._spawn_remaining <= 0.0:
                self._spawn_pigeon()
                self._spawn_remaining = random.uniform(2.0, 3.0)

        if self.current_spm is not None and self.current_spm >= (self.CADENCE_SHOOT - self.CADENCE_MARGIN):
            if self.current_spm >= 32.0:
                interval = self.BULLET_INTERVAL_HIGH
            else:
                factor = (self.current_spm - 28.0) / 4.0
                interval = self.BULLET_INTERVAL_LOW + factor * (
                    self.BULLET_INTERVAL_HIGH - self.BULLET_INTERVAL_LOW
                )
            self._bullet_remaining -= dt
            while self._bullet_remaining <= 0.0:
                self.bullets.append(Bullet(self.WIDTH / 2, self.HEIGHT - 100, self.BULLET_SPEED))
                self.shots_fired += 1
                self._bullet_remaining += interval
        else:
            self._bullet_remaining = 0.0

        for pigeon in self.pigeons:
            pigeon.x += pigeon.direction * pigeon.speed * dt
            pigeon.phase += dt * 3.0
            pigeon.y = pigeon.base_y + math.sin(pigeon.phase) * 18.0
        for bullet in self.bullets:
            bullet.y -= bullet.speed * dt

        # Retire immédiatement les objets touchés pour libérer leurs références.
        live_bullets: list[Bullet] = []
        hit_pigeons: set[int] = set()
        for bullet in self.bullets:
            hit_index = None
            for index, pigeon in enumerate(self.pigeons):
                if index in hit_pigeons:
                    continue
                if (
                    is_between(bullet.x, pigeon.x, pigeon.x + self.PIGEON_SIZE)
                    and is_between(bullet.y, pigeon.y, pigeon.y + self.PIGEON_SIZE)
                ):
                    hit_index = index
                    break
            if hit_index is not None:
                hit_pigeons.add(hit_index)
                self.add_score(10)
            elif bullet.y + 5 >= self.HUD_HEIGHT:
                live_bullets.append(bullet)
        self.bullets = live_bullets
        self.pigeons = [
            pigeon for index, pigeon in enumerate(self.pigeons)
            if index not in hit_pigeons
            and -self.PIGEON_SIZE < pigeon.x < self.WIDTH
        ]

    # -------------------------------------------------------------------------
    def _spawn_pigeon(self) -> None:

        from_left = random.choice((True, False))
        x = 35.0 if from_left else self.WIDTH - 60.0
        direction = 1 if from_left else -1
        base_y = random.uniform(self.HUD_HEIGHT + 18, self.HUD_HEIGHT + 150)

        self.pigeons.append(Pigeon(
            x=x, y=base_y, base_y=base_y,
            speed=random.uniform(11.0, 17.5),
            direction=direction,
            phase=random.uniform(0.0, math.tau),
        ))

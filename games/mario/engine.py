"""Prototype de plateforme inspiré des jeux de plateforme 16 bits."""

from dataclasses import dataclass

import math

from setup.lang import get_text

from games.game import Game
from games.game_input import GameInput
from games.cadence import input_cadence

# =============================================================================
@dataclass(slots=True)
class Coin:

    x: float
    collected: bool = False

# =============================================================================
class MarioGame(Game):
    
    WIDTH = 1000
    HEIGHT = 700
    HUD_HEIGHT = 70
    DURATION_SECONDS = 240.0
    SCROLL_SPEED = 150.0
    PLAYER_X = 220.0
    GROUND_Y = 560.0
    JUMP_DURATION = 0.82
    JUMP_HEIGHT = 145.0

    # -------------------------------------------------------------------------
    def __init__(self) -> None:

        super().__init__("mario", get_text("MENU_GAMES_MARIO"), self.DURATION_SECONDS)
        
        self.current_spm: float | None = None
        self.world_distance = 0.0
        self.jump_elapsed = 0.0
        self.jumping = False
        self.coins: list[Coin] = []
        self._next_coin_distance = 260.0

    # -------------------------------------------------------------------------
    def reset(self) -> None:

        self.current_spm = None
        self.world_distance = 0.0
        self.jump_elapsed = 0.0
        self.jumping = False
        self.coins = [Coin(x) for x in (440.0, 720.0, 1010.0, 1320.0)]
        self._next_coin_distance = 1600.0

    # -------------------------------------------------------------------------
    def update_game(self, dt: float, game_input: GameInput) -> None:
        
        self.current_spm = input_cadence(game_input)
        self.world_distance += self.SCROLL_SPEED * dt
        if game_input.stroke_event and not self.jumping:
            self.jumping = True
            self.jump_elapsed = 0.0

        if self.jumping:
            self.jump_elapsed += dt
            if self.jump_elapsed >= self.JUMP_DURATION:
                self.jumping = False
                self.jump_elapsed = 0.0
        
        while self._next_coin_distance < self.world_distance + self.WIDTH + 200:
            self.coins.append(Coin(self._next_coin_distance))
            self._next_coin_distance += 260.0
        
        for coin in self.coins:
            screen_x = coin.x - self.world_distance + self.PLAYER_X
            if not coin.collected and abs(screen_x - self.PLAYER_X) < 34:
                jump_height = self._jump_height()
                if jump_height > 35:
                    coin.collected = True
                    self.add_score(10)
        
        self.coins = [coin for coin in self.coins if not coin.collected and coin.x > self.world_distance - 100]

    # -------------------------------------------------------------------------
    def _jump_height(self) -> float:

        if not self.jumping:
            return 0.0
        
        phase = min(1.0, self.jump_elapsed / self.JUMP_DURATION)
        return math.sin(math.pi * phase) * self.JUMP_HEIGHT

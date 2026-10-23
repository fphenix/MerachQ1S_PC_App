"""Moteur de Ramio : course, sauts, terrain et pièces à collecter."""

from dataclasses import dataclass

import math

from setup.lang import get_text
from setup.utils import interpolate

from games.game import Game
from games.game_input import GameInput, input_cadence

# =============================================================================
@dataclass(slots=True)
class Coin:

    x: float
    y: float
    collected: bool = False

# =============================================================================
@dataclass(slots=True)
class Platform:

    x: float
    width: float
    top: float
    kind: str  # floating, linked, stairs

# =============================================================================
@dataclass(slots=True)
class Enemy:

    x: float
    y: float
    hit: bool = False

# =============================================================================
class MarioGame(Game):
    
    WIDTH: int = 1000
    HEIGHT: int = 700
    HUD_HEIGHT: int = 70
    DURATION_SECONDS: float = 240.0

    PLAYER_X: float = 220.0
    GROUND_Y: float = 560.0
    PLAYER_WIDTH: float = 38.0
    PLAYER_HEIGHT: float = 54.0

    RUN_CADENCE_TARGET: float = 24.0
    RUN_FULL_SPEED_FROM: float = 22.0
    RUN_HALF_SPEED_AT: float = 20.0
    RUN_STOP_AT: float = 18.0
    RUN_SPEED: float = 180.0

    JUMP_CADENCE_TARGET: float = 30.0
    JUMP_TRIGGER_FROM: float = 28.0
    JUMP_HEIGHT: float = 150.0
    JUMP_DURATION: float = 0.9

    LEVEL_LENGTH: float = 45000.0
    COIN_POINT: int = 10
    ENEMY_POINT_PENALTY: int = 5

    # -------------------------------------------------------------------------
    def __init__(self) -> None:

        super().__init__("mario", get_text("MENU_GAMES_MARIO"), self.DURATION_SECONDS)
        
        self.reset()

    # -------------------------------------------------------------------------
    def reset(self) -> None:

        self.current_spm: float | None = None
        self.world_distance: float = 0.0
        self.jump_elapsed: float = 0.0
        self.jumping: bool = False
        self.last_speed_factor: float = 0.0
        self.player_ground_y: float = self.GROUND_Y
        self._jump_requested: bool = False
        self._distance_score_awarded: int = 0

        self.coins: list[Coin] = []
        self.platforms: list[Platform] = []
        self.enemies: list[Enemy] = []

        self._level_reset()

    # -------------------------------------------------------------------------
    def _level_reset(self) -> None:

        # Un tronçon récurrent de niveau est répété jusqu'au château. Cela évite
        # que les 3 dernières minutes de jeu se déroulent dans un décor vide.
        platform_template = [
            (780, 240, 470, "floating"),
            (1380, 205, 480, "linked"),
            (1980, 230, 430, "floating"),
            (2700, 270, 470, "stairs"),
            (3480, 225, 440, "linked"),
            (4140, 270, 455, "floating"),
            (4860, 290, 455, "stairs"),
            (5640, 215, 420, "linked"),
            (6420, 270, 470, "floating"),
            (7200, 290, 455, "stairs"),
            (7980, 230, 430, "linked"),
            (8760, 270, 470, "floating"),
            (9600, 310, 455, "stairs"),
            (10500, 225, 425, "linked"),
            (11280, 275, 465, "floating"),
            (12120, 300, 455, "stairs"),
        ]
        coin_template = [
            (520, 455), (970, 420), (1180, 435), (1740, 440),
            (2160, 365), (2205, 345), (2250, 365), (3000, 400),
            (3780, 370), (3825, 350), (3870, 370), (4500, 410),
            (5280, 400), (6060, 360), (6105, 340), (6150, 360),
            (6780, 420), (7560, 390), (8400, 365), (9180, 420),
            (10080, 385), (10920, 360), (11760, 415), (12720, 390),
            (7080, 420), (7150, 365), (7220, 330), (7290, 365),
            (7360, 420), (7430, 365), (7500, 330), (7570, 365), (7640, 420),
            (10680, 390), (10750, 335), (10820, 300), (10890, 335),
            (10960, 390), (11030, 335), (11100, 300), (11170, 335), (11240, 390),
        ]
        enemy_template = (2460, 4260, 5940, 8220, 9900, 11880)

        segment_length = 13200.0
        segment_count = int(self.LEVEL_LENGTH // segment_length) + 1

        self.platforms = []
        self.coins = []
        self.enemies = []
        for segment_index in range(segment_count):
            offset = segment_index * segment_length
            for x, width, top, kind in platform_template:
                world_x = offset + x
                if world_x < self.LEVEL_LENGTH - 250:
                    self.platforms.append(Platform(world_x, width, top, kind))
            for x, y in coin_template:
                world_x = offset + x
                if world_x < self.LEVEL_LENGTH - 200:
                    self.coins.append(Coin(float(world_x), float(y)))
            for x in enemy_template:
                world_x = offset + x
                if world_x < self.LEVEL_LENGTH - 200:
                    self.enemies.append(Enemy(float(world_x), self.GROUND_Y - 30))

    # -------------------------------------------------------------------------
    def update_game(self, dt: float, game_input: GameInput) -> None:
        
        self.current_spm = input_cadence(game_input)
        cadence = self.current_spm or 0.0
        speed_factor = self._speed_factor(cadence)
        self.last_speed_factor = speed_factor

        # La course et le saut sont indépendants : le déplacement horizontal
        # continue pendant le saut. Le saut est déclenché sur un coup de rame.
        if game_input.stroke_event and cadence >= self.JUMP_TRIGGER_FROM and not self.jumping:
            self.jumping = True
            self.jump_elapsed = 0.0

        jump_height_before = self._jump_height()
        proposed_distance = self.world_distance + self.RUN_SPEED * speed_factor * dt
        current_feet = self.player_ground_y - jump_height_before

        # Seuls les murs / faces verticales du terrain lié bloquent le joueur.
        for platform in self.platforms:
            if platform.kind != "linked":
                continue
            wall_screen_x = platform.x - self.world_distance + self.PLAYER_X
            next_wall_screen_x = platform.x - proposed_distance + self.PLAYER_X
            if wall_screen_x >= self.PLAYER_X + self.PLAYER_WIDTH / 2 and next_wall_screen_x <= self.PLAYER_X + self.PLAYER_WIDTH / 2:
                if current_feet > platform.top + 8:
                    proposed_distance = max(
                        self.world_distance,
                        platform.x - self.PLAYER_WIDTH / 2,
                    )
                    break

        old_distance = self.world_distance
        self.world_distance = min(self.LEVEL_LENGTH, proposed_distance)

        previous_feet = self.player_ground_y - jump_height_before
        if self.jumping:
            self.jump_elapsed += dt
            if self.jump_elapsed >= self.JUMP_DURATION:
                self.jumping = False
                self.jump_elapsed = 0.0
        
        jump_height = self._jump_height()
        # Le joueur reste fixe à l'écran : en coordonnées du monde, sa
        # position est world_distance (PLAYER_X n'est que l'ancrage écran).
        player_center_x = self.world_distance
        current_feet = self.player_ground_y - jump_height

        # Atterrissage sur une plateforme traversée pendant la descente.
        landed_on_platform = False
        if self.jumping and current_feet >= previous_feet:
            for platform in self.platforms:
                if platform.kind == "stairs":
                    continue
                if platform.x <= player_center_x <= platform.x + platform.width:
                    if previous_feet <= platform.top <= current_feet:
                        self.player_ground_y = platform.top
                        self.jumping = False
                        self.jump_elapsed = 0.0
                        jump_height = 0.0
                        landed_on_platform = True
                        break

        # Les escaliers font monter progressivement le niveau du sol.
        on_stairs = False
        for platform in self.platforms:
            if platform.kind != "stairs" or not (platform.x <= player_center_x <= platform.x + platform.width):
                continue
            ratio = (player_center_x - platform.x) / platform.width
            self.player_ground_y = self.GROUND_Y - ratio * (self.GROUND_Y - platform.top)
            on_stairs = True
            break

        if not on_stairs and not landed_on_platform:
            on_top = any(
                platform.kind != "stairs"
                and platform.x <= player_center_x <= platform.x + platform.width
                and abs(self.player_ground_y - platform.top) < 1.0
                for platform in self.platforms
            )
            if not on_top and not self.jumping:
                self.player_ground_y = self.GROUND_Y

        player_y = self.player_ground_y - self.PLAYER_HEIGHT - jump_height
        
        # Les pièces sont des objets de collecte, jamais des plateformes.
        for coin in self.coins:
            if coin.collected:
                continue
            if abs(coin.x - player_center_x) < 30 and abs(coin.y - (player_y + self.PLAYER_HEIGHT / 2)) < 38:
                coin.collected = True
                self.add_score(self.COIN_POINT)

        for enemy in self.enemies:
            if enemy.hit or abs(enemy.x - player_center_x) > 28:
                continue
            if jump_height < 42:
                enemy.hit = True
                self.add_score(-self.ENEMY_POINT_PENALTY)

        # Le score de distance ne progresse qu'avec la distance réellement gagnée.
        distance_score = int(self.world_distance / 10)
        if distance_score > self._distance_score_awarded:
            self.add_score(distance_score - self._distance_score_awarded)
            self._distance_score_awarded = distance_score

    # -------------------------------------------------------------------------
    @classmethod
    def _speed_factor(cls, cadence: float) -> float:

        if cadence >= cls.RUN_FULL_SPEED_FROM:
            return 1.0
        if cadence <= cls.RUN_STOP_AT:
            return 0.0
        if cadence <= cls.RUN_HALF_SPEED_AT:
            return interpolate(cadence, cls.RUN_STOP_AT, 0.0, cls.RUN_HALF_SPEED_AT, 0.5)

        return interpolate(cadence, cls.RUN_HALF_SPEED_AT, 0.5, cls.RUN_FULL_SPEED_FROM, 1.0)

    # -------------------------------------------------------------------------
    def _jump_height(self) -> float:

        if not self.jumping:
            return 0.0
        
        phase = min(1.0, self.jump_elapsed / self.JUMP_DURATION)
        return math.sin(math.pi * phase) * self.JUMP_HEIGHT

    # -------------------------------------------------------------------------
    def on_finished(self) -> None:
        # La durée normale du jeu se termine devant le château, sans déplacer
        # le joueur artificiellement jusqu'à la fin du niveau.
        pass


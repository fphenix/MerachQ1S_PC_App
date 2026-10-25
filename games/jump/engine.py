"""Moteur du jeu Jump, inspiré du Dino Runner."""

from dataclasses import dataclass

import random

from setup.lang import get_text
from setup.utils import is_within, is_between, clamp_to_zero

from games.game import Game
from games.game_input import GameInput, input_cadence

# =============================================================================
@dataclass(slots=True)
class Obstacle:

    x: float
    kind: str
    resolved: bool = False
    jump_type: str | None = None

# =============================================================================
@dataclass(slots=True)
class Flower:
    
    x: float
    rare: bool = False
    resolved: bool = False

# =============================================================================
class JumpGame(Game):

    GAME_ID: str = "jump"

    WIDTH: int = 1000
    HEIGHT: int = 700
    HUD_HEIGHT: int = 70
    DURATION_SECONDS: float = 240.0
    
    PLAYER_X: float = 175.0
    PLAYER_GROUND_Y: float = 565.0
    PLAYER_WIDTH: float = 54.0
    PLAYER_HEIGHT: float = 64.0
    SCROLL_SPEED: float = 145.0
    ZONE_DURATION_MIN: float = 20.0 # seconds
    ZONE_DURATION_MAX: float = 45.0 # seconds
    OBSTACLE_TRAVEL_SECONDS: float = (WIDTH + 20.0 - (PLAYER_X + PLAYER_WIDTH)) / SCROLL_SPEED
    ZONE_WEIGHTS: list[tuple[str, int]] = [("slow", 1), ("medium", 3), ("fast", 2)]
    RARE_FLOWER_FREQ: float = 5.0 # in percent
    JUMP_TRIGGER_DISTANCE: float = 55.0 # pix
    CADENCE_HOLD_SECONDS: float = 5.0 # seconds
    CADENCE_OBSTACLE_MARGIN: float = 2.0
    CADENCE_RUN_MARGIN: float = 2.0
    CADENCE_RARE_FLOWER_MARGIN: float = 1.5
    FIRST_FLOWER_DELAY_SECONDS: float = 4.0
    FIRST_OBSTACLE_DELAY_SECONDS: float = 7.0 # seconds
    ZONE_TRANSITION_GAP_SECONDS: float = 3.5 # seconds
    MIN_OBSTACLE_GAP_SECONDS: float = 3.8 # seconds
    MAX_OBSTACLES_PER_ZONE: int = 6 # number
    SIMPLE_JUMP_DURATION: float = 0.72
    DOUBLE_JUMP_DURATION: float = 0.98
    SIMPLE_JUMP_HEIGHT: float = 76.0
    DOUBLE_JUMP_HEIGHT: float = 154.0

    CADENCE_RUN: int = 22.0 # CPM
    CADENCE_ROCK: float = 26.0 # CPM
    CADENCE_CACTUS: float = 30.0 # CPM
    CADENCE_RARE_FLOWER: float = 18.0 # CPM

    POINTS_ROCK: int = 15
    POINTS_CACTUS: int = 30
    POINTS_NONE: int = 10
    POINTS_RARE_FLOWER: int = 100

    # -------------------------------------------------------------------------
    def __init__(self) -> None:

        super().__init__(
            game_id= self.GAME_ID,
            title= get_text("MENU_GAMES_JUMP"),
            duration= self.DURATION_SECONDS
        )

        self.reset()

    # -------------------------------------------------------------------------
    def reset(self) -> None:

        self.current_spm: float | None = None
        self._last_valid_spm: float | None = None
        self._cadence_hold_remaining: float = 0.0
        self.scroll_offset: float = 0.0
        self.obstacles: list[Obstacle] = []
        self.flowers: list[Flower] = []
        self.zone_kind: str = self._choose_zone_kind()
        self.next_zone_kind: str = self._choose_zone_kind(previous=self.zone_kind)
        self.zone_duration: float = random.uniform(self.ZONE_DURATION_MIN, self.ZONE_DURATION_MAX)
        self.zone_elapsed: float = 0.0
        self._zone_obstacle_times: list[float] = self._make_zone_obstacle_times(self.zone_duration)
        self._zone_obstacles_spawned: int = 0
        self._flower_spawn_remaining: float = random.uniform(3.0, 5.0)
        self.jump_type: str | None = None
        self.jump_elapsed: float = 0.0
        self.jump_duration: float = 0.0
        self.jump_height: float = 0.0
        self._score_popups: list[tuple[float, float, int, float]] = [] # x, y, points, age

    # -------------------------------------------------------------------------
    def update_game(self, dt: float, game_input: GameInput) -> None:

        measured_spm = input_cadence(game_input)
        if measured_spm is not None:
            self._last_valid_spm = measured_spm
            self._cadence_hold_remaining = self.CADENCE_HOLD_SECONDS
            self.current_spm = measured_spm
        else:
            self._cadence_hold_remaining = clamp_to_zero(self._cadence_hold_remaining - dt)
            self.current_spm = self._last_valid_spm if self._cadence_hold_remaining > 0.0 else None
        # Ne pas reboucler à 1000 px : les couches de montagnes ont leur propre
        # modulo. Le rebouclage ici provoquait un saut visuel.
        self.scroll_offset += self.SCROLL_SPEED * dt

        if self.jump_type is not None:
            self.jump_elapsed += dt
            if self.jump_elapsed >= self.jump_duration:
                self.jump_type = None
                self.jump_elapsed = 0.0
                self.jump_height = 0.0

        self.zone_elapsed += dt

        # Plusieurs obstacles/événements par zone. Le premier n'arrive qu'après
        # 10 s, afin de laisser le temps au joueur d'adopter la nouvelle cadence.
        while (
            self._zone_obstacles_spawned < len(self._zone_obstacle_times)
            and self.zone_elapsed >= self._zone_obstacle_times[self._zone_obstacles_spawned]
        ):
            kind = {"slow": "empty", "medium": "rock", "fast": "cactus"}[self.zone_kind]
            self.obstacles.append(Obstacle(x=self.WIDTH + 20.0, kind=kind))
            self._zone_obstacles_spawned += 1

        # Chaque événement vide rapporte 10 points si la cadence lente est
        # tenue au passage du point de validation. Les rochers/cactus se
        # valident au passage du joueur après le saut correspondant.
        active_obstacle = any(not obstacle.resolved for obstacle in self.obstacles)

        # La transition attend que tous les obstacles déjà créés soient résolus.
        if (
            self.zone_elapsed >= self.zone_duration
            and self._zone_obstacles_spawned >= len(self._zone_obstacle_times)
            and not active_obstacle
        ):
            self.zone_kind = self.next_zone_kind
            self.next_zone_kind = self._choose_zone_kind(previous=self.zone_kind)
            self.zone_duration = random.uniform(self.ZONE_DURATION_MIN, self.ZONE_DURATION_MAX)
            self.zone_elapsed = 0.0
            self._zone_obstacle_times = self._make_zone_obstacle_times(self.zone_duration)
            self._zone_obstacles_spawned = 0

        self._flower_spawn_remaining -= dt
        if self._flower_spawn_remaining <= 0.0:
            # Les fleurs rares restent volontairement très inhabituelles.
            rare = random.random() < (self.RARE_FLOWER_FREQ / 100.0)
            self.flowers.append(Flower(self.WIDTH + 15.0, rare=rare))
            self._flower_spawn_remaining = random.uniform(8.0, 14.0) if rare else random.uniform(3.5, 5.5)

        for obstacle in self.obstacles:
            obstacle.x -= self.SCROLL_SPEED * dt
            distance = obstacle.x - self.PLAYER_X
            # Le saut est automatique : la cadence choisit le type de saut.
            # Le déclenchement est proche de l'obstacle pour éviter un saut trop tôt.
            if (
                obstacle.kind in ("rock", "cactus")
                and self.jump_type is None
                and obstacle.jump_type is None
                and not obstacle.resolved
                and is_between(distance, 20.0, self.JUMP_TRIGGER_DISTANCE)
            ):
                cadence = self.current_spm
                if obstacle.kind == "rock" and cadence is not None and is_within(cadence, self.CADENCE_ROCK, self.CADENCE_OBSTACLE_MARGIN):
                    self._start_jump("simple", obstacle)
                elif obstacle.kind == "cactus" and cadence is not None and is_within(cadence, self.CADENCE_CACTUS, self.CADENCE_OBSTACLE_MARGIN):
                    self._start_jump("double", obstacle)

            if not obstacle.resolved and obstacle.x <= self.PLAYER_X + self.PLAYER_WIDTH:
                obstacle.resolved = True
                if obstacle.kind == "empty":
                    if self.current_spm is not None and is_within(self.current_spm, self.CADENCE_RUN, self.CADENCE_RUN_MARGIN):
                        self.add_score(self.POINTS_NONE)
                        # x, y, points, age
                        self._score_popups.append((
                            self.PLAYER_X + 20.0, self.PLAYER_GROUND_Y - 35.0,
                            self.POINTS_NONE,
                            0.0
                        ))
                else:
                    correct_jump = (
                        (obstacle.kind == "rock" and obstacle.jump_type == "simple")
                        or (obstacle.kind == "cactus" and obstacle.jump_type == "double")
                    )
                    if correct_jump:
                        points = self.POINTS_ROCK if obstacle.kind == "rock" else self.POINTS_CACTUS
                        self.add_score(points)
                        # x, y, points, age
                        self._score_popups.append((
                            obstacle.x, self.PLAYER_GROUND_Y - 80.0,
                            points,
                            0.0
                        ))

        for flower in self.flowers:
            flower.x -= self.SCROLL_SPEED * dt
            if (
                not flower.resolved
                and flower.x <= self.PLAYER_X + self.PLAYER_WIDTH
                and flower.x + 12.0 >= self.PLAYER_X
            ):
                flower.resolved = True
                if flower.rare and self.current_spm is not None and is_within(self.current_spm, self.CADENCE_RARE_FLOWER, self.CADENCE_RARE_FLOWER_MARGIN):
                    self.add_score(self.POINTS_RARE_FLOWER)
                    # x, y, points, _age
                    self._score_popups.append((
                        flower.x, self.PLAYER_GROUND_Y - 35.0,
                        100,
                        0.0
                    ))

        self.obstacles = [obs for obs in self.obstacles if obs.x > -90.0]
        self.flowers = [flo for flo in self.flowers if flo.x > -35.0]
        updated_popups = []
        for x, y, points, age in self._score_popups:
            age += dt
            if age < 1.0:
                updated_popups.append((x - self.SCROLL_SPEED * dt, y - 38.0 * dt, points, age))
        self._score_popups = updated_popups

    # -------------------------------------------------------------------------
    @classmethod
    def _make_zone_obstacle_times(cls, duration: float) -> list[float]:
        """Crée 2 à 6 événements, espacés et hors du début de la zone."""
 
        first = cls.FIRST_OBSTACLE_DELAY_SECONDS
        transition_spawn_time = duration - (cls.WIDTH + 20.0) / cls.SCROLL_SPEED
        last = transition_spawn_time - cls.ZONE_TRANSITION_GAP_SECONDS
        if last <= first:
            return [first]
        
        max_count = min(
            cls.MAX_OBSTACLES_PER_ZONE,
            int((last - first) // cls.MIN_OBSTACLE_GAP_SECONDS) + 1,
        )
        count = random.randint(min(2, max_count), max_count)
        if count == 1:
            return [first]
        
        available = last - first - cls.MIN_OBSTACLE_GAP_SECONDS * (count - 1)
        # Distribuer les événements sur la zone avec une marge aléatoire,
        # tout en garantissant l'espacement minimal.
        slack = sorted(random.uniform(0.0, available) for _ in range(count - 1))
        times = [first]
        for index in range(1, count):
            times.append(first + index * cls.MIN_OBSTACLE_GAP_SECONDS + slack[index - 1])
        # La formule précédente peut concentrer la fin : trier et recaler en
        # avant garantit que le dernier événement reste dans la fenêtre.
        times = sorted(times)
        if times[-1] > last:
            shift = times[-1] - last
            times = [max(first + i * cls.MIN_OBSTACLE_GAP_SECONDS, t - shift) for i, t in enumerate(times)]

        return times

    # -------------------------------------------------------------------------
    @classmethod
    def _choose_zone_kind(cls, previous: str | None = None) -> str:
        """Choisit une zone pondérée, sans répéter la précédente."""

        choices = [item for item in cls.ZONE_WEIGHTS if item[0] != previous]
        kinds, weights = zip(*choices)
        return random.choices(kinds, weights=weights, k=1)[0]

    # -------------------------------------------------------------------------
    def _start_jump(self, jump_type: str, obstacle: Obstacle) -> None:

        self.jump_type = jump_type
        self.jump_elapsed = 0.0
        if jump_type == "simple":
            self.jump_duration = self.SIMPLE_JUMP_DURATION
            self.jump_height = self.SIMPLE_JUMP_HEIGHT
        else:
            self.jump_duration = self.DOUBLE_JUMP_DURATION
            self.jump_height = self.DOUBLE_JUMP_HEIGHT
        obstacle.jump_type = jump_type

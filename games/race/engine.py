"""Moteur commun des courses de rameur (1000 m et 2000 m)."""

from dataclasses import dataclass
import random

from setup.lang import get_text
from setup.utils import clamp_between, clamp_to_zero, interpolate

from games.game import Game
from games.game_input import GameInput, input_cadence

# =============================================================================
@dataclass(slots=True)
class Boat:
    
    name: str
    distance: float
    lane: int
    color: str
    is_player: bool = False
    speed: float = 0.0
    stroke_timer: float = 0.0
    stroke_period: float = 2.4
    variation: float = 0.0
    fatigue: float = 0.0
    base_cadence: float = 25.0

# =============================================================================
class RaceGame(Game):

    WIDTH: int = 1000
    HEIGHT: int = 700
    HUD_HEIGHT: int = 70
    MAX_DURATION_SECONDS: float = 900.0 # 900sec is 15 minutes, we must be well enough for a 2k race

    PLAYER_X: float = 400.0

    # Configurable : conseillé: 1, 2 ou 4 adversaires (soit 2, 3 ou 5 bateaux au total).
    OPPONENT_COUNT_1000: int = 2
    OPPONENT_COUNT_2000: int = 4

    # Repères indicatifs de temps sur 2000 m, en fonction du niveau normalisé.
    # Le niveau 0.35 est calibré autour du résultat utilisateur (~7 min 55 s).
    LEVEL_TIME_2000: list[tuple[float, float]] = [
        (0.00, 660.0),
        (0.10, 600.0),
        (0.20, 550.0),
        (0.35, 480.0),
        (0.50, 435.0),
        (0.65, 395.0),
        (0.80, 370.0),
        (0.90, 355.0),
        (1.00, 340.0),
    ]

    BOAT_MIN_FACTOR: float = 0.72
    BOAT_MAX_FACTOR: float = 1.15
    BOAT_REF_CADENCE: float = 25.0
    BOAT_FACTOR_MULTIPLIER: float = 0.012

    PLAYER_STROKE_TIMEOUT_SECONDS: float = 4.0
    PLAYER_STROKE_IMPULSE: float = 1.06
    STROKE_IMPULSE_DECAY_PER_SECOND: float = 4.0
    PLAYER_SPEED_SMOOTHING_PER_SECOND: float = 2.4
    FINISH_TIMEOUT_MARGIN_SECONDS: float = 15.0
    OPPONENT_REFERENCE_CADENCE: float = BOAT_REF_CADENCE
    OPPONENT_CADENCE_VARIATION: float = 2.0
    OPPONENT_SPEED_PER_CPM: float = 0.012

    # -------------------------------------------------------------------------
    def __init__(
        self,
        distance_m: int,
        game_id: str,
        title_key: str
    ) -> None:

        self.race_distance = float(distance_m)

        super().__init__(game_id, get_text(title_key), self.MAX_DURATION_SECONDS)

        self.profile_level_norm: float = 0.35

        self.reset()

    # -------------------------------------------------------------------------
    def reset(self) -> None:

        self.current_spm: float | None = None
        self.race_elapsed: float = 0.0
        self.countdown_elapsed: float = 0.0
        self.countdown_finished: bool = False
        self.player_won: bool | None = None
        self._race_started: bool = False
        self._stroke_elapsed: float = 0.0
        self.stroke_impulse: float = 0.0
        self.nb_opponents: int = (
            self.OPPONENT_COUNT_1000
            if self.game_id == "race_1000"
            else self.OPPONENT_COUNT_2000
        )
        self.boats: list[Boat] = []

        total_boats = self.nb_opponents + 1
        player_lane = (total_boats - 1) // 2
        self.boats.append(Boat("PLAYER", 0.0, player_lane, "#48d9ff", True))

        colors = ("#ffbd59", "#91e38f", "#ef6262", "#b69cff")
        opponent_lanes = [lane for lane in range(total_boats) if lane != player_lane]
        for index, lane in enumerate(opponent_lanes):
            self.boats.append(Boat(
                name=f"ADV_{index + 1}",
                distance=0.0,
                lane=lane,
                color=colors[index % len(colors)],
            ))

        # Adversaires déterministes pour calibrer la difficulté : un légèrement
        # plus rapide que la référence, puis un légèrement plus lent.
        reference = self.reference_time_2000(self.profile_level_norm)
        distance_factor = self.race_distance / 2000.0
        speed_factors = (0.98, 1.02, 0.96, 1.04)
        for index, boat in enumerate(self.boats[1:]):
            target_time = reference * distance_factor * speed_factors[index % len(speed_factors)]
            boat.speed = self.race_distance / target_time
            boat.fatigue = 0.0
            boat.base_cadence = self.OPPONENT_REFERENCE_CADENCE
            boat.stroke_timer = 0.0
            self._set_opponent_stroke(boat)

    # -------------------------------------------------------------------------
    def _set_opponent_stroke(self, boat: Boat) -> None:
        cadence = random.uniform(
            boat.base_cadence - self.OPPONENT_CADENCE_VARIATION,
            boat.base_cadence + self.OPPONENT_CADENCE_VARIATION,
        )
        boat.stroke_period = 60.0 / cadence
        boat.variation = (cadence - boat.base_cadence) * self.OPPONENT_SPEED_PER_CPM

    # -------------------------------------------------------------------------
    def set_profile_level(self, level: float) -> None:
        self.profile_level_norm = clamp_between(float(level), 0.0, 1.0)

    # -------------------------------------------------------------------------
    @classmethod
    def reference_time_2000(cls, level: float) -> float:

        level = clamp_between(level, 0.0, 1.0)

        for index in range(1, len(cls.LEVEL_TIME_2000)):
            level0, time0 = cls.LEVEL_TIME_2000[index - 1]
            level1, time1 = cls.LEVEL_TIME_2000[index]
            if level <= level1:
                return interpolate(level, level0, time0, level1, time1)
           
        return cls.LEVEL_TIME_2000[-1][1]

    # -------------------------------------------------------------------------
    @property
    def player_boat(self) -> Boat:
        return self.boats[0]

    # -------------------------------------------------------------------------
    def hud_score_text(self) -> str:
        distance = min(self.race_distance, self.player_boat.distance) if self.boats else 0.0
        return f"{get_text('DISTANCE')}: {distance:5.0f} m"

    # -------------------------------------------------------------------------
    def hud_time_text(self) -> str:
        seconds = int(self.race_elapsed)
        return f"{get_text('TIME')}: {seconds // 60:02d}:{seconds % 60:02d}"

    # -------------------------------------------------------------------------
    def update_game(self, dt: float, game_input: GameInput) -> None:

        self.current_spm = input_cadence(game_input)

        if not self.countdown_finished:
            self.countdown_elapsed += dt
            if self.countdown_elapsed >= 3.5:
                self.countdown_finished = True
                self._race_started = True
            return

        self.race_elapsed += dt
        self._stroke_elapsed += dt
        if game_input.stroke_event:
            self._stroke_elapsed = 0.0
            self.stroke_impulse = 1.0
            self.player_boat.stroke_timer = 0.0
        else:
            self.player_boat.stroke_timer += dt
            self.stroke_impulse *= clamp_between(1.0 - dt * self.STROKE_IMPULSE_DECAY_PER_SECOND, 0.0, 1.0)
        player = self.player_boat

        # Le niveau calibre l'adversaire ; la cadence instantanée modifie la vitesse du joueur.
        # 24 CPM correspond au point de calibration, avec une progression modérée autour.
        cadence = self.current_spm or 0.0
        if cadence > 0.0:
            player.stroke_period = 60.0 / cadence
        cadence_factor = clamp_between(
            1.0 + (cadence - self.BOAT_REF_CADENCE) * self.BOAT_FACTOR_MULTIPLIER,
            self.BOAT_MIN_FACTOR,
            self.BOAT_MAX_FACTOR
        )
        target_player_speed = self.race_distance / (
            self.reference_time_2000(self.profile_level_norm) * self.race_distance / 2000.0
        ) * cadence_factor
        if self._stroke_elapsed > self.PLAYER_STROKE_TIMEOUT_SECONDS or cadence <= 0.0:
            target_player_speed = 0.0

        # Impulsion à chaque coup de rame, puis retour progressif vers l'allure moyenne.
        if game_input.stroke_event:
            player.speed = max(player.speed, target_player_speed * self.PLAYER_STROKE_IMPULSE)
        player.speed += (target_player_speed - player.speed) * clamp_between(dt * self.PLAYER_SPEED_SMOOTHING_PER_SECOND, 0.0, 1.0)
        player.distance += clamp_to_zero(player.speed) * dt

        for boat in self.boats[1:]:
            boat.stroke_timer += dt
            if boat.stroke_timer >= boat.stroke_period:
                boat.stroke_timer %= boat.stroke_period
                # Chaque coup reçoit une cadence légèrement différente autour
                # de la cadence de base, puis garde son effet jusqu'au suivant.
                self._set_opponent_stroke(boat)
            boat.distance += clamp_to_zero(boat.speed * (1.0 + boat.variation - boat.fatigue)) * dt

        finishers = [boat for boat in self.boats if boat.distance >= self.race_distance]
        if finishers:
            # Estime le premier franchissement lorsque plusieurs bateaux dépassent
            # la ligne dans la même frame.
            winner = min(
                (boat for boat in self.boats if boat.distance >= self.race_distance),
                key=lambda boat: (boat.distance - self.race_distance) / max(boat.speed, 0.01),
            )
            self.player_won = winner.is_player
            self.score = int(round(self.race_elapsed)) if self.player_won else 0
            self.finished = True
            self.phase = self.PHASE_FINISHED
            self.phase_elapsed = 0.0

        elif self.race_elapsed >= self.MAX_DURATION_SECONDS - self.FINISH_TIMEOUT_MARGIN_SECONDS:
            self.player_won = False
            self.score = 0
            self.finished = True
            self.phase = self.PHASE_FINISHED
            self.phase_elapsed = 0.0

    # -------------------------------------------------------------------------
    def hud_result_text(self) -> str:

        if self.player_won is None:
            return ""
        
        if self.player_won:
            minutes, seconds = divmod(int(self.score), 60)
            return f"{get_text('GAME_RACE_WON')}  {minutes:02d}:{seconds:02d}"

        return get_text("GAME_RACE_LOST")

    # -------------------------------------------------------------------------
    def records_score(self) -> bool:
        return self.player_won is True

# =============================================================================
class Race1000Game(RaceGame):
    def __init__(self) -> None:
        super().__init__(1000, "race_1000", "MENU_GAMES_RACE_1000")

# =============================================================================
class Race2000Game(RaceGame):
    def __init__(self) -> None:
        super().__init__(2000, "race_2000", "MENU_GAMES_RACE_2000")

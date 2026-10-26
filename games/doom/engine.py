""" Doom : avancer à cadence modérée, accélérer pour tirer. """

from dataclasses import dataclass

import math
import random
from enum import Enum

from setup.lang import get_text
from setup.utils import (
    clamp_to_zero, clamp_between,
    clamp_to_max, clamp_to_min,
    is_between, is_within,
    format_duration,
)

from games.game import Game
from games.game_input import GameInput, input_cadence

# =============================================================================
@dataclass
class Monster:
    
    kind: "DoomGame.MonsterType"
    hits: int
    side: int
    blood: int

    remaining: float
    approach_progress: float

    # -------------------------------------------------------------------------
    @property
    def is_alive(self) -> bool:
        return self.hits > 0

# =============================================================================
class DoomGame(Game):

    GAME_ID: str = "doom"

    WIDTH: int = 1000
    HEIGHT: int = 700
    HUD_HEIGHT: int = 0 # Doom possède son propre HUD en bas de l'écran.
    LEVEL_DURATION_SECONDS: float = 300.0
    BOSS_APPROACH_SECONDS: float = 3.0
    BOSS_DURATION_SECONDS: float = 35.0
    DURATION_SECONDS: float = (
        LEVEL_DURATION_SECONDS + BOSS_APPROACH_SECONDS + BOSS_DURATION_SECONDS
    )

    MOVE_CADENCE: float = 24.0
    MOVE_TOLERANCE_LOW: float = 5.0
    MOVE_TOLERANCE_HIGH: float = 5.0

    FIRE_CADENCE: float = 32.0
    FIRE_TOLERANCE: float = 3.0

    BOSS_CADENCE: float = 34.0
    BOSS_CADENCE_TOLERANCE: float = 2.0

    EXPLORE_MIN_SECONDS: float = 15.0
    EXPLORE_MAX_SECONDS: float = 30.0
    COMBAT_SECONDS: float = 20.0
    SHOT_INTERVAL: float = 60.0 / FIRE_CADENCE
    TURN_DURATION: float = 6.4
    MAX_INJURIES: int = 5

    ARMORED_SPAWN_PERCENT: float = 40.0
    BOSS_HITS_REQUIRED: int = 12
    MONSTER_LIVES_ARMORED: int = 5
    MONSTER_LIVES_FAST: int = 3

    class MonsterType(Enum):
        ARMORED: str = "armored"
        FAST: str = "fast"

    class GamePhase(Enum):
        EXPLORE: str = "explore"
        COMBAT: str = "combat"
        BOSSFIGHT: str = "boss"

    # -------------------------------------------------------------------------
    def __init__(self) -> None:

        super().__init__(
            game_id= self.GAME_ID,
            title= get_text("MENU_GAMES_DOOM"),
            duration= self.DURATION_SECONDS
        )

        self.reset()

    # -------------------------------------------------------------------------
    def reset(self) -> None:

        self.current_spm: float | None = None
        self.kills: int = 0
        self.injuries: int = 0
        self.enemies: list[Monster] = []
        self.phase_name: DoomGame.GamePhase = self.GamePhase.EXPLORE
        self.explore_remaining: float = random.uniform(self.EXPLORE_MIN_SECONDS, self.EXPLORE_MAX_SECONDS)
        self.combat_remaining: float = 0.0
        self.shot_flash: float = 0.0
        self.hit_flash: float = 0.0
        self.bullet_progress: float = 0.0
        self._shot_elapsed: float = 0.0
        self.world_distance: float = 0.0
        self.turn_progress: float = 0.0
        self.turn_direction: int = random.choice((-1, 1))
        self.next_turn_distance: float = random.uniform(8.0, 14.0)
        self.turn_start_distance: float = clamp_to_zero(self.next_turn_distance - 2.0)
        self.room_open: bool = False
        self.room_progress: float = 0.0
        self.message_key: str = "GAME_DOOM_EXPLORE"
        self.score: int = 0
        self.boss_remaining: float = self.BOSS_DURATION_SECONDS
        self.boss_approach_duration: float = self.BOSS_APPROACH_SECONDS
        self.boss_approach_elapsed: float = 0.0
        self.boss_defeated: bool = False
        self.boss_hits: int = 0

    # -------------------------------------------------------------------------
    def update_game(self, dt: float, game_input: GameInput) -> None:

        self.current_spm = input_cadence(game_input)
        self.shot_flash = clamp_to_zero(self.shot_flash - dt)
        self.hit_flash = clamp_to_zero(self.hit_flash - dt)
        cadence = self.current_spm or 0.0

        is_explore_cadence = is_between(
            cadence,
            self.MOVE_CADENCE - self.MOVE_TOLERANCE_LOW,
            self.MOVE_CADENCE + self.MOVE_TOLERANCE_HIGH
        )
        is_combat_cadence = (cadence > (self.FIRE_CADENCE - self.FIRE_TOLERANCE))
        is_boss_cadence = is_within(cadence, self.BOSS_CADENCE, self.BOSS_CADENCE_TOLERANCE)

        # Après les 300 secondes de niveau, le boss impose 35 secondes à 34 SPM.
        if (
            self.elapsed >= self.LEVEL_DURATION_SECONDS
            and self.phase_name != self.GamePhase.BOSSFIGHT
        ):
            # Le boss remplace immédiatement tout ennemi en cours de combat.
            self.phase_name = self.GamePhase.BOSSFIGHT
            self.boss_remaining = self.BOSS_DURATION_SECONDS
            self.boss_approach_elapsed = 0.0
            self.boss_hits = 0
            self.enemies.clear()
            self._shot_elapsed = 0.0
            self.bullet_progress = 0.0
            self.shot_flash = 0.0
            self.message_key = "GAME_DOOM_BOSS"

        # Boss Fight
        if self.phase_name == self.GamePhase.BOSSFIGHT:
            # Le Cacodemon entre depuis le fond du couloir pendant trois secondes.
            # Ce temps d'arrivée ne consomme pas les 35 secondes du combat.
            if self.boss_approach_elapsed < self.boss_approach_duration:
                self.boss_approach_elapsed = min(
                    self.boss_approach_duration,
                    self.boss_approach_elapsed + dt,
                )
                self._shot_elapsed = 0.0
                self.bullet_progress = 0.0
                self.shot_flash = 0.0
                self.message_key = "GAME_DOOM_BOSS"
                return

            self.boss_remaining = clamp_to_zero(self.boss_remaining - dt)

            if game_input.stroke_event:
                if is_boss_cadence:
                    stroke_count = clamp_to_min(game_input.stroke_delta, 1)
                    self.boss_hits += stroke_count
                    self.shot_flash = 0.12
                    self.bullet_progress = 1.0
                else:
                    self.injuries += clamp_to_min(game_input.stroke_delta, 1)
                    self.hit_flash = 0.7

            # Boss fight result
            if self.boss_remaining <= 0.0:
                self.boss_defeated = (self.boss_hits >= self.BOSS_HITS_REQUIRED)
                self.message_key = (
                    "GAME_DOOM_BOSS_VICTORY" if self.boss_defeated else "GAME_OVER"
                )
                self.score = self.kills
                self.finished = True
                self.phase = self.Phase.FINISHED
                self.phase_elapsed = 0.0

            return

        # Exploration
        if self.phase_name == self.GamePhase.EXPLORE:
            self.message_key = (
                "GAME_DOOM_EXPLORE"
                if is_explore_cadence
                else "GAME_DOOM_ROW_TO_MOVE"
            )
            if is_explore_cadence:
                self.world_distance += dt
                self.explore_remaining -= dt
                # Animation complète entrée -> apex -> sortie. Le virage suivant
                # n'est programmé qu'après la fin de cette fenêtre.
                turn_duration = self.TURN_DURATION
                turn_end_distance = self.turn_start_distance + turn_duration
                if self.world_distance < self.turn_start_distance:
                    self.turn_progress = 0.0
                elif self.world_distance < turn_end_distance:
                    progress = (self.world_distance - self.turn_start_distance) / turn_duration
                    self.turn_progress = math.sin(math.pi * progress)
                else:
                    self.turn_progress = 0.0
                    self.turn_direction = random.choice((-1, 1))
                    self.next_turn_distance = self.world_distance + random.uniform(12.0, 18.0)
                    self.turn_start_distance = self.next_turn_distance - (self.TURN_DURATION / 2)

                # Une pièce s'ouvre progressivement puis se referme : pas de saut
                # brutal de largeur au changement d'intervalle.
                room_cycle = int(self.world_distance // 38.0) % 3
                room_phase = (self.world_distance % 38.0) / 38.0
                self.room_open = room_cycle == 1 and is_between(room_phase, 0.0, 1.0, True, True)
                self.room_progress = room_phase

                if (
                    is_between(self.explore_remaining, 0.0, 3.5, True)
                    and not self.enemies
                ):
                    self._spawn_approaching_enemy()
                elif self.enemies and self.phase_name == self.GamePhase.EXPLORE:
                    for enemy in self.enemies:
                        enemy.approach_progress = clamp_between(
                            1.0 - self.explore_remaining / 3.5,
                            0.0, 1.0
                        )

                if self.explore_remaining <= 0.0:
                    self._start_encounter()
            return

        # Combat
        # L'ennemi est immobile. Le temps de combat s'écoule même si la cadence
        # n'est pas suffisante : il faut tirer efficacement dans le temps imparti.
        self.combat_remaining = clamp_to_zero(self.combat_remaining - dt)
        self.message_key = (
            "GAME_DOOM_FIRE"
            if is_combat_cadence
            else "GAME_DOOM_ROW_TO_MOVE"
        )
        if is_combat_cadence:
            self._shot_elapsed += dt
            self.bullet_progress = clamp_to_max(self._shot_elapsed / self.SHOT_INTERVAL, 1.0)
            while self._shot_elapsed >= self.SHOT_INTERVAL and self.enemies:
                self._shot_elapsed -= self.SHOT_INTERVAL
                self.bullet_progress = 0.0
                self.shot_flash = 0.15
                self._hit_enemy()
        else:
            self._shot_elapsed = 0.0
            self.bullet_progress = 0.0

        if not self.enemies:
            self._resume_exploration()

        elif self.combat_remaining <= 0.0:
            self.enemies.clear()
            self.injuries += 1
            self.hit_flash = 0.7
            self.message_key = "GAME_DOOM_INJURY"
            self._resume_exploration()

    # -------------------------------------------------------------------------
    def _spawn_approaching_enemy(self) -> None:

        armored: bool = random.random() < (self.ARMORED_SPAWN_PERCENT / 100.0)
        self.enemies = [Monster(
            kind= self.MonsterType.ARMORED if armored else self.MonsterType.FAST,
            hits= self.MONSTER_LIVES_ARMORED if armored else self.MONSTER_LIVES_FAST,
            side= random.choice((-1, 1)),
            blood= 0,
            remaining= self.COMBAT_SECONDS,
            approach_progress= 0.0,
        )]
        self.message_key = "GAME_DOOM_ENEMY_ARMORED" if armored else "GAME_DOOM_ENEMY_FAST"

    # -------------------------------------------------------------------------
    def _start_encounter(self) -> None:

        if not self.enemies:
            self._spawn_approaching_enemy()

        for enemy in self.enemies:
            enemy.approach_progress = 1.0

        self.phase_name = self.GamePhase.COMBAT
        self.combat_remaining = self.enemies[0].remaining if self.enemies else self.COMBAT_SECONDS
        self._shot_elapsed = 0.0
        self.bullet_progress = 0.0
        enemy_kind = self.enemies[0].kind if self.enemies else self.MonsterType.FAST
        self.message_key = (
            "GAME_DOOM_ENEMY_ARMORED"
            if enemy_kind == self.MonsterType.ARMORED
            else "GAME_DOOM_ENEMY_FAST"
        )

    # -------------------------------------------------------------------------
    def _resume_exploration(self) -> None:

        self.phase_name = self.GamePhase.EXPLORE
        self.enemies.clear()
        self.explore_remaining = random.uniform(self.EXPLORE_MIN_SECONDS, self.EXPLORE_MAX_SECONDS)
        self._shot_elapsed = 0.0
        self.bullet_progress = 0.0
        self.message_key = "GAME_DOOM_EXPLORE"

    # -------------------------------------------------------------------------
    def _hit_enemy(self) -> None:

        if not self.enemies:
            return

        enemy = self.enemies[0]
        enemy.hits -= 1
        enemy.blood += 1
        if not enemy.is_alive:
            self.enemies.clear()
            self.kills += 1
            self.score = self.kills

    # -------------------------------------------------------------------------
    def hud_score_text(self) -> str:
        return f"{get_text('GAME_DOOM_KILLS')}: {self.kills:03d}   {get_text('GAME_DOOM_INJURIES')}: {self.injuries:03d}"

    # -------------------------------------------------------------------------
    def hud_result_text(self) -> str:
        result = (
            get_text("GAME_RACE_WON")
            if self.boss_defeated
            else f"{get_text('GAME_OVER')} — {get_text('GAME_RACE_LOST')}"
        )
        score = (
            f"{get_text('GAME_DOOM_KILLS')}: {self.kills:03d}   |   "
            f"{get_text('GAME_DOOM_INJURIES')}: {self.injuries:03d}"
        )
        return f"{result}\n{score}"

    # -------------------------------------------------------------------------
    def hud_time_text(self) -> str:
        if self.phase_name == self.GamePhase.BOSSFIGHT:
            remaining = self.boss_remaining
        else:
            remaining = clamp_to_zero(self.LEVEL_DURATION_SECONDS - self.elapsed)
        return f"{get_text('TIME')}: {format_duration(remaining)}"

    # -------------------------------------------------------------------------
    # Overrides Game class records_score() to add the condition "Boss killed"
    # to allow the recording of the score
    def records_score(self) -> bool:
        return self.boss_defeated

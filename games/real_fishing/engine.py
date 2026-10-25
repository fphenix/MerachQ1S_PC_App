"""Moteur du jeu de pêche au bouchon."""

import random
from enum import Enum

from setup.lang import get_text
from setup.utils import is_within

from games.game import Game
from games.game_input import GameInput, input_cadence

# =============================================================================
class RealFishingGame(Game):

    GAME_ID: str = "real_fishing"

    WIDTH: int = 1000
    HEIGHT: int = 700
    HUD_HEIGHT: int = 70
    DURATION_SECONDS: float = 480.0 # 480 sec = 8 minutes

    # Cadences cibles avec une tolérance de +/- 2 CPM.
    CAST_CADENCE: float = 26.0
    UNHOOK_CADENCE: float = 22.0
    NORMAL_REEL_CADENCE: float = 30.0
    RARE_REEL_CADENCE: float = 34.0
    CADENCE_MARGIN: float = 2.0

    CADENCE_TIMEOUT_SECONDS: float = 4.0

    CAST_DURATION_SECONDS: float = 1.5
    BITE_WAIT_MIN_SECONDS: float = 15.0
    BITE_WAIT_MAX_SECONDS: float = 30.0
    BITE_REACTION_SECONDS: float = 8.0

    REEL_DURATION_MIN_SECONDS: float = 15.0
    REEL_DURATION_MAX_SECONDS: float = 30.0
    UNHOOK_DURATION_SECONDS: float = 15.0

    GOLDEN_FISH_CHANCE: float = 8.0 # percent

    FISH_REGULAR_TYPES: list[str] = ["salmon", "pike", "carp"] # all, but "golden"
    FISH_POINTS: dict[str, int] = {"carp": 1, "pike": 3, "salmon": 5, "golden": 10}
    FISH_LABELS: dict[str, str] = {
        "salmon": "GAME_REAL_FISHING_SALMON",
        "pike": "GAME_REAL_FISHING_PIKE",
        "carp": "GAME_REAL_FISHING_CARP",
        "golden": "GAME_REAL_FISHING_GOLDEN",
    }

    class State(Enum):
        CASTING: str = "st_casting"
        FISHING: str = "st_fishing"
        BITE: str = "st_bite"
        REELING: str = "st_reeling"
        UNHOOK: str = "st_unhook"

    # -------------------------------------------------------------------------
    def __init__(self) -> None:

        super().__init__(
            game_id= self.GAME_ID,
            title= get_text("MENU_GAMES_REAL_FISHING"),
            duration= self.DURATION_SECONDS,
        )

        self.reset()

    # -------------------------------------------------------------------------
    def reset(self) -> None:

        self.current_spm: float | None = None
        self.fishing_state: RealFishingGame.State = self.State.CASTING
        self.state_elapsed: float = 0.0
        self.bite_remaining: float = 0.0
        self.hook_window_remaining: float = 0.0
        self.reel_duration: float = 0.0
        self.unhook_progress: float = 0.0
        self.current_fish: str | None = None
        self.fish_count: int = 0
        self.points_total: int = 0
        self._cadence_age: float = 999.0
        self._last_event: str = ""
        self._event_elapsed: float = 0.0
        self._bobber_phase: float = 0.0
        self._needs_recast: bool = False

    # -------------------------------------------------------------------------
    def hud_score_text(self) -> str:
        return f"{get_text('GAME_SCORE')}: {self.score:.2f}"

    # -------------------------------------------------------------------------
    def hud_result_text(self) -> str:
        return get_text('GAME_REAL_FISHING_RESULT').format(
            count=self.fish_count, points=self.points_total
        )

    # -------------------------------------------------------------------------
    @property
    def is_golden_fish(self) -> bool:
        return self.current_fish == "golden"

    # -------------------------------------------------------------------------
    @property
    def fish_label(self) -> str:

        if self.current_fish is None:
            return ""
        
        return get_text(self.FISH_LABELS[self.current_fish])

    # -------------------------------------------------------------------------
    @property
    def status_key(self) -> str:
        return {
            self.State.CASTING: "GAME_REAL_FISHING_CAST",
            self.State.FISHING: "GAME_REAL_FISHING_WAITING",
            self.State.BITE: "GAME_REAL_FISHING_BITE",
            self.State.REELING: (
                "GAME_REAL_FISHING_RARE_REEL"
                if self.is_golden_fish
                else "GAME_REAL_FISHING_REEL"
            ),
            self.State.UNHOOK: "GAME_REAL_FISHING_UNHOOK",
        }[self.fishing_state]

    # -------------------------------------------------------------------------
    @property
    def target_cadence(self) -> int:

        if self.fishing_state == self.State.UNHOOK:
            return int(self.UNHOOK_CADENCE)
        
        if self.fishing_state in (self.State.BITE, self.State.REELING):
            return int(self.RARE_REEL_CADENCE if self.is_golden_fish else self.NORMAL_REEL_CADENCE)

        return int(self.CAST_CADENCE)

    # -------------------------------------------------------------------------
    @property
    def bobber_on_bank(self) -> bool:
        return self.fishing_state == self.State.UNHOOK or self._needs_recast

    # -------------------------------------------------------------------------
    @property
    def bobber_moving(self) -> bool:
        return self.fishing_state == self.State.BITE

    # -------------------------------------------------------------------------
    def update_game(self, dt: float, game_input: GameInput) -> None:

        self._event_elapsed += dt
        self._bobber_phase += dt

        if game_input.stroke_event:
            cadence = input_cadence(game_input)
            if cadence is not None:
                self.current_spm = cadence
                self._cadence_age = 0.0
        else:
            self._cadence_age += dt

        if self._cadence_age > self.CADENCE_TIMEOUT_SECONDS:
            self.current_spm = None

        cadence = self.current_spm
        self.state_elapsed += dt

        if self.fishing_state == self.State.CASTING:
            if self._is_cast_cadence(cadence):
                if self.state_elapsed >= self.CAST_DURATION_SECONDS:
                    self._needs_recast = False
                    self.fishing_state = self.State.FISHING
                    self.state_elapsed = 0.0
                    self.bite_remaining = random.uniform(
                        self.BITE_WAIT_MIN_SECONDS,
                        self.BITE_WAIT_MAX_SECONDS,
                    )
                    self._set_event("cast")
            else:
                # Après le décrochage, le bouchon reste sur la berge jusqu'à
                # ce que la cadence de lancer (26 CPM) soit reprise.
                self.state_elapsed = 0.0

        elif self.fishing_state == self.State.FISHING:
            # La ligne reste dans l'eau, mais les poissons ne mordent que si
            # le joueur conserve une cadence moyenne.
            if self._is_cast_cadence(cadence):
                self.bite_remaining -= dt
                if self.bite_remaining <= 0.0:
                    self._start_bite()
            
        elif self.fishing_state == self.State.BITE:
            if self._can_reel(cadence):
                self.fishing_state = self.State.REELING
                self.state_elapsed = 0.0
                self.reel_duration = random.uniform(
                    self.REEL_DURATION_MIN_SECONDS,
                    self.REEL_DURATION_MAX_SECONDS,
                )
                self._set_event("hooked")
            else:
                self.hook_window_remaining -= dt
                if self.hook_window_remaining <= 0.0:
                    self._fish_escaped()

        elif self.fishing_state == self.State.REELING:
            if self._can_reel(cadence):
                if self.state_elapsed >= self.reel_duration:
                    self.fishing_state = self.State.UNHOOK
                    self.state_elapsed = 0.0
                    self.unhook_progress = 0.0
                    self._set_event("landed")
            else:
                self._fish_escaped()

        elif self.fishing_state == self.State.UNHOOK:
            if self._is_unhook_cadence(cadence):
                self.unhook_progress += dt
                if self.unhook_progress >= self.UNHOOK_DURATION_SECONDS:
                    self.fish_count += 1
                    self.points_total += self.FISH_POINTS[self.current_fish]
                    # Encodage du classement : nombre de poissons en partie
                    # entière, points en deux décimales (ex. 5 poissons / 11 pts = 5.11).
                    self.score = round(self.fish_count + self.points_total / 100.0, 2)
                    self.current_fish = None
                    self.fishing_state = self.State.CASTING
                    self._needs_recast = True
                    self.state_elapsed = 0.0
                    self.unhook_progress = 0.0
                    self._set_event("netted")
            # Hors de la plage lente, la progression s'arrête mais ne repart
            # pas de zéro : le joueur peut reprendre la bonne cadence.

    # -------------------------------------------------------------------------
    def _start_bite(self) -> None:

        self.current_fish = (
            "golden" if random.random() < (self.GOLDEN_FISH_CHANCE / 100.0)
            else random.choice(self.FISH_REGULAR_TYPES)
        )
        self.fishing_state = self.State.BITE
        self.state_elapsed = 0.0
        self.hook_window_remaining = self.BITE_REACTION_SECONDS
        self._set_event("bite")

    # -------------------------------------------------------------------------
    def _fish_escaped(self) -> None:

        self.current_fish = None
        self.fishing_state = self.State.FISHING
        self.state_elapsed = 0.0
        self.bite_remaining = random.uniform(
            self.BITE_WAIT_MIN_SECONDS,
            self.BITE_WAIT_MAX_SECONDS,
        )
        self._set_event("escaped")

    # -------------------------------------------------------------------------
    def _set_event(self, event: str) -> None:
        self._last_event = event
        self._event_elapsed = 0.0

    # -------------------------------------------------------------------------
    @classmethod
    def _is_cast_cadence(cls, cadence: float | None) -> bool:
        return cadence is not None and is_within(
            cadence, cls.CAST_CADENCE, cls.CADENCE_MARGIN
        )

    # -------------------------------------------------------------------------
    @classmethod
    def _is_unhook_cadence(cls, cadence: float | None) -> bool:
        return cadence is not None and is_within(
            cadence, cls.UNHOOK_CADENCE, cls.CADENCE_MARGIN
        )

    # -------------------------------------------------------------------------
    def _can_reel(self, cadence: float | None) -> bool:

        if cadence is None:
            return False
        
        if self.is_golden_fish:
            return cadence >= (self.RARE_REEL_CADENCE - self.CADENCE_MARGIN)
        
        return cadence >= (self.NORMAL_REEL_CADENCE - self.CADENCE_MARGIN)

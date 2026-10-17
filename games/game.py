"""Socle commun des jeux."""

from abc import ABC, abstractmethod

from setup.lang import get_text
from setup.utils import format_duration

from games.game_input import GameInput

# =============================================================================
class Game(ABC):

    START_DELAY_SECONDS: float = 1.0
    RESTART_DELAY_SECONDS: float = 1.0

    PHASE_WAITING: str = "waiting"
    PHASE_PLAYING: str = "playing"
    PHASE_FINISHED: str = "finished"

    # -------------------------------------------------------------------------
    def __init__(
        self,
        game_id: str,
        title: str,
        duration: float
    ) -> None:

        self.game_id: str = game_id
        self.title: str = title
        self.duration: float = duration

        self.score: int = 0
        self.elapsed: float = 0.0
        self.finished: bool = False
        self.phase: str = self.PHASE_WAITING
        self.phase_elapsed: float = 0.0

    # -------------------------------------------------------------------------
    def start(self) -> None:

        self.score = 0
        self.elapsed = 0.0
        self.finished = False
        self.phase = self.PHASE_WAITING
        self.phase_elapsed = 0.0

        self.reset()

    # -------------------------------------------------------------------------
    def update(self, dt: float, game_input: GameInput) -> None:

        self.phase_elapsed += dt

        if self.phase == self.PHASE_WAITING:
            if self.phase_elapsed < self.START_DELAY_SECONDS:
                return

            if not game_input.stroke_event:
                return
            
            self.phase = self.PHASE_PLAYING
            self.phase_elapsed = 0.0

        if self.phase == self.PHASE_FINISHED:
            if self.phase_elapsed < self.RESTART_DELAY_SECONDS:
                return

            if game_input.stroke_event:
                self.start()
                self.phase = self.PHASE_PLAYING
                self.phase_elapsed = 0.0

            return

        self.elapsed += dt
        self.update_game(dt, game_input)

        if self.elapsed >= self.duration:
            
            self.elapsed = self.duration
            self.finished = True
            self.phase = self.PHASE_FINISHED
            self.phase_elapsed = 0.0
            self.on_finished()

    # -------------------------------------------------------------------------
    def add_score(self, points: int) -> None:
        self.score = max(0, self.score + points)

    # -------------------------------------------------------------------------
    def remaining(self) -> float:
        return max(0.0, self.duration - self.elapsed)

    # -------------------------------------------------------------------------
    def hud_score_text(self) -> str:
        return f"{get_text('GAME_SCORE')}: {self.score:05d}"

    # -------------------------------------------------------------------------
    def hud_time_text(self) -> str:
        return f"{get_text('TIME')}: {format_duration(self.remaining())}"

    # -------------------------------------------------------------------------
    def records_score(self) -> bool:
        return True

    # -------------------------------------------------------------------------
    def reset(self) -> None:
        pass

    # -------------------------------------------------------------------------
    def on_finished(self) -> None:
        pass

    # -------------------------------------------------------------------------
    @abstractmethod
    def update_game(self, dt: float, game_input: GameInput) -> None:
        pass

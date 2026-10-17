"""Moteur de Simon, avec trois couleurs commandées par la cadence."""

import random

from setup.lang import get_text
from setup.utils import is_within

from games.game import Game
from games.game_input import GameInput
from games.cadence import input_cadence

# =============================================================================
class SimonGame(Game):

    WIDTH = 1000
    HEIGHT = 700
    HUD_HEIGHT = 70
    DURATION_SECONDS = 240.0

    PLAYBACK_ON_SECONDS = 1.95
    PLAYBACK_GAP_SECONDS = 0.45
    INPUT_FLASH_SECONDS = 0.45

    STABLE_STROKES_REQUIRED = 3
    STABLE_CADENCE_DELTA = 1.5

    CADENCE_REPLAY_THRESHOLD = 16.0
    CADENCE_LOW = 18.0
    CADENCE_MID = 24.0
    CADENCE_HIGH = 30.0
    CADENCE_MARGIN = 2.0
    CADENCE_TARGETS = (CADENCE_LOW, CADENCE_MID, CADENCE_HIGH)

    # -------------------------------------------------------------------------
    def __init__(self) -> None:

        super().__init__(
            game_id="simon",
            title=get_text("MENU_GAMES_SIMON"),
            duration=self.DURATION_SECONDS,
        )

        self.current_spm: float | None = None
        self.sequence: list[int] = []
        self.input_index = 0
        self.showing_sequence = True
        self._candidate_lane: int | None = None
        self._candidate_cadences: list[float] = []
        self.playback_index = 0
        self.playback_elapsed = 0.0
        self.active_lane: int | None = None
        self.flash_remaining = 0.0
        self.round_number = 0
        self.message_key = "GAME_SIMON_WATCH"
        self.result_key = ""

    # -------------------------------------------------------------------------
    def reset(self) -> None:

        self.current_spm = None
        self.sequence = []
        self.input_index = 0
        self.showing_sequence = True
        self.playback_index = 0
        self.playback_elapsed = 0.0
        self.active_lane = None
        self.flash_remaining = 0.0
        self.round_number = 0
        self.message_key = "GAME_SIMON_WATCH"
        self.result_key = ""
        self._reset_cadence_candidate()
        self._start_round()

    # -------------------------------------------------------------------------
    def _start_round(self) -> None:

        self.sequence.append(random.randrange(3))
        self.round_number = len(self.sequence)
        self.input_index = 0
        self.showing_sequence = True
        self.playback_index = 0
        self.playback_elapsed = 0.0
        self.active_lane = None
        self._reset_cadence_candidate()
        self.message_key = "GAME_SIMON_WATCH"

    # -------------------------------------------------------------------------
    def update_game(self, dt: float, game_input: GameInput) -> None:

        self.current_spm = input_cadence(game_input)
        self.flash_remaining = max(0.0, self.flash_remaining - dt)
        if self.flash_remaining <= 0.0:
            self.active_lane = None

        if self.showing_sequence:
            self.playback_elapsed += dt
            cycle = self.PLAYBACK_ON_SECONDS + self.PLAYBACK_GAP_SECONDS
            if self.playback_elapsed >= cycle:
                self.playback_elapsed -= cycle
                self.playback_index += 1
                if self.playback_index >= len(self.sequence):
                    self.showing_sequence = False
                    self.input_index = 0
                    self.active_lane = None
                    self._reset_cadence_candidate()
                    self.message_key = "GAME_SIMON_REPEAT"
                else:
                    self.active_lane = self.sequence[self.playback_index]
            elif self.playback_elapsed < self.PLAYBACK_ON_SECONDS:
                self.active_lane = self.sequence[self.playback_index]
            else:
                self.active_lane = None

            # Le joueur peut continuer à ramer, mais les coups de démonstration
            # ne sont jamais comptés dans sa réponse.
            return

        if not game_input.stroke_event:
            return

        cadence = self.current_spm

        # Une cadence très basse pendant le tour du joueur signifie qu'il est
        # probablement perdu : Simon redémontre la séquence courante, sans
        # ajouter de bouton ni pénaliser le joueur. Le coup déclencheur est
        # ignoré et les coups effectués pendant la démonstration aussi.
        if cadence is not None and cadence <= self.CADENCE_REPLAY_THRESHOLD:
            self._replay_sequence()
            return

        lane = self._cadence_lane(cadence)
        if lane is None or cadence is None:
            self._reset_cadence_candidate()
            self.message_key = "GAME_SIMON_WAIT_CADENCE"
            return

        # Les trois coups doivent appartenir à la même voie et rester proches
        # en cadence. Cela écarte les valeurs intermédiaires pendant une
        # transition Lent <-> Rapide, qui ne doit pas être interprétée comme
        # une entrée Moyen.
        if lane != self._candidate_lane:
            self._candidate_lane = lane
            self._candidate_cadences = [cadence]
        elif (
            self._candidate_cadences
            and max(self._candidate_cadences + [cadence])
            - min(self._candidate_cadences + [cadence])
            > self.STABLE_CADENCE_DELTA
        ):
            # La fenêtre entière doit rester stable : une hausse graduelle
            # traversant la zone Moyen ne doit pas valider une fausse réponse.
            self._candidate_cadences = [cadence]
        else:
            self._candidate_cadences.append(cadence)

        self.active_lane = lane
        self.flash_remaining = self.INPUT_FLASH_SECONDS
        self.message_key = "GAME_SIMON_REPEAT"

        if len(self._candidate_cadences) < self.STABLE_STROKES_REQUIRED:
            return

        self._reset_cadence_candidate()
        if lane != self.sequence[self.input_index]:
            self.result_key = "GAME_SIMON_MISSED"
            self.finished = True
            self.phase = self.PHASE_FINISHED
            self.phase_elapsed = 0.0
            return

        self.input_index += 1
        if self.input_index >= len(self.sequence):
            self.add_score(self.round_number * 100)
            self._start_round()

    # -------------------------------------------------------------------------
    def _replay_sequence(self) -> None:
        """Redémontre la séquence actuelle sans la modifier."""

        self.showing_sequence = True
        self.input_index = 0
        self.playback_index = 0
        self.playback_elapsed = 0.0
        self.active_lane = None
        self.flash_remaining = 0.0
        self._reset_cadence_candidate()
        self.message_key = "GAME_SIMON_WATCH"

    # -------------------------------------------------------------------------
    def _reset_cadence_candidate(self) -> None:

        self._candidate_lane = None
        self._candidate_cadences = []

    # -------------------------------------------------------------------------
    @classmethod
    def _cadence_lane(cls, cadence: float | None) -> int | None:

        if cadence is None:
            return None

        for lane, target in enumerate(cls.CADENCE_TARGETS):
            if is_within(cadence, target, cls.CADENCE_MARGIN):
                return lane

        return None

    # -------------------------------------------------------------------------
    def hud_result_text(self) -> str:

        if self.result_key:
            return get_text(self.result_key)

        return ""

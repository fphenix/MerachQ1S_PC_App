"""Moteur de Simon, avec trois couleurs commandées par la cadence."""

import random

from setup.lang import get_text
from setup.utils import is_within, clamp_to_zero

from games.game import Game
from games.game_input import GameInput, input_cadence

# =============================================================================
class SimonGame(Game):

    GAME_ID: str = "simon"

    WIDTH: int = 1000
    HEIGHT: int = 700
    HUD_HEIGHT: int = 70
    DURATION_SECONDS: float = 240.0

    PLAYBACK_ON_SECONDS: float = 1.95
    PLAYBACK_GAP_SECONDS: float = 0.45
    INPUT_FLASH_SECONDS: float = 0.45

    STABLE_STROKES_REQUIRED: int = 3
    STABLE_CADENCE_DELTA: float = 1.5

    CADENCE_REPLAY_THRESHOLD: float = 16.0
    CADENCE_LOW: float = 18.0
    CADENCE_MID: float = 24.0
    CADENCE_HIGH: float = 30.0
    CADENCE_MARGIN: float = 2.0
    CADENCE_TARGETS: list[float] = [CADENCE_LOW, CADENCE_MID, CADENCE_HIGH]

    # -------------------------------------------------------------------------
    def __init__(self) -> None:

        super().__init__(
            game_id= self.GAME_ID,
            title= get_text("MENU_GAMES_SIMON"),
            duration= self.DURATION_SECONDS,
        )

        self.reset()

    # -------------------------------------------------------------------------
    def reset(self) -> None:

        self.current_spm: float | None = None
        self.max_successful_sequence_length: int = 0

        self.input_index: int = 0
        self.showing_sequence: bool = True
        self.playback_index: int = 0
        self.playback_revealed_count: int = 0
        self.playback_repeat_count: int = 0
        self.playback_elapsed: float = 0.0
        self.flash_remaining: float = 0.0
        self.message_key: str = "GAME_SIMON_WATCH"
        self.result_key: str = ""

        self._reset_cadence_candidate()

        self.sequence: list[int] = []
        self.round_number: int = 0
        self.active_lane: int | None = None

        self._start_round()

    # -------------------------------------------------------------------------
    def _reset_cadence_candidate(self) -> None:

        self._candidate_lane: int | None = None
        self._candidate_cadences: list[float] = []

    # -------------------------------------------------------------------------
    def _start_round(self) -> None:

        # Prépare le tour suivant sans effacer la séquence déjà mémorisée.
        self.input_index = 0
        self.showing_sequence = True
        self.playback_index = 0
        self.playback_revealed_count = 0
        self.playback_repeat_count = 0
        self.playback_elapsed = 0.0
        self.flash_remaining = 0.0
        self.message_key = "GAME_SIMON_WATCH"
        self.result_key = ""

        self._reset_cadence_candidate()

        self.sequence.append(random.randrange(3))
        self.round_number = len(self.sequence)
        self.active_lane = self.sequence[0]

    # -------------------------------------------------------------------------
    def _replay_sequence(self) -> None:
        """Redémontre la séquence actuelle sans la modifier."""

        self.input_index = 0
        self.showing_sequence = True
        self.playback_index = 0
        self.playback_revealed_count = 0
        self.playback_repeat_count = 0
        self.playback_elapsed = 0.0
        self.flash_remaining = 0.0
        self.message_key = "GAME_SIMON_WATCH"

        self._reset_cadence_candidate()

        self.active_lane = self.sequence[0] if self.sequence else None

    # -------------------------------------------------------------------------
    def update_game(self, dt: float, game_input: GameInput) -> None:

        self.current_spm = input_cadence(game_input)
        self.flash_remaining = clamp_to_zero(self.flash_remaining - dt)
        if self.flash_remaining <= 0.0:
            self.active_lane = None

        if self.showing_sequence:
            # Simon ne révèle la séquence que tant qu'une cadence valide est
            # détectée. Une cadence nulle/absente met la démonstration en pause.
            if self.current_spm is None:
                self.active_lane = None
                self.message_key = "GAME_SIMON_WAIT_CADENCE"
                return

            self.message_key = "GAME_SIMON_WATCH"
            self.playback_elapsed += dt
            cycle = self.PLAYBACK_ON_SECONDS + self.PLAYBACK_GAP_SECONDS
            while self.playback_elapsed >= cycle and self.showing_sequence:
                self.playback_elapsed -= cycle
                self.playback_repeat_count += 1
                if self.playback_repeat_count >= 3:
                    self.playback_repeat_count = 0
                    self.playback_index += 1
                if self.playback_index >= len(self.sequence):
                    self.showing_sequence = False
                    self.input_index = 0
                    self.active_lane = None
                    self._reset_cadence_candidate()
                    self.message_key = "GAME_SIMON_REPEAT"
                else:
                    self.active_lane = self.sequence[self.playback_index]

            if self.showing_sequence:
                if self.playback_elapsed < self.PLAYBACK_ON_SECONDS:
                    self.active_lane = self.sequence[self.playback_index]
                    self.playback_revealed_count = max(
                        self.playback_revealed_count,
                        self.playback_index + 1,
                    )
                else:
                    self.active_lane = None

            # La séquence entière est montrée trois fois, chaque étape à son
            # tour. Les coups de rame pendant la démonstration sont ignorés.
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
            and (
                max(self._candidate_cadences + [cadence])
                - min(self._candidate_cadences + [cadence])
                > self.STABLE_CADENCE_DELTA
            )
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
            # Une erreur fait recommencer la séquence courante, sans la rallonger.
            self.result_key = "GAME_SIMON_MISSED"
            self._replay_sequence()
            return

        self.input_index += 1
        if self.input_index >= len(self.sequence):
            self.max_successful_sequence_length = max(
                self.max_successful_sequence_length,
                len(self.sequence),
            )
            self.score = self.max_successful_sequence_length
            self._start_round()

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

    # -------------------------------------------------------------------------
    def on_finished(self) -> None:
        # Le score final est la longueur de la plus longue séquence réussie.
        self.score = self.max_successful_sequence_length

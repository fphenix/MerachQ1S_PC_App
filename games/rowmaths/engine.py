"""Moteur du quiz de calcul RowMaths, piloté par la cadence."""

import random
from collections import deque

from setup.utils import (
    calc_average, clamp_to_max, clamp_to_min,
    is_within, is_in_percent,
)
from setup.lang import get_text

from games.game import Game
from games.game_input import GameInput, input_cadence

# =============================================================================
class RowMathsGame(Game):

    GAME_ID: str = "rowmaths"

    WIDTH: int = 1000
    HEIGHT: int = 700
    HUD_HEIGHT: int = 70

    DURATION_SECONDS: float = 420.0
    NUMBER_MIN: int = 1
    NUMBER_MAX: int = 99                 # Peut être porté à 999.
    OPERATORS: tuple[str, ...] = ("+", "-", "x", "/")

    ANSWER_CADENCES: tuple[int, ...] = (20, 24, 28, 32)
    ROUND_SECONDS: float = 30.0
    FLASH_SECONDS: float = 15.0
    RESULT_SECONDS: float = 3.0
    FLASH_EVERY_MIN: int = 3
    FLASH_EVERY_MAX: int = 6
    CADENCE_TOLERANCE: float = 2.0
    SAMPLE_COUNT: int = 3

    FREQ_UNITY_ERR: float = 55.0
    FREQ_TENTH_ERR: float = 30.0

    POINTS_CORRECT: int = 10
    POINTS_WRONG: int = -3
    POINTS_FLASH: int = 15

    # -------------------------------------------------------------------------
    def __init__(self) -> None:

        super().__init__(
            game_id= self.GAME_ID,
            title= get_text("MENU_GAMES_ROWMATHS"),
            duration= self.DURATION_SECONDS,
        )

        self.reset()

    # -------------------------------------------------------------------------
    def reset(self) -> None:

        self.current_spm: float | None = None
        self.question_number: int = 0
        self.round_elapsed: float = 0.0
        self.result_elapsed: float = 0.0
        self.showing_result: bool = False
        self.result_correct: bool = False
        self.result_points: int = 0
        self.result_message: str = ""
        self.flash_round: bool = False
        self.next_flash_at: int = random.randint(
            self.FLASH_EVERY_MIN, self.FLASH_EVERY_MAX
        )
        self.samples: deque[float] = deque(maxlen=self.SAMPLE_COUNT)
        self.question: str = ""
        self.correct_answer: int = 0
        self.answers: list[int] = []
        self.correct_index: int = 0

        self._new_question()

    # -------------------------------------------------------------------------
    def _calculate(self, left: int, operator: str, right: int) -> int:

        if operator == "+":
            return left + right
        if operator == "-":
            return left - right
        if operator == "x":
            return left * right
        return left // right

    # -------------------------------------------------------------------------
    def _make_operands(self, operator: str) -> tuple[int, int]:

        low, high = self.NUMBER_MIN, self.NUMBER_MAX

        if operator == "/":
            divisor  = random.randint(1, clamp_to_min(int(high ** 0.5), 1))
            quotient = random.randint(1, clamp_to_min(high // divisor, 1))
            return divisor * quotient, divisor

        if operator == "-":
            left  = random.randint(low, high)
            right = random.randint(low, left)
            return left, right

        return random.randint(low, high), random.randint(low, high)

    # -------------------------------------------------------------------------
    def _make_distractors(
        self,
        left: int, operator: str, right: int,
        result: int
    ) -> list[int]:
        """Pièges issus d'erreurs plausibles, complétés par des variantes aléatoires."""

        candidates: set[int] = set()
        limit = self.NUMBER_MAX * self.NUMBER_MAX

        # Erreurs de calcul fréquentes : retenue oubliée, ordre inversé,
        # confusion d'opérateur et erreur d'unité/dizaine.
        if is_in_percent(self.FREQ_UNITY_ERR):
            candidates.update((result - 1, result + 1))
        if is_in_percent(self.FREQ_TENTH_ERR):
            candidates.add(random.choice((result - 10, result + 10)))

        candidates.add(self._calculate(right, operator, left))
        candidates.update((left + right, left - right, left * right))

        if operator == "+":
            candidates.add((left % 10) + (right % 10))
            candidates.add((left // 10) * 10 + (right % 10))
            candidates.add((left % 10) * 10 + (right // 10))
        elif operator == "-":
            candidates.add(abs(left - right))
            candidates.add((left % 10) - (right % 10))
        elif operator == "x":
            candidates.add(left + right)
            candidates.add(left * (right % 10))
        elif operator == "/" and right:
            candidates.add(left + right)
            candidates.add(left - right)

        # Check if the distractor is within acceptable value range
        # and if it is not equal to the actual answer.
        candidates = {
            value for value in candidates
            if isinstance(value, int) and 0 <= value <= limit and value != result
        }

        # Les pièges ne doivent pas donner une règle de sélection répétitive :
        # on mélange les erreurs plausibles et des nombres arbitraires.
        pool = list(candidates)
        random.shuffle(pool)

        selected = pool[:3]
        while len(selected) < 3:
            candidate = random.randint(0, limit)
            if candidate != result and candidate not in selected:
                selected.append(candidate)

        random.shuffle(selected)

        return selected

    # -------------------------------------------------------------------------
    def _new_question(self) -> None:

        self.question_number += 1

        operator = random.choice(self.OPERATORS)

        left, right = self._make_operands(operator)
        self.correct_answer = self._calculate(left, operator, right)
        self.question = f"{left} {operator} {right} = ?"

        options = self._make_distractors(left, operator, right, self.correct_answer)
        self.correct_index = random.randrange(len(self.ANSWER_CADENCES))
        options.insert(self.correct_index, self.correct_answer)
        self.answers = options

        self.flash_round = self.question_number >= self.next_flash_at
        if self.flash_round:
            self.next_flash_at = (
                self.question_number
                + random.randint(self.FLASH_EVERY_MIN, self.FLASH_EVERY_MAX)
            )

        self.round_elapsed = 0.0
        self.result_elapsed = 0.0
        self.showing_result = False
        self.samples.clear()

    # -------------------------------------------------------------------------
    def update_game(self, dt: float, game_input: GameInput) -> None:

        cadence = input_cadence(game_input)
        self.current_spm = cadence

        if self.showing_result:
            self.result_elapsed += dt
            if self.result_elapsed >= self.RESULT_SECONDS:
                self._new_question()
            return

        self.round_elapsed += dt
        if game_input.stroke_event and cadence is not None:
            self.samples.append(cadence)

        round_duration = self.FLASH_SECONDS if self.flash_round else self.ROUND_SECONDS
        if self.round_elapsed >= round_duration:
            self._resolve_round()

    # -------------------------------------------------------------------------
    def _resolve_round(self) -> None:

        sample_count = clamp_to_max(len(self.samples), self.SAMPLE_COUNT)
        recent = list(self.samples)[-sample_count:] if self.samples else []
        average = calc_average(recent) if len(recent) >= self.SAMPLE_COUNT else None

        correct = (
            average is not None
            and is_within(
                average,
                self.ANSWER_CADENCES[self.correct_index],
                self.CADENCE_TOLERANCE,
            )
        )

        self.result_correct = correct
        if correct:
            self.result_points = self.POINTS_FLASH if self.flash_round else self.POINTS_CORRECT
            self.add_score(self.result_points)
            self.result_message = f"+{self.result_points}  •  {get_text("GAME_ROWMATHS_SUCCESS")}!"
        elif self.flash_round:
            self.result_points = 0
            self.result_message = f"{get_text("GAME_ROWMATHS_QFLASH")} {get_text("GAME_ROWMATHS_FAILED")}"
        else:
            self.result_points = self.POINTS_WRONG
            self.add_score(self.POINTS_WRONG)
            self.result_message = f"{self.POINTS_WRONG}  •  {get_text("GAME_ROWMATHS_BAD_SPM")}"

        self.showing_result = True
        self.result_elapsed = 0.0

    # -------------------------------------------------------------------------
    def hud_result_text(self) -> str:
        return f"{get_text("GAME_SCORE")} : {self.score}\n{get_text("GAME_ROWMATHS_QUESTION")} : {self.question_number}"

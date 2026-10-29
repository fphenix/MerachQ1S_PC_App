"""
Options de classement des Hi-Scores propres à chaque jeu.

"ascending" means that the lower the value the better the score is.
"descending" (default) means the higher the score the better it is.
"""
from enum import Enum

class GameHiScoreDirection(Enum):
    ASCENDING: str = "ascending"
    DEFAULT: str   = "descending"

GAME_SCORE_ORDERS: dict[str, GameHiScoreDirection] = {
    "race_1000": GameHiScoreDirection.ASCENDING,
    "race_2000": GameHiScoreDirection.ASCENDING,
}

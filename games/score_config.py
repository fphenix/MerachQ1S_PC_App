"""
Options de classement des Hi-Scores propres à chaque jeu.

"ascending" means that the lower the value the better the score is.
"descending" (default) means the higher the score the better it is.
"""

GAME_HISCORE_ASC: str = "ascending"
GAME_HISCORE_DEFAULT: str = "descending"

GAME_SCORE_ORDERS: dict[str, str] = {
    "race_1000": GAME_HISCORE_ASC,
    "race_2000": GAME_HISCORE_ASC,
}

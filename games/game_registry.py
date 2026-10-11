"""Registre des moteurs, vues et règles des jeux disponibles."""

from pathlib import Path
from games.fishing.engine import FishingGame
from games.fishing.widget import FishingWidget
from games.fishing2.engine import Fishing2Game

GAME_CLASSES = {
    "fishing": FishingGame,
    "fishing2": Fishing2Game,
}
GAME_VIEWS = {
    "fishing": FishingWidget,
    "fishing2": FishingWidget,
}
GAME_RULES = {
    "fishing": Path(__file__).parent / "fishing" / "rules.json",
    "fishing2": Path(__file__).parent / "fishing2" / "rules.json",
}

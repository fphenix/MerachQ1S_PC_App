"""Registre des moteurs, vues, règles et modes de classement."""

from pathlib import Path

from games.fishing.engine import FishingGame
from games.fishing2.engine import Fishing2Game
from games.fishing.widget import FishingWidget

from games.pigeon.engine import PigeonGame
from games.pigeon.widget import PigeonWidget

from games.jump.engine import JumpGame
from games.jump.widget import JumpWidget

from games.slowngo.engine import SlowNGoGame
from games.slowngo.widget import SlowNGoWidget

from games.path.engine import PathGame
from games.path.widget import PathWidget

from games.race.engine import Race1000Game, Race2000Game
from games.race.widget import RaceWidget

from games.mario.engine import MarioGame
from games.mario.widget import MarioWidget

from games.simon.engine import SimonGame
from games.simon.widget import SimonWidget

GAME_CLASSES = {
    "fishing": FishingGame,
    "fishing2": Fishing2Game,
    "pigeon": PigeonGame,
    "jump": JumpGame,
    "slowngo": SlowNGoGame,
    "path": PathGame,
    "race_1000": Race1000Game,
    "race_2000": Race2000Game,
    "mario": MarioGame,
    "simon": SimonGame,
}

GAME_VIEWS = {
    "fishing": FishingWidget,
    "fishing2": FishingWidget,
    "pigeon": PigeonWidget,
    "jump": JumpWidget,
    "slowngo": SlowNGoWidget,
    "path": PathWidget,
    "race_1000": RaceWidget,
    "race_2000": RaceWidget,
    "mario": MarioWidget,
    "simon": SimonWidget,
}

GAME_RULES = {
    "fishing": Path(__file__).parent / "fishing" / "rules.json",
    "fishing2": Path(__file__).parent / "fishing2" / "rules.json",
    "pigeon": Path(__file__).parent / "pigeon" / "rules.json",
    "jump": Path(__file__).parent / "jump" / "rules.json",
    "slowngo": Path(__file__).parent / "slowngo" / "rules.json",
    "path": Path(__file__).parent / "path" / "rules.json",
    "race_1000": Path(__file__).parent / "race" / "rules_1000.json",
    "race_2000": Path(__file__).parent / "race" / "rules_2000.json",
    "mario": Path(__file__).parent / "mario" / "rules.json",
    "simon": Path(__file__).parent / "simon" / "rules.json",
}

from pathlib import Path

VERSION: str = "4.8"

GUI_REFRESH_MS   = 100 # milliseconds
WORKOUT_TIMER_MS = 20 # milliseconds

WINDOW_WIDTH = 1100 # pixels
WINDOW_HEIGHT = 700 # pixels
WINDOW_TO_SCREEN_LEFT_MARGIN = 35 # pixels
WINDOW_TO_SCREEN_TOP_MARGIN = 0.33 # 0.33 = 33% of the margin at the top, 66% at the bottom

MAIN_FONT  = "Consolas"
TITLE_FONT = "Segoe UI"

BIG_FONT_SIZE          = 22 # point
AVERAGE_FONT_SIZE      = 16 # point
SMALL_FONT_SIZE        = 12 # point

WIDGET_TITLE_FONT_SIZE = 11 # point
WIDGET_VALUE_FONT_SIZE = 28 # point
WIDGET_UNIT_FONT_SIZE  = 10 # point
SPLIT_LIST_FONT_SIZE   = 12 # point

DEFAULT_SPLIT_LENGTH  = 500.0 # meters
MIN_SPLIT_LENGTH = 100   # meters
MAX_SPLIT_LENGTH = 2000  # meters
SPLIT_LENGTH_STEP = 100  # meters

SPLIT_MODES_NORMAL: str  = "normal"
SPLIT_MODES_500M: str    = "500m"
SPLIT_MODES_WORKOUT: str = "workout"

DEFAULT_SPLIT_MODE: str = SPLIT_MODES_NORMAL

SPLIT_MODES: list[str] = [
    SPLIT_MODES_NORMAL,
    SPLIT_MODES_500M,
    SPLIT_MODES_WORKOUT,
]

DEFAULT_LANGUAGE: str = "fr" # "fr" or "en"

LANGUAGES: dict[str, str] = {
    "fr": "Français",
    "en": "English",
}

# ----------------------------------------------------------------------
# Files and Directories
# ----------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

CONFIG_DIR: Path   = BASE_DIR / "config"
WORKOUTS_DIR: Path = BASE_DIR / "workouts"
USERS_DIR: Path    = BASE_DIR / "users"

LANG_FILE: Path         = CONFIG_DIR / "lang.json"
USERS_CONFIG_FILE: Path = CONFIG_DIR / "users.json"

SETTINGS_FILE_NAME: str = "settings.json"
LOGS_DIR_NAME: str = "logs"

print(BASE_DIR)

FILE_ENCODING: str = "utf-8"
FILE_ENCODING_BOM: str = "utf-8-sig"

# ----------------------------------------------------------------------
# Analyzer et Plot_Wo
# ----------------------------------------------------------------------

ANALYZER_WIDTH  = 1400 # pixels
ANALYZER_HEIGHT = 1000 # pixels

ANALYZER_STATS_FONT_SIZE = 11 # point
ANALYZER_STATS_MIN_WIDTH = 260 # pixels
ANALYZER_STATS_MAX_WIDTH = 320 # pixels

PLOTWO_WIDTH  = 1300 # pixels
PLOTWO_HEIGHT =  800 # pixels

PLOTWO_CODE_FONT_SIZE = 12 # point
PLOTWO_CODE_MIN_WIDTH = 300 # pixels
PLOTWO_CODE_MAX_WIDTH = 600 # pixels

ANALYZER_SHOW_CHECKBUTTONS = False

# ----------------------------------------------------------------------
# Logger
# ----------------------------------------------------------------------

# Intervalle (en secondes) entre deux flush() du fichier CSV.
# Permet de limiter les pertes de données en cas d'arrêt brutal.
LOGGER_FLUSH_PERIOD: float = 5.0 # seconds

# Temps (en secondes) sans nouveau coup avant de considérer que
# la séance est terminée et de forcer un flush().
LOGGER_END_SESSION_TIMEOUT: float = 10.0 # seconds

# LOGGER_FORMAT choisi de créer un .csv OU un .zip contenant un .csv
LOGGER_FORMAT_CSV: str = "csv"
LOGGER_FORMAT_ZIP: str = "zip"
LOGGER_FORMAT = LOGGER_FORMAT_ZIP

ALLOWED_REPLAY_EXT: list[str] = [
    LOGGER_FORMAT_CSV,
    LOGGER_FORMAT_ZIP,
]

# ----------------------------------------------------------------------
# Replay
# ----------------------------------------------------------------------
# Source de Données (Bluetooth vs. Replay Log)
# On peut relancer une séance rameur en "rejouant" un log.
# Cela permet de valider une modification au script sans avoir à
# se connecter au rameur pour faire un test. Il suffit de rejouer
# un ancien log pour simuler le BT d'une séance de rameur et
# valider le nouveau code.
# Dans ce cas USE_REPLAY est "True" et le nom du log est dans
# REPLAY_FILE (on peut utiliser un csv ou un csv zippé).
# Pour passer en mode normal (c-à-d Data venant du Q1S
# via BlueTooth), mettre USE_REPLAY à "False".
# ----------------------------------------------------------------------

# Normal Mode vs. Replay Mode : USE_REPLAY
# * False : (Mode Normal) BT vient du rameur ou
# * True  : (Mode Dvp/Debug) BT émulé en rejouant une session loggée précédente.
USE_REPLAY: bool = False

USE_REPLAY_WORKOUT: bool = True and USE_REPLAY

# Le fichier REPLAY_FILE peut être:
# * un .csv
# * un .zip ayant un (et un seul) .csv à l'intérieur
REPLAY_USER: str = "Fred"
REPLAY_FILE: Path = (
    USERS_DIR / REPLAY_USER / LOGS_DIR_NAME
    / "session_20260918_114100.zip"
)
REPLAY_WORKOUT_FILE: Path = WORKOUTS_DIR / "spm_power.wo"

REPLAY_SPEED: float = 100.0 # 1.0: temps réel, 10: 10x plus rapide, 100: 100x plus rapide, etc.

# ----------------------------------------------------------------------
# Power recalibration / profile
# ----------------------------------------------------------------------

DEFAULT_USER_NAME: str = "Default"

MIN_PROFILE_AGE: int = 18 # years
MAX_PROFILE_AGE: int = 100 # years
DEFAULT_PROFILE_AGE: int = 40 # years

MIN_PROFILE_WEIGHT: float = 35.0 # kg
MAX_PROFILE_WEIGHT: float = 200.0 # kg
DEFAULT_PROFILE_WEIGHT: float = 75.0 # kg

MIN_PROFILE_HEIGHT: float = 140.0 # cm
MAX_PROFILE_HEIGHT: float = 220.0 # cm
DEFAULT_PROFILE_HEIGHT: float = 180.0 # cm

PROFILE_LEVELS_KEYS: list[str] = ["D", "I", "C", "A"]
PROFILE_LEVELS_THRESHOLDS: dict[str, float] = {
    "D" : 0.0,
    "I" : 0.33,
    "C" : 0.66,
    "A" : 1.0,
}
DEFAULT_PROFILE_LEVEL: str = "I"
DEFAULT_PROFILE_NORM_LEVEL: float = 0.33

DEFAULT_PROFILE_SEX: str = "M"

# ----------------------------------------------------------------------
# Workout
# ----------------------------------------------------------------------

DEFAULT_DELAY_SECONDS = 15
MIN_DELAY_SECONDS = 0
MAX_DELAY_SECONDS = 60
DELAY_SECONDS_STEP = 5

WORKOUT_WIDTH  = 720 # pixels
WORKOUT_HEIGHT = WINDOW_HEIGHT # pixels

WORKOUT_EDIT_WIDTH  = 1200  # pixels
WORKOUT_EDIT_HEIGHT =  800  # pixels

WORKOUT_TITLE_FONT_SIZE = 24 # point
WORKOUT_LIST_FONT_SIZE  = 14 # point
WORKOUT_INFO_FONT_SIZE  = 18 # point

LIST_WIDTH = 220  # pixels
BAR_HEIGHT = 28   # pixels

METRONOME_MARGIN = 100  # pixels

WINDOW_BACKGROUND   = "#303030"
LIST_BACKGROUND     = "#202020"
BAR_BACKGROUND      = "#202020"
MENU_SEL_BACKGROUND = "#505050"
BAR_BORDER          = "#666666"
BAR_COLOR           = "#00CC44"
TEXT_COLOR          = "white"
LISTTEXT_COLOR = TEXT_COLOR

WO_KEYWORD: dict[str, str] = {
    "Comment" : "#",
    "Title"   : "WORKOUT:",
    "Field"   : "FIELD:",
    "Info"    : "INFO:",
}

PART_DICT_KEYS: list[str] = ["O", "A", "C", "L", "AC", "LC"]
INTENSITY_DICT_KEYS: list[str] = ["R", "E", "N", "F", "M"]

INTENSITY_COLORS: dict[str, str] = {
    "R": "#7FDBFF",
    "E": "#0055FF",
    "N": "#00AA00",
    "F": "#DD2222",
    "M": "#BB44DD",
}

DURATION_UNITS: dict[str, int] = {
    "sec":  1,
    "min": 60,
    "h": 3600,
}

# min, max and step
DURATION_RANGES: dict[str, tuple[int|float, int, float]] = {
    "sec": (1, 3600, 1.0),
    "min": (0.01, 120, 0.5),
    "h":   (0.01, 2, 0.5),
}

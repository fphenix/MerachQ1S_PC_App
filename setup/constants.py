VERSION = 4.0

GUI_REFRESH_MS = 100 # miliseconds

WINDOW_TITLE = "Rower PM Monitor"
WINDOW_WIDTH = 1100 # pixels
WINDOW_HEIGHT = 700 # pixels

SPLIT_LENGTH = 500.0 # meters

MAIN_FONT = "Consolas"
TITLE_FONT = "Segoe UI"

from pathlib import Path

LOGS_DIR = (
      Path(__file__).resolve().parent.parent
    / "logs"  
)
WORKOUTS_DIR = (
    Path(__file__).resolve().parent.parent
    / "workouts"
)


# ----------------------------------------------------------------------
# Logger
# ----------------------------------------------------------------------

# Intervalle (en secondes) entre deux flush() du fichier CSV.
# Permet de limiter les pertes de données en cas d'arrêt brutal.
LOGGER_FLUSH_PERIOD = 5.0 # seconds

# Temps (en secondes) sans nouveau coup avant de considérer que
# la séance est terminée et de forcer un flush().
LOGGER_END_SESSION_TIMEOUT = 10.0 # seconds

# LOGGER_FORMAT choisi de créer un .csv OU un .zip contenant un .csv
LOGGER_FORMAT_CSV = "csv"
LOGGER_FORMAT_ZIP = "zip"
LOGGER_FORMAT = LOGGER_FORMAT_ZIP

# ----------------------------------------------------------------------
# Replay
# ----------------------------------------------------------------------

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
USE_REPLAY = False
USE_REPLAY_WORKOUT = False

# Le fichier REPLAY_FILE peut être:
# * un .csv
# * un .zip ayant un (et un seul) .csv à l'intérieur
REPLAY_FILE = (
    #f"{LOGS_DIR}/session_20260824_172641.zip" # Choose Log to replay (csv ou zip)
    f"{LOGS_DIR}/session_20260908_102813.zip"
)
REPLAY_WORKOUT_FILE = (
    f"{WORKOUTS_DIR}/ex17.wo"
)

REPLAY_SPEED = 10.0 # 1.0: temps réel, 10: 10x plus rapide, 100: 100x plus rapide, etc.

# ----------------------------------------------------------------------
# Workout
# ----------------------------------------------------------------------

DELAY_SECONDS = 15
FPS = 50

WORKOUT_WIDTH = 720 # pixels

TITLE_FONT_SIZE = 24
BIG_FONT_SIZE = 22
LIST_FONT_SIZE = 14

LIST_WIDTH = 220
BAR_HEIGHT = 28
METRONOME_MARGIN = 100

WINDOW_BACKGROUND = "#303030"
LIST_BACKGROUND = "#202020"
BAR_BACKGROUND = "#202020"
MENU_SEL_BACKGROUND = "#505050"
BAR_BORDER = "#666666"
BAR_COLOR = "#00CC44"
TEXT_COLOR = "white"
LISTTEXT_COLOR = TEXT_COLOR

PART_DICT = {
    "O": "OPTIONEL",
    "A": "Arms",
    "C": "Core",
    "L": "Legs",
    "AC": "Arms+Core",
    "LC": "Legs+Core",
}

INTENSITY_DICT = {
    "R": "Recovery (Très facile)",
    "E": "Active Recovery / Facile",
    "N": "Normale",
    "F": "Forte",
    "M": "Max / Très Forte",
}

INTENSITY_COLORS = {
    "R": "#7FDBFF",
    "E": "#0055FF",
    "N": "#00AA00",
    "F": "#DD2222",
    "M": "#BB44DD",
}

# ----------------------------------------------------------------------
# Analyzer et Plot_Wo
# ----------------------------------------------------------------------

ANALYZER_WIDTH  = 1400 # pixels
ANALYZER_HEIGHT = 1000 # pixels

PLOTWO_WIDTH  = 1000 # pixels
PLOTWO_HEIGHT =  800 # pixels

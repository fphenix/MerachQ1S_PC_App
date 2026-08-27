VERSION = 3.3

GUI_REFRESH_MS = 100 # miliseconds

WINDOW_TITLE = "Rower PM Monitor"
WINDOW_WIDTH = 1200 # pixels
WINDOW_HEIGHT = 700 # pixels

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
# Cela permet de valider une modification au script sans avoir se
# connecter au rameur pour faire un test. Il suffit de rejouer un
# ancien log pour simuler le BT d'une séance de rameur et valider
# le nouveau code.
# Dans ce cas USE_REPKAY est "True" et le nom du log est dans
# REPLAY_FILE (on peut utiliser un csv ou un csv zippé).
# Pour passer en mode normal (c-à-d Data venant du Q1S
# via BlueTooth), mettre USE_REPLAY à "False".
# ----------------------------------------------------------------------

# Normal Mode vs. Replay Mode : USE_REPLAY
# * False : (Mode Normal) BT vient du rameur ou
# * True  : (Mode Dvp/Debug) BT émulé en rejouant une session loggée précédente.
USE_REPLAY = False

# Le fichier REPLAY_FILE peut être:
# * un .csv
# * un .zip ayant un (et un seul) .csv à l'intérieur
REPLAY_FILE = (
    "logs/session_20260824_172641.zip" # Choose Log to replay (csv ou zip)
)

REPLAY_SPEED = 50.0 # 1.0: temps réel, 10: 10x plus rapide, 100: 100x plus rapide, etc.

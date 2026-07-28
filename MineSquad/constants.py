# Coefficient Concept2.
# Peut être ajusté expérimentalement pour le Merach Q1S.
DRAG_FACTOR  = 2.8

GUI_REFRESH_MS = 100
CADENCE_WINDOW = 5
CADENCE_SMOOTHING = 3
CALORIE_OFFSET = 300.0

WINDOW_TITLE = "Merach PM Monitor"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700

# BlueTooth address of your Q1S Merach machine. Use a BT scanner to get it.
# Adresse Bluetooth du rameur Merach Q1S. Utiliser un scanner BT pour l'obtenir
ROWER_ADDRESS = "24:00:0C:A0:A2:E7"


# ----------------------------------------------------------------------
# Logger
# ----------------------------------------------------------------------

# Intervalle (en secondes) entre deux flush() du fichier CSV.
# Permet de limiter les pertes de données en cas d'arrêt brutal.
LOGGER_FLUSH_PERIOD = 5.0

# Temps (en secondes) sans nouveau coup avant de considérer que
# la séance est terminée et de forcer un flush().
LOGGER_END_SESSION_TIMEOUT = 10.0

# ----------------------------------------------------------------------
# Source de Données (Bluetooth vs. Replay Log)
# On peut relancer une séance rameur en "rejouant" un log.
# Cela permet de valider une modification au script sans avoir se
# connecter au rameur pour faire un test. Il suffit de rejouer un
# ancien log to simuler une séance de rameur et valider le nouveau code.
# Dans ce cas USE_REPKAY est "True" et le nom du log est dans
# REPLAY_FILE. Pour passer en mode normal (Data venant du Q1S
# via BlueTooth), mettre USE_REPLAY à "False".
# ----------------------------------------------------------------------

USE_REPLAY = False # False or True

REPLAY_FILE = (
    "logs/session_20260718_164643.csv" # Choose Log to replay
)

REPLAY_SPEED = 1.0

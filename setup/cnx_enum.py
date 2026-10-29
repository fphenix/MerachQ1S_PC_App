from enum import Enum

# =============================================================================
class CnxState(Enum):
    CONNECTED: int    = 0
    SEEKING: int      = 1
    DISCONNECTED: int = 2
    PAUSE: int        = 3
    STOP: int         = 4
    REPLAY: int       = 5

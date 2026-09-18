from enum import Enum

# =============================================================================
class CnxState(Enum):
    CONNECTED    = 0
    SEEKING      = 1
    DISCONNECTED = 2
    PAUSE        = 3
    STOP         = 4
    REPLAY       = 5

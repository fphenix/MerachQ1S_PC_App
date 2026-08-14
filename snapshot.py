from dataclasses import dataclass

from rowers.data import RowerData
from session import SessionData

# =============================================================================
@dataclass(slots=True)
class Snapshot:
    
    rowerdata: RowerData
    session: SessionData


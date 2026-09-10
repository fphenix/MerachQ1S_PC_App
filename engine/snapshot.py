from dataclasses import dataclass

from rowers.data import RowerData

# =============================================================================
@dataclass(slots=True)
class Snapshot:
    
    rowerdata: RowerData

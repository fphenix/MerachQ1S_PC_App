# L'Abstract class va imposer l'interface aux class filles.
# Toutes les méthodes définies comme "abstract méthod" doivent
# être définies dans la class qui hérite de RowerClient
from abc import ABC, abstractmethod

from rowers.data import RowerData

# =============================================================================
class RowerClient(ABC):

    def __init__(self, address: str, state, settings) -> None:
        
        self.address: str = address
        self.state = state

        self.settings = settings

    # -------------------------------------------------------------------------
    def process(
        self,
        rowerdata: RowerData,
        delta_elapsed: float,
    ) -> RowerData:
        
        return rowerdata

    # -------------------------------------------------------------------------
    # Abstract
    @abstractmethod
    def start(self) -> None:
        pass

    # -------------------------------------------------------------------------
    # Abstract
    @abstractmethod
    def stop(self) -> None:
        pass

    # -------------------------------------------------------------------------
    # Abstract
    @abstractmethod
    def reset(self) -> None:
        pass

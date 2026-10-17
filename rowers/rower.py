# L'Abstract class va imposer l'interface aux class filles.
# Toutes les méthodes définies comme "abstract méthod" doivent
# être définies dans la class qui hérite de RowerClient
from abc import ABC, abstractmethod

from setup.settings import Settings

from engine.state import RowState

from rowers.data import RowerData

# =============================================================================
class RowerClient(ABC):

    def __init__(
        self,
        address: str,
        state: RowState,
        settings: Settings
    ) -> None:
        
        self.address: str = address
        self.state: RowState = state

        self.settings: Settings = settings

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

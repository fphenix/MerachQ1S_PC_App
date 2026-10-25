# L'Abstract class va imposer l'interface aux class filles.
# Toutes les méthodes définies comme "abstract méthod" doivent
# être définies dans la class qui hérite de RowerClient
from abc import ABC, abstractmethod
from typing import Any

from setup.settings import Settings

from rowers.data import RowerData

# =============================================================================
class RowerClient(ABC):

    def __init__(
        self,
        address: str,
        state: Any,
        settings: Settings
    ) -> None:
        
        self.address: str = address
        self.state: Any = state

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
    def reset_session_metrics(self) -> None:
        """Reset derived metrics without resetting the live transport/cache."""
        return None

    # -------------------------------------------------------------------------
    # Abstract
    @abstractmethod
    def reset(self) -> None:
        """Reset/reinitialize the rower client itself, not a session split."""
        pass

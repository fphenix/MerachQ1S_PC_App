"""Données d'entrée communes aux jeux."""

from dataclasses import dataclass

# =============================================================================
@dataclass(slots=True)
class GameInput:

    spm: float = 0.0
    raw_spm: float = 0.0

    elapsed: float = 0.0

    stroke_event: bool = False
    stroke_count: int = 0
    stroke_delta: int = 0

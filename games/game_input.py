"""Données d'entrée communes aux jeux."""

from __future__ import annotations
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



# =============================================================================
def input_cadence(game_input: GameInput) -> float | None:
    """Renvoie la cadence mesurée ou estimée, sinon None."""

    cadence = game_input.raw_spm or game_input.spm
    return float(cadence) if cadence > 0.0 else None

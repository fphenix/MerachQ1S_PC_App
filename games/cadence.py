""" Utilitaires génériques de cadence partagés par les jeux """

from __future__ import annotations

from games.game_input import GameInput

# =============================================================================
def input_cadence(game_input: GameInput) -> float | None:
    """Renvoie la cadence mesurée ou estimée, sinon None."""

    cadence = game_input.raw_spm or game_input.spm
    return float(cadence) if cadence > 0.0 else None

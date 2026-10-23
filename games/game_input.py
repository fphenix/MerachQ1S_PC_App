"""Données d'entrée communes aux jeux."""

from __future__ import annotations
from dataclasses import dataclass

MIN_VALID_CADENCE = 10.0
MAX_VALID_CADENCE = 40.0
MAX_CADENCE_AGE_SECONDS = 5.5

# =============================================================================
@dataclass(slots=True)
class GameInput:

    spm: float = 0.0
    raw_spm: float = 0.0

    elapsed: float = 0.0

    stroke_event: bool = False
    stroke_count: int = 0
    stroke_delta: int = 0
    cadence_age: float = 0.0

# =============================================================================
def resolve_game_cadence(
    raw_spm: float,
    measured_spm: float,
    estimated_spm: float,
) -> float:
    """Choisit la meilleure source de cadence, sans correction empirique.

    La cadence calculée par le pipeline du rameur reste la référence de jeu.
    La valeur brute peut être instantanée/bruitée et ne doit pas écraser une
    cadence calculée valide (notamment quand raw_spm sous-estime la cible).
    L'estimation perf_counter sert ensuite de secours avant la valeur brute.
    """

    for value in (measured_spm, estimated_spm, raw_spm):
        try:
            cadence = float(value)
        except (TypeError, ValueError):
            continue
        if MIN_VALID_CADENCE <= cadence <= MAX_VALID_CADENCE:
            return cadence

    return 0.0

# =============================================================================
def input_cadence(game_input: GameInput) -> float | None:
    """Renvoie la première cadence valide, sinon None."""

    # La cadence est maintenue entre deux coups, mais ne doit pas rester valable
    # indéfiniment après l'arrêt du rameur. cadence_age=0 préserve la compatibilité
    # des GameInput construits directement (tests et simulations).
    if game_input.cadence_age > MAX_CADENCE_AGE_SECONDS:
        return None

    # Ne pas borner une valeur aberrante à 10 ou 40 : cela la transformerait en
    # cadence apparemment valide et pourrait déclencher une mécanique de jeu.
    for value in (game_input.spm, game_input.raw_spm):
        try:
            cadence = float(value)
        except (TypeError, ValueError):
            continue
        if MIN_VALID_CADENCE <= cadence <= MAX_VALID_CADENCE:
            return cadence

    return None

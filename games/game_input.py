"""
Données d'entrée communes aux jeux.

La chaîne de Cadence est:

* GameWidget._update_game (Détecte les nouveaux coups, calcule stroke_delta et estime éventuellement la cadence avec perf_counter.) 
    - Données du rameur Q1S arrive au GameWidget via le Snapshot de RowerData (rowerdata.cadence · raw_stroke_rate · stroke_count)
    - appel à resolve_game_cadence() de game_input (Choisit une source : cadence mesurée, estimation locale ou valeur brute.)
    - Instanciation de GameInput (ransmet spm, raw_spm, cadence_age, stroke_event, stroke_count et stroke_delta)
* Game.update() puis update_game() (socle commun gère les phases du jeu, puis chaque moteur applique ses règles.)
* engine.py des jeux appellent input_cadence(game_input) (Vérifie la fraîcheur de la cadence et renvoie une valeur utilisable ou None.)
Le mode debug par SPACE suit un chemin distinct : il calcule sa cadence à partir des frappes successives, sans laisser une ancienne cadence du Q1S prendre le dessus.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from collections import deque
from statistics import median

from setup.utils import is_between

MIN_VALID_CADENCE: float = 10.0
MAX_VALID_CADENCE: float = 40.0
MAX_CADENCE_AGE_SECONDS: float = 5.5

# Stratégies comparables sur le Q1S :
# - "historical" : cadence lissée, puis estimation par intervalle, puis raw.
#    Moins réactif mais moins de bruit.
# - "single_interval" : estimation du dernier intervalle en priorité.
#   Privilégie l'estimation calculée entre les derniers coups détectés.
#   Plus réactive mais plus bruitée.
# - "short_window" : médiane des derniers échantillons raw distincts.
#    Compromis des deux autres.
CADENCE_WINDOW_SIZE: int = 2
class GameCadenceMode(Enum):
    HISTORICAL: str = "historical"
    RESPONSIVE: str = "single_interval" # inutilisable, trop de bruit
    SHORT_WINDOW: str = "short_window"

GAME_CADENCE_MODE: GameCadenceMode = GameCadenceMode.SHORT_WINDOW

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
class ShortWindowCadenceFilter:
    """Filtre court de la cadence brute, échantillonné une fois par donnée Q1S distincte.

    Les ticks du Q1S arrivent environ chaque seconde. La cadence brute peut être
    plus réactive que la cadence lissée, mais présenter des valeurs isolées.
    Une médiane sur CADENCE_WINDOW_SIZE échantillons rejette certains pics isolés
    sans la latence d'une moyenne longue. Le sample_key empêche d'ajouter plusieurs
    fois la même donnée quand le widget est rafraîchi à 30 FPS entre deux paquets.
    """

    def __init__(self) -> None:

        self._samples: deque[float] = deque(maxlen=CADENCE_WINDOW_SIZE)
        self._last_sample_key: tuple[float, int, float] | None = None

    # -------------------------------------------------------------------------
    def reset(self) -> None:
        self._samples.clear()
        self._last_sample_key = None

    # -------------------------------------------------------------------------
    def update(
        self,
        raw_spm: float,
        sample_key: tuple[float, int, float],
    ) -> float | None:
        """Ajoute une nouvelle observation et renvoie la médiane si prête."""

        if sample_key != self._last_sample_key:
            self._last_sample_key = sample_key
            try:
                cadence = float(raw_spm)
            except (TypeError, ValueError):
                cadence = 0.0

            if is_between(cadence, MIN_VALID_CADENCE, MAX_VALID_CADENCE):
                # self._sample is a deque queue of maxlen=CADENCE_WINDOW_SIZE, therefore
                # it keeps the last CADENCE_WINDOW_SIZE items appended into it.
                self._samples.append(cadence)

        if len(self._samples) < CADENCE_WINDOW_SIZE:
            return None

        return float(median(self._samples))

# =============================================================================
def resolve_game_cadence(
    raw_spm: float,
    measured_spm: float,
    estimated_spm: float,
    filtered_raw_spm: float | None = None,
) -> float:
    """Choisit la meilleure source de cadence, sans correction empirique.

    Plusieurs stratégies sont disponibles pour faciliter la comparaison sur le Q1S.

    - Mode réactif : privilégie estimated_spm, calculé depuis l'intervalle entre
      les coups détectés par perf_counter. Un changement de rythme peut donc être
      pris en compte dès le coup suivant, sans attendre le lissage du rameur.
    - Mode historique : privilégie measured_spm, mais le filtre réduit la réactivité.
    - Filtrage fenêtre courte

    La cadence brute reste le dernier recours : elle a déjà présenté des écarts
    notables par rapport à la cadence réelle sur le Q1S.
    """

    if GAME_CADENCE_MODE == GameCadenceMode.RESPONSIVE: # Inutilisable
        candidates = (estimated_spm, measured_spm, raw_spm)

    elif GAME_CADENCE_MODE == GameCadenceMode.SHORT_WINDOW:
        # Tant que la fenêtre n'est pas remplie, utiliser les sources historiques.
        if filtered_raw_spm is not None:
            candidates = (filtered_raw_spm, measured_spm, estimated_spm, raw_spm)
        else:
            candidates = (measured_spm, estimated_spm, raw_spm)

    elif GAME_CADENCE_MODE == GameCadenceMode.HISTORICAL:
        candidates = (measured_spm, estimated_spm, raw_spm)

    else:
        raise ValueError(f"Unknown GAME_CADENCE_MODE: {GAME_CADENCE_MODE!r}")

    for value in candidates:
        try:
            cadence = float(value)
        except (TypeError, ValueError):
            continue

        if is_between(cadence, MIN_VALID_CADENCE, MAX_VALID_CADENCE):
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

        if is_between(cadence, MIN_VALID_CADENCE, MAX_VALID_CADENCE):
            return cadence

    return None

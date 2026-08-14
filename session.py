from dataclasses import dataclass

# =============================================================================
@dataclass(slots=True)
class SessionData:
    
    # travail développée
    work_j: float = 0.0
    work_per_stroke: float = 0.0

    # distance calculée par intégration
    distance: float = 0.0

    # distance/coup
    distance_per_stroke: float = 0.0

    # vitesse
    speed: float = 0.0
    speed_avg: float = 0.0

    # cadence
    cadence: float = 0.0            # cadence instantanée lissée
    cadence_raw: float = 0.0        # cadence instantanée non lissée
    cadence_avg: float = 0.0        # cadence moyenne sur la séance

    # split
    split: float = 0.0
    split_avg: float = 0.0

    # calories calculées
    calories: float = 0.0
    calories_rate: float = 0.0

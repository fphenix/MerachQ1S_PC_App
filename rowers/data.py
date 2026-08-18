from dataclasses import dataclass

# =============================================================================
@dataclass(slots=True)
class RowerData:
    connection: str = "Recherche..."

    elapsed_time: float = 0.0
    delta_strokes: int = 0
    stroke_event: bool = False

    stroke_count: int = 0

    distance: float = 0.0
    distance_per_stroke: float = 0.0

    power: float = 0.0
    power_avg: float = 0.0

    speed: float = 0.0
    speed_avg: float = 0.0

    cadence_raw: float = 0.0    # cadence instantanée non lissée
    cadence: float = 0.0        # cadence instantanée lissée
    cadence_avg: float = 0.0    # cadence moyenne sur la session

    split_inst: float = 0.0
    split_avg: float = 0.0

    calories_rate:float = 0.0
    calories: float = 0.0
    calories_hour: float = 0.0
    calories_minute: float = 0.0

    work_j: float = 0.0
    work_per_stroke: float = 0.0

    resistance_level: int = 0
    training_status: int = 0
    heart_rate: int = 0

    # -------------------------------------------------------------------------
    # Valeurs brutes reçues du rameur.
    # Ces valeurs ne doivent jamais être modifiées par les calculateurs.
    raw_distance: float = 0.0

    raw_stroke_rate: float = 0.0        # cadence_raw
    raw_stroke_rate_avg: float = 0.0    # cadence_raw average

    raw_split_inst: float = 0.0
    raw_split_avg: float = 0.0

    raw_calories: float = 0.0
    raw_calories_hour: float = 0.0
    raw_calories_minute: float = 0.0

    raw_resistance: int = 0
    raw_training_status: int = 0
    raw_heart_rate: int = 0

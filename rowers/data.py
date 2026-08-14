from dataclasses import dataclass

# =============================================================================
@dataclass(slots=True)
class RowerData:
    connection: str = "Recherche..."

    elapsed_time: float = 0

    delta_strokes: int = 0
    stroke_event: bool = False

    distance: float = 0
    distance_per_stroke: float = 0.0

    power: float = 0
    power_avg: float = 0

    stroke_rate: float = 0
    stroke_rate_avg: float = 0

    stroke_count: int = 0

    speed: float = 0.0
    speed_avg: float = 0.0

    cadence_raw: float = 0.0    # cadence instantanée non lissée
    cadence: float = 0.0        # cadence instantanée lissée

    split_inst: float = 0
    split_avg: float = 0

    kcal_rate:float = 0
    kcal: float = 0

    energy_hour: float = 0
    energy_minute: float = 0

    work_j: float = 0.0
    work_per_stroke: float = 0.0

    resistance_level: int = 0

    training_status: int = 0

    heart_rate: int = 0

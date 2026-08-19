from dataclasses import dataclass

# =============================================================================
@dataclass(slots=True)
class RowerData:

    connection: str = "Recherche..."

    elapsed_time: float = 0.0               # session time
    delta_strokes: int = 0                  # nb of strokes between packets
    stroke_event: bool = False              # True of a stroke occured

    stroke_count: int = 0                   # Number of strokes

    distance: float = 0.0                   # distance in meters
    distance_per_stroke: float = 0.0        # distance (m) per stroke

    power: float = 0.0                      # Power inst (W)
    power_avg: float = 0.0                  # Power average (W)

    speed: float = 0.0                      # speed inst (m/s)
    speed_avg: float = 0.0                  # speed average (m/s)

    cadence_raw: float = 0.0                # cadence (strokes per minute) instantanée non lissée
    cadence: float = 0.0                    # cadence (strokes per minute) instantanée lissée
    cadence_avg: float = 0.0                # cadence (strokes per minute) moyenne sur la session

    split_inst: float = 0.0                 # time inst per 500m
    split_avg: float = 0.0                  # time average per 500m

    calories_rate: float = 0.0              # calories inst (kcal/s)
    calories: float = 0.0                   # calories total (kcal)
    calories_hour: float = 0.0              # calories (kcal) per hour
    calories_minute: float = 0.0            # calories (kcal) per minute

    work_j: float = 0.0                     # Total Work (J)
    work_per_stroke: float = 0.0            # Work per stroke (J/stroke)

    resistance_level: int = 0               # resistance (number)
    training_status: int = 0                # training status (FTMS code, 13=Manual Mode)
    heart_rate: int = 0                     # Heart rate (pulse/min) : Not available on Q1S)

    # -------------------------------------------------------------------------
    # Valeurs brutes reçues du rameur.
    # Ces valeurs ne doivent jamais être modifiées par les calculateurs.
    raw_distance: float = 0.0               # Raw distance in meters

    raw_stroke_rate: float = 0.0            # Raw cadence_raw (strokes per minute)
    raw_stroke_rate_avg: float = 0.0        # Raw cadence_raw average

    raw_split_inst: float = 0.0             # Raw time inst per 500m
    raw_split_avg: float = 0.0              # Raw time average per 500m

    raw_calories: float = 0.0               # Raw calories total (kcal)
    raw_calories_hour: float = 0.0          # Raw calories (kcal) per hour
    raw_calories_minute: float = 0.0        # Raw calories (kcal) per minute

    raw_resistance: int = 0                 # Raw resistance (number)
    raw_training_status: int = 0            # Raw training status (FTMS code, 13=Manual Mode)
    raw_heart_rate: int = 0                 # Raw Heart rate (pulse/min) : Not available on Q1S)

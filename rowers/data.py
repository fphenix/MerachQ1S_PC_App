from dataclasses import dataclass

# =============================================================================
@dataclass(slots=True)
class RowerData:

    connection: str = "Recherche..."

    delta_strokes: int = 0                  # nb of strokes between packets
    stroke_event: bool = False              # True of a stroke occured
    elapsed_time: float = 0.0               # Temps mains indépendant de la Machine, revient à 0 en cas de "Nouvelle Session"
    stroke_count: int = 0                   # Number of strokes (remis à 0 si "Nouvelle Session")

    distance: float = 0.0                   # distance in meters
    distance_per_stroke: float = 0.0        # distance (m) per stroke

    speed: float = 0.0                      # speed inst (m/s)
    speed_avg: float = 0.0                  # speed average (m/s)

    cadence_inst: float = 0.0               # cadence ou stroke_rate (strokes per minute) instantanée, calculée non lissée
    cadence: float = 0.0                    # cadence ou stroke_rate (strokes per minute) instantanée lissée
    cadence_avg: float = 0.0                # cadence ou stroke_rate (strokes per minute) moyenne sur la session

    split_inst: float = 0.0                 # time inst per 500m
    split_avg: float = 0.0                  # time average per 500m

    calories_rate: float = 0.0              # calories inst (kcal/s)
    calories: float = 0.0                   # calories total (kcal)
    calories_hour: float = 0.0              # calories (kcal) per hour
    calories_minute: float = 0.0            # calories (kcal) per minute

    work_j: float = 0.0                     # Total Work (J)
    work_per_stroke: float = 0.0            # Work per stroke (J/stroke)

    resistance_level: int = 0               # resistance (number)
    training_status: int = 0                # training status (eg. FTMS code, 13=Manual Mode)
    heart_rate: int = 0                     # Heart rate (pulse/min) : Not available on Q1S)

    # -------------------------------------------------------------------------
    # Valeurs brutes reçues du rameur.
    # Ces valeurs ne doivent jamais être modifiées par les calculateurs.
    raw_elapsed_time: float = 0.0           # Rower session time
    raw_distance: float = 0.0               # Rower distance in meters

    raw_stroke_count: int = 0               # Rower Number of strokes

    raw_stroke_rate: float = 0.0            # Rower cadence inst (strokes per minute)
    raw_stroke_rate_avg: float = 0.0        # Rower cadence average

    raw_power: float = 0.0                  # Rower Power inst (W)
    raw_power_avg: float = 0.0              # Rower Power average (W)

    raw_split_inst: float = 0.0             # Rower time inst per 500m
    raw_split_avg: float = 0.0              # Rower time average per 500m

    raw_calories: float = 0.0               # Rower calories total (kcal)
    raw_calories_hour: float = 0.0          # Rower calories (kcal) per hour
    raw_calories_minute: float = 0.0        # Rower calories (kcal) per minute

    raw_resistance: int = 0                 # Rower resistance (number)
    raw_training_status: int = 0            # Rower training status (eg. FTMS code, 13=Manual Mode)
    raw_heart_rate: int = 0                 # Rower Heart rate (pulse/min) : Not available on Q1S)

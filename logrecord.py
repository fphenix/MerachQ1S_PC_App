from dataclasses import dataclass

# Column Title, variable holding the data
CSV_FIELDS = [
    ("Packet", "packet"),

    ("PC_Time", "pc_time"),
    ("Delta_PC", "delta_pc"),

    ("Elapsed", "elapsed"),
    ("Delta_Elapsed", "delta_elapsed"),

    ("Power", "power"),
    ("Power_Avg", "power_avg"),

    ("Stroke_Count", "stroke_count"),
    ("Delta_Strokes", "delta_strokes"),
    ("Stroke_Event", "stroke_event"),

    ("Speed", "speed"),
    ("Speed_Avg", "speed_avg"),

    ("Distance", "distance"),

    ("Cadence", "cadence_raw"),
    ("Cadence_Inst", "cadence"),
    ("Cadence_Avg", "cadence_avg"),

    ("Split", "split"),
    ("Split_Avg", "split_avg"),

    ("Distance_Per_Stroke", "distance_per_stroke"),

    ("Calories_Rate", "calories_rate"),
    ("Calories", "calories"),

    ("Work_J", "work_j"),
    ("Work_Per_Stroke", "work_per_stroke"),

    ("Raw_Distance", "raw_distance"),
    ("Raw_Stroke_Rate", "raw_stroke_rate"),
    ("Raw_Stroke_Rate_Avg", "raw_stroke_rate_avg"),

    ("Raw_Split_Instant", "raw_split_inst"),
    ("Raw_Split_Avg", "raw_split_avg"),

    ("Raw_Energy", "raw_calories"),
    ("Raw_Energy_Hour", "raw_calories_hour"),
    ("Raw_Energy_Minute", "raw_calories_minute"),

    ("Raw_Resistance", "raw_resistance"),
    ("Raw_Training_Status", "raw_training_status"),
    ("Raw_Heart_Rate", "raw_heart_rate"),
]

# =============================================================================
@dataclass(slots=True)
class LogRecord:

    packet: int = 0

    pc_time: float = 0.0
    delta_pc: float = 0.0

    elapsed: float = 0.0
    delta_elapsed: float = 0.0

    power: float = 0.0
    power_avg: float = 0.0

    stroke_count: int = 0
    delta_strokes: int = 0
    stroke_event: bool = False

    speed: float = 0.0
    speed_avg: float = 0.0

    distance: float = 0.0

    cadence_raw: float = 0.0
    cadence: float = 0.0
    cadence_avg: float = 0.0

    split: float = 0.0
    split_avg: float = 0.0

    distance_per_stroke: float = 0.0

    calories_rate: float = 0.0
    calories: float = 0.0

    work_j: float = 0.0
    work_per_stroke: float = 0.0

    #
    # Données brutes (FTMS pour Q1S)
    #

    raw_distance: float = 0.0
    raw_stroke_rate: float = 0.0
    raw_stroke_rate_avg: float = 0.0

    raw_split_inst: float = 0.0
    raw_split_avg: float = 0.0

    raw_calories: float = 0.0
    raw_calories_hour: float = 0.0
    raw_calories_minute: float = 0.0

    raw_resistance: int = 0
    raw_training_status: int = 0
    raw_heart_rate: int = 0

    # -------------------------------------------------------------------------
    @classmethod
    def csv_header(cls):
        return [header for header, _ in CSV_FIELDS]

    # -------------------------------------------------------------------------
    def csv_row(self):
        return [getattr(self, field_name) for _, field_name in CSV_FIELDS]

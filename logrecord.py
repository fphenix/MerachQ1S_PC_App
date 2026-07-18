from dataclasses import dataclass


@dataclass(slots=True)
class LogRecord:

    packet: int

    pc_time: float
    delta_pc: float

    elapsed: float
    delta_elapsed: float

    power: float
    power_avg: float

    stroke_count: int
    delta_strokes: int
    stroke_event: bool

    speed: float
    speed_avg: float

    distance: float

    cadence: float
    cadence_avg: float

    split: float
    split_avg: float

    distance_per_stroke: float

    calories: float

    #
    # Données FTMS brutes
    #

    ftms_distance: float
    ftms_spm: float
    ftms_spm_avg: float
    ftms_split_avg: float
    ftms_energy: float

    def csv_header(self):

        return [

            "Packet",

            "PC_Time",
            "Delta_PC",

            "Elapsed",
            "Delta_Elapsed",

            "Power",
            "Power_Avg",

            "Stroke_Count",
            "Delta_Strokes",
            "Stroke_Event",

            "Speed",
            "Speed_Avg",

            "Distance",

            "Cadence",
            "Cadence_Avg",

            "Split",
            "Split_Avg",

            "Distance_Per_Stroke",

            "Calories",

            "FTMS_Distance",
            "FTMS_SPM",
            "FTMS_SPM_Avg",
            "FTMS_Split_Avg",
            "FTMS_Energy",
        ]

    def csv_row(self):

        return [

            self.packet,

            self.pc_time,
            self.delta_pc,

            self.elapsed,
            self.delta_elapsed,

            self.power,
            self.power_avg,

            self.stroke_count,
            self.delta_strokes,
            self.stroke_event,

            self.speed,
            self.speed_avg,

            self.distance,

            self.cadence,
            self.cadence_avg,

            self.split,
            self.split_avg,

            self.distance_per_stroke,

            self.calories,

            self.ftms_distance,
            self.ftms_spm,
            self.ftms_spm_avg,
            self.ftms_split_avg,
            self.ftms_energy,

        ]
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
    work_j: float

    #
    # Données FTMS brutes
    #

    ftms_distance: float
    ftms_spm: float
    ftms_spm_avg: float

    ftms_split_inst: float
    ftms_split_avg: float

    ftms_energy: float
    ftms_energy_hour: float
    ftms_energy_minute: float

    ftms_resistance: int
    ftms_training_status: int
    ftms_heart_rate: int

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
            "Work_J",

            "FTMS_Distance",

            "FTMS_SPM",
            "FTMS_SPM_Avg",

            "FTMS_Split_Instant",
            "FTMS_Split_Avg",

            "FTMS_Energy",
            "FTMS_Energy_Per_Hour",
            "FTMS_Energy_Per_Minute",

            "FTMS_Resistance",

            "FTMS_Training_Status",

            "FTMS_Heart_Rate",
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
            self.work_j,

            self.ftms_distance,

            self.ftms_spm,
            self.ftms_spm_avg,

            self.ftms_split_inst,
            self.ftms_split_avg,

            self.ftms_energy,
            self.ftms_energy_hour,
            self.ftms_energy_minute,

            self.ftms_resistance,

            self.ftms_training_status,

            self.ftms_heart_rate,
        ]
from collections import deque
from PySide6.QtGui import QColor

from setup.lang import get_text
from setup.constants import (
    INTENSITY_DICT_KEYS,
    PART_DICT_KEYS,
    WO_KEYWORD,
    FILE_ENCODING,
)

from workout.workout import Workout
from workout.step import WorkoutStep

# -----------------------------------------------------------------------------
def load_workout(filename: str) -> Workout:

    workout = Workout(filename)

    title: str | None = None
    field: str | None = None
    pending_info: str | None = None
    pending_comment: str | None = None

    with open(
        filename,
        "r",
        encoding= FILE_ENCODING,
    ) as rfile:

        for lineno, raw in enumerate(
            rfile,
            start= 1,
        ):

            line = raw.strip()

            if not line:
                continue

            #
            # Commentaires "#"
            #

            if line.startswith(WO_KEYWORD["Comment"]):

                new_comment = line.lstrip(WO_KEYWORD["Comment"]).strip()

                if not new_comment:
                    print(
                        f"{get_text("WO_FILE_WARNING_LINE")} {lineno}: ",
                        get_text("WO_FILE_EMPTY_CMT")
                    )
                    
                    continue

                if pending_comment is not None:
                    print(
                        f"{get_text("WO_FILE_WARNING_LINE")} {lineno}: ",
                        get_text("WO_FILE_CONSEC_CMT")
                    )

                    pending_comment = (
                        f"{pending_comment} ; {new_comment}"
                    )

                else:
                    pending_comment = new_comment

                continue

            #
            # Information Etape : "INFO:"
            #

            upper = line.upper()

            if upper.startswith(WO_KEYWORD["Info"]):
                new_info = line[len(WO_KEYWORD["Info"]):].strip()

                if not new_info:
                    print(
                        f"{get_text("WO_FILE_WARNING_LINE")} {lineno}: ",
                        get_text("WO_FILE_EMPTY_INFO")
                    )

                    continue

                if pending_info is not None:
                    print(
                        f"{get_text("WO_FILE_WARNING_LINE")} {lineno}: ",
                         get_text("WO_FILE_CONSEC_INFO")
                    )

                    pending_info = (
                        f"{pending_info} ; {new_info}"
                    )

                else:
                    pending_info = new_info

                continue

            #
            # Workout Titre : "WORKOUT:"
            #

            if upper.startswith(WO_KEYWORD["Title"]):
                if title is not None:
                    raise ValueError(
                        f"{get_text("WO_FILE_ERROR_LINE")} {lineno}: ",
                        f"{get_text("WO_FILE_KEYWORD")} ",
                        f"{WO_KEYWORD["Title"]} ",
                        get_text("WO_FILE_KW_UNIQUE")
                    )

                title = line[len(WO_KEYWORD["Title"]):].strip()

                workout.title = (
                    title
                    if title
                    else "Placeholder Workout"
                )

                continue

            #
            # Field : "FIELD:"
            #

            if upper.startswith(WO_KEYWORD["Field"]):
                if field is not None:
                    raise ValueError(
                        f"{get_text("WO_FILE_ERROR_LINE")} {lineno}: ",
                        f"{get_text("WO_FILE_KEYWORD")} ",
                        f"{WO_KEYWORD["Field"]} ",
                        get_text("WO_FILE_KW_UNIQUE")
                    )

                field = line[len(WO_KEYWORD["Field"]):].strip()

                workout.field = (
                    field
                    if field
                    else "Placeholder Field"
                )

                continue

            #
            # Data : time spm intensity <part>
            #

            parts = line.split()

            if len(parts) not in (3, 4):
                raise ValueError(
                    f"{get_text("WO_FILE_ERROR_LINE")} {lineno}: ",
                    get_text("WO_FILE_EXPECTED_DATA")
                )

            try:
                duration_seconds = float(parts[0])
                spm = int(parts[1])
                intensity = str(parts[2])
                part = (
                    str(parts[3])
                    if len(parts) == 4
                    else None
                )

            except ValueError:
                raise ValueError(
                    f"{get_text("WO_FILE_ERROR_LINE")} {lineno}: ",
                    get_text("WO_FILE_EXP_DATA_TYPE")
                )

            if not is_between(
                duration_seconds, 0.0, 7200.0,
                strict_min= True,
                strict_max= False
            ):
                raise ValueError(
                    f"{get_text("WO_FILE_ERROR_LINE")} {lineno}: ",
                    get_text("WO_FILE_EXP_DURATION")
                )

            if not is_between(
                spm, 0, 50,
                strict_min= True, strict_max= False
            ):
                raise ValueError(
                    f"{get_text("WO_FILE_ERROR_LINE")} {lineno}: ",
                    get_text("WO_FILE_EXP_SPM")
                )

            if intensity not in INTENSITY_DICT_KEYS:
                raise ValueError(
                    f"{get_text("WO_FILE_ERROR_LINE")} {lineno}: ",
                    get_text("WO_FILE_EXP_INTENSITY")
                )

            if part is not None and part not in PART_DICT_KEYS:
                raise ValueError(
                    f"{get_text("WO_FILE_ERROR_LINE")} {lineno}: ",
                    f"{get_text("WO_FILE_EXP_PART")} : {PART_DICT_KEYS}"
                )

            workout.steps.append(
                WorkoutStep(
                    duration_seconds= duration_seconds,
                    spm= spm,
                    intensity= intensity,
                    part= part,
                    info= pending_info,
                    comment= pending_comment,
                )
            )

            pending_info = None
            pending_comment = None

    if pending_info is not None:
        print(
            f"{get_text("WO_FILE_WARNING_LINE")} {lineno}: ",
            get_text("WO_FILE_EOF_INFO")
        )

    if pending_comment is not None:
        print(
            f"{get_text("WO_FILE_WARNING_LINE")} {lineno}: ",
            get_text("WO_FILE_EOF_CMT")
        )

    if not workout.steps:
        raise ValueError(
            f"{get_text("WO_FILE_ERROR_LINE")} {lineno}: ",
            get_text("WO_FILE_EMPTY")
        )

    return workout

# -----------------------------------------------------------------------------
# These are just "print()" renamed, but:
# * echo() will be used to print some admin info into the console
#   (BT connexion, logs removed because empty, etc.);
# * echoerr() prefixes a "Erreur" before the string;
# * debug() (and bare print()) will be used to temporarily print
#   debug informations. 
#   Note: debug() adds a "DBG" before the string.
def echo(*args, **kwargs) -> None:
    print(*args, **kwargs)

def echoerr(*args, **kwargs) -> None:
    print("Erreur", *args, **kwargs)

def debug(*args, **kwargs) -> None:
    print("DBG", *args, **kwargs)

# -----------------------------------------------------------------------------
def format_split(seconds: float) -> str:
    """
    Convertit un temps en secondes vers le format m:ss.

    Exemple :
        118.4 -> 1:58
        89.9  -> 1:30
    """

    if seconds < 0.0:
        return "--:--"

    total = int(round(seconds))

    minutes = total // 60
    secondes = total % 60

    return f"{minutes}:{secondes:02}"

# -----------------------------------------------------------------------------
def format_time(seconds: float) -> str:
    """
    Convertit un temps en secondes vers le format h:mm:ss.

    Exemple :
        118.4 -> 0:01:58
        89.9  -> 0:01:30
    """
    
    if seconds <= 0.0:
        return "--:--:--"
    
    total = int(round(seconds))

    hours = total // 3600
    total -= hours * 3600

    minutes = total // 60
    secondes = total % 60

    return f"{hours}:{minutes:02}:{secondes:02}"

# -----------------------------------------------------------------------------
def format_duration(duration_seconds: float) -> str:
    """Format a duration as MM:SS or HH:MM:SS."""

    seconds = int(duration_seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return f"{minutes:02d}:{seconds:02d}"

# -----------------------------------------------------------------------------
# clamp negative values to 0
def clamp_to_zero(value: int | float) -> int | float:
    """ If value is <= 0, return 0, else return value """

    return max(0, value)

# -----------------------------------------------------------------------------
# clamp values to a max
def clamp_to_max(value: int | float, vmax: int | float) -> int | float:
    """ If value is >= vmax, return vmax, else return value """

    return min(vmax, value)

# -----------------------------------------------------------------------------
# clamp values to a min
def clamp_to_min(value: int | float, vmin: int | float) -> int | float:
    """ If value is <= vmin, return vmin, else return value """

    return max(vmin, value)
# -----------------------------------------------------------------------------
# clamp values between min and max
def clamp_between(value: int | float, minval: int | float, maxval: int | float) -> int | float:
    """ 
        If value is <= min, return min, 
        else_if value >= max return max
        else value
    """
    return max(minval, min(maxval, value))

# -----------------------------------------------------------------------------
# clamp values between min and max but on steps between
def clamp_step(
    value: int|float,
    minimum: int|float,
    maximum: int|float,
    step: int|float,
) -> int|float:

    # clamp between min & max
    value = clamp_between(
        value,
        minimum,
        maximum
    )

    # ralign so the value snap on the
    # closest subdivision based on step
    return round(
        value / step
    ) * step

# -----------------------------------------------------------------------------
# Returns a boolean answering the question:
# "Is 'value' between 'minimum' and 'maximum' ?"
# By default the lower and upper bounds are not strict
# (i.e value may be equal to minimum or to maximum).
# However the strict_min and strict_max boolean
# can be used to change the behavior at the boundaries.
def is_between(
    value: int|float,
    minimum: int|float,
    maximum: int|float,
    strict_min: bool = False,
    strict_max: bool = False
) -> bool:
    
    return (
            (strict_min and (minimum < value))
            or 
            (not strict_min and (minimum <= value))
        ) and (
            (strict_max and (value < maximum))
            or
            (not strict_max and (value <= maximum))
    )

# -----------------------------------------------------------------------------
# Linearly interpolate a point between two points
def interpolate(
    xval: int | float,
    x0: int | float, y0: int | float,
    x1: int | float, y1: int | float
) -> float:
        
    tx = float(xval - x0) / float(x1 - x0)
    return y0 + (tx * float(y1 - y0))

# -------------------------------------------------------------------------
# Trouve la couleur intermédiaire entre color1 et color2
# en fonction du ratio normalisé.
def interpolate_color(
    color1: str,
    color2: str,
    ratio: float,
) -> str:

    c1 = QColor(color1)
    c2 = QColor(color2)

    r = int( c1.red()   + (c2.red() - c1.red()) * ratio )
    g = int( c1.green() + (c2.green() - c1.green()) * ratio )
    b = int( c1.blue()  + (c2.blue() - c1.blue()) * ratio )

    return f"#{r:02x}{g:02x}{b:02x}"

# -----------------------------------------------------------------------------
# return the average in a deque
# both values must be in the same unit
def calc_average(values: deque) -> float:
    return sum(values) / len(values)

# -----------------------------------------------------------------------------
# delta = curr - prev
# both values must be in the same unit
def calc_delta(curr: int|float, prev: int|float) -> int|float:
    return curr - prev

# -----------------------------------------------------------------------------
# deltatime = curr - prev
# both values must be float
def calc_deltatime(curr: float, prev: float) -> float:
    return curr - prev

# -----------------------------------------------------------------------------
# generic metric average : metric / per_unit
# returns 0.0 if the per_unit is negative or null
def calc_metric_avg(metric: float, per_unit: int|float) -> float:
    return (
        metric / float(per_unit)
        if float(per_unit) > 0.0
         else 0.0
    )

# -----------------------------------------------------------------------------
# Calcule de l'Indice de Masse Corporelle (IMC)
# or BMI (Body Mass Index)
def bmi(
    weight_kg: float,
    height_cm: float,
) -> float:
    
    height_m = clamp_to_min(float(height_cm) / 100.0, 0.01)
    weight = clamp_to_zero(float(weight_kg))

    return weight / (height_m * height_m)

# -----------------------------------------------------------------------------
# returns the normalized progression (from 0.0 to 1.0)
# represented by 'value' (mod ref) within one 'ref'
def fractional_progress(value: int|float, ref: int|float) -> float:
    if float(ref) == 0.0:
        return 0.0
    return (float(value) % float(ref)) / float(ref)

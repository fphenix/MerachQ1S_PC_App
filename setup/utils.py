from workout.workout import Workout
from workout.step import WorkoutStep

from setup.constants import (
    INTENSITY_DICT,
    PART_DICT,
)

# -----------------------------------------------------------------------------
def load_workout(filename):

    workout = Workout(filename)

    with open(
        filename,
        "r",
        encoding="utf-8",
    ) as fr:

        for lineno, raw in enumerate(
            fr,
            start=1,
        ):

            line = raw.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            upper = line.upper()

            if upper.startswith("WORKOUT"):

                title = line[len("WORKOUT"):].strip()

                workout.title = (
                    title
                    if title
                    else "Workout"
                )

                continue

            if upper.startswith("FIELD"):

                field = line[len("FIELD"):].strip()

                workout.field = (
                    field
                    if field
                    else "Field"
                )

                continue

            parts = line.split()

            if len(parts) not in (3, 4):
                raise ValueError(
                    f"Line {lineno}: expected "
                    "'minutes cpm intensity <part>'"
                )

            try:
                minutes = float(parts[0])
                cpm = int(parts[1])
                intensity = str(parts[2])
                part = (
                    str(parts[3])
                    if len(parts) == 4
                    else None
                )

            except ValueError:
                raise ValueError(
                    f"Line {lineno}: invalid data type; "
                    "must be: int_or_float int character"
                )

            if minutes <= 0.0 or minutes > 120.0:
                raise ValueError(
                    f"Line {lineno}: duration must be "
                    "> 0 and <= 120"
                )

            if cpm <= 0 or cpm > 50:
                raise ValueError(
                    f"Line {lineno}: CPM must be "
                    "> 0 and <= 50"
                )

            if intensity not in INTENSITY_DICT:
                raise ValueError(
                    f"Line {lineno}: intensity must be "
                    "one of R, E, N, F or M"
                )

            if part is not None and part not in PART_DICT:
                raise ValueError(
                    f"Line {lineno}: part must be one "
                    f"of {PART_DICT.keys()}"
                )

            workout.steps.append(
                WorkoutStep(
                    minutes,
                    cpm,
                    intensity,
                    part,
                )
            )

    if not workout.steps:
        raise ValueError(
            "Workout is empty."
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
def echo(*args, **kwargs):
    print(*args, **kwargs)

def echoerr(*args, **kwargs):
    print("Erreur", *args, **kwargs)

def debug(*args, **kwargs):
    print("DBG", *args, **kwargs)

# -----------------------------------------------------------------------------
def format_pace(seconds: float) -> str:
    """
    Convertit un temps en secondes vers le format m:ss.

    Exemple :
        118.4 -> 1:58
        89.9  -> 1:30
    """

    if seconds <= 0:
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
    
    if seconds <= 0:
        return "--:--:--"
    
    total = int(round(seconds))

    hours = total // 3600
    total -= hours * 3600

    minutes = total // 60
    secondes = total % 60

    return f"{hours}:{minutes:02}:{secondes:02}"

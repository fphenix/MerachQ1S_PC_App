from setup.constants import (
    INTENSITY_DICT,
    PART_DICT,
    WO_KEYWORD,
)

from workout.workout import Workout
from workout.step import WorkoutStep

# -----------------------------------------------------------------------------
def load_workout(filename):

    workout = Workout(filename)

    title: str | None = None
    field: str | None = None
    pending_info: str | None = None
    pending_comment: str | None = None

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

            #
            # Commentaires "#"
            #

            if line.startswith(WO_KEYWORD["Comment"]):

                new_comment = line.lstrip(WO_KEYWORD["Comment"]).strip()

                if not new_comment:
                    print(
                        f"Warning line {lineno}: "
                        "Enmpty comments are ignored."
                    )
                    
                    continue

                if pending_comment is not None:
                    print(
                        f"Warning line {lineno}: "
                        "consecutive comments merged."
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
                        f"Warning line {lineno}: "
                        "Enmpty INFO: are ignored."
                    )

                    continue

                if pending_info is not None:
                    print(
                        f"Warning line {lineno}: "
                        "consecutive INFO: lines merged."
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
                        f"Line {lineno}: Keyword {WO_KEYWORD["Title"]} must be unique in a .wo file"
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
                        f"Line {lineno}: Keyword {WO_KEYWORD["Field"]} must be unique in a .wo file"
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
                    f"Line {lineno}: expected "
                    "'seconds cpm intensity <part>'"
                )

            try:
                duration_seconds = float(parts[0])
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
                    "must be: int_or_float int char <char_or_str>"
                )

            if duration_seconds <= 0.0 or duration_seconds > 7200.0:
                raise ValueError(
                    f"Line {lineno}: duration must be "
                    "> 0 and <= 7200"
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
                    duration_seconds= duration_seconds,
                    cpm= cpm,
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
            "Warning: INFO: at end of file "
            "is not associated with a workout step."
        )

    if pending_comment is not None:
        print(
            "Warning: comment at end of file "
            "is not associated with a workout step."
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

# -----------------------------------------------------------------------------
def format_duration(duration_seconds: float) -> str:
    """Format a duration as MM:SS or HH:MM:SS."""

    seconds = int(duration_seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return f"{minutes:02d}:{seconds:02d}"

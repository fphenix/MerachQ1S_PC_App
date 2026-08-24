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

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

# ---------------------------------------------------------------------------------

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
